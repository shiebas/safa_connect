from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Avg, Count
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.db import transaction
from decimal import Decimal
import json

from .models import (
    ProductCategory, Product, ProductVariant, ShoppingCart, 
    CartItem, Order, OrderItem, Wishlist, ProductReview
)
from supporters.models import SupporterProfile


def store_home(request):
    """Redirect to product listing page"""
    from django.shortcuts import redirect
    return redirect('merchandise:product_list')


def product_list(request, category_slug=None):
    """Product listing with filtering and search"""
    products = Product.objects.filter(status='ACTIVE').select_related('category')
    
    # Category filtering
    category = None
    if category_slug:
        category = get_object_or_404(ProductCategory, slug=category_slug, is_active=True)
        products = products.filter(category=category)
    
    # Search functionality
    search_query = request.GET.get('search', '').strip()
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(tags__icontains=search_query)
        )
    
    # Filtering
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    if price_min:
        products = products.filter(price__gte=price_min)
    if price_max:
        products = products.filter(price__lte=price_max)
    
    # Sorting
    sort_by = request.GET.get('sort', 'name')
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    elif sort_by == 'rating':
        products = products.annotate(avg_rating=Avg('reviews__rating')).order_by('-avg_rating')
    else:
        products = products.order_by('name')
    
    # Pagination
    paginator = Paginator(products, 12)  # 12 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all categories for sidebar
    categories = ProductCategory.objects.filter(is_active=True).order_by('name')
    
    context = {
        'products': page_obj,
        'category': category,
        'categories': categories,
        'search_query': search_query,
        'current_sort': sort_by,
    }
    return render(request, 'merchandise/product_list.html', context)


def product_detail(request, slug):
    """Product detail page"""
    product = get_object_or_404(Product, slug=slug, status='ACTIVE')
    
    # Get product variants
    variants = product.variants.filter(is_active=True).order_by('size', 'color')
    
    # Get product reviews
    reviews = product.reviews.filter(is_approved=True).order_by('-created_at')
    avg_rating = reviews.aggregate(avg=Avg('rating'))['avg']
    rating_counts = {i: reviews.filter(rating=i).count() for i in range(1, 6)}
    
    # Related products
    related_products = Product.objects.filter(
        category=product.category, status='ACTIVE'
    ).exclude(id=product.id)[:6]
    
    # Check if in wishlist (for authenticated users)
    in_wishlist = False
    if request.user.is_authenticated and hasattr(request.user, 'supporter_profile'):
        wishlist, _ = Wishlist.objects.get_or_create(supporter=request.user.supporter_profile)
        in_wishlist = wishlist.products.filter(id=product.id).exists()
    
    context = {
        'product': product,
        'variants': variants,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'rating_counts': rating_counts,
        'related_products': related_products,
        'in_wishlist': in_wishlist,
    }
    return render(request, 'merchandise/product_detail.html', context)


@login_required
@require_POST
def add_to_cart(request):
    """Add product to shopping cart"""
    try:
        product_id = request.POST.get('product_id')
        variant_id = request.POST.get('variant_id')
        quantity = int(request.POST.get('quantity', 1))
        
        product = get_object_or_404(Product, id=product_id, status='ACTIVE')
        variant = None
        if variant_id:
            variant = get_object_or_404(ProductVariant, id=variant_id, product=product)
        
        # Get or create cart
        supporter = request.user.supporter_profile
        cart, created = ShoppingCart.objects.get_or_create(supporter=supporter)
        
        # Calculate unit price
        if variant:
            unit_price = variant.final_price
        else:
            unit_price = product.current_price
        
        # Check stock
        if product.manage_stock:
            available_stock = variant.stock_quantity if variant else product.stock_quantity
            if quantity > available_stock:
                return JsonResponse({
                    'success': False,
                    'message': f'Only {available_stock} items available in stock'
                })
        
        # Add or update cart item
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            variant=variant,
            defaults={
                'quantity': quantity,
                'unit_price': unit_price
            }
        )
        
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Product added to cart successfully',
            'cart_total_items': cart.total_items
        })
        
    except Exception as e:
        print(f"Error adding to cart: {e}") # Add this line for debugging
        return JsonResponse({
            'success': False,
            'message': 'Failed to add product to cart'
        })


