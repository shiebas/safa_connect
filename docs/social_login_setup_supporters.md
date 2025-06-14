# Social Login Setup for Supporter Registration (Google, Facebook, Instagram, X/Twitter, TikTok)

This guide will help you enable and configure social login for your supporter registration page.

---

## 1. Prerequisites
- `django-allauth` must be installed and in `INSTALLED_APPS`.
- Your `accounts` app should be set up for allauth (already present in your project).
- You need to register your app with each social provider to get client IDs/secrets.

---

## 2. Register Your App with Each Provider

### Google
1. Go to [Google Cloud Console](https://console.developers.google.com/).
2. Create a project, enable “OAuth consent screen”, and add credentials for “OAuth 2.0 Client IDs”.
3. Set the redirect URI to:
   `https://your-domain/accounts/social/login/callback/google-oauth2/`
4. Save the client ID and secret.

### Facebook
1. Go to [Facebook Developers](https://developers.facebook.com/).
2. Create an app, add “Facebook Login” product.
3. Set the redirect URI to:
   `https://your-domain/accounts/social/login/callback/facebook/`
4. Save the app ID and secret.

### Instagram
1. Go to [Meta for Developers](https://developers.facebook.com/).
2. Create an Instagram app (requires Facebook app).
3. Set the redirect URI to:
   `https://your-domain/accounts/social/login/callback/instagram/`
4. Save the client ID and secret.

### X (Twitter)
1. Go to [Twitter Developer Portal](https://developer.twitter.com/).
2. Create a project/app, enable OAuth 2.0.
3. Set the callback URL to:
   `https://your-domain/accounts/social/login/callback/twitter/`
4. Save the client ID and secret.

### TikTok
1. Go to [TikTok for Developers](https://developers.tiktok.com/).
2. Register your app, enable login kit.
3. Set the callback URL to:
   `https://your-domain/accounts/social/login/callback/tiktok/`
4. Save the client key and secret.

---

## 3. Add Social Applications in Django Admin
1. Go to Django admin > **Sites > Social applications**.
2. For each provider:
   - Add a new Social Application.
   - Select the provider (Google, Facebook, etc.).
   - Enter the client ID and secret.
   - Attach it to your site (e.g., example.com or localhost).
   - Save.

---

## 4. Test the Integration
1. Visit `/supporters/register/`.
2. Click a social login button (Google, Facebook, Instagram, X, TikTok).
3. You should be redirected to the provider, then back to your site after login.
4. On first login, the user is created and can complete the supporter registration form.

---

## 5. Troubleshooting
- If a provider button does not work, check:
  - The provider is enabled in Django admin.
  - The client ID/secret is correct.
  - The callback URL matches exactly.
  - The provider is listed in `SOCIALACCOUNT_PROVIDERS` in `settings.py` (if you use custom settings).
- For local testing, use `http://localhost:8000` as the site domain.
- For production, use your real domain and HTTPS.

---

## 6. Notes
- Some providers (Instagram, TikTok) may require extra review or permissions.
- You can add more providers by repeating the above steps.
- The social login buttons in your template use the default allauth URLs and will work as soon as the provider is configured in Django admin.

---

If you need more help or want to add more providers, let your developer know!
