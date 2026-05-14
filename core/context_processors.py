def subscription_status(request):
    """Expose active subscription status to all templates."""
    has_active_subscription = False
    active_subscription_plan_id = None

    if request.user.is_authenticated:
        try:
            from subscription.models import UserSubscription
            user_subscription = request.user.subscription
            if user_subscription.is_valid():
                has_active_subscription = True
                active_subscription_plan_id = user_subscription.plan.id if user_subscription.plan else None
        except Exception:
            pass

    return {
        'has_active_subscription': has_active_subscription,
        'active_subscription_plan_id': active_subscription_plan_id,
    }
