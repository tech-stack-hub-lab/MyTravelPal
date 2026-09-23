# from django.conf import settings
# from django.contrib import messages
# from django.contrib.auth.decorators import login_required
# from django.shortcuts import redirect, render
# from django.utils import timezone
# from datetime import timedelta
# from requests import request
# import stripe

# stripe.api_key = settings.STRIPE_SECRET_KEY


# def pricing(request):
#     plans = {
#         "free": {"name": "Free", "price": 0},
#         "premium": {"name": "Premium", "price": settings.STRIPE_PRICE_ID},
#     }

#     return render(
#         request,
#         "pricing-page-view.html",
#         {"plans": plans}
#     )


# def create_checkout_session(request):
#     if request.method == 'POST':
#         # Retrieve the price ID sent from the form
#         price_id = request.POST.get('price_id')

#         # Fallback check to prevent sending empty string to Stripe
#         # if not price_id:
#         # return render(request, 'error.html', {'message': 'Invalid Price ID.'})
        

#         checkout_session = stripe.checkout.Session.create(
#              mode="subscription",
#              line_items=[
#               {
#                 "price": price_id,
#                 "quantity": 1,
#               }
#             ],
#         domain = request.build_absolute_uri("/")[:-1]

#         success_url=f"{domain}/success/?session_id={{CHECKOUT_SESSION_ID}}",
#         cancel_url=f"{domain}/cancel/",
#         client_reference_id=request.user.id,
#     )
        


#     return redirect(checkout_session.url)


# @login_required
# def success(request):
#     session_id = request.GET.get("session_id")
#     print("Checkout Session ID:", checkout_session.id)
#     print("Checkout URL:", checkout_session.url)

#     if not session_id:
#         messages.error(request, "Missing Stripe session.")
#         return redirect("homepage:dashboard")

#     try:
#         session = stripe.checkout.Session.retrieve(session_id)

#         if session.payment_status == "paid":
#             user = request.user

#             # Store plan in session
#             request.session["current_plan"] = "Premium"

#             # Update user subscription
#             user.subscription_plan = "Premium"
#             user.billing_cycle = "Monthly"
#             user.subscription_status = "Active"
#             user.subscription_start = timezone.now().date()
#             user.subscription_end = timezone.now().date() + timedelta(days=30)
#             user.save()
#             print (f"User {user.username} upgraded to Premium. Subscription ends on {user.subscription_plan}.")
#             messages.success(
#                 request,
#                 "🎉 Success! Your account has been upgraded to Premium.",
#                 extra_tags="alert-success",
#             )

#             if session.payment_status == "paid":
#                 return redirect("homepage:dashboard")
#     except Exception as exc:
#         print(f"Stripe Error: {exc}")
#         return redirect("payment:success")
        

        

# def cancel(request):
#     return render(request, "cancel.html")

from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY


def pricing(request):
    plans = {
        "free": {
            "name": "Free",
            "price": 0,
        },
        "premium": {
            "name": "Premium",
            "price": settings.STRIPE_PRICE_ID,
        },
    }

    return render(
        request,
        "pricing-page-view.html",
        {"plans": plans},
    )


@login_required
def create_checkout_session(request):
    if request.method != "POST":
        return redirect("payment:pricing")

    price_id = request.POST.get("price_id")

    if not price_id:
        messages.error(request, "Invalid Price ID.")
        return redirect("payment:pricing")

    try:
        success_url = (
            request.build_absolute_uri("/success/")
            + "?session_id={CHECKOUT_SESSION_ID}"
        )

        cancel_url = request.build_absolute_uri("/cancel/")

        print("SUCCESS URL:", success_url)

        checkout_session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[
                {
                    "price": price_id,
                    "quantity": 1,
                }
            ],
            success_url=success_url,
            cancel_url=cancel_url,
            client_reference_id=request.user.id,
        )

        print("STRIPE SESSION ID:", checkout_session.id)

        return redirect(checkout_session.url)

    except Exception as exc:
        print("Stripe Checkout Error:", exc)

        messages.error(
            request,
            "Unable to create Stripe checkout session.",
        )

        return redirect("payment:pricing")


@login_required
def success(request):
    session_id = request.GET.get("session_id")

    print("SESSION ID RECEIVED:", session_id)

    if not session_id:
        messages.error(request, "Missing Stripe session.")
        return redirect("homepage:dashboard")

    try:
        session = stripe.checkout.Session.retrieve(session_id)

        print("PAYMENT STATUS:", session.payment_status)

        if session.payment_status == "paid":
            user = request.user

            # Session
            request.session["current_plan"] = "Premium"
            request.session.modified = True

            # Database
            user.subscription_plan = "Premium"
            user.billing_cycle = "Monthly"
            user.subscription_status = "Active"
            user.subscription_start = timezone.now().date()
            user.subscription_end = (
                timezone.now().date() + timedelta(days=30)
            )
            user.save()

            print(
                f"User {user.username} upgraded to "
                f"{user.subscription_plan}"
            )

            messages.success(
                request,
                "🎉 Success! Your account has been upgraded to Premium.",
                extra_tags="alert-success",
            )

        return redirect("homepage:dashboard")

    except Exception as exc:
        print("Stripe Error:", exc)

        messages.error(
            request,
            "There was an issue verifying your payment."
        )

        return redirect("homepage:dashboard")


def cancel(request):
    messages.warning(
        request,
        "Payment was cancelled."
    )

    return redirect("payment:pricing")