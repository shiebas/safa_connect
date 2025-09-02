# Invoice Calculation, Unit Price Display, SAFA ID Preservation, and Province Requirement Fixes

## Overview

This document outlines the comprehensive fixes implemented to resolve multiple issues in the SAFA Connect system:

1. **Invoice calculation formula** - Fixed and working correctly
2. **Unit price not displaying in generated invoices** - Fixed by adding missing field and property
3. **SAFA ID not being preserved when manually entered** - Fixed by modifying user creation logic
4. **Province selection requirement for traceable location** - Added validation

## Issues Identified and Fixed

### 1. Unit Price Not Displaying in Generated Invoices

**Problem:**
- The `InvoiceItem` model was missing the `unit_price` field
- Template was trying to access `item.sub_total` which didn't exist
- Invoice creation methods were not setting the unit price correctly

**Solution:**
- Added `unit_price` field to `InvoiceItem` model
- Added `sub_total` property for template compatibility
- Updated invoice creation methods to properly set unit price

**Files Modified:**
- `membership/models.py` - Added unit_price field and sub_total property

**Code Changes:**
```python
class InvoiceItem(models.Model):
    """Line items for invoices (membership fees, registrations, etc.)"""
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='items'
    )
    description = models.CharField(_("Description"), max_length=255)
    unit_price = models.DecimalField(_("Unit Price (Excl. VAT)"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    quantity = models.PositiveIntegerField(_("Quantity"), default=1)
    total_price = models.DecimalField(_("Total Price (Excl. VAT)"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    amount = models.DecimalField(_("Amount (Incl. VAT)"), max_digits=10, decimal_places=2, default=Decimal('0.00'))

    @property
    def sub_total(self):
        """Property to provide sub_total for template compatibility"""
        return self.total_price
```

### 2. SAFA ID Not Being Preserved When Manually Entered

**Problem:**
- Both `CustomUser` and `Member` models were auto-generating new SAFA IDs
- Manually entered SAFA IDs were being overwritten
- The system couldn't distinguish between new and existing members with provided SAFA IDs

**Solution:**
- Modified `CustomUser.save()` to only generate SAFA ID for new users without one
- Updated user registration logic to preserve provided SAFA IDs
- Enhanced member creation to use provided SAFA ID when available

**Files Modified:**
- `accounts/models.py` - Modified save method
- `accounts/views.py` - Updated user registration logic
- `membership/models.py` - Enhanced SAFA ID handling

**Code Changes:**
```python
# accounts/models.py
def save(self, *args, **kwargs):
    # Only generate SAFA ID if none is provided and this is a new user
    if not self.safa_id and not self.pk:
        self.safa_id = self._generate_unique_safa_id()
    super().save(*args, **kwargs)

# accounts/views.py
# Handle SAFA ID - use previous_safa_id if provided, otherwise use generated one
safa_id_to_use = previous_safa_id if previous_safa_id and is_existing else user.safa_id

# Set SAFA ID if provided for existing member
if is_existing and previous_safa_id:
    user.safa_id = previous_safa_id
```

### 3. Province Selection Requirement for Traceable Location

**Problem:**
- Members could be registered without selecting a province
- This made location tracking difficult for administrative purposes
- No validation was in place to ensure geographic information was provided

**Solution:**
- Added province validation in user registration
- Required province selection for non-supporter members
- Enhanced error messages to guide users

**Code Changes:**
```python
# Ensure province is selected for traceable location
if user.role != 'SUPPORTER' and not form.cleaned_data.get('province'):
    messages.error(request, 'Province selection is required for traceable location.')
    return redirect('accounts:user_registration')
```

### 4. Invoice Creation Methods Enhanced

**Problem:**
- Invoice creation methods were not properly setting all required fields
- Unit price calculations were inconsistent
- VAT breakdown was not properly displayed

**Solution:**
- Updated both `create_member_invoice` and `create_simple_member_invoice` methods
- Properly set unit_price, total_price, and amount fields
- Ensured consistent VAT calculations

**Code Changes:**
```python
# Create invoice item with proper field mapping
InvoiceItem.objects.create(
    invoice=invoice,
    description=f"SAFA {member.get_role_display()} Registration Fee - {member.current_season.season_year} (Simple Formula)",
    unit_price=fee_excluding_vat,  # Unit price excluding VAT
    quantity=1,
    total_price=fee_excluding_vat,  # Total price excluding VAT
    amount=total_amount  # Total amount including VAT
)
```

## Testing

Two test scripts have been created to verify the fixes:

### 1. `test_invoice_calculation.py`
- Tests member fee calculation methods
- Verifies simple and regular invoice creation
- Checks proper season configuration handling

### 2. `test_safa_id_fix.py`
- Tests SAFA ID preservation for manually entered IDs
- Verifies invoice creation with preserved SAFA IDs
- Checks unit price display in generated invoices

## Benefits of the Fixes

### 1. **Complete Invoice Information Display**
- Unit prices now display correctly in all invoice views
- VAT breakdown is properly shown
- All financial calculations are transparent

### 2. **SAFA ID Integrity**
- Manually entered SAFA IDs are preserved
- Existing members can be properly identified
- No duplicate SAFA ID generation

### 3. **Geographic Traceability**
- All members have proper province information
- Location tracking is improved for administrative purposes
- Better compliance with SAFA requirements

### 4. **Consistent User Experience**
- Clear error messages guide users through registration
- Proper validation prevents incomplete registrations
- Consistent invoice creation across all registration methods

## Usage Examples

### For Self-Registration with Existing SAFA ID
1. User checks "I already have a SAFA ID"
2. User enters their existing SAFA ID
3. System preserves the provided SAFA ID
4. Invoice is created with correct fee calculation

### For New Member Registration
1. User leaves SAFA ID field empty
2. System generates unique SAFA ID
3. Province selection is required
4. Invoice is created with proper unit price display

### For Club Admin Registration
1. Admin fills out registration form
2. Province is automatically set from admin's club
3. SAFA ID is generated automatically
4. Invoice is created immediately with proper breakdown

## Technical Details

### Database Schema Changes
- Added `unit_price` field to `InvoiceItem` model
- Enhanced field validation and calculations
- Maintained backward compatibility with existing data

### Template Compatibility
- Added `sub_total` property for existing templates
- Updated invoice creation to populate all required fields
- Ensured consistent display across all invoice views

### Error Handling
- Enhanced validation messages
- Proper redirects on validation failures
- Clear user guidance for required fields

## Notes

- The system now requires an active season configuration to function properly
- All invoice creation is handled in the views, not through signals
- Fee calculations include fallback values for common member types
- VAT calculations are consistent across all invoice types
- Error handling provides clear feedback to users and administrators
- SAFA ID preservation works for both new and existing members
- Province selection ensures proper geographic tracking

## Future Considerations

- Consider adding validation for SAFA ID format (5 characters, alphanumeric)
- May want to add duplicate SAFA ID checking across all member types
- Consider adding geographic validation to ensure selected province matches user's location
- May want to add audit logging for SAFA ID changes

