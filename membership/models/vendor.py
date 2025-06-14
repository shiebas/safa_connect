from django.db import models
from django.utils.translation import gettext_lazy as _

class Vendor(models.Model):
    """
    Vendor model for organizations that can be billed for services (e.g., clubs, LFAs, external partners).
    """
    name = models.CharField(_('Vendor Name'), max_length=255, unique=True)
    email = models.EmailField(_('Contact Email'), blank=True)
    phone = models.CharField(_('Contact Phone'), max_length=50, blank=True)
    address = models.TextField(_('Address'), blank=True)
    logo = models.ImageField(_('Logo'), upload_to='vendor_logos/', blank=True, null=True)
    is_active = models.BooleanField(_('Active'), default=True)
    created = models.DateTimeField(_('Created'), auto_now_add=True)
    modified = models.DateTimeField(_('Modified'), auto_now=True)

    class Meta:
        verbose_name = _('Vendor')
        verbose_name_plural = _('Vendors')
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def logo_url(self):
        if self.logo and hasattr(self.logo, 'url'):
            return self.logo.url
        return None
