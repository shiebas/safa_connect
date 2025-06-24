# SAFA Official Merchandise Store - Comprehensive Manual

## Table of Contents
1. [Overview](#overview)
2. [Store Access](#store-access)
3. [User Features](#user-features)
4. [Admin Management](#admin-management)
5. [Payment Integration](#payment-integration)
6. [UI/UX Features](#uiux-features)
7. [Technical Architecture](#technical-architecture)
8. [Troubleshooting](#troubleshooting)

---

## Overview

The SAFA Official Merchandise Store is a comprehensive e-commerce platform integrated into the SAFA Global system, allowing supporters to purchase official SAFA branded merchandise including jerseys, training gear, accessories, and memorabilia.

### Key Features
- **Product Catalog**: Browse products by categories (Jerseys, Training Gear, Casual Wear, Accessories, Equipment, Souvenirs)
- **Advanced Search & Filtering**: Search by name, filter by price range, category, and sort options
- **Shopping Cart**: Add products with variants (sizes, colors) to cart
- **Wishlist**: Save favorite products for later purchase
- **Order Management**: Complete checkout process with shipping details
- **Order History**: Track past purchases and order status
- **Admin Dashboard**: Complete product and order management for staff
- **Mobile Responsive**: Fully optimized for all device sizes
- **Secure Checkout**: Protected payment processing with VAT calculation

---

## Store Access

### For All Users (Authenticated and Guests)

#### Primary Navigation:
- **Main Navigation Bar**: "SAFA Store" link is visible to all users in the top navigation
- **Direct URL Access**: `https://yourdomain.com/store/`

### For Authenticated Supporters

#### Member Portal Access:
1. **Member Portal Dropdown**: 
   - "SAFA Store" - Main store homepage
   - "Shopping Cart" - View cart contents
   - "My Wishlist" - Saved favorite products
   - "Order History" - Past purchase records

2. **Supporter Profile Page**:
   - "SAFA Store" action button for direct access

#### Available URLs:
- **Store Home**: `/store/`
- **Product Categories**: `/store/category/<category-slug>/`
- **Product Details**: `/store/product/<product-slug>/`
- **Shopping Cart**: `/store/cart/`
- **Checkout**: `/store/checkout/`
- **Wishlist**: `/store/wishlist/`
- **Order History**: `/store/orders/`
- **Order Details**: `/store/order/<order-number>/`

### For Superusers/Admins

#### Superuser Dashboard Access:
1. **Quick Action Button**: "SAFA Store" button in dashboard for immediate access
2. **Django Admin Access**: `/admin/merchandise/` for backend management

#### Admin URLs:
- **Product Management**: `/admin/merchandise/product/`
- **Category Management**: `/admin/merchandise/productcategory/`
- **Order Management**: `/admin/merchandise/order/`
- **Inventory Management**: `/admin/merchandise/productvariant/`

---

## User Features

### 1. Product Browsing
- **Category Navigation**: Browse by product categories
- **Search Functionality**: Text search across product names, descriptions, and tags
- **Filtering Options**: 
  - Price range filtering
  - Category filtering
  - Sort by: Name, Price (Low to High), Price (High to Low), Newest, Rating
- **Pagination**: 12 products per page for optimal loading

### 2. Product Details
- **High-Quality Images**: Multiple product images with zoom functionality
- **Product Variants**: Size, color, and style options
- **Detailed Descriptions**: Complete product information
- **Pricing Information**: Regular price and sale price display
- **Stock Status**: Real-time availability checking
- **Customer Reviews**: Rating system and review display

### 3. Shopping Cart
- **Add to Cart**: Single-click product addition
- **Quantity Management**: Update quantities or remove items
- **Variant Selection**: Choose size, color, and other options
- **Cart Persistence**: Cart contents saved across sessions
- **Price Calculation**: Real-time subtotal updates
- **Mobile Optimized**: Touch-friendly cart management

### 4. Wishlist
- **Save for Later**: Heart icon to add/remove from wishlist
- **Wishlist Management**: View all saved products
- **Quick Actions**: Add wishlist items to cart
- **Wishlist Stats**: Total items and estimated value
- **Bulk Operations**: Add all wishlist items to cart at once

### 5. Checkout Process
- **Secure Checkout**: Protected payment processing
- **Shipping Information**: Complete address collection
- **Order Summary**: Detailed cost breakdown
- **Tax Calculation**: Automatic 15% VAT calculation
- **Shipping Costs**: R50 flat rate shipping
- **Order Notes**: Optional special instructions field

### 6. Order Management
- **Order Confirmation**: Immediate order confirmation with unique order number
- **Order History**: Complete purchase history
- **Order Tracking**: Status updates (Pending → Confirmed → Processing → Shipped → Delivered)
- **Order Details**: Full itemized order information
- **Reorder Functionality**: Quick reorder from past purchases

---

## Admin Management

### 1. Product Management
- **Add New Products**: Complete product creation form
- **Product Categories**: Organize products into logical categories
- **Product Images**: Multiple image upload with automatic resizing
- **Inventory Management**: Stock level tracking and alerts
- **Product Variants**: Manage sizes, colors, and SKUs
- **Pricing Control**: Set regular prices, sale prices, and discount periods

### 2. Order Management
- **Order Overview**: Dashboard view of all orders
- **Order Processing**: Update order status and tracking
- **Customer Information**: Access to customer details and shipping addresses
- **Order Fulfillment**: Print shipping labels and packing slips
- **Revenue Reporting**: Sales analytics and reporting tools

### 3. Content Management
- **Featured Products**: Highlight special products on homepage
- **Category Management**: Create and organize product categories
- **Promotional Banners**: Manage store promotions and sales
- **SEO Management**: Meta descriptions and search optimization

---

## Payment Integration

### Current Status
The store is prepared for payment integration with the following features:

### 1. Payment Processing Framework
- **Order Creation**: Complete order objects with payment fields
- **Tax Calculation**: Automatic 15% VAT calculation
- **Shipping Costs**: Configurable shipping rate calculation
- **Order Totals**: Accurate price calculation including all fees

### 2. Recommended Payment Gateways for South Africa
- **PayFast** (Recommended): Local payment gateway supporting EFT, Credit Cards, and Instant EFT
- **PayGate**: Enterprise payment solutions
- **Stripe**: International payment processing
- **PayPal**: Global payment platform

### 3. Payment Integration Steps
1. **Choose Payment Provider**: Select from recommended gateways
2. **API Integration**: Add payment gateway SDK
3. **Security Setup**: Implement SSL and security measures
4. **Testing**: Comprehensive payment testing
5. **Go Live**: Production payment processing

---

## UI/UX Features

### 1. Modern Design
- **SAFA Brand Colors**: Consistent green (#006633) color scheme
- **Responsive Layout**: Mobile-first design approach
- **Clean Typography**: Easy-to-read fonts and spacing
- **Intuitive Navigation**: Clear menu structure and breadcrumbs

### 2. Mobile Optimization
- **Touch-Friendly**: Large buttons and touch targets
- **Swipe Navigation**: Mobile-friendly product browsing
- **Mobile Cart**: Optimized shopping cart for mobile devices
- **Fast Loading**: Optimized images and code for mobile networks

### 3. User Experience
- **Quick Add to Cart**: One-click product addition
- **Visual Feedback**: Loading states and success messages
- **Error Handling**: Clear error messages and recovery options
- **Accessibility**: WCAG compliant design elements

### 4. Interactive Elements
- **Product Image Zoom**: Hover and click to zoom on product images
- **Quantity Selectors**: Easy quantity adjustment controls
- **Wishlist Hearts**: Animated heart icons for wishlist actions
- **Toast Notifications**: Non-intrusive success and error messages

---

## Technical Architecture

### 1. Django Models
- **Product**: Core product information and metadata
- **ProductCategory**: Hierarchical category organization
- **ProductVariant**: Size, color, and SKU management
- **ProductImage**: Multiple image support per product
- **ShoppingCart**: User-specific cart persistence
- **CartItem**: Individual cart item management
- **Order**: Complete order information and status
- **OrderItem**: Individual order line items
- **Wishlist**: User wishlist functionality
- **ProductReview**: Customer review and rating system

### 2. Views and Templates
- **Class-Based Views**: Organized view structure
- **Template Inheritance**: Consistent design across all pages
- **AJAX Integration**: Dynamic cart and wishlist updates
- **Form Handling**: Secure form processing and validation

### 3. Static Assets
- **CSS Framework**: Bootstrap 5 with custom SAFA styling
- **JavaScript**: Modern ES6+ JavaScript for interactivity
- **Image Processing**: Automatic image optimization and resizing
- **Font Awesome**: Comprehensive icon library

### 4. Security Features
- **CSRF Protection**: Cross-site request forgery protection
- **User Authentication**: Django's built-in authentication system
- **Input Validation**: Server-side and client-side validation
- **SQL Injection Protection**: Django ORM protection

---

## Troubleshooting

### Common Issues and Solutions

#### 1. Products Not Displaying
**Issue**: Products not showing on store homepage
**Solution**: 
- Check if products are marked as "ACTIVE" status
- Verify product images are properly uploaded
- Run: `python manage.py populate_merchandise` to add sample data

#### 2. Cart Issues
**Issue**: Items not adding to cart
**Solution**:
- Ensure user is logged in (cart requires authentication)
- Check if product variants are properly configured
- Verify CSRF tokens are included in AJAX requests

#### 3. Checkout Problems
**Issue**: Checkout form not submitting
**Solution**:
- Verify all required fields are filled
- Check shipping address validation
- Ensure payment integration is properly configured

#### 4. Image Display Issues
**Issue**: Product images not displaying
**Solution**:
- Check MEDIA_URL and MEDIA_ROOT settings
- Verify image file permissions
- Ensure proper image file formats (JPEG, PNG, WebP)

#### 5. Order History Empty
**Issue**: Users can't see their order history
**Solution**:
- Verify user has supporter profile
- Check if orders are properly associated with user
- Ensure order history view has correct permissions

### Admin Troubleshooting

#### 1. Product Management
- **Creating Products**: Use Django admin `/admin/merchandise/product/`
- **Managing Categories**: Organize through `/admin/merchandise/productcategory/`
- **Inventory Updates**: Monitor stock levels and update variants

#### 2. Order Processing
- **Order Status Updates**: Change status through admin interface
- **Customer Communication**: Use order notes for customer updates
- **Shipping Management**: Update tracking information

### Performance Optimization

#### 1. Database Optimization
- **Indexing**: Ensure proper database indexes on frequently queried fields
- **Query Optimization**: Use select_related and prefetch_related for complex queries
- **Database Maintenance**: Regular cleanup of old cart items and session data

#### 2. Image Optimization
- **Image Compression**: Optimize product images for web display
- **Lazy Loading**: Implement lazy loading for product images
- **CDN Integration**: Consider CDN for static file delivery

---

## Getting Started

### For New Users
1. **Browse Products**: Visit `/store/` to explore available products
2. **Create Account**: Register for full shopping features
3. **Add to Cart**: Start shopping by adding products to cart
4. **Checkout**: Complete purchase with shipping information
5. **Track Orders**: Monitor order status in order history

### For Administrators
1. **Access Admin**: Log in to Django admin interface
2. **Add Products**: Create new products and categories
3. **Manage Orders**: Process and fulfill customer orders
4. **Monitor Analytics**: Track sales and inventory levels
5. **Update Content**: Maintain product information and pricing

### For Developers
1. **Setup Environment**: Install requirements and configure settings
2. **Run Migrations**: Apply database migrations
3. **Populate Data**: Use management command to add sample data
4. **Configure Payment**: Integrate chosen payment gateway
5. **Deploy**: Set up production environment with proper security

---

This comprehensive manual covers all aspects of the SAFA Official Merchandise Store, from user experience to technical implementation. The store is fully functional and ready for payment integration and production deployment.
   - Product Categories
   - Products
   - Orders
   - Shopping Carts
   - Wishlists
   - Product Reviews

#### Admin URLs:
- **Product Management**: `/admin/merchandise/product/`
- **Category Management**: `/admin/merchandise/productcategory/`
- **Order Management**: `/admin/merchandise/order/`
- **Analytics**: Superuser Dashboard → Store metrics

---

## Admin Management

### Product Management

#### Adding New Products:
1. Navigate to Django Admin → Merchandise → Products → Add Product
2. Fill required fields:
   - **Name**: Product display name
   - **Slug**: URL-friendly name (auto-generated)
   - **Category**: Select from existing categories
   - **Description**: Detailed product description
   - **Price**: Base price in ZAR
   - **SKU**: Unique product identifier
   - **Stock Management**: Enable/disable inventory tracking
   - **Images**: Upload main product image

#### Product Variants:
- **Size Variants**: S, M, L, XL, XXL
- **Color Variants**: Different colors available
- **Price Adjustments**: Additional cost for specific variants
- **Stock Tracking**: Individual stock levels per variant

#### Category Management:
1. **Create Categories**: Django Admin → Product Categories
2. **Featured Categories**: Mark for homepage display
3. **Display Order**: Control category appearance order
4. **Category Images**: Upload category thumbnails

### Order Management

#### Order Processing:
1. **View Orders**: Django Admin → Orders
2. **Order Status Options**:
   - Pending Payment
   - Paid
   - Processing
   - Shipped
   - Delivered
   - Cancelled
   - Refunded

#### Order Details:
- Customer information
- Shipping address
- Order items with quantities
- Payment status
- Tracking information

### Inventory Management:
- **Stock Levels**: Monitor product availability
- **Low Stock Alerts**: Automated warnings
- **Stock Updates**: Bulk inventory adjustments
- **Variant Tracking**: Individual variant stock levels

---

## User Features

### Browsing Products

#### Product Catalog:
- **Grid View**: Visual product cards with images
- **Category Filtering**: Browse by product type
- **Search Function**: Text search across products
- **Price Filtering**: Set min/max price ranges
- **Sorting Options**:
  - Name (A-Z)
  - Price (Low to High / High to Low)
  - Newest First
  - Highest Rated

#### Product Details:
- **Image Gallery**: Multiple product photos
- **Variant Selection**: Choose size, color options
- **Stock Status**: Availability information
- **Pricing**: Current price, sale pricing, discounts
- **Product Information**: Description, dimensions, weight
- **Customer Reviews**: Ratings and review system

### Shopping Experience

#### Shopping Cart:
- **Add to Cart**: Single or multiple quantities
- **Variant Support**: Size/color selection
- **Quantity Updates**: Modify item quantities
- **Remove Items**: Delete unwanted products
- **Price Calculation**: Subtotal, shipping, tax display
- **Persistent Cart**: Saved between sessions

#### Wishlist:
- **Save for Later**: Heart icon to add/remove
- **Wishlist Page**: View all saved products
- **Quick Actions**: Move to cart, remove items
- **Sharing**: Share wishlist with others

#### Checkout Process:
1. **Cart Review**: Verify items and quantities
2. **Shipping Information**: Delivery address details
3. **Payment Method**: Select payment option
4. **Order Confirmation**: Review before submission
5. **Order Placement**: Receive order number
6. **Email Confirmation**: Automated order receipt

### Account Features

#### Order History:
- **Past Orders**: Complete order listing
- **Order Details**: Item details, status, tracking
- **Reorder**: Quickly reorder previous purchases
- **Order Status**: Real-time status updates
- **Download Invoices**: PDF order receipts

#### Profile Integration:
- **Supporter Profile**: Linked to SAFA supporter account
- **Shipping Defaults**: Saved shipping addresses
- **Preference Tracking**: Purchase history insights
- **Membership Benefits**: Supporter-specific discounts

---

## Payment System

### Current Implementation:
- **Invoice Generation**: Orders create invoices in existing system
- **Payment Reference**: Unique payment identifiers
- **Currency**: South African Rand (ZAR)
- **Tax Calculation**: 15% VAT included
- **Shipping Costs**: Flat rate shipping

### Payment Integration Options:

#### PayFast (Recommended for South Africa):
```python
# Payment configuration
PAYFAST_MERCHANT_ID = 'your_merchant_id'
PAYFAST_MERCHANT_KEY = 'your_merchant_key'
PAYFAST_SANDBOX = True  # Set False for production
```

#### Payment Gateway Features:
- **Secure Processing**: PCI compliant payment handling
- **Multiple Methods**: Credit cards, EFT, instant banking
- **Mobile Payments**: Mobile-optimized checkout
- **Fraud Protection**: Advanced security measures
- **Webhooks**: Real-time payment notifications

### Order Fulfillment:
1. **Payment Confirmation**: Automated status updates
2. **Inventory Deduction**: Stock level adjustments
3. **Fulfillment Workflow**: Pick, pack, ship process
4. **Tracking Updates**: Shipping notifications
5. **Delivery Confirmation**: Completion notifications

---

## Technical Architecture

### Models Structure:

#### Core Models:
- **ProductCategory**: Product categorization
- **Product**: Main product information
- **ProductVariant**: Size/color variations
- **ProductImage**: Product photo gallery
- **ShoppingCart**: User cart management
- **CartItem**: Individual cart items
- **Order**: Order header information
- **OrderItem**: Order line items
- **Wishlist**: Saved product lists
- **ProductReview**: Customer feedback

#### Database Relationships:
```
ProductCategory (1) → (Many) Product
Product (1) → (Many) ProductVariant
Product (1) → (Many) ProductImage
SupporterProfile (1) → (1) ShoppingCart
ShoppingCart (1) → (Many) CartItem
SupporterProfile (1) → (Many) Order
Order (1) → (Many) OrderItem
SupporterProfile (1) → (1) Wishlist
Product (Many) ← → (Many) Wishlist
```

### URL Structure:
```
/store/                          # Store homepage
/store/products/                 # All products
/store/category/<slug>/          # Category products
/store/product/<slug>/           # Product detail
/store/cart/                     # Shopping cart
/store/checkout/                 # Checkout process
/store/orders/                   # Order history
/store/order/<order_number>/     # Order detail
/store/wishlist/                 # User wishlist
```

### API Endpoints:
```
POST /store/cart/add/            # Add to cart
POST /store/cart/update/         # Update cart item
POST /store/wishlist/toggle/     # Wishlist management
```

### Templates:
- `merchandise/store_home.html` - Store homepage
- `merchandise/product_list.html` - Product catalog
- `merchandise/product_detail.html` - Product details
- `merchandise/shopping_cart.html` - Cart management
- `merchandise/checkout.html` - Checkout process
- `merchandise/order_history.html` - Order listing
- `merchandise/order_detail.html` - Order details
- `merchandise/wishlist.html` - Wishlist management

---

## Sample Data

### Pre-loaded Products:

#### Official Jerseys:
- Bafana Bafana Home Jersey 2024 (R799 - was R899)
- Bafana Bafana Away Jersey 2024 (R899)
- Banyana Banyana Home Jersey 2024 (R849)

#### Training Gear:
- SAFA Training Polo Shirt (R399)
- SAFA Training Shorts (R249 - was R299)
- SAFA Football Training Cones Set (R199)

#### Casual Wear:
- SAFA Casual T-Shirt (R249)
- SAFA Hoodie (R599)
- SAFA Track Suit (R749 - was R899)

#### Accessories:
- SAFA Baseball Cap (R199)
- SAFA Scarf (R149)
- SAFA Water Bottle (R89)

#### Equipment:
- Official SAFA Match Ball (R599)
- SAFA Goalkeeper Gloves (R449)

#### Souvenirs:
- SAFA Keychain (R39)
- SAFA Mug (R99)
- SAFA Car Sticker Set (R69)

### Product Features:
- **Size Variants**: S, M, L, XL, XXL for apparel
- **Stock Management**: Realistic inventory levels
- **Pricing**: Sale prices and discounts
- **Categories**: 6 main product categories
- **Featured Products**: Highlighted on homepage

---

## Troubleshooting

### Common Issues:

#### Product Images Not Displaying:
- **Cause**: Missing image files or incorrect media configuration
- **Solution**: Check MEDIA_URL and MEDIA_ROOT settings
- **Fallback**: Placeholder images automatically generated

#### Cart Items Not Persisting:
- **Cause**: Session configuration issues
- **Solution**: Verify Django session middleware enabled
- **Check**: User authentication status

#### Payment Processing Errors:
- **Cause**: Payment gateway configuration
- **Solution**: Verify API keys and webhook URLs
- **Testing**: Use sandbox mode for development

#### Stock Management Issues:
- **Cause**: Concurrent order processing
- **Solution**: Database transaction handling
- **Monitor**: Inventory levels vs. sales

#### Performance Issues:
- **Optimization**: Database query optimization
- **Caching**: Implement product catalog caching
- **Images**: Optimize image sizes and formats

### Admin Access Issues:

#### Cannot Access Admin:
- **Check**: User has superuser permissions
- **Verify**: Django admin URLs are configured
- **Solution**: Create superuser account

#### Product Creation Errors:
- **Slug Conflicts**: Ensure unique product slugs
- **Required Fields**: Verify all mandatory fields completed
- **Image Upload**: Check file permissions and media settings

### User Experience Issues:

#### Mobile Responsiveness:
- **CSS**: Bootstrap responsive classes implemented
- **Testing**: Cross-device compatibility verified
- **Images**: Responsive image sizing

#### Search Not Working:
- **Database**: Check product search fields
- **Indexes**: Verify database indexing
- **Filtering**: Test category and price filters

---

## Maintenance

### Regular Tasks:
1. **Inventory Updates**: Monitor stock levels
2. **Order Processing**: Daily order review
3. **Product Updates**: Add new products seasonally
4. **Image Management**: Optimize and update product photos
5. **Performance Monitoring**: Track site speed and errors

### Security:
- **Payment Security**: PCI compliance maintenance
- **User Data**: GDPR/POPI Act compliance
- **Admin Access**: Regular permission audits
- **SSL Certificates**: Ensure HTTPS encryption

### Analytics:
- **Sales Reports**: Track popular products
- **User Behavior**: Monitor cart abandonment
- **Inventory Turnover**: Optimize stock levels
- **Revenue Tracking**: Monthly sales analysis

---

## Support

### For Users:
- **Contact**: SAFA customer service
- **Email**: store@safa.net
- **Phone**: +27 11 494 3522
- **Hours**: Monday-Friday 8AM-5PM

### For Admins:
- **Technical Support**: IT department
- **Training**: Admin user training sessions
- **Documentation**: This manual and Django documentation
- **Updates**: Regular system update notifications

---

*Last Updated: June 23, 2025*
*Version: 1.0*
