from django.urls import path

from myapp import views

urlpatterns = [
    path('', views.home, name='home'),
    path('products/<slug:slug>/', views.product_detail, name='product_detail'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<slug:slug>/', views.cart_add, name='cart_add'),
    path('cart/update/<slug:slug>/', views.cart_update, name='cart_update'),
    path('cart/remove/<slug:slug>/', views.cart_remove, name='cart_remove'),
    path('checkout/', views.checkout, name='checkout'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('faq/', views.faq, name='faq'),
    path('shipping-returns/', views.shipping_returns, name='shipping_returns'),
]