from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.shortcuts import render, redirect
from django.forms import modelformset_factory
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from .models import Province, Region, GeographyUpdateLog
from .forms import ProvinceForm, RegionForm

class GeographyManagementView(LoginRequiredMixin, View):
    template_name = 'geography/geography_management.html'

    def _can_user_approve(self, user, update_log):
        """Check if a user has permission to approve a specific update."""
        if not user.is_authenticated:
            return False

        content_object = update_log.content_object

        if isinstance(content_object, Province):
            return user.role == 'ADMIN_NATIONAL'

        if isinstance(content_object, Region):
            return user.role == 'ADMIN_PROVINCE' and user.province == content_object.province

        return False

    def get_context_data(self, request, formset=None):
        user = request.user
        context = {}

        pending_updates_qs = GeographyUpdateLog.objects.filter(status='PENDING').select_related('user', 'content_type').prefetch_related('content_object')

        pending_updates_with_perms = []
        for update in pending_updates_qs:
            update.can_approve = self._can_user_approve(user, update)
            pending_updates_with_perms.append(update)

        context['pending_updates'] = pending_updates_with_perms

        if formset is not None:
            context['formset'] = formset
            context['level'] = formset.model.__name__
            return context

        if user.role == 'ADMIN_NATIONAL':
            queryset = Province.objects.all().order_by('name')
            formset_class = modelformset_factory(Province, form=ProvinceForm, extra=0)
            context['formset'] = formset_class(queryset=queryset, prefix='provinces')
            context['level'] = 'Province'
        elif user.role == 'ADMIN_PROVINCE' and user.province:
            queryset = Region.objects.filter(province=user.province).order_by('name')
            formset_class = modelformset_factory(Region, form=RegionForm, extra=0)
            context['formset'] = formset_class(queryset=queryset, prefix='regions')
            context['level'] = 'Region'
        else:
            context['formset'] = None
            context['level'] = 'N/A'

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(request)
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        user = request.user

        if 'approve' in request.POST or 'reject' in request.POST:
            action = 'approve' if 'approve' in request.POST else 'reject'
            update_log_id = request.POST.get(action)

            try:
                update_log = GeographyUpdateLog.objects.get(id=update_log_id)

                if not self._can_user_approve(user, update_log):
                    messages.error(request, "You do not have permission to perform this action.")
                    return redirect('geography:geography_management')

                if action == 'approve':
                    update_log.approve(user, notes="Approved via management interface.")
                    messages.success(request, f"Change to {update_log.content_object} approved.")
                else:
                    update_log.reject(user, notes="Rejected via management interface.")
                    messages.warning(request, f"Change to {update_log.content_object} rejected.")

            except GeographyUpdateLog.DoesNotExist:
                messages.error(request, "The change you tried to action no longer exists.")

            return redirect('geography:geography_management')

        formset = None
        if 'provinces-TOTAL_FORMS' in request.POST:
            formset_class = modelformset_factory(Province, form=ProvinceForm, extra=0)
            formset = formset_class(request.POST, prefix='provinces')
            model = Province
        elif 'regions-TOTAL_FORMS' in request.POST:
            formset_class = modelformset_factory(Region, form=RegionForm, extra=0)
            formset = formset_class(request.POST, prefix='regions')
            model = Region

        if formset and formset.is_valid():
            for form in formset.changed_forms:
                instance = form.instance
        else:
            if formset:
                print(formset.errors)
                for field_name in form.changed_data:
                    old_value = form.initial.get(field_name)
                    new_value = form.cleaned_data.get(field_name)

                    GeographyUpdateLog.objects.create(
                        user=user,
                        content_type=ContentType.objects.get_for_model(instance),
                        object_id=instance.pk,
                        field_name=field_name,
                        old_value=str(old_value),
                        new_value=str(new_value),
                        status='PENDING'
                    )
            messages.success(request, "Your changes have been submitted for approval.")
            return redirect('geography:geography_management')

        context = self.get_context_data(request, formset=formset)
        return render(request, self.template_name, context)
