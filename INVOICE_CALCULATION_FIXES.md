# Invoice Calculation Fixes for User Registration and Add-Person

## Overview

This document outlines the fixes implemented to resolve invoice calculation issues in the `user_registration` and `club_admin_add_person` views of the SAFA Connect system.

## Issues Identified

### 1. Missing Season Configuration
- Members were being created without a `current_season` field set
- This caused invoice creation to fail with "No active season found" errors
- Fee calculations couldn't determine the correct fee structure

### 2. Inconsistent Invoice Creation
- Invoices were being created through signals, leading to potential duplicates
- Different calculation methods were not being used consistently
- Club-admin-created members vs. self-registered members had different fee structures

### 3. Fee Calculation Failures
- When no fee structure was found, methods returned R0.00
- No fallback fees for common member types
- VAT calculations were inconsistent

## Fixes Implemented

### 1. Fixed User Registration View (`accounts/views.py`)

**Before:**
```python
# No season configuration
member = Member.objects.create(**member_data)

# Invoice creation without proper error handling
invoice = Invoice.create_member_invoice(member)
```

**After:**
```python
# Get active season configuration
active_season = SAFASeasonConfig.get_active_season()
if not active_season:
    messages.error(request, 'No active season configuration found. Please contact support.')
    return redirect('accounts:user_registration')

member_data.update({
    'current_season': active_season,  # Set the current season
    'registration_method': 'SELF'    # Mark as self-registration
})

# Create invoice using simple calculation method with proper error handling
try:
    invoice = Invoice.create_simple_member_invoice(member)
    if invoice:
        messages.success(request, 'Registration successful! Please complete payment to proceed.')
        return redirect('membership:invoice_detail', uuid=invoice.uuid)
    else:
        messages.error(request, 'Registration successful but invoice creation failed. Please contact support.')
        return redirect('accounts:modern_home')
except Exception as e:
    messages.error(request, f'Registration successful but invoice creation failed: {str(e)}. Please contact support.')
    return redirect('accounts:modern_home')
```

### 2. Fixed Club Admin Add Person View (`accounts/views.py`)

**Before:**
```python
# No season configuration
member = Member.objects.create(
    # ... member data ...
    registration_method='CLUB'
)

# Invoice creation relied on signals
# Invoice will be created automatically by signals using simple calculation for club-admin-created members
```

**After:**
```python
# Get active season configuration
active_season = SAFASeasonConfig.get_active_season()
if not active_season:
    messages.error(request, 'No active season configuration found. Please contact support.')
    return redirect('accounts:club_admin_add_person')

member = Member.objects.create(
    # ... member data ...
    current_season=active_season,  # Set the current season
    registration_method='CLUB'    # Mark as club registration
)

# Create invoice immediately using simple calculation for club-admin-created members
try:
    invoice = Invoice.create_simple_member_invoice(member)
    if not invoice:
        messages.warning(request, f"{form.cleaned_data.get('role').capitalize()} '{user.get_full_name()}' was added successfully, but invoice creation failed. Please contact support.")
        return redirect('accounts:club_admin_dashboard')
except Exception as e:
    messages.warning(request, f"{form.cleaned_data.get('role').capitalize()} '{user.get_full_name()}' was added successfully, but invoice creation failed: {str(e)}. Please contact support.")
    return redirect('accounts:club_admin_dashboard')
```

### 3. Enhanced Invoice Creation Methods (`membership/models.py`)

**Enhanced `create_member_invoice` method:**
```python
@classmethod
def create_member_invoice(cls, member):
    """Create invoice for member registration"""
    try:
        # Ensure member has a current season
        if not member.current_season:
            member.current_season = SAFASeasonConfig.get_active_season()
            if not member.current_season:
                print(f"❌ No active season found for member {member.safa_id}")
                return None
            member.save()
        
        # ... rest of the method
```

**Enhanced `create_simple_member_invoice` method:**
```python
@classmethod
def create_simple_member_invoice(cls, member):
    """Create invoice for member registration using the specific formula: Fee = Total / 1.15, VAT = Fee * 15%"""
    try:
        # Ensure member has a current season
        if not member.current_season:
            member.current_season = SAFASeasonConfig.get_active_season()
            if not member.current_season:
                print(f"❌ No active season found for member {member.safa_id}")
                return None
            member.save()
        
        # ... rest of the method
```

