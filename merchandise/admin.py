from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Avg, Count
from .models import (
    ProductCategory, Product, ProductImage, ProductVariant, 
    ShoppingCart, CartItem, Order, OrderItem, Wishlist, ProductReview
)


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'product_count', 'is_featured', 'is_active', 'display_order']
    list_filter = ['is_featured', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['display_order', 'name']
    
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'alt_text', 'display_order']


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ['name', 'size', 'color', 'sku', 'price_adjustment', 'stock_quantity', 'is_active']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category', 'current_price_display', 'stock_status', 
        'rating_display', 'is_featured', 'status', 'created_at'
    ]
    list_filter = [
        'category', 'status', 'is_featured', 'is_digital', 
        'requires_shipping', 'created_at'
    ]
    search_fields = ['name', 'description', 'sku', 'tags']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'category', 'description', 'short_description', 'tags')
        }),
        ('Pricing', {
            'fields': ('price', 'sale_price', 'cost_price')
        }),
        ('Product Details', {
            'fields': ('sku', 'weight', 'dimensions', 'main_image')
        }),
        ('Stock Management', {
            'fields': ('manage_stock', 'stock_quantity', 'low_stock_threshold')
        }),
        ('Features', {
            'fields': ('is_featured', 'is_digital', 'requires_shipping')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('status', 'created_at', 'updated_at')
        }),
    )
    
    inlines = [ProductImageInline, ProductVariantInline]
    
    def current_price_display(self, obj):
        if obj.is_on_sale:
            return format_html(
                '<span style="text-decoration: line-through;">R{}</span> '
                '<span style="color: red; font-weight: bold;">R{}</span>',
                obj.price, obj.current_price
            )
        return f"R{obj.current_price}"
    current_price_display.short_description = 'Price'
    
    def stock_status(self, obj):
        if not obj.manage_stock:
            return format_html('<span style="color: blue;">Not Managed</span>')
        elif obj.stock_quantity == 0:
            return format_html('<span style="color: red;">Out of Stock</span>')
        elif obj.is_low_stock:
            return format_html('<span style="color: orange;">Low Stock ({})</span>', obj.stock_quantity)
        else:
            return format_html('<span style="color: green;">In Stock ({})</span>', obj.stock_quantity)
    stock_status.short_description = 'Stock'
    
    def rating_display(self, obj):
        avg_rating = obj.reviews.aggregate(avg=Avg('rating'))['avg']
        review_count = obj.reviews.count()
        if avg_rating:
            stars = '★' * int(avg_rating) + '☆' * (5 - int(avg_rating))
            return format_html('{} ({} reviews)', stars, review_count)
        return 'No reviews'
    rating_display.short_description = 'Rating'


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ['product', 'name', 'size', 'color', 'sku', 'final_price', 'stock_quantity', 'is_active']
    list_filter = ['product__category', 'size', 'color', 'is_active']
    search_fields = ['product__name', 'name', 'sku']


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ['total_price']


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ['supporter', 'total_items_display', 'subtotal_display', 'updated_at']
    search_fields = ['supporter__user__first_name', 'supporter__user__last_name', 'supporter__user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    inlines = [CartItemInline]
    
    def total_items_display(self, obj):
        return f"{obj.total_items} items"
    total_items_display.short_description = 'Items'
    
    def subtotal_display(self, obj):
        return f"R{obj.subtotal}"
    subtotal_display.short_description = 'Subtotal'


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['total_price']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'supporter', 'status', 'total_amount_display', 
        'payment_status', 'created_at'
    ]
    list_filter = ['status', 'created_at', 'shipped_date']
    search_fields = [
        'order_number', 'supporter__user__first_name', 
        'supporter__user__last_name', 'supporter__user__email'
    ]
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'supporter', 'status', 'order_notes')
        }),
        ('Pricing', {
            'fields': ('subtotal', 'shipping_cost', 'tax_amount', 'discount_amount', 'total_amount')
        }),
        ('Payment', {
            'fields': ('invoice', 'payment_method')
        }),
        ('Shipping Address', {
            'fields': (
                'shipping_name', 'shipping_address_line1', 'shipping_address_line2',
                'shipping_city', 'shipping_province', 'shipping_postal_code', 'shipping_phone'
            )
        }),
        ('Tracking', {
            'fields': ('tracking_number', 'shipped_date', 'delivered_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    inlines = [OrderItemInline]
    
    def total_amount_display(self, obj):
        return f"R{obj.total_amount}"
    total_amount_display.short_description = 'Total'
    
    def payment_status(self, obj):
        if obj.invoice and obj.invoice.status == 'PAID':
            return format_html('<span style="color: green;">Paid</span>')
        elif obj.status == 'PENDING':
            return format_html('<span style="color: orange;">Pending</span>')
        else:
            return format_html('<span style="color: red;">Unpaid</span>')
    payment_status.short_description = 'Payment'


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['supporter', 'product_count', 'updated_at']
    search_fields = ['supporter__user__first_name', 'supporter__user__last_name']
    filter_horizontal = ['products']
    
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = [
        'product', 'supporter', 'rating', 'title', 
        'is_verified_purchase', 'is_approved', 'created_at'
    ]
    list_filter = ['rating', 'is_verified_purchase', 'is_approved', 'created_at']
    search_fields = ['product__name', 'supporter__user__first_name', 'title', 'review_text']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Review Information', {
            'fields': ('product', 'supporter', 'order_item', 'rating', 'title', 'review_text')
        }),
        ('Images', {
            'fields': ('image1', 'image2', 'image3')
        }),
        ('Status', {
            'fields': ('is_verified_purchase', 'is_approved', 'created_at')
        }),
    )
