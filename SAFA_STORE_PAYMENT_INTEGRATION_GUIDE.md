# SAFA Store Payment Integration Guide

## Overview

This guide provides step-by-step instructions for integrating payment processing into the SAFA Official Merchandise Store. The store is currently set up with all necessary order management and checkout functionality, requiring only payment gateway integration to be fully operational.

## Recommended Payment Gateways for South Africa

### 1. PayFast (Recommended)
**Best for**: Local South African businesses
**Supports**: Credit/Debit Cards, EFT, Instant EFT, Bitcoin
**Fees**: 2.9% + R2.00 per transaction
**Setup Difficulty**: Easy

**Advantages**:
- Local South African company with ZAR support
- Extensive payment method support
- Good documentation and support
- Instant EFT for immediate payments
- Mobile-optimized payment pages

### 2. PayGate
**Best for**: Enterprise-level businesses
**Supports**: Credit/Debit Cards, EFT, Mobile payments
**Fees**: Negotiable based on volume
**Setup Difficulty**: Medium

**Advantages**:
- Established South African payment processor
- High-volume transaction support
- Custom integration options
- Strong security compliance

### 3. Stripe
**Best for**: International expansion
**Supports**: Credit/Debit Cards, Digital wallets
**Fees**: 2.9% + R2.00 per transaction
**Setup Difficulty**: Medium

**Advantages**:
- Global payment processing
- Excellent developer tools
- Strong security and compliance
- Subscription billing support

## PayFast Integration (Recommended Implementation)

### Step 1: PayFast Account Setup

1. **Register Account**:
   - Visit https://www.payfast.co.za/
   - Sign up for a merchant account
   - Complete verification process

2. **Get API Credentials**:
   - Merchant ID
   - Merchant Key
   - Passphrase (set in PayFast dashboard)

### Step 2: Install PayFast Package

```bash
pip install django-payfast
```

Add to `requirements.txt`:
```
django-payfast==1.0.0
```

### Step 3: Django Settings Configuration

Add to `settings.py`:

```python
# PayFast Settings
PAYFAST_MERCHANT_ID = 'your_merchant_id'
PAYFAST_MERCHANT_KEY = 'your_merchant_key'  
PAYFAST_PASSPHRASE = 'your_passphrase'
PAYFAST_SANDBOX = True  # Set to False for production

# For development/testing
if DEBUG:
    PAYFAST_MERCHANT_ID = '10000100'  # PayFast test merchant ID
    PAYFAST_MERCHANT_KEY = '46f0cd694581a'  # PayFast test merchant key
    PAYFAST_PASSPHRASE = 'payfast'  # Test passphrase
    PAYFAST_SANDBOX = True

INSTALLED_APPS = [
    # ... existing apps
    'payfast',
]
```

### Step 4: Update Order Model

Add payment fields to the Order model:

```python
# merchandise/models.py
class Order(models.Model):
    # ... existing fields
    
    # Payment fields
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('COMPLETE', 'Complete'),
            ('CANCELLED', 'Cancelled'),
            ('FAILED', 'Failed'),
        ],
        default='PENDING'
    )
    payment_date = models.DateTimeField(blank=True, null=True)
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
```

### Step 5: Create Payment Views

Create `merchandise/views_payment.py`:

