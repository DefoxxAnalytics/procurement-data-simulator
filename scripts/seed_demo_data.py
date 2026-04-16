"""
Generate synthetic P2P, Contract, and Policy demo data for a target organization.

Usage:
    python manage.py seed_demo_data --org <slug> [--wipe] [--seed 42]
"""
import random
import uuid
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

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

N_CONTRACTS = 80
N_PRS = 500
N_POS = 400
N_GRS = 350
N_INVOICES = 300
N_VIOLATIONS = 150

DEFAULT_DEPARTMENTS = [
    "Operations", "Facilities", "IT", "Engineering", "Finance",
    "Human Resources", "Marketing", "R&D", "Logistics", "Procurement",
]
DEFAULT_COST_CENTER_PREFIX = "CC"
DEFAULT_PAYMENT_TERMS = [
    ("Net 30", 30), ("Net 45", 45), ("Net 60", 60), ("Net 15", 15), ("2/10 Net 30", 30),
]
DEFAULT_POLICIES = [
    {
        "name": "High-Value Transaction Approval",
        "description": "Transactions above $10,000 require documented approval.",
        "rules": {"max_transaction_amount": 10000, "required_approval_threshold": 10000},
    },
    {
        "name": "Contract-Backed Spend for Facilities",
        "description": "Facilities spend must be backed by an active contract.",
        "rules": {"require_contract": True, "restricted_categories": ["Facilities"]},
    },
    {
        "name": "IT Preferred Supplier Policy",
        "description": "IT category transactions should use preferred suppliers.",
        "rules": {"restricted_categories": ["IT & Telecoms", "IT Equipment"], "preferred_suppliers_required": True},
    },
    {
        "name": "Travel Expense Cap",
        "description": "Travel category per-transaction cap of $2,500.",
        "rules": {"max_transaction_amount": 2500, "restricted_categories": ["Travel"]},
    },
]


