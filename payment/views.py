from django.shortcuts import render, redirect
from django.conf import settings
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY


def pricing(request):
    plans = {
        "free": {"name": "Free", "price": 0},
        "premium": {"name": "Premium", "price": 5},
    }

    return render(
        request,
        "pricing-page-view.html",
        {"plans": plans}
    )


def create_checkout_session(request):
    checkout_session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[
            {
                "price": settings.STRIPE_PRICE_ID,
                "quantity": 1,
            }
        ],
        success_url=request.build_absolute_uri("/success/"),
        cancel_url=request.build_absolute_uri("/cancel/"),
    )

    return redirect(checkout_session.url)


from django.contrib.auth.decorators import login_required

@login_required
def success(request):
    request.session["plan"] = "premium"
    return render(request, "success.html")



def cancel(request):
    return render(request, "cancel.html")

