# SAFA Connect Invoice System: Comprehensive Training Guide

## Table of Contents

1. [Introduction](#introduction)
2. [System Overview](#system-overview)
3. [User Roles & Permissions](#user-roles-and-permissions)
4. [Invoice Workflow](#invoice-workflow)
5. [Step-by-Step Guides](#step-by-step-guides)
   - [Registering a Player with Invoice Generation](#registering-a-player-with-invoice-generation)
   - [Viewing and Managing Invoices](#viewing-and-managing-invoices)
   - [Processing Payments](#processing-payments)
   - [Generating Reports](#generating-reports)
   - [Sending Payment Reminders](#sending-payment-reminders)
6. [Administrative Functions](#administrative-functions)
   - [Bulk Operations](#bulk-operations)
   - [System Maintenance](#system-maintenance)
7. [Troubleshooting Guide](#troubleshooting-guide)
8. [Best Practices](#best-practices)
9. [Quick Reference](#quick-reference)
10. [FAQ](#frequently-asked-questions)

## Introduction

The SAFA Connect Invoice System is a comprehensive solution designed to manage financial transactions related to player registrations, transfers, and other administrative processes within the South African Football Association. This training guide provides detailed instructions on how to use the system effectively for both administrators and staff members.

## System Overview

### Purpose and Benefits

- **Financial Tracking**: Accurately track payments for all player registrations and transfers
- **Payment Facilitation**: Generate unique payment references and provide banking details
- **Reporting**: Comprehensive reporting on outstanding balances at different organizational levels
- **Automation**: Automatic invoice generation, status updates, and payment reminders
- **Integration**: Seamless integration with the player registration system

### Key Components

The invoice system consists of the following key components:

1. **Invoice Management**: Create, view, update, and track invoices
2. **Payment Processing**: Record payments against invoices
3. **Reporting Tools**: Generate financial reports and outstanding balance summaries
4. **Administrative Interface**: Configure settings and perform batch operations
5. **Notification System**: Send payment reminders automatically

## User Roles and Permissions

Different users have different access levels in the invoice system:

| Role | Permissions |
|------|-------------|
| System Administrator | Full access to all invoices and administrative functions |
| Provincial Admin | View and manage invoices for all clubs in their province |
| Regional Admin | View and manage invoices for all clubs in their region |
| LFA Admin | View and manage invoices for all clubs in their LFA |
| Club Administrator | Create invoices and manage invoices for their club only |
| Player | View their own invoices and make payments |

## Invoice Workflow

The typical lifecycle of an invoice in the system:

1. **Generation**: Invoice is created (automatically during registration or manually by admin)
2. **Notification**: Player or club is notified about the invoice
3. **Payment**: Payment is made via EFT/Bank Transfer or Credit/Debit Card
4. **Confirmation**: Payment is confirmed and invoice status is updated to PAID
5. **Activation**: Player status is automatically updated to ACTIVE after payment

### Invoice Statuses

- **PENDING**: Initial status when invoice is created
- **PAID**: Payment has been received and confirmed
- **OVERDUE**: Payment due date has passed without payment
- **CANCELED**: Invoice has been canceled by administrator
- **REFUNDED**: Payment was received but later refunded

## Step-by-Step Guides

### Registering a Player with Invoice Generation

1. **Start the Registration Process**:
   - Log in as a Club Administrator
   - Navigate to Player Registration section
   - Click "Register New Player"

2. **Enter Player Details**:
   - Fill in all required player information
   - Select appropriate registration type (Junior or Senior)
   - Complete the registration form

3. **Review Payment Information**:
   - System calculates the appropriate fee based on player type
   - Review the fee amount and payment options
   - Click "Continue to Payment"

4. **Invoice Generation**:
   - System automatically generates an invoice
   - A unique payment reference is created
   - The invoice appears in the system with status "PENDING"

5. **Payment Instructions**:
   - Banking details are displayed for EFT/Bank Transfer
   - Alternatively, online payment option is provided
   - Payment reference is prominently shown for tracking

### Viewing and Managing Invoices

1. **Access the Invoice List**:
   - Navigate to `/membership/invoices/`
   - The list shows all invoices you have permission to view
   - Default sorting is by date (newest first)

2. **Filter and Search**:
   - Use the filter panel to narrow down results:
     - Filter by status (Pending, Paid, Overdue)
     - Filter by date range
     - Filter by club (if you have access to multiple clubs)
   - Use the search box to find specific invoices by number or player name

3. **View Invoice Details**:
   - Click on an invoice number to view full details
   - The detail page shows:
     - Invoice header information
     - Player and club details
     - Line items and amounts
     - Payment status and history
     - Payment instructions (for pending invoices)

4. **Available Actions**:
   - Print Invoice: Generate a printable version
   - Download PDF: Save invoice as PDF
   - Mark as Paid: Update payment status (admin only)
   - Send Reminder: Email payment reminder to player

### Processing Payments

#### For EFT/Bank Transfers:

1. **Verify Payment Receipt**:
   - Check bank statements for received payments
   - Match payments using the payment reference

2. **Mark Invoice as Paid**:
   - Locate the invoice in the system
   - Click "Mark as Paid" button
   - System records payment date and updates status
   - Player status is automatically set to ACTIVE (for registration invoices)

#### For Online Card Payments:

1. **Online Payment Processing**:
   - Player clicks "Pay Now" on invoice detail page
   - They are redirected to secure payment gateway
   - After successful payment, system automatically updates invoice status

### Generating Reports

#### Outstanding Balance Report:

1. **Access the Report**:
   - Navigate to `/membership/reports/outstanding-balance/`
   - The report page loads with default settings

2. **Configure Report Options**:
   - Select grouping level:
     - By Club
     - By Local Football Association (LFA)
     - By Region
     - By Province
   - Filter by days overdue (Any, 30+, 60+, 90+ days)
   - Choose sorting order (Amount, Name, Aging)

3. **Analyze Results**:
   - View summary statistics at top of page
   - See aging analysis (30/60/90 days)
   - Drill down into specific entities

4. **Export Options**:
   - Click "Export" and select format:
     - CSV: For data analysis
     - Excel: For spreadsheet processing
     - PDF: For printing and sharing

### Sending Payment Reminders

1. **From Outstanding Balance Report**:
   - Navigate to outstanding balance report
   - Locate the club or entity with outstanding balances
   - Click "Send Reminders" button next to entity
   - Confirm to send emails to all players with outstanding invoices

2. **From Individual Invoice**:
   - Open specific invoice detail page
   - Click "Send Reminder" button
   - System sends email to player with invoice details and payment instructions

## Administrative Functions

### Bulk Operations

The admin interface allows performing actions on multiple invoices at once:

1. **Access Admin Interface**:
   - Navigate to `/admin/membership/invoice/`
   - Log in with administrator credentials

2. **Select Multiple Invoices**:
   - Use checkboxes to select target invoices
   - Filter list first to show only relevant invoices

3. **Choose Action**:
   - From dropdown, select desired action:
     - Mark as Paid
     - Mark as Overdue
     - Export Selected
   - Click "Go" to execute the action

4. **Confirm Results**:
   - System displays confirmation message
   - Records are updated accordingly

### System Maintenance

#### Regular Tasks

1. **Update Overdue Invoices**:
   - Run daily to automatically flag overdue invoices:
   ```bash
   python manage.py update_invoice_status
   ```

2. **Send Notifications**:
   - Include notification parameter to send emails:
   ```bash
   python manage.py update_invoice_status --notify
   ```

3. **Database Backup**:
   - Regular backup of invoice data:
   ```bash
   python manage.py dumpdata membership.invoice membership.invoiceitem > invoice_backup.json
   ```

## Troubleshooting Guide

### Common Issues and Solutions

#### Invoice Not Generated During Registration

**Symptoms**:
- Registration completed but no invoice appears
- Player record created but payment status unclear

**Solutions**:
1. Check registration completion status in logs
2. Verify the player record was created correctly
3. Manually create invoice if necessary through admin interface
4. Check for errors in the transaction process

#### Payment Not Reflecting

**Symptoms**:
- Payment was made but invoice still shows as PENDING
- Money received in bank account but not matched to invoice

**Solutions**:
1. Verify payment reference was used correctly
2. Check bank statement for the exact amount
3. Manually mark invoice as paid with the correct payment date
4. Update player status if not automatically activated

#### Export Functionality Not Working

**Symptoms**:
- Error when attempting to export reports or invoices
- PDF generation fails

**Solutions**:
1. Ensure WeasyPrint is installed correctly:
   ```bash
   pip install WeasyPrint
   ```
2. Check file permissions in output directories
3. Verify required dependencies are installed
4. For large exports, increase timeout settings

### Error Messages and Meanings

| Error Message | Possible Cause | Solution |
|---------------|----------------|----------|
| "PDF generation not available" | WeasyPrint not installed | Install WeasyPrint package |
| "Permission denied" | User lacks required permissions | Contact administrator to adjust permissions |
| "Invalid payment amount" | Amount doesn't match invoice | Verify payment details and try again |
| "Player registration not found" | Missing relationship | Re-link invoice to correct registration |

## Best Practices

1. **Payment References**:
   - Always use the system-generated payment reference for bank transfers
   - Include instructions for players to include reference in payment

2. **Regular Reconciliation**:
   - Match bank statements with invoices weekly
   - Follow up on unidentified payments promptly

3. **Overdue Management**:
   - Run the overdue update command daily
   - Send reminders for payments more than 14 days overdue

4. **Documentation**:
   - Keep records of manual payment confirmations
   - Document any special cases or exceptions

5. **User Training**:
   - Ensure all administrators understand the invoice lifecycle
   - Provide refresher training for seasonal registration periods

## Quick Reference

### Key URLs

- **Invoice List**: `/membership/invoices/`
- **Invoice Detail**: `/membership/invoices/{uuid}/`
- **Outstanding Report**: `/membership/reports/outstanding-balance/`
- **Admin Interface**: `/admin/membership/invoice/`

### Banking Details for EFT Payments

- **Bank**: FNB
- **Branch**: Comm Account services cust
- **Branch Code**: 210554
- **Account Type**: Current account
- **Account Number**: 6309 8138 027
- **Reference**: [Unique payment reference]

### Support Contacts

For technical support with the invoicing system:
- **Primary**: IT Support at support@safa.net
- **Secondary**: System Administrator at admin@safa.net

## Frequently Asked Questions

**Q: How long does it take for a payment to be reflected in the system?**  
A: For online payments, the system updates immediately. For EFT/bank transfers, it depends on when an administrator verifies and marks the payment as received, typically within 1-2 business days.

**Q: Can I create an invoice for something other than registration?**  
A: Yes, the system supports different invoice types including Registration, Transfer, Renewal, and Other. Administrators can create custom invoices through the admin interface.

**Q: What happens if a player pays more than the invoice amount?**  
A: The system will mark the invoice as paid. The extra amount should be documented in the invoice notes, and can be either refunded or credited to future transactions.

**Q: Can I edit an invoice after it's been created?**  
A: Basic invoice details can be edited by administrators through the admin interface, but the invoice number and core financial information should not be changed after creation for audit purposes.

**Q: How do I handle refunds?**  
A: Process the refund through your banking system, then update the invoice status to "REFUNDED" in the admin interface, adding notes about the refund date and reason.

---

*Last Updated: June 12, 2025*  
*For the latest version of this documentation, please contact the SAFA IT Department.*
