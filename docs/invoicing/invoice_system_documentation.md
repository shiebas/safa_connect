# SAFA Invoice System Documentation

## Overview

The SAFA Global Invoice System provides comprehensive functionality for tracking payments related to player registrations, transfers, supporter memberships, and other financial transactions. The system automatically generates invoices for various registration types, tracks payment statuses, and generates reports on outstanding balances.

This documentation serves as a training guide for administrators and staff who will be using the invoice system.

**Note**: For detailed information about the Supporter Invoice System, see the dedicated [Supporter Invoice System Documentation](supporter_invoice_system.md).

## Table of Contents

1. [System Overview](#system-overview)
2. [Core Components](#core-components)
3. [Invoice Types](#invoice-types)
4. [Invoice Generation Process](#invoice-generation-process)
5. [Payment Tracking](#payment-tracking)
6. [Reporting](#reporting)
7. [Administrative Tasks](#administrative-tasks)
8. [Troubleshooting](#troubleshooting)
9. [API Integration](#api-integration)

## System Overview

The SAFA Invoice System handles multiple types of registrations and payments:

- **Player Registrations**: Junior and Senior player membership fees
- **Official Registrations**: Referee and coach certification fees  
- **Supporter Memberships**: Individual and family supporter packages
- **Transfers**: Player transfer fees between clubs
- **Renewals**: Annual membership renewals
- **Other**: Miscellaneous fees and charges

## Invoice Types

### 1. Player Registration Invoices
- **Format**: `PLR-YYYYMMDD-XXXXXX`
- **Scope**: Junior and Senior player registrations
- **Integration**: Automatic during player registration process

### 2. Supporter Registration Invoices
- **Format**: `SUP-YYYYMMDD-XXXXXX`
- **Scope**: All supporter membership tiers
- **Integration**: Automatic during supporter registration
- **Special Features**: Geolocation integration, family packages
- **Pricing**: R150 - R1,500 (plus 15% VAT)

### 3. Official Registration Invoices
- **Format**: `OFF-YYYYMMDD-XXXXXX`
- **Scope**: Referee and coach registrations
- **Integration**: Manual and automatic generation

### 4. Transfer Invoices
- **Format**: `TRF-YYYYMMDD-XXXXXX`
- **Scope**: Player transfers between clubs
- **Integration**: Generated during transfer process

## Core Components

### Invoice Model

The invoice system is built around the `Invoice` model which contains the following key information:

- **Invoice Number**: Automatically generated unique identifier (e.g., `INV-2025-000001`)
- **Reference**: Payment reference code for bank transfers
- **Amount**: Total amount due in ZAR
- **Status**: Current payment status (`PENDING`, `PAID`, `OVERDUE`, `CANCELED`, `REFUNDED`)
- **Player**: The player associated with the invoice
- **Club**: The club associated with the invoice
- **Issue Date**: When the invoice was created
- **Due Date**: When payment is due (defaults to 14 days after issue)
- **Payment Method**: How payment should be made (`EFT`, `CARD`, `CASH`, `OTHER`)

### InvoiceItem Model

Each invoice can contain one or more line items represented by the `InvoiceItem` model:

- **Description**: Description of the item
- **Quantity**: Number of units
- **Unit Price**: Price per unit in ZAR
- **Sub Total**: Calculated total for the line item

## Invoice Generation Process

### Automatic Generation During Registration

1. When a club administrator registers a new player, an invoice is automatically generated
2. The system uses the membership type (Junior or Senior) to determine the fee amount
3. A unique payment reference is generated for tracking the payment
4. The invoice is initially set to `PENDING` status

### Manual Invoice Creation (Admin)

Administrators can also create invoices manually through the admin interface:

1. Navigate to the admin panel (`/admin/membership/invoice/`)
2. Click "Add Invoice"
3. Fill in the required fields
4. Add one or more invoice items
5. Save the invoice

## Payment Tracking

### Payment Methods

The system supports multiple payment methods:

1. **EFT/Bank Transfer**:
   - Player/club transfers money to SAFA bank account
   - Uses the payment reference to identify the transaction
   - Administrator marks the invoice as paid after verifying the payment

2. **Credit/Debit Card**:
   - Online payment through payment gateway
   - System automatically marks the invoice as paid upon successful payment
   - Player receives immediate confirmation

### Marking Invoices as Paid

Administrators can mark invoices as paid:

1. From the invoice list view, click on the invoice
2. Click the "Mark as Paid" button
3. The system will update the status to `PAID` and record the payment date
4. If the invoice is for player registration, the player will be automatically activated

### Overdue Payments

The system automatically flags overdue payments:

1. A scheduled task runs daily to check for invoices past their due date
2. Such invoices are marked as `OVERDUE`
3. Notification emails can be sent to players and club administrators
4. Reports highlight overdue payments for follow-up

## Reporting

### Invoice List

The invoice list provides a comprehensive view of all invoices:

1. Navigate to `/membership/invoices/`
2. Use filters to narrow down by status, date range, or club
3. View summary statistics at the top of the page
4. Export data in CSV, Excel, or PDF format

### Outstanding Balance Report

A key feature is the ability to generate outstanding balance reports:

1. Navigate to `/membership/reports/outstanding-balance/`
2. Select grouping level (Club, LFA, Region, Province)
3. Filter by days overdue if needed
4. View aging analysis (30/60/90 days)
5. Export the report in various formats
6. Send payment reminders directly from the report page

## Administrative Tasks

### Bulk Actions

From the admin interface, administrators can perform bulk actions:

1. Select multiple invoices
2. Choose "Mark as paid" or "Mark as overdue" from the actions dropdown
3. Click "Go" to apply the action to all selected invoices

### Payment Reminders

The system can send payment reminders:

1. Navigate to the outstanding balance report
2. Click "Send Reminders" next to a club or region
3. Confirm to send reminder emails to all players with outstanding balances

### System Maintenance

Regular maintenance tasks:

1. Run the `update_invoice_status` management command daily to flag overdue invoices:
   ```bash
   python manage.py update_invoice_status
   ```

2. To include email notifications:
   ```bash
   python manage.py update_invoice_status --notify
   ```

## Troubleshooting

### Common Issues

1. **Invoice not appearing for a new registration**:
   - Check if transaction completed successfully
   - Verify the player record was created
   - Check for exceptions in the logs

2. **Payment marked as paid but player not activated**:
   - Ensure the player registration record exists
   - Check if the status update was processed correctly
   - Manually activate the player if necessary

3. **Export not working**:
   - Ensure WeasyPrint is installed for PDF generation
   - Check file permissions for output directories

### Support Contacts

For technical support with the invoicing system:
- Primary: IT Support at support@safa.net
- Secondary: System Administrator at admin@safa.net

## API Integration

For developers, the invoice system provides API endpoints for integration with other systems:

1. List all invoices: `GET /api/v1/invoices/`
2. Invoice details: `GET /api/v1/invoices/{uuid}/`
3. Mark as paid: `POST /api/v1/invoices/{uuid}/mark-paid/`
4. Create invoice: `POST /api/v1/invoices/`

*Note: Authentication and proper permissions are required for all API endpoints.*

---

## Quick Reference Guide

### Key URLs

- Invoice List: `/membership/invoices/`
- Invoice Detail: `/membership/invoices/{uuid}/`
- Outstanding Report: `/membership/reports/outstanding-balance/`
- Admin Interface: `/admin/membership/invoice/`

### Payment Statuses

- `PENDING`: Payment has not been received yet
- `PAID`: Payment has been received and confirmed
- `OVERDUE`: Payment is past due date and has not been received
- `CANCELED`: Invoice has been canceled
- `REFUNDED`: Payment was received but later refunded

### Bank Details for EFT Payments

- Bank: FNB
- Branch: Comm Account services cust
- Branch Code: 210554
- Account Type: Current account
- Account Number: 6309 8138 027
- Reference: [Unique payment reference]
