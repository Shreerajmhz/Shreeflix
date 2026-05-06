import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

def create_checkout_session(plan, request=None):
    from django.urls import reverse
    
    # Build absolute URLs for success and cancel
    if request:
        protocol = 'https' if request.is_secure() else 'http'
        domain = request.get_host()
        base_url = f"{protocol}://{domain}"
    else:
        base_url = "http://localhost:8000"
    
    success_url = base_url + reverse('payment_success')
    cancel_url = base_url + reverse('payment_cancel')
    
    # Prepare customer info if user is authenticated
    customer_email = None
    if request and request.user.is_authenticated:
        customer_email = request.user.email
    
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "unit_amount": int(plan.price * 100),  # Stripe uses cents
                "product_data": {
                    "name": plan.name,
                },
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=success_url,
        cancel_url=cancel_url,
        customer_email=customer_email,
    )
    return session
