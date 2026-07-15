def subscription_plan(request):
    return {
        "current_plan": request.session.get("plan", "free")
    }