from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .models import SubscriptionPlan, UserSubscription
from .stripe_utils import create_checkout_session

# -------------------------------
# 1️⃣ Subscription Plans Page
# -------------------------------
@login_required
def plans(request):
    """
    Shows all subscription plans with 'Pay Now' buttons.
    """
    all_plans = SubscriptionPlan.objects.all()
    
    # Check if user is logged in and already has an active subscription
    user_subscription = None
    if request.user.is_authenticated:
        try:
            user_subscription = request.user.subscription
            if user_subscription.is_valid():
                messages.info(request, f"You already have an active {user_subscription.plan.name} subscription until {user_subscription.end_date.strftime('%B %d, %Y')}")
        except:
            pass
    
    return render(request, 'subscription/plans.html', {'plans': all_plans, 'user_subscription': user_subscription})


# -------------------------------
# 2️⃣ Stripe Checkout Redirect
# -------------------------------
@login_required
def payment_redirect(request, plan_id):
    """
    Creates a Stripe checkout session for the selected plan and redirects.
    """
    plan = get_object_or_404(SubscriptionPlan, id=plan_id)
    session = create_checkout_session(plan, request)
    
    # Store session ID in user's session for later retrieval
    request.session['stripe_session_id'] = session.id
    request.session['plan_id'] = plan_id
    
    return redirect(session.url, code=303)


# -------------------------------
# 3️⃣ Success & Cancel Pages
# -------------------------------
@login_required
def payment_success(request):
    """
    Shows a simple success page after payment and creates UserSubscription record.
    """
    plan_id = request.session.get('plan_id')
    
    if plan_id:
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id)
            
            # Create or update user subscription
            subscription, created = UserSubscription.objects.get_or_create(
                user=request.user,
                defaults={
                    'plan': plan,
                    'end_date': timezone.now() + timedelta(days=plan.duration_days),
                    'is_active': True
                }
            )
            
            # If subscription already existed, update it
            if not created:
                subscription.plan = plan
                subscription.end_date = timezone.now() + timedelta(days=plan.duration_days)
                subscription.is_active = True
                subscription.save()
            
            messages.success(request, f"Welcome! Your {plan.name} subscription is now active.")
            
            # Clean up session
            request.session.pop('stripe_session_id', None)
            request.session.pop('plan_id', None)
            
        except SubscriptionPlan.DoesNotExist:
            messages.error(request, "Subscription plan not found.")
    
    return render(request, "subscription/payment_success.html")


@login_required
def payment_cancel(request):
    """
    Shows a cancel page if payment fails or is canceled.
    """
    return render(request, "subscription/payment_fail.html")
