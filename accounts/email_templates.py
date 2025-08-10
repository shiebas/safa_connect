# email_templates.py - Email template contexts
def get_approval_email_context(member):
    """Get context for approval email"""
    return {
        'member': member,
        'safa_id': member.safa_id,
        'login_url': f"{settings.SITE_URL}/accounts/login/",
        'dashboard_url': f"{settings.SITE_URL}/accounts/dashboard/",
        'card_url': f"{settings.SITE_URL}/membership-cards/my-card/",
        'support_email': 'support@safa.net',
        'site_name': 'SAFA Registration System'
    }


def get_rejection_email_context(member, reason):
    """Get context for rejection email"""
    return {
        'member': member,
        'reason': reason,
        'register_url': f"{settings.SITE_URL}/accounts/register/",
        'support_email': 'support@safa.net',
        'contact_url': f"{settings.SITE_URL}/accounts/support/",
        'site_name': 'SAFA Registration System'
    }