class Command(BaseCommand):
    help = "Seed synthetic P2P, contract, and policy data for demo purposes."

    def add_arguments(self, parser):
        parser.add_argument("--org", type=str, required=True, help="Organization slug")
        parser.add_argument("--wipe", action="store_true", help="Delete existing P2P/Contract/Policy data before seeding")
        parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
        parser.add_argument(
            "--industry", choices=list(PROFILES.keys()),
            help="Use industry-specific departments, cost-center prefix, payment terms, and policies.",
        )

    def handle(self, *args, **options):
        org_slug = options["org"]
        try:
            org = Organization.objects.get(slug=org_slug)
        except Organization.DoesNotExist:
            raise CommandError(f"Organization with slug '{org_slug}' not found")

        rng = random.Random(options["seed"])
        self.batch_id = f"seed-{uuid.uuid4().hex[:8]}"

        industry = options.get("industry")
        profile = PROFILES[industry] if industry else None
        self.departments = profile["departments"] if profile else DEFAULT_DEPARTMENTS
        cc_prefix = profile["cost_center_prefix"] if profile else DEFAULT_COST_CENTER_PREFIX
        self.cost_centers = [f"{cc_prefix}-{n:04d}" for n in range(1000, 1030)]
        self.payment_terms = profile["payment_terms"] if profile else DEFAULT_PAYMENT_TERMS
        self.policies_spec = profile["policies"] if profile else DEFAULT_POLICIES

        suppliers = list(
            Supplier.objects.filter(organization=org)
            .annotate(total=Sum("transactions__amount"))
            .order_by("-total")
        )
        categories = list(Category.objects.filter(organization=org))
        if not suppliers or not categories:
            raise CommandError(
                f"Org '{org_slug}' has no suppliers/categories; seed transaction data first."
            )

        self.stdout.write(self.style.NOTICE(
            f"Seeding demo data for '{org.name}' (suppliers={len(suppliers)}, categories={len(categories)})"
        ))

        with transaction.atomic():
            if options["wipe"]:
                self._wipe(org)

            contracts = self._seed_contracts(org, rng, suppliers, categories)
            policies = self._seed_policies(org)
            self._seed_policy_violations(org, rng, policies)
            prs = self._seed_prs(org, rng, suppliers, categories)
            pos = self._seed_pos(org, rng, suppliers, categories, contracts, prs)
            grs = self._seed_grs(org, rng, pos)
            self._seed_invoices(org, rng, pos, grs)

        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully."))
        self._print_summary(org)

    def _wipe(self, org):
        counts = {
            "Invoices": Invoice.objects.filter(organization=org).delete()[0],
            "GoodsReceipts": GoodsReceipt.objects.filter(organization=org).delete()[0],
            "PurchaseOrders": PurchaseOrder.objects.filter(organization=org).delete()[0],
            "PurchaseRequisitions": PurchaseRequisition.objects.filter(organization=org).delete()[0],
            "PolicyViolations": PolicyViolation.objects.filter(organization=org).delete()[0],
            "SpendingPolicies": SpendingPolicy.objects.filter(organization=org).delete()[0],
            "Contracts": Contract.objects.filter(organization=org).delete()[0],
        }
        self.stdout.write(self.style.WARNING(f"Wiped: {counts}"))

    def _seed_contracts(self, org, rng, suppliers, categories):
        top_suppliers_by_spend = list(
            Supplier.objects.filter(organization=org)
            .annotate(total=Sum("transactions__amount"))
            .order_by("-total")[:N_CONTRACTS]
        )
        today = timezone.now().date()
        contracts = []
        for i, sup in enumerate(top_suppliers_by_spend):
            roll = rng.random()
            if roll < 0.70:
                status, start, end = "active", today - timedelta(days=rng.randint(90, 600)), today + timedelta(days=rng.randint(30, 540))
            elif roll < 0.85:
                status, start, end = "expiring", today - timedelta(days=rng.randint(300, 700)), today + timedelta(days=rng.randint(5, 60))
            else:
                status, start, end = "expired", today - timedelta(days=rng.randint(400, 900)), today - timedelta(days=rng.randint(10, 120))

            supplier_spend = float(sup.total or 0)
            annual_value = Decimal(str(round(supplier_spend * rng.uniform(0.6, 1.1) / 2, 2))) if supplier_spend else Decimal("50000")
            total_value = annual_value * Decimal(str(round((end - start).days / 365.0 or 1, 2)))

            contract = Contract.objects.create(
                organization=org,
                supplier=sup,
                contract_number=f"CT-{org.slug.upper()}-{start.year}-{i + 1:04d}",
                title=f"{sup.name[:60]} Master Services Agreement",
                description=f"Multi-year MSA covering services with {sup.name[:80]}",
                total_value=total_value,
                annual_value=annual_value,
                start_date=start,
                end_date=end,
                renewal_notice_days=rng.choice([30, 60, 90, 120]),
                status=status,
                auto_renew=rng.random() < 0.35,
                upload_batch=self.batch_id,
            )
            cat_sample = rng.sample(categories, min(rng.randint(1, 3), len(categories)))
            contract.categories.set(cat_sample)
            contracts.append(contract)

        self.stdout.write(f"  Contracts: {len(contracts)}")
        return contracts

    def _seed_policies(self, org):
        created = []
        for spec in self.policies_spec:
            pol, _ = SpendingPolicy.objects.update_or_create(
                organization=org, name=spec["name"],
                defaults={"description": spec["description"], "rules": spec["rules"], "is_active": True},
            )
            created.append(pol)
        self.stdout.write(f"  Policies: {len(created)}")
        return created

    def _seed_policy_violations(self, org, rng, policies):
        candidate_txns = list(
            Transaction.objects.filter(organization=org, amount__gt=5000).order_by("-amount")[:N_VIOLATIONS * 3]
        )
        if not candidate_txns:
            self.stdout.write("  Policy violations: 0 (no high-value transactions)")
            return

        sampled = rng.sample(candidate_txns, min(N_VIOLATIONS, len(candidate_txns)))
        violation_types = ["amount_exceeded", "no_contract", "non_preferred_supplier", "approval_missing"]
        severities = ["critical", "high", "medium", "low"]
        severity_weights = [0.10, 0.25, 0.45, 0.20]

        violations = []
        for txn in sampled:
            violations.append(PolicyViolation(
                organization=org,
                transaction=txn,
                policy=rng.choice(policies),
                violation_type=rng.choices(violation_types, weights=[0.4, 0.3, 0.2, 0.1])[0],
                severity=rng.choices(severities, weights=severity_weights)[0],
                details={"amount": str(txn.amount), "supplier": txn.supplier.name, "flagged_at": str(txn.date)},
                is_resolved=rng.random() < 0.25,
            ))
        PolicyViolation.objects.bulk_create(violations, batch_size=200)
        self.stdout.write(f"  Policy violations: {len(violations)}")

    def _seed_prs(self, org, rng, suppliers, categories):
        today = timezone.now().date()
        weighted_suppliers = suppliers[:80] * 5 + suppliers[80:200] * 2 + suppliers[200:500]
        status_weights = [
            ("approved", 0.55), ("converted_to_po", 0.20), ("pending_approval", 0.10),
            ("rejected", 0.08), ("draft", 0.05), ("cancelled", 0.02),
        ]
        statuses, weights = zip(*status_weights)
        priorities = ["low", "normal", "high", "urgent"]
        priority_weights = [0.15, 0.60, 0.20, 0.05]

        prs = []
        for i in range(N_PRS):
            created = today - timedelta(days=rng.randint(1, 210))
            status = rng.choices(statuses, weights=weights)[0]
            amount = Decimal(str(round(rng.uniform(500, 50000), 2)))

            submitted = created + timedelta(days=rng.randint(0, 2)) if status != "draft" else None
            approved = submitted + timedelta(days=rng.randint(0, 7)) if submitted and status in {"approved", "converted_to_po"} else None
            rejected = submitted + timedelta(days=rng.randint(1, 5)) if submitted and status == "rejected" else None

            prs.append(PurchaseRequisition(
                organization=org,
                pr_number=f"PR-{org.slug.upper()}-{created.year}-{i + 1:05d}",
                department=rng.choice(self.departments),
                cost_center=rng.choice(self.cost_centers),
                supplier_suggested=rng.choice(weighted_suppliers),
                category=rng.choice(categories),
                description=f"Purchase request #{i + 1} for operational needs",
                estimated_amount=amount,
                status=status,
                priority=rng.choices(priorities, weights=priority_weights)[0],
                created_date=created,
                submitted_date=submitted,
                approval_date=approved,
                rejection_date=rejected,
                rejection_reason="Budget exceeded for period" if rejected else "",
                upload_batch=self.batch_id,
            ))
        PurchaseRequisition.objects.bulk_create(prs, batch_size=200)
        self.stdout.write(f"  Purchase Requisitions: {len(prs)}")
        return list(PurchaseRequisition.objects.filter(organization=org, upload_batch=self.batch_id))

    def _seed_pos(self, org, rng, suppliers, categories, contracts, prs):
        today = timezone.now().date()
        contracts_by_supplier = {}
        for c in contracts:
            contracts_by_supplier.setdefault(c.supplier_id, []).append(c)
        contract_suppliers = [s for s in suppliers if s.id in contracts_by_supplier]

        convertible_prs = [pr for pr in prs if pr.status in {"approved", "converted_to_po"}]
        rng.shuffle(convertible_prs)
        pr_pool = convertible_prs[: int(N_POS * 0.7)]

        status_weights = [
            ("fully_received", 0.35), ("partially_received", 0.15), ("acknowledged", 0.15),
            ("sent_to_supplier", 0.10), ("approved", 0.10), ("closed", 0.05),
            ("pending_approval", 0.05), ("draft", 0.03), ("cancelled", 0.02),
        ]
        statuses, weights = zip(*status_weights)

        pos_to_create = []
        for i in range(N_POS):
            linked_pr = pr_pool[i] if i < len(pr_pool) else None
            if linked_pr and linked_pr.supplier_suggested:
                supplier = linked_pr.supplier_suggested
                category = linked_pr.category
                created = linked_pr.approval_date or linked_pr.created_date
                base_amount = linked_pr.estimated_amount
            else:
                if contract_suppliers and rng.random() < 0.75:
                    supplier = rng.choice(contract_suppliers)
                else:
                    supplier = rng.choice(suppliers[:500])
                category = rng.choice(categories)
                created = today - timedelta(days=rng.randint(1, 180))
                base_amount = Decimal(str(round(rng.uniform(1000, 80000), 2)))

            amount_variance_pct = rng.uniform(0.95, 1.08)
            total = Decimal(str(round(float(base_amount) * amount_variance_pct, 2)))
            tax = total * Decimal("0.08")
            freight = Decimal(str(round(rng.uniform(0, 500), 2)))

            contract_pool = contracts_by_supplier.get(supplier.id, [])
            contract_backed = bool(contract_pool) and rng.random() < 0.80
            contract = rng.choice(contract_pool) if contract_backed else None

            status = rng.choices(statuses, weights=weights)[0]
            approval_date = created + timedelta(days=rng.randint(0, 3)) if status not in {"draft", "pending_approval"} else None
            sent_date = approval_date + timedelta(days=rng.randint(0, 2)) if approval_date and status in {"sent_to_supplier", "acknowledged", "partially_received", "fully_received", "closed"} else None
            required_date = created + timedelta(days=rng.randint(14, 60))
            promised_date = required_date + timedelta(days=rng.randint(-5, 10)) if sent_date else None

            amendment_count = rng.choices([0, 1, 2, 3], weights=[0.75, 0.17, 0.06, 0.02])[0]
            original_amount = total / Decimal(str(rng.uniform(1.0, 1.15))) if amendment_count > 0 else None

            pos_to_create.append(PurchaseOrder(
                organization=org,
                po_number=f"PO-{org.slug.upper()}-{created.year}-{i + 1:05d}",
                supplier=supplier,
                category=category,
                total_amount=total,
                tax_amount=tax,
                freight_amount=freight,
                contract=contract,
                is_contract_backed=bool(contract),
                status=status,
                created_date=created,
                approval_date=approval_date,
                sent_date=sent_date,
                required_date=required_date,
                promised_date=promised_date,
                original_amount=original_amount,
                amendment_count=amendment_count,
                requisition=linked_pr,
                upload_batch=self.batch_id,
            ))
        PurchaseOrder.objects.bulk_create(pos_to_create, batch_size=200)

        for pr in pr_pool:
            if pr.status == "approved":
                pr.status = "converted_to_po"
        PurchaseRequisition.objects.bulk_update([pr for pr in pr_pool if pr.status == "converted_to_po"], ["status"])

        self.stdout.write(f"  Purchase Orders: {len(pos_to_create)} ({sum(1 for p in pos_to_create if p.contract_id)} contract-backed)")
        return list(PurchaseOrder.objects.filter(organization=org, upload_batch=self.batch_id))

    def _seed_grs(self, org, rng, pos):
        receivable_pos = [po for po in pos if po.status in {"partially_received", "fully_received", "acknowledged", "closed"}]
        rng.shuffle(receivable_pos)
        target_pos = receivable_pos[:N_GRS]

        grs_to_create = []
        for i, po in enumerate(target_pos):
            base_date = po.sent_date or po.approval_date or po.created_date
            received = base_date + timedelta(days=rng.randint(7, 45))
            if received > timezone.now().date():
                received = timezone.now().date() - timedelta(days=rng.randint(0, 7))

            qty_ordered = Decimal(str(rng.choice([1, 5, 10, 25, 50, 100, 250])))
            if po.status == "partially_received":
                qty_received = qty_ordered * Decimal(str(round(rng.uniform(0.4, 0.85), 2)))
            else:
                qty_received = qty_ordered * Decimal(str(round(rng.uniform(0.95, 1.02), 2)))

            accept_roll = rng.random()
            if accept_roll < 0.80:
                qty_accepted, status = qty_received, "accepted"
            elif accept_roll < 0.92:
                qty_accepted, status = qty_received * Decimal("0.90"), "partial_accept"
            elif accept_roll < 0.97:
                qty_accepted, status = Decimal("0"), "rejected"
            else:
                qty_accepted, status = None, "pending"

            amount_received = po.total_amount * (qty_received / qty_ordered)

            grs_to_create.append(GoodsReceipt(
                organization=org,
                gr_number=f"GR-{org.slug.upper()}-{received.year}-{i + 1:05d}",
                purchase_order=po,
                received_date=received,
                quantity_ordered=qty_ordered,
                quantity_received=qty_received,
                quantity_accepted=qty_accepted,
                amount_received=amount_received.quantize(Decimal("0.01")),
                status=status,
                inspection_notes="Quality acceptable" if status == "accepted" else ("Minor defects on partial lot" if status == "partial_accept" else ""),
                upload_batch=self.batch_id,
            ))
        GoodsReceipt.objects.bulk_create(grs_to_create, batch_size=200)
        self.stdout.write(f"  Goods Receipts: {len(grs_to_create)}")
        return list(GoodsReceipt.objects.filter(organization=org, upload_batch=self.batch_id))

    def _seed_invoices(self, org, rng, pos, grs):
        grs_by_po = {gr.purchase_order_id: gr for gr in grs}
        today = timezone.now().date()

        pos_with_grs = [po for po in pos if po.id in grs_by_po]
        rng.shuffle(pos_with_grs)
        target_pos = pos_with_grs[:N_INVOICES]

        match_status_weights = [("3way_matched", 0.55), ("2way_matched", 0.15), ("exception", 0.20), ("unmatched", 0.10)]
        exception_types_weights = [("price_variance", 0.35), ("quantity_variance", 0.25), ("missing_gr", 0.15), ("no_po", 0.10), ("duplicate", 0.05), ("other", 0.10)]

        invoices = []
        for i, po in enumerate(target_pos):
            gr = grs_by_po[po.id]
            invoice_date = gr.received_date + timedelta(days=rng.randint(0, 14))
            if invoice_date > today:
                invoice_date = today

            term_label, term_days = rng.choice(self.payment_terms)
            received_date = invoice_date + timedelta(days=rng.randint(0, 3))
            if received_date > today:
                received_date = today
            due_date = received_date + timedelta(days=term_days)
            days_outstanding = (today - invoice_date).days

            variance_multiplier = Decimal(str(round(rng.uniform(0.97, 1.06), 4)))
            invoice_amount = (po.total_amount * variance_multiplier).quantize(Decimal("0.01"))
            tax = (invoice_amount * Decimal("0.08")).quantize(Decimal("0.01"))
            net = (invoice_amount - tax).quantize(Decimal("0.01"))

            match_labels, match_weights = zip(*match_status_weights)
            match_status = rng.choices(match_labels, weights=match_weights)[0]
            has_exception = match_status == "exception"
            exception_type = rng.choices(*zip(*exception_types_weights))[0] if has_exception else ""
            exception_amount = (invoice_amount - po.total_amount).copy_abs() if has_exception else None
            exception_resolved = has_exception and rng.random() < 0.25

            paid_date = None
            if days_outstanding < 30 and rng.random() < 0.50 and match_status in {"3way_matched", "2way_matched"}:
                paid_date = received_date + timedelta(days=rng.randint(5, min(term_days, max(days_outstanding, 6))))
            status_mapping = {
                "3way_matched": "approved",
                "2way_matched": "matched",
                "exception": "exception" if not exception_resolved else "approved",
                "unmatched": "pending_match",
            }
            status = "paid" if paid_date else status_mapping[match_status]
            approved_date = received_date + timedelta(days=rng.randint(1, 10)) if status in {"approved", "paid"} else None

            invoices.append(Invoice(
                organization=org,
                invoice_number=f"INV-{org.slug.upper()}-{invoice_date.year}-{i + 1:06d}",
                supplier=po.supplier,
                purchase_order=po,
                goods_receipt=gr,
                invoice_amount=invoice_amount,
                tax_amount=tax,
                net_amount=net,
                payment_terms=term_label,
                payment_terms_days=term_days,
                invoice_date=invoice_date,
                received_date=received_date,
                due_date=due_date,
                approved_date=approved_date,
                paid_date=paid_date,
                status=status,
                match_status=match_status,
                has_exception=has_exception,
                exception_type=exception_type,
                exception_amount=exception_amount,
                exception_resolved=exception_resolved,
                exception_notes="Auto-flagged during 3-way match" if has_exception else "",
                upload_batch=self.batch_id,
            ))
        Invoice.objects.bulk_create(invoices, batch_size=200)
        self.stdout.write(f"  Invoices: {len(invoices)}")

    def _print_summary(self, org):
        self.stdout.write(self.style.SUCCESS("\n=== Summary ==="))
        for label, qs in [
            ("Contracts", Contract.objects.filter(organization=org)),
            ("Policies", SpendingPolicy.objects.filter(organization=org)),
            ("PolicyViolations", PolicyViolation.objects.filter(organization=org)),
            ("PRs", PurchaseRequisition.objects.filter(organization=org)),
            ("POs", PurchaseOrder.objects.filter(organization=org)),
            ("GRs", GoodsReceipt.objects.filter(organization=org)),
            ("Invoices", Invoice.objects.filter(organization=org)),
        ]:
            self.stdout.write(f"  {label}: {qs.count()}")
