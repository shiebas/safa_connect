# SAFA Invoice System: Quick Reference Guide

## Invoice Types & Formats

| Type | Format | Example | Purpose |
|------|--------|---------|---------|
| Player | PLR-YYYYMMDD-XXXXXX | PLR-20250622-000001 | Player registrations |
| Supporter | SUP-YYYYMMDD-XXXXXX | SUP-20250622-000001 | Supporter memberships |
| Official | OFF-YYYYMMDD-XXXXXX | OFF-20250622-000001 | Referee/coach registrations |
| Transfer | TRF-YYYYMMDD-XXXXXX | TRF-20250622-000001 | Player transfers |

## Supporter Membership Pricing (including 15% VAT)

| Membership Type | Base Price | VAT | Total |
|----------------|------------|-----|-------|
| Premium Individual | R150.00 | R22.50 | **R172.50** |
| VIP Individual | R300.00 | R45.00 | **R345.00** |
| Family Basic | R450.00 | R67.50 | **R517.50** |
| Family Premium | R900.00 | R135.00 | **R1,035.00** |
| Family VIP | R1,500.00 | R225.00 | **R1,725.00** |

## Common Tasks

### Viewing Invoices

1. **Navigate to invoice list**: Go to `/membership/invoices/`
2. **Filter invoices**: Use status, date, and club filters
3. **View invoice details**: Click on invoice number

### Processing Payments

#### Mark Invoice as Paid (EFT/Bank Transfer)

1. Open invoice detail page
2. Click "Mark as Paid" button
3. Verify player activation for registration invoices

#### Online Card Payment

1. Open invoice detail page
2. Click "Pay Now" button
3. Complete payment through secure gateway

### Generating Reports

1. Go to `/membership/reports/outstanding-balance/`
2. Select grouping level (Club, LFA, Region, Province)
3. Apply filters as needed
4. Click "Export" for CSV, Excel, or PDF export

### Managing Overdue Invoices

1. Run maintenance command: `python manage.py update_invoice_status`
2. Navigate to outstanding balance report
3. Send reminders to entities with overdue payments

## Bank Details

- **Bank**: FNB
- **Branch**: Comm Account services cust
- **Branch Code**: 210554
- **Account Number**: 6309 8138 027
- **Reference Format**: [Invoice Reference Number]

## Support Contacts

- IT Support: support@safa.net
- System Admin: admin@safa.net

*For complete documentation, see the full training guide*