### 4. Improved Fee Calculation Methods (`membership/models.py`)

**Enhanced `calculate_registration_fee` method:**
```python
def calculate_registration_fee(self, season_config=None):
    # ... existing logic ...
    
    if not fee_structure:
        logger.warning(f"No SAFAFeeStructure found for entity_type: {entity_type} and season: {season_config.season_year}")
        # Return a default fee if no fee structure is found
        if entity_type == 'PLAYER_JUNIOR':
            return Decimal('100.00')
        elif entity_type == 'PLAYER_SENIOR':
            return Decimal('200.00')
        elif 'OFFICIAL' in entity_type:
            return Decimal('250.00')
        else:
            return Decimal('200.00')  # Default fee
```

**Enhanced `calculate_simple_registration_fee` method:**
```python
def calculate_simple_registration_fee(self, season_config=None):
    # ... existing logic ...
    
    if not fee_structure:
        logger.warning(f"No SAFAFeeStructure found for entity_type: {entity_type} and season: {season_config.season_year}")
        # Return a default fee if no fee structure is found
        if entity_type == 'PLAYER_JUNIOR':
            total_amount = Decimal('100.00')
        elif entity_type == 'PLAYER_SENIOR':
            total_amount = Decimal('200.00')
        elif 'OFFICIAL' in entity_type:
            total_amount = Decimal('250.00')
        else:
            total_amount = Decimal('200.00')  # Default fee
    else:
        total_amount = fee_structure.annual_fee
```

### 5. Disabled Automatic Invoice Creation in Signals (`membership/signals.py`)

**Before:**
```python
# Create member invoice if season is active
# Use simple calculation for club-admin-created members, complex for regular registrations
try:
    active_season = SAFASeasonConfig.get_active_season()
    if active_season:
        # Check if this member was created by a club admin (using simple calculation)
        if hasattr(instance, 'registration_method') and instance.registration_method == 'CLUB':
            # Use simple calculation for club-admin-created members
            invoice = Invoice.create_simple_member_invoice(instance)
            print(f"✅ Created simple invoice {invoice.invoice_number} for {instance.get_full_name()} (Club Admin)")
        else:
            # Use regular calculation for other registrations
            invoice = Invoice.create_member_invoice(instance, active_season)
            print(f"✅ Created regular invoice {invoice.invoice_number} for {instance.get_full_name()}")
except Exception as e:
    print(f"❌ Failed to create invoice for {instance.get_full_name()}: {str(e)}")
```

**After:**
```python
# Invoice creation is now handled directly in the views to prevent duplicates
# and ensure proper season configuration
print(f"✅ Member {instance.get_full_name()} created - invoice will be created by view")
```

## Benefits of the Fixes

### 1. Consistent Season Configuration
- All members now have a `current_season` field set during creation
- Invoice creation no longer fails due to missing season configuration
- Fee structures can be properly looked up

### 2. Reliable Invoice Creation
- Invoices are created directly in the views, preventing duplicates
- Proper error handling and user feedback
- Consistent fee calculation methods based on registration type

### 3. Fallback Fee Support
- Default fees when no fee structure is found
- Junior players: R100
- Senior players: R200
- Officials: R250
- General fallback: R200

### 4. Better User Experience
- Clear error messages when invoice creation fails
- Success messages with payment instructions
- Proper redirects based on operation success/failure

## Testing

A test script (`test_invoice_calculation.py`) has been created to verify:
1. Member fee calculation methods
2. Simple invoice creation
3. Regular invoice creation
4. Proper season configuration handling

## Usage

### For Self-Registration (User Registration)
- Uses `Invoice.create_simple_member_invoice(member)`
- Applies the formula: Fee = Total / 1.15, VAT = Fee * 15%
- Creates invoices with proper VAT breakdown

### For Club Admin Registration (Add Person)
- Uses `Invoice.create_simple_member_invoice(member)`
- Same formula as self-registration for consistency
- Immediate invoice creation with proper error handling

## Notes

- The system now requires an active season configuration to function properly
- All invoice creation is handled in the views, not through signals
- Fee calculations include fallback values for common member types
- VAT calculations are consistent across all invoice types
- Error handling provides clear feedback to users and administrators

