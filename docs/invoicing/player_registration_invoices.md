# Player Registration Invoice System

## Overview

The SAFA Global system now automatically generates invoices when registering new players. The invoice amount is determined by the player's age:

- Junior players (under 18): R100
- Senior players (18 and above): R200

Players cannot be approved until their registration invoice is paid.

## How it Works

### Invoice Creation

1. When a club administrator registers a new player, an invoice is automatically generated.
2. The system determines whether the player is a junior or senior based on their date of birth.
3. The appropriate registration fee (R100 for juniors, R200 for seniors) is set on the invoice.
4. The invoice status is set to "PENDING" by default.
5. A unique reference number is generated for the payment.

### Player Approval Process

1. Club administrators can view pending player registrations in the approval list.
2. Players with unpaid invoices are clearly marked with an "Unpaid" badge.
3. When attempting to approve a player, the system checks if all registration invoices are paid.
4. If any unpaid invoices exist, the approval is blocked and an error message is displayed.
5. Once all invoices are paid, the player can be approved.

### Viewing Invoice Details

1. The player detail page displays all invoices associated with the player.
2. Each invoice shows:
   - Invoice number
   - Amount
   - Status (Pending, Paid, Overdue)
   - Issue date
   - Due date
   - Payment date (if paid)
   - Payment reference (for pending invoices)
3. For unpaid invoices, a warning is displayed indicating that the player cannot be approved until payment.

## Payment Process

The payment process for invoices follows the standard SAFA payment workflow:

1. Payments are made using the reference number displayed on the invoice.
2. Once payment is received, administrators can mark the invoice as paid.
3. When an invoice is marked as paid, the player becomes eligible for approval.

## Accessing Invoices

1. From the Player Detail page: Invoices are displayed in the "Registration Invoice" section.
2. From the Player Approval List: The invoice status is shown in the "Invoice" column.
3. Through the main invoicing module: All invoices can be managed through the SAFA invoicing system.

## Report Generation

The system supports generating reports for:

1. Pending invoices by club, region, or province
2. Paid invoices within a specific date range
3. Overdue invoices requiring follow-up

## Troubleshooting

If you encounter issues with the invoice system:

1. Verify that the player has a valid date of birth (required to determine Junior/Senior status).
2. Check if the invoice was created successfully in the player detail view.
3. If an invoice is missing, contact a system administrator to manually create one.
4. If payment was made but not reflected in the system, provide the payment reference and receipt to update the invoice status.
