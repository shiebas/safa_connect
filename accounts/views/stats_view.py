from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def stats_dashboard(request):
    """View to demonstrate the stat_filters template tags"""
    context = {
        'completed': 75,
        'total': 100,
        'progress_percent': 65,
    }
    return render(request, 'accounts/stats_dashboard.html', context)
