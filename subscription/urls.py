from django.urls import path
from . import views     

urlpatterns = [
    # Subscription plans page
    path('', views.plans, name='plans'),

    # Stripe payment redirect
    path("pay/<int:plan_id>/", views.payment_redirect, name="pay"),

    # Account page
    path('account/', views.account, name='subscription_account'),
    path('account/delete/', views.delete_account, name='subscription_delete_account'),

    # Stripe success & cancel
    path("payment/success/", views.payment_success, name="payment_success"),
    path("payment/cancel/", views.payment_cancel, name="payment_cancel"),
]
