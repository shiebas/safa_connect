from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    SAFACoinWallet, SAFACoinTransaction, SAFACoinTransfer,
    SAFACoinReward, SAFACoinCompetition, SAFACoinCompetitionParticipation,
    SAFACoinLoyaltyConversion
)

@admin.register(SAFACoinWallet)
class SAFACoinWalletAdmin(admin.ModelAdmin):
    list_display = ['user', 'balance', 'total_earned', 'total_spent', 'created_at', 'wallet_actions']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'user__safa_id']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-balance']
    
    def wallet_actions(self, obj):
        """Display wallet action buttons"""
        return format_html(
            '<a class="button" href="{}">View Transactions</a>',
            reverse('admin:digital_coins_safacointransaction_changelist') + f'?wallet__id__exact={obj.id}'
        )
    wallet_actions.short_description = 'Actions'

@admin.register(SAFACoinTransaction)
class SAFACoinTransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'wallet_user', 'transaction_type', 'amount', 'reason', 'balance_after', 'created_at']
    list_filter = ['transaction_type', 'created_at', 'wallet__user__role']
    search_fields = ['wallet__user__first_name', 'wallet__user__last_name', 'wallet__user__email', 'reason']
    readonly_fields = ['id', 'created_at', 'balance_after']
    ordering = ['-created_at']
    
    def wallet_user(self, obj):
        """Display user information"""
        user = obj.wallet.user
        return format_html(
            '<strong>{}</strong><br><small>SAFA ID: {}</small>',
            user.get_full_name(),
            user.safa_id
        )
    wallet_user.short_description = 'User'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('wallet__user')

@admin.register(SAFACoinTransfer)
class SAFACoinTransferAdmin(admin.ModelAdmin):
    list_display = ['id', 'from_user', 'to_user', 'amount', 'status', 'created_at', 'transfer_actions']
    list_filter = ['status', 'created_at']
    search_fields = ['from_wallet__user__first_name', 'from_wallet__user__last_name', 'to_wallet__user__first_name', 'to_wallet__user__last_name']
    readonly_fields = ['id', 'created_at', 'completed_at']
    ordering = ['-created_at']
    
    def from_user(self, obj):
        """Display sender information"""
        user = obj.from_wallet.user
        return format_html(
            '<strong>{}</strong><br><small>SAFA ID: {}</small>',
            user.get_full_name(),
            user.safa_id
        )
    from_user.short_description = 'From User'
    
    def to_user(self, obj):
        """Display receiver information"""
        user = obj.to_wallet.user
        return format_html(
            '<strong>{}</strong><br><small>SAFA ID: {}</small>',
            user.get_full_name(),
            user.safa_id
        )
    to_user.short_description = 'To User'
    
    def transfer_actions(self, obj):
        """Display transfer action buttons"""
        if obj.status == 'PENDING':
            return format_html(
                '<a class="button" href="{}">Execute</a>',
                reverse('admin:digital_coins_safacointransfer_execute', args=[obj.id])
            )
        return obj.get_status_display()
    transfer_actions.short_description = 'Actions'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('from_wallet__user', 'to_wallet__user')

@admin.register(SAFACoinReward)
class SAFACoinRewardAdmin(admin.ModelAdmin):
    list_display = ['user', 'reward_type', 'amount', 'reason', 'claimed', 'created_at', 'reward_actions']
    list_filter = ['reward_type', 'claimed', 'created_at']
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'reason']
    readonly_fields = ['created_at', 'claimed_at']
    ordering = ['-created_at']
    
    def reward_actions(self, obj):
        """Display reward action buttons"""
        if not obj.claimed and obj.can_claim:
            return format_html(
                '<a class="button" href="{}">Claim</a>',
                reverse('admin:digital_coins_safacoinreward_claim', args=[obj.id])
            )
        elif obj.claimed:
            return format_html('<span style="color: green;">✓ Claimed</span>')
        elif obj.is_expired:
            return format_html('<span style="color: red;">✗ Expired</span>')
        return 'N/A'
    reward_actions.short_description = 'Actions'

