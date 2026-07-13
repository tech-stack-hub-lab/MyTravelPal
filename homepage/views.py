from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import logout
from django.http import JsonResponse
from .forms import BookingImportForm, TripForm
from .models import BookingImport, CalendarEvent, Flight, HotelBooking, Trip
from django.views.decorators.cache import cache_page
from django.contrib.auth.decorators import login_required
import stripe
from django.utils import timezone
from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from .forms import (
    TripForm,
    FlightForm,
    HotelBookingForm,
    CalendarEventForm)
from .models import (
    Trip,
    Flight,
    HotelBooking,
    CalendarEvent)


stripe.api_key = settings.STRIPE_SECRET_KEY



@cache_page(20)
def index(request):
    return render(request, 'index.html')

@login_required
def dashboard(request):
 
    trips = Trip.objects.filter(user=request.user)
 
    flights = Flight.objects.filter(
        trip__user=request.user
    )
 
    hotels = HotelBooking.objects.filter(
        trip__user=request.user
    )
 
    events = CalendarEvent.objects.filter(
        trip__user=request.user
    )
 
    upcoming_trips = trips.filter(
        start_date__gte=timezone.now().date()
    )
    progress = 0
    if trips.exists():
        progress += 25
    if flights.exists():
        progress += 25
    if hotels.exists():
        progress += 25
    if events.exists():
        progress += 25
 
    context = {
        "trip_count": trips.count(),
        "flight_count": flights.count(),
        "hotel_count": hotels.count(),
        "event_count": events.count(),
        "upcoming_trips": upcoming_trips[:5],
        "progress": progress,
    }
 
    return render(
        request,
        "dashboard.html",
        context
    )
@login_required
def trip_list(request):
 
    trips = Trip.objects.filter(
        user=request.user
    )
 
    return render(
        request,
        "trip_list.html",
        {"trips": trips}
    )
 
 
@login_required
def trip_create(request):
 
    form = TripForm(
        request.POST or None
    )
 
    if request.method == "POST":
 
        if form.is_valid():
 
            trip = form.save(
                commit=False
            )
 
            trip.user = request.user
 
            trip.save()
 
            return redirect(
                "homepage:trip_detail",
                trip.id
            )
        print(form.errors)
 
    return render(
        request,
        "trip_form.html",
        {"form": form}
    )

@login_required
def trip_detail(
    request,
    trip_id
):
 
    trip = get_object_or_404(
        Trip,
        id=trip_id,
        user=request.user
    )
 
    return render(
        request,
        "trip_detail.html",
        {"trip": trip}
    )
@login_required
def flight_list(request):
 
    flights = Flight.objects.filter(
        trip__user=request.user
    )
 
    return render(
        request,
        "flight_list.html",
        {
            "flights": flights
        }
    )
 
 
@login_required
def flight_create(request):
 
    form = FlightForm(
        request.POST or None
    )
 
    if request.method == "POST":
 
        if form.is_valid():
 
            form.save()
 
            return redirect(
                "homepage:flight_list"
            )
    print(form.errors)
    return render(
        request,
        "flight_form.html",
        {
            "form": form
        }
    )
@login_required
def hotel_list(request):
 
    hotels = HotelBooking.objects.filter(
        trip__user=request.user
    )
 
    return render(
        request,
        "hotel_list.html",
        {
            "hotels": hotels
        }
    )
 
 
@login_required
def hotel_create(request):
 
    form = HotelBookingForm(
        request.POST or None
    )
 
    if request.method == "POST":
 
        if form.is_valid():
 
            form.save()
 
            return redirect(
                "homepage:hotel_list"
            )
 
    print(form.errors)
    return render(
        request,
        "hotel_form.html",
        {
            "form": form
        }
    )
@login_required
def event_list(request):
 
    events = CalendarEvent.objects.filter(
        trip__user=request.user
    )
 
    return render(
        request,
        "event_list.html",
        {
            "events": events
        }
    )
 
 
@login_required
def event_create(request):
 
    form = CalendarEventForm(
        request.POST or None
    )
 
    if request.method == "POST":
 
        if form.is_valid():
 
            form.save()
 
            return redirect(
                "homepage:events"
            )
    print(form.errors)
    return render(
        request,
        "event_form.html",
        {
            "form": form
        }
    )
@login_required
def calendar_events(request):
 
    events = CalendarEvent.objects.filter(
        trip__user=request.user
    )
 
    data = []
 
    for event in events:
 
        data.append({
            "title": event.title,
            "start": event.start_datetime.isoformat(),
            "end": event.end_datetime.isoformat(),
            "color": event.color_code,
        })
 
    return JsonResponse(
        data,
        safe=False
    )
