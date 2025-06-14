# SAFA Digital/Physical Membership Card System Manual

## 1. Overview

This system provides modern, customizable digital and physical membership cards for SAFA, supporting dynamic branding, club/player logos, loyalty fields, and NFC/QR code verification. It is designed for both web and mobile, with easy customization and support for supporters as a separate registration flow.

---

## 2. Card Template Customization

### Location

- Main template:  
  `/home/shaun/safa_global/templates/membership_cards/bank_card.html`

### Key Features

- **Dynamic branding:** Background gradient, text color, and watermark are set via Django context variables.
- **Logos:** Supports both SAFA and club logos.
- **Member info:** Name, photo, SAFA ID, role, and loyalty points.
- **Status badge:** Color-coded for status (active, suspended, expired).
- **QR code:** For verification and linking to member data.
- **Watermark:** Optional, for club or association branding.

### How to Add or Change Fields

1. **Add a new field in the template:**
   ```html
   <div class="loyalty">Loyalty: {{ card.loyalty_points }} pts</div>
   ```
2. **Pass the value from your Django view:**
   ```python
   context['card'].loyalty_points = member.loyalty_points
   ```
3. **Style as needed in the `<style>` block.**

### Dynamic Colors and Branding

- Set via inline style in the template:
  ```html
  <div class="bank-card"
       style="--card-bg: {{ card.bg_color|default:'#FFD700' }};
              --card-text: {{ card.text_color|default:'#222' }};">
  ```
- Use these variables in your CSS:
  ```css
  .bank-card {
      background: var(--card-bg, #FFD700);
      color: var(--card-text, #222);
      /* ... */
  }
  ```

### Club and Player Logos

- Club logo:
  ```html
  {% if card.club_logo_url %}
  <img src="{{ card.club_logo_url }}" alt="Club Logo" class="club-logo">
  {% endif %}
  ```
- Player photo:
  ```html
  {% if user.profile_photo %}
  <img src="{{ user.profile_photo.url }}" alt="Profile Photo" class="member-photo">
  {% endif %}
  ```

---

## 3. Django View Integration

- Pass all dynamic fields (colors, logos, loyalty, etc.) from your view:
  ```python
  context = {
      'card': {
          'bg_color': club.card_bg_color,
          'text_color': club.card_text_color,
          'club_logo_url': club.logo.url if club.logo else None,
          'loyalty_points': member.loyalty_points,
          'watermark_url': club.watermark.url if club.watermark else None,
          # ...other fields...
      },
      'user': user,
      'qr_base64': qr_code_base64,
      # ...
  }
  ```

---

## 4. Supporter Registration Flow

- Implement a separate registration form/view for supporters (e.g., `/supporters/register/`).
- Store supporters as a separate model or user type.
- Issue cards using the same template, but with "Supporter" role and possibly different branding/fields.

---

## 5. Physical Cards (NFC/QR)

- The same template can be used for print (add print-specific CSS if needed).
- For NFC/QR, encode the card number or member ID.
- The QR code is rendered from the `qr_base64` context variable.

---

## 6. Customization Steps

1. **Edit the template** (`bank_card.html`) for layout, fields, and branding.
2. **Update Django views** to pass new or changed fields.
3. **Add/modify model fields** as needed for new data.
4. **Test** by viewing a card in the browser.
5. **For supporters**, ensure their registration and card logic is handled in a separate flow.

---

## 7. Example: Adding a New Field

- Add to model:  
  `loyalty_points = models.IntegerField(default=0)`
- Pass in view:  
  `context['card'].loyalty_points = member.loyalty_points`
- Add to template:  
  `<div class="loyalty">Loyalty: {{ card.loyalty_points }} pts</div>`

---

## 8. Advanced Customization

- For per-club or per-tier branding, store branding info in the club model and pass to the template.
- For advanced print styles, add a `@media print` CSS block.

---

## 9. File Reference

- **Template:** `/home/shaun/safa_global/templates/membership_cards/bank_card.html`
- **Views:** `/home/shaun/safa_global/membership_cards/views.py`
- **Models:** `/home/shaun/safa_global/membership/models.py`

---

## 10. Saving and Sharing

- This manual is saved as `SAFA_Card_System_Manual.md` in your `/docs/` folder.

---

If you need further code samples (e.g., for supporter registration), just ask!