@login_required
def shopping_cart(request):
    """Shopping cart page"""
    supporter = request.user.supporter_profile
    cart, created = ShoppingCart.objects.get_or_create(supporter=supporter)
    
    context = {
        'cart': cart,
    }
    return render(request, 'merchandise/shopping_cart.html', context)


@login_required
@require_POST
def update_cart_item(request):
    """Update cart item quantity"""
    try:
        item_id = request.POST.get('item_id')
        quantity = int(request.POST.get('quantity', 1))
        
        cart_item = get_object_or_404(
            CartItem, 
            id=item_id, 
            cart__supporter=request.user.supporter_profile
        )
        
        if quantity <= 0:
            cart_item.delete()
            return JsonResponse({
                'success': True,
                'message': 'Item removed from cart',
                'removed': True
            })
        else:
            cart_item.quantity = quantity
            cart_item.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Cart updated successfully',
                'item_total': float(cart_item.total_price),
                'cart_subtotal': float(cart_item.cart.subtotal)
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Failed to update cart'
        })


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
    shipping_cost = Decimal('50.00')  # Fixed shipping for now
    tax_amount = subtotal * Decimal('0.15')  # 15% VAT
    total = subtotal + shipping_cost + tax_amount
    
    if request.method == 'POST':
        # Process checkout
        with transaction.atomic():
            # Create order
            order = Order.objects.create(
                supporter=supporter,
                subtotal=subtotal,
                shipping_cost=shipping_cost,
                tax_amount=tax_amount,
                total_amount=total,
                shipping_name=request.POST.get('shipping_name'),
                shipping_address_line1=request.POST.get('shipping_address_line1'),
                shipping_address_line2=request.POST.get('shipping_address_line2', ''),
                shipping_city=request.POST.get('shipping_city'),
                shipping_province=request.POST.get('shipping_province'),
                shipping_postal_code=request.POST.get('shipping_postal_code'),
                shipping_phone=request.POST.get('shipping_phone', ''),
                order_notes=request.POST.get('order_notes', ''),
            )
            
            # Create order items
            for cart_item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    variant=cart_item.variant,
                    product_name=cart_item.product.name,
                    product_sku=cart_item.variant.sku if cart_item.variant else cart_item.product.sku,
                    variant_name=cart_item.variant.name if cart_item.variant else '',
                    quantity=cart_item.quantity,
                    unit_price=cart_item.unit_price,
                    total_price=cart_item.total_price,
                )
            
            # Clear cart
            cart.items.all().delete()
            
            messages.success(request, f'Order {order.order_number} placed successfully!')
            return redirect('merchandise:order_detail', order_number=order.order_number)
    
    context = {
        'cart': cart,
        'subtotal': subtotal,
        'shipping_cost': shipping_cost,
        'tax_amount': tax_amount,
        'total': total,
    }
    return render(request, 'merchandise/checkout.html', context)


@login_required
def order_detail(request, order_number):
    """Order detail page"""
    order = get_object_or_404(
        Order, 
        order_number=order_number, 
        supporter=request.user.supporter_profile
    )
    
    context = {
        'order': order,
    }
    return render(request, 'merchandise/order_detail.html', context)


@login_required
def order_history(request):
    """Order history page"""
    orders = Order.objects.filter(
        supporter=request.user.supporter_profile
    ).order_by('-created_at')
    
    context = {
        'orders': orders,
    }
    return render(request, 'merchandise/order_history.html', context)


@login_required
def wishlist(request):
    """Wishlist page"""
    supporter = request.user.supporter_profile
    wishlist_obj, created = Wishlist.objects.get_or_create(supporter=supporter)
    
    context = {
        'wishlist': wishlist_obj,
    }
    return render(request, 'merchandise/wishlist.html', context)


@login_required
@require_POST
def toggle_wishlist(request):
    """Add/remove product from wishlist"""
    try:
        product_id = request.POST.get('product_id')
        product = get_object_or_404(Product, id=product_id)
        
        supporter = request.user.supporter_profile
        wishlist_obj, created = Wishlist.objects.get_or_create(supporter=supporter)
        
        if wishlist_obj.products.filter(id=product.id).exists():
            wishlist_obj.products.remove(product)
            in_wishlist = False
            message = 'Product removed from wishlist'
        else:
            wishlist_obj.products.add(product)
            in_wishlist = True
            message = 'Product added to wishlist'
        
        return JsonResponse({
            'success': True,
            'in_wishlist': in_wishlist,
            'message': message
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Failed to update wishlist'
        })
