# Registration Template Cleanup Instructions

## Deprecated Files to Remove
- templates/accounts/national_registration.html
- static/js/registration-debug.js
- static/js/registration.js
- static/js/national_registration.js

## Unified Template
- Use only: templates/accounts/register.html

## Checklist
- [ ] Confirm all admin types (National, Province, Region, LFA, Club) can register via the unified form
- [ ] Confirm region assignment and display works (no 'Not assigned' if region is selected)
- [ ] Remove deprecated files above
- [ ] Update documentation and user manual to reference only the unified registration process
