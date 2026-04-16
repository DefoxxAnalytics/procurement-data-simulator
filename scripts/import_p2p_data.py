"""
Management command to import P2P (Procure-to-Pay) data from CSV files.

Supports importing:
- Purchase Requisitions (PR)
- Purchase Orders (PO)
- Goods Receipts (GR)
- Invoices

Usage:
    python manage.py import_p2p_data --org-slug <slug> --type <type> --file <path>

Examples:
    python manage.py import_p2p_data --org-slug acme --type pr --file pr_data.csv
    python manage.py import_p2p_data --org-slug acme --type po --file po_data.csv
    python manage.py import_p2p_data --org-slug acme --type gr --file gr_data.csv
    python manage.py import_p2p_data --org-slug acme --type invoice --file invoice_data.csv
"""
import csv
import uuid
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.authentication.models import Organization
from apps.procurement.models import (
    PurchaseRequisition, PurchaseOrder, GoodsReceipt, Invoice,
    Supplier, Category
)


class Command(BaseCommand):
    help = 'Import P2P data from CSV files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--org-slug',
            type=str,
            required=True,
            help='Organization slug to import data into'
        )
        parser.add_argument(
            '--type',
            type=str,
            required=True,
            choices=['pr', 'po', 'gr', 'invoice'],
            help='Type of P2P document to import: pr, po, gr, invoice'
        )
        parser.add_argument(
            '--file',
            type=str,
            required=True,
            help='Path to the CSV file to import'
        )
        parser.add_argument(
            '--skip-errors',
            action='store_true',
            help='Skip rows with errors instead of failing'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Validate without importing'
        )
        parser.add_argument(
            '--batch-id',
            type=str,
            help='Custom batch ID for tracking this import'
        )

    def handle(self, *args, **options):
        org_slug = options['org_slug']
        doc_type = options['type']
        file_path = options['file']
        skip_errors = options['skip_errors']
        dry_run = options['dry_run']
        batch_id = options.get('batch_id') or str(uuid.uuid4())

        # Get organization
        try:
            organization = Organization.objects.get(slug=org_slug, is_active=True)
        except Organization.DoesNotExist:
            raise CommandError(f'Organization with slug "{org_slug}" not found')

        self.stdout.write(f'Importing {doc_type.upper()} data for organization: {organization.name}')
        self.stdout.write(f'Batch ID: {batch_id}')

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No data will be imported'))

        # Read CSV file
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
        except FileNotFoundError:
            raise CommandError(f'File not found: {file_path}')
        except Exception as e:
            raise CommandError(f'Error reading file: {e}')

        self.stdout.write(f'Found {len(rows)} rows in CSV')

        # Import based on type
        if doc_type == 'pr':
            stats = self._import_purchase_requisitions(
                rows, organization, batch_id, skip_errors, dry_run
            )
        elif doc_type == 'po':
            stats = self._import_purchase_orders(
                rows, organization, batch_id, skip_errors, dry_run
            )
        elif doc_type == 'gr':
            stats = self._import_goods_receipts(
                rows, organization, batch_id, skip_errors, dry_run
            )
        elif doc_type == 'invoice':
            stats = self._import_invoices(
                rows, organization, batch_id, skip_errors, dry_run
            )

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Import complete:'))
        self.stdout.write(f'  Successful: {stats["successful"]}')
        self.stdout.write(f'  Failed: {stats["failed"]}')
        self.stdout.write(f'  Skipped: {stats["skipped"]}')

        if stats['errors']:
            self.stdout.write(self.style.WARNING(f'\nErrors ({len(stats["errors"])}):'))
            for error in stats['errors'][:20]:  # Show first 20 errors
                self.stdout.write(f'  Row {error["row"]}: {error["message"]}')
            if len(stats['errors']) > 20:
                self.stdout.write(f'  ... and {len(stats["errors"]) - 20} more errors')

    def _parse_date(self, date_str):
        """Parse date from various formats."""
        if not date_str or date_str.strip() == '':
            return None

        formats = [
            '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y',
            '%m-%d-%Y', '%d-%m-%Y', '%Y/%m/%d'
        ]
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt).date()
            except ValueError:
                continue
        return None

    def _parse_decimal(self, value_str):
        """Parse decimal from string, handling currency symbols."""
        if not value_str or value_str.strip() == '':
            return Decimal('0')
        try:
            clean = value_str.strip().replace('$', '').replace(',', '')
            return Decimal(clean)
        except InvalidOperation:
            return None

    def _get_or_create_supplier(self, name, organization):
        """Get or create supplier by name."""
        if not name or name.strip() == '':
            return None
        name = name.strip()
        supplier, _ = Supplier.objects.get_or_create(
            organization=organization,
            name__iexact=name,
            defaults={'name': name}
        )
        return supplier

    def _get_or_create_category(self, name, organization):
        """Get or create category by name."""
        if not name or name.strip() == '':
            return None
        name = name.strip()
        category, _ = Category.objects.get_or_create(
            organization=organization,
            name__iexact=name,
            defaults={'name': name}
        )
        return category

    def _import_purchase_requisitions(self, rows, organization, batch_id, skip_errors, dry_run):
        """
        Import Purchase Requisitions from CSV.

        Expected columns:
        - pr_number (required)
        - department
        - cost_center
        - description
        - estimated_amount (required)
        - currency
        - budget_code
        - status (draft, pending_approval, approved, rejected, converted_to_po, cancelled)
        - priority (low, medium, high, critical)
        - created_date
        - submitted_date
        - approval_date
        - supplier_suggested
        - category
        """
        stats = {'successful': 0, 'failed': 0, 'skipped': 0, 'errors': []}

        for row_num, row in enumerate(rows, start=2):
            try:
                pr_number = row.get('pr_number', '').strip()
                if not pr_number:
                    if skip_errors:
                        stats['failed'] += 1
                        stats['errors'].append({'row': row_num, 'message': 'Missing pr_number'})
                        continue
                    raise CommandError(f'Row {row_num}: Missing pr_number')

                # Check for duplicates
                if PurchaseRequisition.objects.filter(
                    organization=organization,
                    pr_number=pr_number
                ).exists():
                    stats['skipped'] += 1
                    continue

                estimated_amount = self._parse_decimal(row.get('estimated_amount', ''))
                if estimated_amount is None:
                    if skip_errors:
                        stats['failed'] += 1
                        stats['errors'].append({'row': row_num, 'message': 'Invalid estimated_amount'})
                        continue
                    raise CommandError(f'Row {row_num}: Invalid estimated_amount')

                if not dry_run:
                    with transaction.atomic():
                        supplier = self._get_or_create_supplier(
                            row.get('supplier_suggested', ''), organization
                        )
                        category = self._get_or_create_category(
                            row.get('category', ''), organization
                        )

                        PurchaseRequisition.objects.create(
                            organization=organization,
                            pr_number=pr_number,
                            department=row.get('department', '').strip(),
                            cost_center=row.get('cost_center', '').strip(),
                            description=row.get('description', '').strip(),
                            estimated_amount=estimated_amount,
                            currency=row.get('currency', 'USD').strip() or 'USD',
                            budget_code=row.get('budget_code', '').strip(),
                            status=row.get('status', 'draft').strip() or 'draft',
                            priority=row.get('priority', 'medium').strip() or 'medium',
                            created_date=self._parse_date(row.get('created_date', '')) or datetime.now().date(),
                            submitted_date=self._parse_date(row.get('submitted_date', '')),
                            approval_date=self._parse_date(row.get('approval_date', '')),
                            supplier_suggested=supplier,
                            category=category,
                            upload_batch=batch_id
                        )

                stats['successful'] += 1

            except Exception as e:
                if skip_errors:
                    stats['failed'] += 1
                    stats['errors'].append({'row': row_num, 'message': str(e)})
                else:
                    raise CommandError(f'Row {row_num}: {e}')

        return stats

    def _import_purchase_orders(self, rows, organization, batch_id, skip_errors, dry_run):
        """
        Import Purchase Orders from CSV.

        Expected columns:
        - po_number (required)
        - supplier_name (required)
        - total_amount (required)
        - currency
        - tax_amount
        - freight_amount
        - status
        - category
        - created_date
        - approval_date
        - sent_date
        - required_date
        - promised_date
        - pr_number (links to existing PR)
        - is_contract_backed
        """
        stats = {'successful': 0, 'failed': 0, 'skipped': 0, 'errors': []}

        for row_num, row in enumerate(rows, start=2):
            try:
                po_number = row.get('po_number', '').strip()
                if not po_number:
                    if skip_errors:
                        stats['failed'] += 1
                        stats['errors'].append({'row': row_num, 'message': 'Missing po_number'})
                        continue
                    raise CommandError(f'Row {row_num}: Missing po_number')

                # Check for duplicates
                if PurchaseOrder.objects.filter(
                    organization=organization,
                    po_number=po_number
                ).exists():
                    stats['skipped'] += 1
                    continue

                supplier_name = row.get('supplier_name', '').strip()
                if not supplier_name:
                    if skip_errors:
                        stats['failed'] += 1
                        stats['errors'].append({'row': row_num, 'message': 'Missing supplier_name'})
                        continue
                    raise CommandError(f'Row {row_num}: Missing supplier_name')

                total_amount = self._parse_decimal(row.get('total_amount', ''))
                if total_amount is None:
                    if skip_errors:
                        stats['failed'] += 1
                        stats['errors'].append({'row': row_num, 'message': 'Invalid total_amount'})
                        continue
                    raise CommandError(f'Row {row_num}: Invalid total_amount')

                if not dry_run:
                    with transaction.atomic():
                        supplier = self._get_or_create_supplier(supplier_name, organization)
                        category = self._get_or_create_category(
                            row.get('category', ''), organization
                        )

                        # Link to existing PR if provided
                        requisition = None
                        pr_number = row.get('pr_number', '').strip()
                        if pr_number:
                            requisition = PurchaseRequisition.objects.filter(
                                organization=organization,
                                pr_number=pr_number
                            ).first()

                        is_contract_backed = row.get('is_contract_backed', '').strip().lower() in ('true', 'yes', '1')

                        PurchaseOrder.objects.create(
                            organization=organization,
                            po_number=po_number,
                            supplier=supplier,
                            category=category,
                            total_amount=total_amount,
                            currency=row.get('currency', 'USD').strip() or 'USD',
                            tax_amount=self._parse_decimal(row.get('tax_amount', '')) or Decimal('0'),
                            freight_amount=self._parse_decimal(row.get('freight_amount', '')) or Decimal('0'),
                            status=row.get('status', 'draft').strip() or 'draft',
                            created_date=self._parse_date(row.get('created_date', '')) or datetime.now().date(),
                            approval_date=self._parse_date(row.get('approval_date', '')),
                            sent_date=self._parse_date(row.get('sent_date', '')),
                            required_date=self._parse_date(row.get('required_date', '')),
                            promised_date=self._parse_date(row.get('promised_date', '')),
                            requisition=requisition,
                            is_contract_backed=is_contract_backed,
                            original_amount=total_amount,
                            upload_batch=batch_id
                        )

                stats['successful'] += 1

            except Exception as e:
                if skip_errors:
                    stats['failed'] += 1
                    stats['errors'].append({'row': row_num, 'message': str(e)})
                else:
                    raise CommandError(f'Row {row_num}: {e}')

        return stats

    def _import_goods_receipts(self, rows, organization, batch_id, skip_errors, dry_run):
        """
        Import Goods Receipts from CSV.

        Expected columns:
        - gr_number (required)
        - po_number (required, links to existing PO)
        - received_date (required)
        - quantity_ordered
        - quantity_received (required)
        - quantity_accepted
        - amount_received
        - status
        - inspection_notes
        """
        stats = {'successful': 0, 'failed': 0, 'skipped': 0, 'errors': []}

        for row_num, row in enumerate(rows, start=2):
            try:
                gr_number = row.get('gr_number', '').strip()
                if not gr_number:
                    if skip_errors:
                        stats['failed'] += 1
                        stats['errors'].append({'row': row_num, 'message': 'Missing gr_number'})
                        continue
                    raise CommandError(f'Row {row_num}: Missing gr_number')

                # Check for duplicates
                if GoodsReceipt.objects.filter(
                    organization=organization,
                    gr_number=gr_number
                ).exists():
                    stats['skipped'] += 1
                    continue

                # Find linked PO
                po_number = row.get('po_number', '').strip()
                if not po_number:
                    if skip_errors:
                        stats['failed'] += 1
                        stats['errors'].append({'row': row_num, 'message': 'Missing po_number'})
                        continue
                    raise CommandError(f'Row {row_num}: Missing po_number')

                purchase_order = PurchaseOrder.objects.filter(
                    organization=organization,
                    po_number=po_number
                ).first()

                if not purchase_order:
                    if skip_errors:
                        stats['failed'] += 1
                        stats['errors'].append({'row': row_num, 'message': f'PO not found: {po_number}'})
                        continue
                    raise CommandError(f'Row {row_num}: PO not found: {po_number}')

                received_date = self._parse_date(row.get('received_date', ''))
                if not received_date:
                    if skip_errors:
                        stats['failed'] += 1
                        stats['errors'].append({'row': row_num, 'message': 'Invalid received_date'})
                        continue
                    raise CommandError(f'Row {row_num}: Invalid received_date')

                quantity_received = self._parse_decimal(row.get('quantity_received', ''))
                if quantity_received is None:
                    if skip_errors:
                        stats['failed'] += 1
                        stats['errors'].append({'row': row_num, 'message': 'Invalid quantity_received'})
                        continue
                    raise CommandError(f'Row {row_num}: Invalid quantity_received')

                if not dry_run:
                    with transaction.atomic():
                        GoodsReceipt.objects.create(
                            organization=organization,
                            gr_number=gr_number,
                            purchase_order=purchase_order,
                            received_date=received_date,
                            quantity_ordered=self._parse_decimal(row.get('quantity_ordered', '')) or quantity_received,
                            quantity_received=quantity_received,
                            quantity_accepted=self._parse_decimal(row.get('quantity_accepted', '')) or quantity_received,
                            amount_received=self._parse_decimal(row.get('amount_received', '')) or Decimal('0'),
                            status=row.get('status', 'received').strip() or 'received',
                            inspection_notes=row.get('inspection_notes', '').strip(),
                            upload_batch=batch_id
                        )

                stats['successful'] += 1

            except Exception as e:
                if skip_errors:
                    stats['failed'] += 1
                    stats['errors'].append({'row': row_num, 'message': str(e)})
                else:
                    raise CommandError(f'Row {row_num}: {e}')

        return stats

    def _import_invoices(self, rows, organization, batch_id, skip_errors, dry_run):
        """
        Import Invoices from CSV.

        Expected columns:
        - invoice_number (required)
        - supplier_name (required)
        - invoice_amount (required)
        - invoice_date (required)
        - due_date (required)
        - currency
        - tax_amount
        - net_amount
        - payment_terms
        - payment_terms_days
        - status
        - match_status
        - po_number (links to existing PO)
        - gr_number (links to existing GR)
        - received_date
        - approved_date
        - paid_date
        - has_exception
        - exception_type
        - exception_amount
        - exception_notes
        """
        stats = {'successful': 0, 'failed': 0, 'skipped': 0, 'errors': []}

        for row_num, row in enumerate(rows, start=2):
            try:
                invoice_number = row.get('invoice_number', '').strip()
                if not invoice_number:
                    if skip_errors:
                        stats['failed'] += 1
                        stats['errors'].append({'row': row_num, 'message': 'Missing invoice_number'})
                        continue
                    raise CommandError(f'Row {row_num}: Missing invoice_number')

                # Check for duplicates
                if Invoice.objects.filter(
                    organization=organization,
                    invoice_number=invoice_number
                ).exists():
                    stats['skipped'] += 1
                    continue

                supplier_name = row.get('supplier_name', '').strip()
                if not supplier_name:
                    if skip_errors:
                        stats['failed'] += 1
                        stats['errors'].append({'row': row_num, 'message': 'Missing supplier_name'})
                        continue
                    raise CommandError(f'Row {row_num}: Missing supplier_name')

                invoice_amount = self._parse_decimal(row.get('invoice_amount', ''))
                if invoice_amount is None:
                    if skip_errors:
                        stats['failed'] += 1
                        stats['errors'].append({'row': row_num, 'message': 'Invalid invoice_amount'})
                        continue
                    raise CommandError(f'Row {row_num}: Invalid invoice_amount')

                invoice_date = self._parse_date(row.get('invoice_date', ''))
                if not invoice_date:
                    if skip_errors:
                        stats['failed'] += 1
                        stats['errors'].append({'row': row_num, 'message': 'Invalid invoice_date'})
                        continue
                    raise CommandError(f'Row {row_num}: Invalid invoice_date')

                due_date = self._parse_date(row.get('due_date', ''))
                if not due_date:
                    if skip_errors:
                        stats['failed'] += 1
                        stats['errors'].append({'row': row_num, 'message': 'Invalid due_date'})
                        continue
                    raise CommandError(f'Row {row_num}: Invalid due_date')

                if not dry_run:
                    with transaction.atomic():
                        supplier = self._get_or_create_supplier(supplier_name, organization)

                        # Link to existing PO if provided
                        purchase_order = None
                        po_number = row.get('po_number', '').strip()
                        if po_number:
                            purchase_order = PurchaseOrder.objects.filter(
                                organization=organization,
                                po_number=po_number
                            ).first()

                        # Link to existing GR if provided
                        goods_receipt = None
                        gr_number = row.get('gr_number', '').strip()
                        if gr_number:
                            goods_receipt = GoodsReceipt.objects.filter(
                                organization=organization,
                                gr_number=gr_number
                            ).first()

                        has_exception = row.get('has_exception', '').strip().lower() in ('true', 'yes', '1')

                        Invoice.objects.create(
                            organization=organization,
                            invoice_number=invoice_number,
                            supplier=supplier,
                            invoice_amount=invoice_amount,
                            invoice_date=invoice_date,
                            due_date=due_date,
                            currency=row.get('currency', 'USD').strip() or 'USD',
                            tax_amount=self._parse_decimal(row.get('tax_amount', '')) or Decimal('0'),
                            net_amount=self._parse_decimal(row.get('net_amount', '')) or invoice_amount,
                            payment_terms=row.get('payment_terms', '').strip(),
                            payment_terms_days=int(row.get('payment_terms_days', '30') or '30'),
                            status=row.get('status', 'received').strip() or 'received',
                            match_status=row.get('match_status', 'unmatched').strip() or 'unmatched',
                            purchase_order=purchase_order,
                            goods_receipt=goods_receipt,
                            received_date=self._parse_date(row.get('received_date', '')) or invoice_date,
                            approved_date=self._parse_date(row.get('approved_date', '')),
                            paid_date=self._parse_date(row.get('paid_date', '')),
                            has_exception=has_exception,
                            exception_type=row.get('exception_type', '').strip() if has_exception else '',
                            exception_amount=self._parse_decimal(row.get('exception_amount', '')) if has_exception else None,
                            exception_notes=row.get('exception_notes', '').strip() if has_exception else '',
                            upload_batch=batch_id
                        )

                stats['successful'] += 1

            except Exception as e:
                if skip_errors:
                    stats['failed'] += 1
                    stats['errors'].append({'row': row_num, 'message': str(e)})
                else:
                    raise CommandError(f'Row {row_num}: {e}')

        return stats
