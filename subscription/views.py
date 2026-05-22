from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.contrib.auth.models import User
import stripe
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
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
# 2️⃣ Account Detail Page
# -------------------------------
@login_required
def account(request):
    """
    Displays the current user's subscription details and a link to change plan.
    """
    user_subscription = None
    try:
        user_subscription = request.user.subscription
    except UserSubscription.DoesNotExist:
        user_subscription = None

    return render(request, 'subscription/account.html', {
        'user_subscription': user_subscription,
    })


@login_required
def delete_account(request):
    """
    Deletes the current authenticated user account.
    """
    if request.method != 'POST':
        messages.error(request, 'Invalid request method for account deletion.')
        return redirect('subscription_account')

    user = request.user
    auth_logout(request)
    user.delete()

    messages.success(request, 'Your account has been deleted successfully.')
    return redirect('index')


# -------------------------------
# 3️⃣ Stripe Checkout Redirect
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
    stripe_session_id = request.session.get('stripe_session_id')
    
    if plan_id and stripe_session_id:
        try:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            session = stripe.checkout.Session.retrieve(stripe_session_id)
            
            if session.payment_status == 'paid':
                plan = SubscriptionPlan.objects.get(id=plan_id)
                
                # Create or update user subscription
                subscription, created = UserSubscription.objects.get_or_create(
                    user=request.user,
                    defaults={
                        'plan': plan,
                        'end_date': timezone.now() + timedelta(days=plan.duration_days),
                        'is_active': True,
                        'stripe_session_id': stripe_session_id
                    }
                )
                
                # If subscription already existed, update it
                if not created:
                    subscription.plan = plan
                    subscription.end_date = timezone.now() + timedelta(days=plan.duration_days)
                    subscription.is_active = True
                    subscription.stripe_session_id = stripe_session_id
                    subscription.save()
                
                messages.success(request, f"Welcome! Your {plan.name} subscription is now active.")
            else:
                messages.error(request, "Your payment has not been completed yet.")
                return redirect('plans')
            
            # Clean up session
            request.session.pop('stripe_session_id', None)
            request.session.pop('plan_id', None)
            
        except stripe.error.StripeError:
            messages.error(request, "An error occurred while verifying your payment.")
            return redirect('plans')
        except SubscriptionPlan.DoesNotExist:
            messages.error(request, "Subscription plan not found.")
            return redirect('plans')
    else:
        # Fallback/Direct access: check if they already have an active subscription
        # (e.g. if the webhook processed it, or if they are refreshing the page)
        try:
            subscription = request.user.subscription
            if not subscription.is_valid():
                messages.error(request, "No active subscription found. Please select a plan.")
                return redirect('plans')
        except UserSubscription.DoesNotExist:
            messages.error(request, "No active subscription found. Please select a plan.")
            return redirect('plans')
            
    return render(request, "subscription/payment_success.html")


@login_required
def payment_cancel(request):
    """
    Shows a cancel page if payment fails or is canceled.
    """
    return render(request, "subscription/payment_fail.html")


@csrf_exempt
def stripe_webhook(request):
    """
    Webhook handler to receive checkout session events from Stripe.
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET
    event = None

    if not sig_header and not settings.DEBUG:
        return HttpResponse(status=400)

    try:
        if not endpoint_secret and settings.DEBUG:
            # For testing without signature validation in debug mode
            import json
            event = stripe.Event.construct_from(
                json.loads(payload), stripe.api_key
            )
        else:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)
    except Exception as e:
        return HttpResponse(status=400)

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        # Get user and plan details from metadata or client_reference_id
        user_id = session.get('metadata', {}).get('user_id') or session.get('client_reference_id')
        plan_id = session.get('metadata', {}).get('plan_id')
        stripe_session_id = session.get('id')

        if user_id and plan_id:
            try:
                user = User.objects.get(id=int(user_id))
                plan = SubscriptionPlan.objects.get(id=int(plan_id))

                # Create or update user subscription
                subscription, created = UserSubscription.objects.get_or_create(
                    user=user,
                    defaults={
                        'plan': plan,
                        'end_date': timezone.now() + timedelta(days=plan.duration_days),
                        'is_active': True,
                        'stripe_session_id': stripe_session_id
                    }
                )

                if not created:
                    subscription.plan = plan
                    subscription.end_date = timezone.now() + timedelta(days=plan.duration_days)
                    subscription.is_active = True
                    subscription.stripe_session_id = stripe_session_id
                    subscription.save()

            except (User.DoesNotExist, SubscriptionPlan.DoesNotExist):
                pass

    return HttpResponse(status=200)
