from django.urls import path
from . import views

app_name = 'merchandise'

urlpatterns = [
    # Store pages
    path('', views.store_home, name='store_home'),
    path('products/', views.product_list, name='product_list'),
    path('category/<slug:category_slug>/', views.product_list, name='category_products'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    
    # Shopping cart
    path('cart/', views.shopping_cart, name='cart'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/', views.update_cart_item, name='update_cart_item'),
    
    # Checkout and orders
    path('checkout/', views.checkout, name='checkout'),
    path('orders/', views.order_history, name='order_history'),
    path('order/<str:order_number>/', views.order_detail, name='order_detail'),
    
    # Wishlist
    path('wishlist/', views.wishlist, name='wishlist'),
    path('wishlist/toggle/', views.toggle_wishlist, name='toggle_wishlist'),
]
