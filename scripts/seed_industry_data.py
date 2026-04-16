"""
Generate synthetic industry-specific transaction data (base layer).

Creates/updates an organization with realistic suppliers, categories, and
transactions matching the target industry's procurement profile. Run
seed_demo_data on top for P2P/Contract/Policy layer.

Usage:
    python manage.py seed_industry_data --industry healthcare --org-slug uch --wipe
    python manage.py seed_industry_data --industry higher-ed --org-slug tsu --wipe
"""
import math
import random
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction as db_transaction

from apps.authentication.models import Organization
from apps.procurement.models import (
    Category,
    Contract,
    GoodsReceipt,
    Invoice,
    PolicyViolation,
    PurchaseOrder,
    PurchaseRequisition,
    SpendingPolicy,
    Supplier,
    Transaction,
)

from ._industry_profiles import PROFILES


class Command(BaseCommand):
    help = "Seed realistic industry-specific transaction base data for demo purposes."

    def add_arguments(self, parser):
        parser.add_argument("--industry", choices=list(PROFILES.keys()), required=True)
        parser.add_argument("--org-slug", type=str, required=True, help="Target organization slug")
        parser.add_argument("--org-name", type=str, help="Override org display name (default: profile name)")
        parser.add_argument("--wipe", action="store_true", help="Wipe ALL procurement data for the org before seeding")
        parser.add_argument("--seed", type=int, default=42)
        parser.add_argument("--transactions", type=int, default=25000, help="Target transaction count")
        parser.add_argument(
            "--start-year", type=int, default=2022,
            help="First calendar year for transaction dates (default 2022)",
        )
        parser.add_argument(
            "--end-date",
            type=str,
            help="Last transaction date (YYYY-MM-DD). Defaults to today.",
        )

    def handle(self, *args, **options):
        industry = options["industry"]
        profile = PROFILES[industry]
        slug = options["org_slug"]
        org_name = options["org_name"] or profile["name"]
        rng = random.Random(options["seed"])

        org, created = Organization.objects.get_or_create(
            slug=slug, defaults={"name": org_name}
        )
        if not created and org.name != org_name:
            self.stdout.write(self.style.WARNING(f"Renaming org '{org.name}' -> '{org_name}'"))
            org.name = org_name
            org.save(update_fields=["name"])
        self.stdout.write(self.style.NOTICE(
            f"Seeding {industry} data into org '{org.name}' (slug={slug})"
        ))

        end_date = date.fromisoformat(options["end_date"]) if options["end_date"] else date.today()
        start_date = date(options["start_year"], 1, 1)

        with db_transaction.atomic():
            if options["wipe"]:
                self._wipe(org)
            categories = self._create_categories(org, profile)
            suppliers_by_cat = self._create_suppliers(org, profile, rng)
            self._generate_transactions(
                org, rng, profile, categories, suppliers_by_cat,
                start_date, end_date, options["transactions"],
            )

        self.stdout.write(self.style.SUCCESS("Industry base data seeded."))
        self._print_summary(org)

    def _wipe(self, org):
        invoice_ct = Invoice.objects.filter(organization=org).delete()[0]
        gr_ct = GoodsReceipt.objects.filter(organization=org).delete()[0]
        po_ct = PurchaseOrder.objects.filter(organization=org).delete()[0]
        pr_ct = PurchaseRequisition.objects.filter(organization=org).delete()[0]
        viol_ct = PolicyViolation.objects.filter(organization=org).delete()[0]
        policy_ct = SpendingPolicy.objects.filter(organization=org).delete()[0]
        contract_ct = Contract.objects.filter(organization=org).delete()[0]
        txn_ct = Transaction.objects.filter(organization=org).delete()[0]
        cat_ct = Category.objects.filter(organization=org).delete()[0]
        sup_ct = Supplier.objects.filter(organization=org).delete()[0]
        self.stdout.write(self.style.WARNING(
            f"Wiped: invoices={invoice_ct} grs={gr_ct} pos={po_ct} prs={pr_ct} "
            f"violations={viol_ct} policies={policy_ct} contracts={contract_ct} "
            f"transactions={txn_ct} categories={cat_ct} suppliers={sup_ct}"
        ))

    def _create_categories(self, org, profile):
        categories = {}
        for cat_def in profile["categories"]:
            cat, _ = Category.objects.get_or_create(organization=org, name=cat_def["name"])
            categories[cat_def["name"]] = cat
        self.stdout.write(f"  Categories: {len(categories)}")
        return categories

    def _create_suppliers(self, org, profile, rng):
        suppliers_by_cat = {}
        all_named = set()
        for cat_def in profile["categories"]:
            names = cat_def["named_suppliers"]
            all_named.update(names)
            cat_suppliers = []
            for name in names:
                sup, _ = Supplier.objects.get_or_create(organization=org, name=name)
                cat_suppliers.append(sup)
            suppliers_by_cat[cat_def["name"]] = cat_suppliers

        tail_suppliers = []
        cities = profile["tail_cities"]
        regions = profile["tail_regions"]
        for template, count in profile["tail_supplier_templates"]:
            for _ in range(count):
                name = template.format(city=rng.choice(cities), region=rng.choice(regions))
                suffix = 1
                unique_name = name
                while unique_name in all_named:
                    suffix += 1
                    unique_name = f"{name} #{suffix}"
                all_named.add(unique_name)
                sup, _ = Supplier.objects.get_or_create(organization=org, name=unique_name)
                tail_suppliers.append(sup)

        for cat_def in profile["categories"]:
            cat_tail_count = max(10, len(tail_suppliers) // len(profile["categories"]))
            cat_tail = rng.sample(tail_suppliers, min(cat_tail_count, len(tail_suppliers)))
            suppliers_by_cat[cat_def["name"]].extend(cat_tail)

        total_suppliers = Supplier.objects.filter(organization=org).count()
        self.stdout.write(f"  Suppliers: {total_suppliers} ({len(all_named)} named, {len(tail_suppliers)} tail)")
        return suppliers_by_cat

    def _generate_transactions(self, org, rng, profile, categories, suppliers_by_cat,
                               start_date, end_date, target_count):
        seasonality = profile["seasonality"]
        cat_defs = profile["categories"]
        cat_weights = [c["spend_share"] for c in cat_defs]

        cat_txn_counts = self._allocate_transaction_counts(cat_defs, target_count)

        total_days = (end_date - start_date).days
        if total_days <= 0:
            raise CommandError("end-date must be after start-date")

        batch = []
        total_created = 0
        batch_size = 2000
        for cat_def in cat_defs:
            cat = categories[cat_def["name"]]
            suppliers = suppliers_by_cat[cat_def["name"]]
            named_count = len(cat_def["named_suppliers"])
            named_suppliers = suppliers[:named_count]
            tail_suppliers = suppliers[named_count:]

            mu = cat_def["amount_mu"]
            sigma = cat_def["amount_sigma"]
            n_txn = cat_txn_counts[cat_def["name"]]

            for _ in range(n_txn):
                txn_date = self._pick_seasonal_date(rng, start_date, total_days, seasonality)
                supplier = self._pick_supplier(rng, named_suppliers, tail_suppliers)
                amount = self._pick_amount(rng, mu, sigma)

                batch.append(Transaction(
                    organization=org, supplier=supplier, category=cat,
                    amount=amount, date=txn_date,
                ))
                if len(batch) >= batch_size:
                    Transaction.objects.bulk_create(batch, batch_size=batch_size)
                    total_created += len(batch)
                    batch.clear()

        if batch:
            Transaction.objects.bulk_create(batch, batch_size=batch_size)
            total_created += len(batch)

        self.stdout.write(f"  Transactions: {total_created}")

    def _allocate_transaction_counts(self, cat_defs, total):
        shares = [c["spend_share"] for c in cat_defs]
        normalizer = sum(shares)
        counts = {}
        remaining = total
        for i, c in enumerate(cat_defs):
            if i == len(cat_defs) - 1:
                counts[c["name"]] = remaining
            else:
                n = max(1, int(total * c["spend_share"] / normalizer))
                counts[c["name"]] = n
                remaining -= n
        return counts

    def _pick_seasonal_date(self, rng, start_date, total_days, seasonality):
        for _ in range(6):
            days_offset = rng.randint(0, total_days)
            candidate = start_date + timedelta(days=days_offset)
            month_weight = seasonality[candidate.month - 1]
            if rng.random() <= month_weight / max(seasonality):
                return candidate
        return start_date + timedelta(days=rng.randint(0, total_days))

    def _pick_supplier(self, rng, named, tail):
        roll = rng.random()
        if named and roll < 0.75:
            weights = [max(1, len(named) - i) for i in range(len(named))]
            return rng.choices(named, weights=weights)[0]
        if tail:
            return rng.choice(tail)
        return rng.choice(named)

    def _pick_amount(self, rng, mu, sigma):
        try:
            raw = rng.lognormvariate(mu, sigma)
        except OverflowError:
            raw = math.exp(mu)
        amount = round(raw, 2)
        amount = max(amount, 1.00)
        amount = min(amount, 5_000_000.00)
        return Decimal(str(amount))

    def _print_summary(self, org):
        from django.db.models import Sum
        total_spend = Transaction.objects.filter(organization=org).aggregate(s=Sum("amount"))["s"] or 0
        self.stdout.write(self.style.SUCCESS("\n=== Summary ==="))
        self.stdout.write(f"  Organization: {org.name} (slug={org.slug})")
        self.stdout.write(f"  Categories: {Category.objects.filter(organization=org).count()}")
        self.stdout.write(f"  Suppliers: {Supplier.objects.filter(organization=org).count()}")
        self.stdout.write(f"  Transactions: {Transaction.objects.filter(organization=org).count()}")
        self.stdout.write(f"  Total spend: ${float(total_spend):,.2f}")
