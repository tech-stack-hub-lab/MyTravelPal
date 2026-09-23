def subscription_plan(request):
    if request.user.is_authenticated:
        return {
            "current_plan": request.user.subscription_plan,
            "billing_cycle": request.user.billing_cycle,
            "subscription_status": request.user.subscription_status,
            "subscription_start": request.user.subscription_start,
            "subscription_end": request.user.subscription_end,
        }

    return {}