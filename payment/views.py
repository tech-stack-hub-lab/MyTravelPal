from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY


def pricing(request):
    plans = {
        "free": {"name": "Free", "price": 0},
        "premium": {"name": "Premium", "price": settings.STRIPE_PRICE_ID},
    }

    return render(
        request,
        "pricing-page-view.html",
        {"plans": plans}
    )


def create_checkout_session(request):
    if request.method == 'POST':
        # Retrieve the price ID sent from the form
        price_id = request.POST.get('price_id')

        # Fallback check to prevent sending empty string to Stripe
        if not price_id:
            return render(request, 'error.html', {'message': 'Invalid Price ID.'})
    checkout_session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[
            {
                "price": price_id,
                "quantity": 1,
            }
        ],
        success_url=request.build_absolute_uri(
            '/success/?session_id={CHECKOUT_SESSION_ID}'
        ),
        cancel_url=request.build_absolute_uri('/cancel/'),
        client_reference_id=request.user.id,
    )

    return redirect(checkout_session.url, code=330)


@login_required
def success(request):
    session_id = request.GET.get('session_id')

    if session_id:
        try:
            session = stripe.checkout.Session.retrieve(session_id)

            if session.payment_status == 'paid':
                user = request.user
                user.subscription_status = 'active'
                user.subscription_plan = 'premium'
                user.save(update_fields=['subscription_status', 'subscription_plan'])
                messages.success(
                    request,
                    '🎉 Success! Your account has been upgraded to Premium.',
                )
                return redirect('homepage:dashboard')
        except Exception as exc:
            print(f'Stripe Error: {exc}')
            messages.error(
                request,
                'There was an issue verifying your payment.',
            )

    return redirect('homepage:dashboard')


def cancel(request):
    return render(request, "cancel.html")
