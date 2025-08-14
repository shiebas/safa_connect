# SAFA Connect Design Protocol

## Design Change Protocol

To protect the design integrity of the SAFA Connect project, this document outlines the protocol that any AI assistant (or human collaborator) should follow when suggesting changes to design elements.

### Files Requiring Explicit Confirmation

The following file types should NEVER be modified without explicit confirmation from the project owner:

1. **Template files**:
   - All files in `/templates/` directory and subdirectories
   - Any HTML files containing layout or design elements

2. **CSS files**:
   - All files in `/static/css/` directory
   - Any files determining the visual appearance of the site

3. **JavaScript files**:
   - Any JS files that affect UI behavior or animations

4. **Images and Media**:
   - Logo files
   - Brand color definitions
   - Icons and visual assets

### Confirmation Process

Before changing ANY design-related file, assistants MUST:

1. **Explain intentions**: Clearly state which files would be modified and how
2. **Show before/after**: When possible, show the current state and proposed state
3. **Request explicit confirmation**: Ask for a clear "yes" to proceed
4. **Wait for approval**: Do not proceed with changes until approval is received

### Example Confirmation Request

```
I'm planning to make the following changes to the home page template:
- Change the card layout from 3 columns to 4 columns
- Update the button colors to match your brand guidelines

Would you like me to proceed with these changes? (Please reply with "yes" to confirm)
```

### Brand Guidelines

SAFA Connect uses specific colors and styles:

- **Brand Colors**:
  - Primary Gold: #FFD700
  - Dark Gold: #D4AF37
  - Text color: #000000 (Black)
  - Button styles should follow the existing `btn-safa` class definition

- **Layout**:
  - Card-based design with consistent spacing
  - Mobile-responsive elements
  - Centered content where appropriate

### Notes

This project represents the South African Football Association digital systems and maintaining professional appearance and brand consistency is critical.

Last updated: June 12, 2025