```python
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import HttpResponse
import hashlib
import urllib.parse
from .models import Order

@login_required
def process_payment(request, order_number):
    """Initiate PayFast payment"""
    order = get_object_or_404(Order, order_number=order_number, supporter=request.user.supporter_profile)
    
    # PayFast payment data
    payment_data = {
        'merchant_id': settings.PAYFAST_MERCHANT_ID,
        'merchant_key': settings.PAYFAST_MERCHANT_KEY,
        'return_url': request.build_absolute_uri(reverse('merchandise:payment_return')),
        'cancel_url': request.build_absolute_uri(reverse('merchandise:payment_cancel')),
        'notify_url': request.build_absolute_uri(reverse('merchandise:payment_notify')),
        'name_first': order.supporter.user.first_name,
        'name_last': order.supporter.user.last_name,
        'email_address': order.supporter.user.email,
        'item_name': f'SAFA Store Order #{order.order_number}',
        'item_description': f'Order containing {order.items.count()} items',
        'amount': str(order.total_amount),
        'm_payment_id': order.order_number,
        'custom_str1': order.id,
    }
    
    # Generate signature
    signature = generate_payfast_signature(payment_data, settings.PAYFAST_PASSPHRASE)
    payment_data['signature'] = signature
    
    payfast_url = 'https://sandbox.payfast.co.za/eng/process' if settings.PAYFAST_SANDBOX else 'https://www.payfast.co.za/eng/process'
    
    context = {
        'order': order,
        'payment_data': payment_data,
        'payfast_url': payfast_url,
    }
    
    return render(request, 'merchandise/payment_process.html', context)

@csrf_exempt
@require_POST
def payment_notify(request):
    """Handle PayFast IPN notification"""
    data = request.POST.dict()
    
    # Verify signature
    if verify_payfast_signature(data, settings.PAYFAST_PASSPHRASE):
        order_number = data.get('m_payment_id')
        payment_status = data.get('payment_status')
        
        try:
            order = Order.objects.get(order_number=order_number)
            
            if payment_status == 'COMPLETE':
                order.payment_status = 'COMPLETE'
                order.payment_method = 'PayFast'
                order.payment_reference = data.get('pf_payment_id')
                order.payment_amount = data.get('amount_gross')
                order.status = 'CONFIRMED'
                order.save()
                
            else:
                order.payment_status = 'FAILED'
                order.save()
                
        except Order.DoesNotExist:
            pass
    
    return HttpResponse('OK')

def payment_return(request):
    """Handle successful payment return"""
    messages.success(request, 'Payment completed successfully!')
    return redirect('merchandise:order_history')

def payment_cancel(request):
    """Handle cancelled payment"""
    messages.warning(request, 'Payment was cancelled.')
    return redirect('merchandise:cart')

def generate_payfast_signature(data, passphrase):
    """Generate PayFast signature"""
    # Sort the data and create query string
    sorted_data = sorted(data.items())
    query_string = urllib.parse.urlencode(sorted_data)
    
    # Add passphrase if provided
    if passphrase:
        query_string += f'&passphrase={passphrase}'
    
    # Generate MD5 hash
    return hashlib.md5(query_string.encode()).hexdigest()

def verify_payfast_signature(data, passphrase):
    """Verify PayFast signature"""
    signature = data.pop('signature', None)
    if not signature:
        return False
    
    generated_signature = generate_payfast_signature(data, passphrase)
    return signature == generated_signature
```

### Step 6: Create Payment Templates

Create `templates/merchandise/payment_process.html`:

```html
{% extends 'base.html' %}
{% load static %}

{% block title %}Payment Processing - SAFA Store{% endblock %}

{% block content %}
<div class="container my-5">
    <div class="row justify-content-center">
        <div class="col-md-8">
            <div class="card">
                <div class="card-header">
                    <h4>Secure Payment</h4>
                </div>
                <div class="card-body">
                    <p>You will be redirected to PayFast to complete your payment securely.</p>
                    
                    <div class="order-summary mb-4">
                        <h5>Order Summary</h5>
                        <p><strong>Order Number:</strong> {{ order.order_number }}</p>
                        <p><strong>Total Amount:</strong> R{{ order.total_amount }}</p>
                    </div>
                    
                    <form action="{{ payfast_url }}" method="post" id="payfast-form">
                        {% for key, value in payment_data.items %}
                            <input type="hidden" name="{{ key }}" value="{{ value }}">
                        {% endfor %}
                        <button type="submit" class="btn btn-success btn-lg">
                            Proceed to Payment
                        </button>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
// Auto-submit form after 3 seconds
setTimeout(function() {
    document.getElementById('payfast-form').submit();
}, 3000);
</script>
{% endblock %}
```

