from django.db import models
from django.contrib.auth import get_user_model
from supporters.models import SupporterProfile
from membership.invoice_models import Invoice
import uuid
from decimal import Decimal

User = get_user_model()


class ProductCategory(models.Model):
    """Categories for SAFA merchandise"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='merchandise/categories/', blank=True)
    
    # Display settings
    is_featured = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['display_order', 'name']
        verbose_name_plural = "Product Categories"
        
    def __str__(self):
        return self.name


class Product(models.Model):
    """SAFA merchandise products"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic product info
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    short_description = models.CharField(max_length=500, blank=True)
    
    # Categorization
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, related_name='products')
    tags = models.CharField(max_length=200, blank=True, help_text="Comma-separated tags")
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Product details
    sku = models.CharField(max_length=50, unique=True)
    weight = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Weight in grams")
    dimensions = models.CharField(max_length=100, blank=True, help_text="L x W x H in cm")
    
    # Images
    main_image = models.ImageField(upload_to='merchandise/products/')
    
    # Stock management
    manage_stock = models.BooleanField(default=True)
    stock_quantity = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=5)
    
    # Product features
    is_featured = models.BooleanField(default=False)
    is_digital = models.BooleanField(default=False)
    requires_shipping = models.BooleanField(default=True)
    
    # SEO and marketing
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.CharField(max_length=500, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=[
        ('DRAFT', 'Draft'),
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('OUT_OF_STOCK', 'Out of Stock'),
    ], default='DRAFT')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return self.name
    
    @property
    def current_price(self):
        """Get the current selling price (sale price if available, otherwise regular price)"""
        return self.sale_price if self.sale_price else self.price
    
    @property
    def is_on_sale(self):
        """Check if product is currently on sale"""
        return self.sale_price is not None and self.sale_price < self.price
    
    @property
    def discount_percentage(self):
        """Calculate discount percentage"""
        if self.is_on_sale:
            return round(((self.price - self.sale_price) / self.price) * 100)
        return 0
    
    @property
    def is_in_stock(self):
        """Check if product is in stock"""
        if not self.manage_stock:
            return True
        return self.stock_quantity > 0
    
    @property
    def is_low_stock(self):
        """Check if product is low in stock"""
        if not self.manage_stock:
            return False
        return self.stock_quantity <= self.low_stock_threshold


class ProductImage(models.Model):
    """Additional product images"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='merchandise/products/gallery/')
    alt_text = models.CharField(max_length=200, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['display_order']
        
    def __str__(self):
        return f"{self.product.name} - Image {self.display_order}"


class ProductVariant(models.Model):
    """Product variants (size, color, etc.)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    
    # Variant attributes
    name = models.CharField(max_length=100)  # "Large Red", "XL Blue", etc.
    size = models.CharField(max_length=20, blank=True)  # S, M, L, XL, XXL
    color = models.CharField(max_length=50, blank=True)
    material = models.CharField(max_length=100, blank=True)
    
    # Variant specifics
    sku = models.CharField(max_length=50, unique=True)
    price_adjustment = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    stock_quantity = models.PositiveIntegerField(default=0)
    
    # Images
    image = models.ImageField(upload_to='merchandise/variants/', blank=True)
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['product', 'size', 'color']
        ordering = ['size', 'color']
        
    def __str__(self):
        return f"{self.product.name} - {self.name}"
    
    @property
    def final_price(self):
        """Calculate final price including adjustments"""
        return self.product.current_price + self.price_adjustment


class ShoppingCart(models.Model):
    """Shopping cart for supporters"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supporter = models.OneToOneField(SupporterProfile, on_delete=models.CASCADE, related_name='shopping_cart')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Cart for {self.supporter.user.get_full_name()}"
    
    @property
    def total_items(self):
        """Get total number of items in cart"""
        return sum(item.quantity for item in self.items.all())
    
    @property
    def subtotal(self):
        """Calculate cart subtotal"""
        return sum(item.total_price for item in self.items.all())
    
    @property
    def total(self):
        """Calculate cart total including shipping"""
        # Add shipping calculation logic here
        return self.subtotal


class CartItem(models.Model):
    """Individual items in shopping cart"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(ShoppingCart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True, blank=True)
    
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['cart', 'product', 'variant']
        
    def __str__(self):
        variant_name = f" - {self.variant.name}" if self.variant else ""
        return f"{self.product.name}{variant_name} x{self.quantity}"
    
    @property
    def total_price(self):
        """Calculate total price for this cart item"""
        return self.unit_price * self.quantity


class Order(models.Model):
    """SAFA merchandise orders"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(max_length=20, unique=True)
    
    # Customer
    supporter = models.ForeignKey(SupporterProfile, on_delete=models.CASCADE, related_name='merchandise_orders')
    
    # Order details
    status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending Payment'),
        ('PAID', 'Paid'),
        ('PROCESSING', 'Processing'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
        ('REFUNDED', 'Refunded'),
    ], default='PENDING')
    
    # Pricing
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Payment
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='merchandise_orders', null=True, blank=True)
    payment_method = models.CharField(max_length=50, blank=True)
    
    # Shipping information
    shipping_name = models.CharField(max_length=200)
    shipping_address_line1 = models.CharField(max_length=200)
    shipping_address_line2 = models.CharField(max_length=200, blank=True)
    shipping_city = models.CharField(max_length=100)
    shipping_province = models.CharField(max_length=100)
    shipping_postal_code = models.CharField(max_length=20)
    shipping_phone = models.CharField(max_length=20, blank=True)
    
    # Tracking
    tracking_number = models.CharField(max_length=100, blank=True)
    shipped_date = models.DateTimeField(null=True, blank=True)
    delivered_date = models.DateTimeField(null=True, blank=True)
    
    # Special instructions
    order_notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Order {self.order_number}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate order number: SAFA-YYYY-XXXXXX
            from django.utils import timezone
            year = timezone.now().year
            count = Order.objects.filter(created_at__year=year).count() + 1
            self.order_number = f"SAFA-{year}-{count:06d}"
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    """Individual items in an order"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True, blank=True)
    
    # Product details at time of order
    product_name = models.CharField(max_length=200)
    product_sku = models.CharField(max_length=50)
    variant_name = models.CharField(max_length=100, blank=True)
    
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        variant_name = f" - {self.variant_name}" if self.variant_name else ""
        return f"{self.product_name}{variant_name} x{self.quantity}"


class Wishlist(models.Model):
    """Supporter wishlists"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supporter = models.OneToOneField(SupporterProfile, on_delete=models.CASCADE, related_name='wishlist')
    products = models.ManyToManyField(Product, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Wishlist for {self.supporter.user.get_full_name()}"


class ProductReview(models.Model):
    """Product reviews by supporters"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    supporter = models.ForeignKey(SupporterProfile, on_delete=models.CASCADE)
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, null=True, blank=True)
    
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])  # 1-5 stars
    title = models.CharField(max_length=200)
    review_text = models.TextField()
    
    # Review images
    image1 = models.ImageField(upload_to='merchandise/reviews/', blank=True)
    image2 = models.ImageField(upload_to='merchandise/reviews/', blank=True)
    image3 = models.ImageField(upload_to='merchandise/reviews/', blank=True)
    
    is_verified_purchase = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['product', 'supporter']
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.product.name} - {self.rating} stars by {self.supporter.user.get_full_name()}"