@admin.register(SAFACoinCompetition)
class SAFACoinCompetitionAdmin(admin.ModelAdmin):
    list_display = ['name', 'competition_type', 'entry_fee', 'prize_pool', 'current_participants', 'status', 'start_date', 'competition_actions']
    list_filter = ['competition_type', 'status', 'start_date', 'end_date']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'current_participants']
    ordering = ['-created_at']
    
    def competition_actions(self, obj):
        """Display competition action buttons"""
        actions = []
        if obj.status == 'DRAFT':
            actions.append(format_html(
                '<a class="button" href="{}">Activate</a>',
                reverse('admin:digital_coins_safacoincompetition_activate', args=[obj.id])
            ))
        elif obj.status == 'ACTIVE':
            actions.append(format_html(
                '<a class="button" href="{}">Pause</a>',
                reverse('admin:digital_coins_safacoincompetition_pause', args=[obj.id])
            ))
        
        actions.append(format_html(
            '<a class="button" href="{}">View Participants</a>',
            reverse('admin:digital_coins_safacoincompetitionparticipation_changelist') + f'?competition__id__exact={obj.id}'
        ))
        
        return mark_safe(' '.join(actions))
    competition_actions.short_description = 'Actions'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'competition_type', 'status')
        }),
        ('Timing', {
            'fields': ('start_date', 'end_date')
        }),
        ('Economics', {
            'fields': ('entry_fee', 'prize_pool', 'max_participants', 'current_participants')
        }),
        ('Configuration', {
            'fields': ('rules', 'prize_distribution', 'created_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(SAFACoinCompetitionParticipation)
class SAFACoinCompetitionParticipationAdmin(admin.ModelAdmin):
    list_display = ['competition', 'user', 'entry_fee_paid', 'score', 'rank', 'prizes_won', 'joined_at']
    list_filter = ['competition__competition_type', 'joined_at', 'competition__status']
    search_fields = ['user__first_name', 'user__last_name', 'competition__name']
    readonly_fields = ['joined_at', 'completed_at']
    ordering = ['-score', '-joined_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'competition')

@admin.register(SAFACoinLoyaltyConversion)
class SAFACoinLoyaltyConversionAdmin(admin.ModelAdmin):
    list_display = ['user', 'loyalty_points', 'coins_awarded', 'conversion_rate', 'converted_at']
    list_filter = ['converted_at']
    search_fields = ['user__first_name', 'user__last_name', 'user__email']
    readonly_fields = ['converted_at']
    ordering = ['-converted_at']

# Custom admin actions
@admin.action(description="Execute selected transfers")
def execute_transfers(modeladmin, request, queryset):
    """Execute pending transfers"""
    executed = 0
    failed = 0
    
    for transfer in queryset.filter(status='PENDING'):
        if transfer.execute_transfer():
            executed += 1
        else:
            failed += 1
    
    modeladmin.message_user(
        request,
        f"Executed {executed} transfers successfully. {failed} transfers failed."
    )

@admin.action(description="Claim selected rewards")
def claim_rewards(modeladmin, request, queryset):
    """Claim unclaimed rewards"""
    claimed = 0
    failed = 0
    
    for reward in queryset.filter(claimed=False):
        if reward.claim_reward():
            claimed += 1
        else:
            failed += 1
    
    modeladmin.message_user(
        request,
        f"Claimed {claimed} rewards successfully. {failed} rewards failed."
    )

# Add actions to admin classes
SAFACoinTransferAdmin.actions = [execute_transfers]
SAFACoinRewardAdmin.actions = [claim_rewards]

# Admin site customization
admin.site.site_header = "SAFA Connect - Digital Coins Administration"
admin.site.site_title = "SAFA Digital Coins"
admin.site.index_title = "SAFA Coin Management Dashboard"