### Step 7: Update URLs

Add to `merchandise/urls.py`:

```python
from .views_payment import process_payment, payment_notify, payment_return, payment_cancel

urlpatterns = [
    # ... existing patterns
    path('payment/<str:order_number>/', process_payment, name='process_payment'),
    path('payment/notify/', payment_notify, name='payment_notify'),
    path('payment/return/', payment_return, name='payment_return'),
    path('payment/cancel/', payment_cancel, name='payment_cancel'),
]
```

### Step 8: Update Checkout View

Modify `merchandise/views.py` checkout view:

```python
@login_required
def checkout(request):
    """Checkout page"""
    supporter = request.user.supporter_profile
    cart = get_object_or_404(ShoppingCart, supporter=supporter)
    
    if not cart.items.exists():
        messages.error(request, 'Your cart is empty.')
        return redirect('merchandise:cart')
    
    # Calculate totals
    subtotal = cart.subtotal
    shipping_cost = Decimal('50.00')
    tax_amount = subtotal * Decimal('0.15')
    total = subtotal + shipping_cost + tax_amount
    
    if request.method == 'POST':
        # Create order (without clearing cart yet)
        with transaction.atomic():
            order = Order.objects.create(
                supporter=supporter,
                subtotal=subtotal,
                shipping_cost=shipping_cost,
                tax_amount=tax_amount,
                total_amount=total,
                # ... shipping fields
                payment_status='PENDING'
            )
            
            # Create order items
            for cart_item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    # ... order item fields
                )
            
            # Redirect to payment processing
            return redirect('merchandise:process_payment', order_number=order.order_number)
    
    context = {
        'cart': cart,
        'subtotal': subtotal,
        'shipping_cost': shipping_cost,
        'tax_amount': tax_amount,
        'total': total,
    }
    return render(request, 'merchandise/checkout.html', context)
```

### Step 9: Run Migrations

```bash
python manage.py makemigrations merchandise
python manage.py migrate
```

### Step 10: Testing

1. **Test Mode Setup**:
   - Use PayFast sandbox credentials
   - Test with various payment scenarios

2. **Test Transactions**:
   - Complete payment flow
   - Cancelled payments
   - Failed payments

3. **IPN Testing**:
   - Use PayFast's IPN simulator
   - Verify order status updates

## Production Deployment

### 1. Security Checklist
- [ ] Use HTTPS for all payment pages
- [ ] Set `PAYFAST_SANDBOX = False`
- [ ] Use production PayFast credentials
- [ ] Implement proper error logging
- [ ] Set up monitoring for failed payments

### 2. PayFast Production Setup
- [ ] Complete PayFast business verification
- [ ] Update to production merchant credentials
- [ ] Test with small live transactions
- [ ] Set up automatic settlement

### 3. Backup and Recovery
- [ ] Regular order data backups
- [ ] Payment reconciliation procedures
- [ ] Dispute resolution process

## Alternative Payment Methods

### 1. Stripe Integration
For international customers, consider adding Stripe:

```bash
pip install stripe
```

### 2. PayPal Integration
For additional payment options:

```bash
pip install django-paypal
```

### 3. Multiple Gateway Support
Implement gateway selection in checkout:

```python
class PaymentGateway(models.Model):
    name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    # Gateway-specific fields
```

## Monitoring and Analytics

### 1. Payment Tracking
- Monitor successful payment rates
- Track payment method preferences
- Identify failed payment patterns

### 2. Revenue Analytics
- Daily/monthly sales reports
- Product performance metrics
- Customer lifetime value

### 3. Error Monitoring
- Payment gateway errors
- Order processing issues
- Customer support tickets

This comprehensive payment integration guide will enable secure, reliable payment processing for the SAFA Official Merchandise Store. Start with PayFast for local South African customers, then expand to additional gateways as needed.