@login_required
def upload_booking(request):
    form = BookingImportForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        booking = form.save(commit=False)
        if request.user.is_authenticated:
            booking.user = request.user
        booking.save()
        booking.extract_data()
        return redirect('homepage:uploaded_files')
    return render(request, 'upload_booking.html', {'form': form})

@login_required
def uploaded_files(request):
    uploads = BookingImport.objects.order_by('-created_at')
    return render(request, 'booking_imports.html', {'uploads': uploads})


def login_view(request):
    return render(request, 'login.html')


def register_view(request):
    return render(request, 'register.html')

@login_required
def logout_view(request):
    logout(request)
    request.session.flush()
    return redirect('homepage:index')

@csrf_exempt
def chat_api(request):
    """Simple chatbot API: accepts JSON POST {message} and returns JSON {reply}.

    This is a lightweight implementation: rule-based replies for now. If an
    OpenAI/LLM key is configured, this can be extended to proxy requests.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)
    try:
        import json
        payload = json.loads(request.body.decode('utf-8'))
        message = (payload.get('message') or '').strip()
    except Exception:
        return JsonResponse({'error': 'invalid json'}, status=400)

    if not message:
        return JsonResponse({'reply': "Please send a message."})

    # If OpenAI is configured, forward the message to OpenAI's ChatCompletion
    from django.conf import settings
    openai_key = getattr(settings, 'OPENAI_API_KEY', '')
    if openai_key:
        try:
            import openai
            openai.api_key = openai_key
            resp = openai.ChatCompletion.create(
                model='gpt-3.5-turbo',
                messages=[
                    {"role": "system", "content": "You are a helpful travel assistant. Provide concise suggestions for itineraries, maps and pricing."},
                    {"role": "user", "content": message},
                ],
                max_tokens=300,
                temperature=0.3,
            )
            reply = resp.choices[0].message.content.strip()
            return JsonResponse({'reply': reply})
        except Exception as exc:
            # Fall back to rule-based reply on error
            pass

    text = message.lower()
    if 'itinerary' in text or 'plan' in text:
        reply = 'I can help build an itinerary. Tell me your destination and dates.'
    elif 'map' in text or 'where' in text:
        reply = 'Open a trip page and use the Itinerary / Map section to view locations.'
    elif 'price' in text or 'pricing' in text or 'subscribe' in text:
        reply = 'Visit our pricing page to upgrade to Premium for extra features.'
    else:
        reply = "Thanks — I\'m still learning. Try asking about itineraries, pricing, or maps."

    return JsonResponse({'reply': reply})

@login_required
def pricing(request):
    print("test1", settings.STRIPE_SECRET_KEY)
    stripe_public = getattr(settings, 'STRIPE_PUBLIC_KEY', 'pk_test_51TrNBK9MayN2qjd9NbBkDkljV7h1VueAhrtUUHs2mX1TogB333jXnqxFPEMULLkyYA8WCzaaJnd9vWoGDcF1ddpk00Z0NVhgfK')
    stripe_price = getattr(settings, 'STRIPE_PRICE_ID', 1000)  # Default price ID for testing
    return render(request, 'pricing.html', {'stripe_public_key': stripe_public, 'stripe_price_id': stripe_price})



def pricing_checkout(request):
    print("test", settings.STRIPE_SECRET_KEY)
    if request.method == "POST":
        price_id = request.POST.get("price_id")

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price": 'price_1TrmCn9MayN2qjd9sbvzNqis',
                    "quantity": 1,
                }
            ],
            mode="subscription",  # use "payment" for one-time payment
            success_url=request.build_absolute_uri(
                reverse("homepage:success")
            ),
            cancel_url=request.build_absolute_uri(
                reverse("homepage:cancel")
            ),
        )

        return redirect(checkout_session.url)

    return redirect("homepage:pricing")
def success(request):
    return render(request, "success.html")


def cancel(request):
    return render(request, "cancel.html")
@login_required
def create_checkout_session(request):
    """Create a Stripe Checkout session (scaffold).

    If Stripe isn't configured this returns a 400 with a clear message.
    """
    if request.method != 'POST':
        return HttpResponse(status=405)
    secret = getattr(settings, 'STRIPE_SECRET_KEY', '')
    if not secret:
        return JsonResponse({'error': 'Stripe not configured'}, status=400)
    try:
        import stripe
        stripe.api_key = secret
        price_id = request.POST.get('price_id') or request.POST.get('plan')
        if not price_id:
            return JsonResponse({'error': 'price_id required'}, status=400)
        domain = request.build_absolute_uri('/')[:-1]
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            mode='subscription',
            line_items=[{'price': price_id, 'quantity': 1}],
            success_url=domain + '/dashboard/?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=domain + '/pricing/',
        )
        return JsonResponse({'url': session.url})
    except Exception as exc:
        return JsonResponse({'error': str(exc)}, status=500)

