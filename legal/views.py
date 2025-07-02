from django.shortcuts import render

def terms_and_conditions(request):
    """Terms and Conditions Page"""
    return render(request, 'legal/terms_and_conditions.html')

def privacy_policy(request):
    """Privacy Policy Page"""
    return render(request, 'legal/privacy_policy.html')

def cookie_policy(request):
    """Cookie Policy Page"""
    return render(request, 'legal/cookie_policy.html')

def paia_act(request):
    """PAIA Act Page"""
    return render(request, 'legal/paia_act.html')

def refund_policy(request):
    """Refund Policy Page"""
    return render(request, 'legal/refund_policy.html')
