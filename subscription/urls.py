from django.urls import path
from . import views     

urlpatterns = [
    # Subscription plans page
    path('', views.plans, name='plans'),

    # Stripe payment redirect
    path("pay/<int:plan_id>/", views.payment_redirect, name="pay"),

    # Stripe success & cancel
    path("payment/success/", views.payment_success, name="payment_success"),
    path("payment/cancel/", views.payment_cancel, name="payment_cancel"),
]
