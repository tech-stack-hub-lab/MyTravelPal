
import io
import json
import os
import re
from datetime import date, datetime
from decimal import Decimal

import requests
from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse, JsonResponse, request
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt
from .utils.llm_extraction import extract_flight_info, extract_hotel_info, ask_travel_assistant, generate_trip_suggestions
import tempfile
import stripe
from .forms import (
    BookingUploadForm,
    CalendarEventForm,
    FlightDetailForm,
    FlightForm,
    HotelBookingForm,
    HotelDetailForm,
    TripForm,
    TripUploadForm,
    TripWizardForm,
)
from .models import (
    BookingImport,
    CalendarEvent,
    Flight,
    HotelBooking,
    ItineraryItem,
    Trip,
    trip_bucket_for,
)
# Import function from your llm.py file


stripe.api_key = settings.STRIPE_SECRET_KEY


class RegistrationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    class Meta:
        model = get_user_model()
        fields = ['username', 'email']

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            self.add_error('password2', 'Passwords do not match.')

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


@cache_page(20)
def index(request):
    return render(request, 'index.html')


def _extract_text_from_upload(uploaded_file):
    if uploaded_file is None:
        return ''

    filename = (getattr(uploaded_file, 'name', '') or '').lower()
    try:
        if filename.endswith(('.png', '.jpg', '.jpeg', '.bmp', '.webp')):
            from PIL import Image
            import pytesseract

            image = Image.open(uploaded_file)
            image = image.convert('RGB')
            return pytesseract.image_to_string(image)

        if filename.endswith('.pdf'):
            from pypdf import PdfReader
            import fitz
            from PIL import Image
            import pytesseract

            file_bytes = uploaded_file.read()
            extracted_pages = []

            try:
                reader = PdfReader(io.BytesIO(file_bytes))
                for page in reader.pages:
                    page_text = page.extract_text() or ''
                    if page_text.strip():
                        extracted_pages.append(page_text)
            except Exception:
                extracted_pages = []

            if not extracted_pages:
                try:
                    doc = fitz.open(stream=file_bytes, filetype='pdf')
                    for page in doc:
                        page_text = page.get_text('text') or ''
                        if page_text.strip():
                            extracted_pages.append(page_text)
                            continue

                        try:
                            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                            image = Image.open(io.BytesIO(pix.tobytes('png')))
                            image = image.convert('RGB')
                            extracted_pages.append(pytesseract.image_to_string(image))
                        except Exception:
                            extracted_pages.append('')
                except Exception:
                    extracted_pages = []

            uploaded_file.seek(0)
            return '\n'.join(part for part in extracted_pages if part)

        uploaded_file.seek(0)
        return uploaded_file.read().decode('utf-8', errors='ignore')
    except Exception:
        try:
            uploaded_file.seek(0)
            return uploaded_file.read().decode('utf-8', errors='ignore')
        except Exception:
            return ''


def _safe_match(patterns, text):
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            value = match.group(1).strip()
            if value:
                return value
    return ''


def _clean_booking_reference(value):
    if value in (None, ''):
        return ''

    cleaned = str(value).strip(' .,:;-/\n\r')
    if not cleaned:
        return ''

    lowered = cleaned.lower()
    if lowered in {'reservation', 'booking', 'confirmation', 'reference', 'ticket'}:
        return ''

    if re.search(r'\d', cleaned):
        return cleaned

    if re.fullmatch(r'[A-Z]{3,}', cleaned.upper()) and len(cleaned) >= 3:
        return cleaned.upper()

    return ''


def _clean_airport_value(value):
    if value in (None, ''):
        return ''

    cleaned = str(value).strip(' .,:;-/\n\r')
    if not cleaned:
        return ''

    lowered = cleaned.lower()
    banned = {
        'reservation', 'booking', 'confirmation', 'reference', 'ticket', 'arrival',
        'departure', 'travel', 'flight', 'support', 'confirmed', 'is', 'are',
        'mer', 'air', 'hotel', 'journey'
    }
    if lowered in banned:
        return ''

    if re.fullmatch(r'[A-Z]{3}', cleaned.upper()):
        return cleaned.upper()

    words = re.split(r'\s+', cleaned.strip())
    if any(word.lower().strip('.,;:-') in banned for word in words):
        return ''

    if len(cleaned) >= 4 and re.fullmatch(r'[A-Za-z][A-Za-z .-]{2,}', cleaned):
        return cleaned.title()

    return ''


def _clean_title_value(value):
    if value in (None, ''):
        return ''

    cleaned = str(value).strip(' .,:;-/\n\r')
    if not cleaned:
        return ''

    lowered = cleaned.lower()
    if lowered in {'reservation', 'booking', 'confirmation', 'reference', 'ticket', 'is confirmed', 'confirmed'}:
        return ''

    if lowered.startswith(('is ', 'are ', 'this ', 'that ', 'please ')):
        return ''

    return cleaned


def _normalize_iso_value(value):
    if value in (None, ''):
        return ''

    text = str(value).strip()
    if not text:
        return ''

    text = text.replace('Z', '+00:00')
    text = text.replace(' ', 'T') if 'T' not in text and re.search(r'\d{4}-\d{2}-\d{2}', text) else text

    try:
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = timezone.make_aware(dt, timezone.get_current_timezone())
        return dt.isoformat(timespec='minutes')
    except ValueError:
        pass

    for fmt in (
        '%Y-%m-%d',
        '%d/%m/%Y',
        '%m/%d/%Y',
        '%d-%m-%Y',
        '%Y/%m/%d',
        '%d %b %Y',
        '%b %d, %Y',
    ):
        try:
            parsed = datetime.strptime(text, fmt)
            return parsed.date().isoformat()
        except ValueError:
            continue

    return text


def _json_safe_session_value(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _json_safe_session_value(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe_session_value(item) for item in value]
    return value


def _call_groq_json(prompt):
    api_key = getattr(settings, 'GROQ_API_KEY', None) or os.environ.get('GROQ_API_KEY')
    if not api_key:
        return {}

    system_prompt = (
        'You are a structured travel-document extractor. Return only valid JSON. '
        'Use exact keys and do not add extra text. Use ISO 8601 dates and datetimes like '
        'YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS; use empty strings for missing values; '
        'do not invent data; if a value is uncertain, set it to an empty string.'
    )

    try:
        response = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            json={
                'model': 'llama-3.1-8b-instant',
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': prompt},
                ],
                'temperature': 0.2,
                'max_tokens': 600,
            },
            timeout=60,
        )
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content']
        content = re.sub(r'^```(?:json)?\s*', '', content, flags=re.IGNORECASE | re.DOTALL)
        content = re.sub(r'\s*```$', '', content, flags=re.IGNORECASE | re.DOTALL)
        return json.loads(content)
    except Exception:
        return {}


def _normalize_extracted_payload(payload, aliases):
    normalized = {}
    for form_name, candidate_keys in aliases.items():
        value = ''
        for key in candidate_keys:
            if payload.get(key) not in (None, ''):
                value = payload.get(key)
                break

        if form_name in {'departure_datetime', 'arrival_datetime'}:
            value = _normalize_iso_value(value)
        elif form_name in {'checkin_date', 'checkout_date'}:
            value = _normalize_iso_value(value)
        elif form_name == 'total_cost':
            if isinstance(value, (int, float, str)):
                text = str(value).strip().replace(',', '')
                try:
                    value = float(text)
                except ValueError:
                    value = 0
        else:
            value = str(value).strip() if value is not None else ''

        normalized[form_name] = value
    return normalized


def _extract_flight_details(raw_text):
    llm_prompt = (
        "Extract the most important travel booking details from this document as valid JSON only. "
        "Use only these exact keys: airline, flight_number, booking_reference, departure_airport, "
        "arrival_airport, departure_datetime, arrival_datetime, seat_number, title, location, type. "
        "Dates and datetimes must be ISO-8601 strings such as YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS; "
        "use empty strings for missing values. Document text:\n" + raw_text[:6000]
    )
    llm_data = _call_groq_json(llm_prompt)
    if isinstance(llm_data, dict) and llm_data:
        normalized = _normalize_extracted_payload(llm_data, {
            'airline': ['airline', 'carrier', 'train_name', 'bus_company'],
            'flight_number': ['flight_number', 'flightNo', 'flight_no'],
            'booking_reference': ['booking_reference', 'confirmation_code', 'reservation_code'],
            'departure_airport': ['departure_airport', 'depart_from', 'from_airport'],
            'arrival_airport': ['arrival_airport', 'arrive_to', 'to_airport'],
            'departure_datetime': ['departure_datetime', 'depart_datetime', 'departure_date'],
            'arrival_datetime': ['arrival_datetime', 'arrival_date'],
            'seat_number': ['seat_number', 'seat'],
            'title': ['title', 'event_name', 'ticket_name'],
            'location': ['location', 'city', 'destination'],
            'type': ['type'],
        })
        return {
            'airline': normalized.get('airline', ''),
            'flight_number': normalized.get('flight_number', ''),
            'booking_reference': normalized.get('booking_reference', ''),
            'departure_airport': normalized.get('departure_airport', ''),
            'arrival_airport': normalized.get('arrival_airport', ''),
            'departure_datetime': normalized.get('departure_datetime', ''),
            'arrival_datetime': normalized.get('arrival_datetime', ''),
            'seat_number': normalized.get('seat_number', ''),
            'title': normalized.get('title', ''),
            'location': normalized.get('location', ''),
            'type': normalized.get('type', 'travel'),
        }

    departure_datetime = _safe_match([
        r'(?:departure|depart)\s*(?:date|datetime|time)?\s*[:\-]?\s*(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}|\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}[T ]\d{2}:\d{2}|\d{2}/\d{2}/\d{4})',
        r'from\s*[A-Za-z ]+\s*(?:on\s*)?(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}|\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}[T ]\d{2}:\d{2}|\d{2}/\d{2}/\d{4})',
    ], raw_text)
    arrival_datetime = _safe_match([
        r'(?:arrival|arrive)\s*(?:date|datetime|time)?\s*[:\-]?\s*(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}|\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}[T ]\d{2}:\d{2}|\d{2}/\d{2}/\d{4})',
        r'to\s*[A-Za-z ]+\s*(?:on\s*)?(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}|\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}[T ]\d{2}:\d{2}|\d{2}/\d{2}/\d{4})',
    ], raw_text)

    fallback = {
        'airline': _safe_match([
            r'airline\s*[:\-]?\s*([A-Za-z0-9 &.-]+)',
            r'carrier\s*[:\-]?\s*([A-Za-z0-9 &.-]+)',
        ], raw_text),
        'flight_number': _safe_match([
            r'flight\s*(?:no|number)?\s*[:\-]?\s*([A-Za-z]{2,5}\s*\d{1,5})',
            r'flight\s*[:\-]?\s*([A-Za-z]{2,5}\s*\d{1,5})',
        ], raw_text),
        'booking_reference': _clean_booking_reference(_safe_match([
            r'confirmation\s*(?:code|no|number)?\s*[:\-]?\s*([A-Za-z0-9-]+)',
            r'booking\s*(?:ref(?:erence)?|id|code)?\s*[:\-]?\s*([A-Za-z0-9-]+)',
            r'reservation\s*(?:code|no|number)?\s*[:\-]?\s*([A-Za-z0-9-]+)',
        ], raw_text)),
        'departure_airport': _clean_airport_value(_safe_match([
            r'departure\s*(?:airport|from)\s*[:\-]?\s*(([A-Za-z][A-Za-z .-]{2,}|[A-Z]{3}))',
            r'from\s*(([A-Za-z][A-Za-z .-]{2,}|[A-Z]{3}))\s*(?:to|destination)',
        ], raw_text)),
        'arrival_airport': _clean_airport_value(_safe_match([
            r'arrival\s*(?:airport|to)\s*[:\-]?\s*(([A-Za-z][A-Za-z .-]{2,}|[A-Z]{3}))',
            r'to\s*(([A-Za-z][A-Za-z .-]{2,}|[A-Z]{3}))',
        ], raw_text)),
        'departure_datetime': _normalize_iso_value(departure_datetime),
        'arrival_datetime': _normalize_iso_value(arrival_datetime),
        'seat_number': _safe_match([
            r'seat\s*(?:no|number)?\s*[:\-]?\s*([A-Za-z0-9-]+)',
            r'seat\s*[:\-]?\s*([A-Za-z0-9-]+)',
        ], raw_text),
        'title': _clean_title_value(_safe_match([
            r'event\s*name\s*[:\-]?\s*([A-Za-z0-9 .,-]+)',
            r'ticket\s*[:\-]?\s*([A-Za-z0-9 .,-]+)',
        ], raw_text)),
        'location': _safe_match([
            r'location\s*[:\-]?\s*([A-Za-z0-9 ,.-]+)',
            r'city\s*[:\-]?\s*([A-Za-z0-9 ,.-]+)',
        ], raw_text),
        'type': 'travel',
    }
    return fallback


def _extract_hotel_details(raw_text):
    llm_prompt = (
        "Extract hotel booking details from this document as valid JSON only. "
        "Use only these exact keys: hotel_name, booking_reference, location, checkin_date, checkout_date, total_cost. "
        "Dates must be ISO-8601 strings like YYYY-MM-DD; use empty strings for missing values. Document text:\n" + raw_text[:6000]
    )
    llm_data = _call_groq_json(llm_prompt)
    if isinstance(llm_data, dict) and llm_data:
        normalized = _normalize_extracted_payload(llm_data, {
            'hotel_name': ['hotel_name', 'property_name'],
            'booking_reference': ['booking_reference', 'confirmation_code'],
            'location': ['location', 'city', 'address'],
            'checkin_date': ['checkin_date', 'check_in_date', 'arrival_date', 'checkin'],
            'checkout_date': ['checkout_date', 'check_out_date', 'depart_date', 'checkout'],
            'total_cost': ['total_cost', 'amount', 'total_amount'],
        })
        return {
            'hotel_name': normalized.get('hotel_name', ''),
            'booking_reference': normalized.get('booking_reference', ''),
            'location': normalized.get('location', ''),
            'checkin_date': normalized.get('checkin_date', ''),
            'checkout_date': normalized.get('checkout_date', ''),
            'total_cost': normalized.get('total_cost', ''),
        }

    fallback = {
        'hotel_name': _safe_match([
            r'hotel\s*[:\-]?\s*([A-Za-z0-9 &.-]+)',
            r'property\s*[:\-]?\s*([A-Za-z0-9 &.-]+)',
        ], raw_text),
        'booking_reference': _clean_booking_reference(_safe_match([
            r'booking\s*(?:ref(?:erence)?|id|code)?\s*[:\-]?\s*([A-Za-z0-9-]+)',
            r'confirmation\s*(?:code|no|number)?\s*[:\-]?\s*([A-Za-z0-9-]+)',
            r'reservation\s*(?:code|no|number)?\s*[:\-]?\s*([A-Za-z0-9-]+)',
        ], raw_text)),
        'location': _safe_match([
            r'location\s*[:\-]?\s*([A-Za-z0-9 ,.-]+)',
            r'city\s*[:\-]?\s*([A-Za-z0-9 ,.-]+)',
        ], raw_text),
        'checkin_date': _normalize_iso_value(_safe_match([
            r'checkin\s*(?:date)?\s*[:\-]?\s*(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})',
            r'arrival\s*(?:date)?\s*[:\-]?\s*(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})',
        ], raw_text)),
        'checkout_date': _normalize_iso_value(_safe_match([
            r'checkout\s*(?:date)?\s*[:\-]?\s*(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})',
            r'departure\s*(?:date)?\s*[:\-]?\s*(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})',
        ], raw_text)),
        'total_cost': _safe_match([
            r'total\s*(?:cost|amount)\s*[:\-]?\s*\$?\s*(\d+(?:\.\d+)?)',
            r'amount\s*[:\-]?\s*\$?\s*(\d+(?:\.\d+)?)',
        ], raw_text),
    }
    return fallback


def _search_hotels(query, destination=''):
    if not query:
        return []

    google_key = getattr(settings, 'GOOGLE_MAPS_API_KEY', None) or os.environ.get('GOOGLE_MAPS_API_KEY')
    if google_key:
        try:
            search_term = f"{query} {destination}".strip()
            response = requests.get(
                'https://maps.googleapis.com/maps/api/place/textsearch/json',
                params={'query': search_term, 'key': google_key, 'type': 'hotel'},
                timeout=30,
            )
            response.raise_for_status()
            results = response.json().get('results', [])
            return [
                {
                    'name': item.get('name', 'Hotel'),
                    'address': item.get('formatted_address', ''),
                    'rating': item.get('rating', 0),
                    'price_level': item.get('price_level', ''),
                }
                for item in results[:5]
            ]
        except Exception:
            pass

    return [
        {'name': f'{query} Stay', 'address': destination or 'City center', 'rating': 4.5, 'price_level': '$$'},
        {'name': f'{query} Boutique', 'address': f'{destination or "City"} downtown', 'rating': 4.7, 'price_level': '$$$'},
        {'name': f'{query} Suites', 'address': f'{destination or "City"} business district', 'rating': 4.4, 'price_level': '$$'},
    ]


def _generate_ai_itinerary(trip):
    api_key = getattr(settings, 'GROQ_API_KEY', None) or os.environ.get('GROQ_API_KEY')
    if not api_key:
        return [
            {
                'day_number': 1,
                'place_name': f'Welcome to {trip.destination}',
                'description': (
                    f'Begin with a relaxed arrival in {trip.destination}, '
                    'then explore the city center and enjoy a local dining experience.'
                ),
                'category': 'arrival',
            },
            {
                'day_number': 2,
                'place_name': 'Local Highlights',
                'description': (
                    'Visit the main attractions, browse local markets, and leave time '
                    'for scenic walking or a short guided tour.'
                ),
                'category': 'attraction',
            },
        ]

    prompt = (
        f"Create a concise day-by-day itinerary for a {trip.category} trip to {trip.destination} "
        f"from {trip.start_date} to {trip.end_date}. Budget is {trip.budget or 0}. "
        "Return 3-5 days with title and short description for each day. "
        "Format each day as: Day X: Place Name - Description."
    )

    try:
        response = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            json={
                'model': 'llama-3.1-8b-instant',
                'messages': [{'role': 'user', 'content': prompt}],
                'temperature': 0.5,
                'max_tokens': 500,
            },
            timeout=60,
        )
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content']
        items = []
        day_blocks = re.split(r'(?=Day\s+\d+)', content)
        for index, block in enumerate([b.strip() for b in day_blocks if b.strip()], start=1):
            first_line = block.splitlines()[0].strip() if block.splitlines() else block
            label = first_line[:120]
            items.append({
                'day_number': index,
                'place_name': label,
                'description': block,
                'category': 'attraction',
            })
        if items:
            return items
    except Exception:
        pass

    return [
        {
            'day_number': 1,
            'place_name': f'Arrival in {trip.destination}',
            'description': 'Settle in, enjoy a local walk, and have dinner near your stay.',
            'category': 'arrival',
        },
        {
            'day_number': 2,
            'place_name': 'City Highlights',
            'description': 'Visit the most iconic attractions and a scenic neighborhood with time for photos.',
            'category': 'attraction',
        },
    ]


@login_required
def dashboard(request):
    trips = Trip.objects.filter(user=request.user).order_by('-created_at')
    flights = Flight.objects.filter(trip__user=request.user)
    hotels = HotelBooking.objects.filter(trip__user=request.user)
    events = CalendarEvent.objects.filter(trip__user=request.user)

    trip_groups = {
        'upcoming': [],
        'present': [],
        'past': [],
        'not_decided': [],
    }
    for trip in trips:
        bucket = trip_bucket_for(trip)
        if bucket in trip_groups:
            trip_groups[bucket].append(trip)

    upcoming_trips = trip_groups['upcoming']
    present_trips = trip_groups['present']
    past_trips = trip_groups['past']
    not_decided_trips = trip_groups['not_decided']

    ai_suggestions = []
    for trip in upcoming_trips[:5]:
            # Skip trips where destination is missing or named "None"
        if (
                trip.destination
                and trip.destination.strip().lower() != 'none'
                and trip.id
            ):
            suggestions_dict = generate_trip_suggestions(
                destination=trip.destination, trip_type=trip.trip_type
            )

            ai_suggestions.append({
                'trip_id': trip.id,  # Ensure actual integer ID is passed
                'trip_title': trip.title,
                'destination': trip.destination,
                'content': suggestions_dict,
            })
            break  # Generate suggestions for the top valid trip

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
        "upcoming_trips": upcoming_trips,
        "present_trips": present_trips,
        "past_trips": past_trips,
        "not_decided_trips": not_decided_trips,
        "trip_sections": [
            ('upcoming', 'Upcoming Trips', upcoming_trips),
            ('present', 'Present Trips', present_trips),
            ('past', 'Past Trips', past_trips),
            ('not_decided', 'Not Decided', not_decided_trips),
        ],
        "trips": trips,
        "progress": progress,
        'ai_suggestions': ai_suggestions,
    }
    return render(request, 'dashboard.html', context)

@login_required
def trip_wizard_step1(request):
    trip_id = request.session.get('trip_wizard_trip_id')
    trip = None
    if trip_id:
        trip = get_object_or_404(Trip, id=trip_id, user=request.user)

    if request.method == 'POST':
        form = TripWizardForm(request.POST, instance=trip)
        if form.is_valid():
            trip_obj = form.save(commit=False)
            trip_obj.user = request.user
            trip_obj.trip_name = trip_obj.title or trip_obj.trip_name or trip_obj.destination
            trip_obj.save()
            request.session['trip_wizard_trip_id'] = trip_obj.id
            messages.success(request, 'Trip details saved. Continue with documents and itinerary setup.')
            return redirect('homepage:trip_wizard_step2')
    else:
        form = TripWizardForm(instance=trip)

    return render(request, 'trip_wizard_step1.html', {'form': form})


# If you have a place-search helper already, import it here, e.g.:
# from utils.places import search_places

def _upsert_flight_for_trip(trip, flight_data):
    if not flight_data:
        return None

    normalized = {k: v for k, v in flight_data.items() if v not in (None, '')}
    if not normalized:
        return None

    flight = None
    if normalized.get('flight_number'):
        flight = trip.flights.filter(flight_number=normalized.get('flight_number')).order_by('-id').first()
    if flight is None and normalized.get('booking_reference'):
        flight = trip.flights.filter(booking_reference=normalized.get('booking_reference')).order_by('-id').first()
    if flight is None:
        flight = trip.flights.create(
            airline=normalized.get('airline', ''),
            flight_number=normalized.get('flight_number', ''),
            booking_reference=normalized.get('booking_reference', ''),
            departure_airport=normalized.get('departure_airport', ''),
            arrival_airport=normalized.get('arrival_airport', ''),
            departure_datetime=timezone.now(),
            arrival_datetime=timezone.now(),
            seat_number=normalized.get('seat_number', ''),
        )

    departure_dt = normalized.get('departure_datetime')
    arrival_dt = normalized.get('arrival_datetime')
    if departure_dt:
        try:
            departure_dt = datetime.fromisoformat(str(departure_dt).replace('Z', '+00:00'))
            if departure_dt.tzinfo is None:
                departure_dt = timezone.make_aware(departure_dt, timezone.get_current_timezone())
        except ValueError:
            departure_dt = timezone.now()
    else:
        departure_dt = timezone.now()

    if arrival_dt:
        try:
            arrival_dt = datetime.fromisoformat(str(arrival_dt).replace('Z', '+00:00'))
            if arrival_dt.tzinfo is None:
                arrival_dt = timezone.make_aware(arrival_dt, timezone.get_current_timezone())
        except ValueError:
            arrival_dt = timezone.now()
    else:
        arrival_dt = timezone.now()

    flight.airline = normalized.get('airline', flight.airline)
    flight.flight_number = normalized.get('flight_number', flight.flight_number)
    flight.booking_reference = normalized.get('booking_reference', flight.booking_reference)
    flight.departure_airport = normalized.get('departure_airport', flight.departure_airport)
    flight.arrival_airport = normalized.get('arrival_airport', flight.arrival_airport)
    flight.departure_datetime = departure_dt
    flight.arrival_datetime = arrival_dt
    flight.seat_number = normalized.get('seat_number', flight.seat_number)
    flight.save()
    return flight


def _upsert_hotel_for_trip(trip, hotel_data):
    if not hotel_data:
        return None

    normalized = {k: v for k, v in hotel_data.items() if v not in (None, '')}
    if not normalized:
        return None

    hotel = None
    if normalized.get('booking_reference'):
        hotel = trip.hotels.filter(booking_reference=normalized.get('booking_reference')).order_by('-id').first()
    if hotel is None and normalized.get('hotel_name'):
        hotel = trip.hotels.filter(hotel_name=normalized.get('hotel_name')).order_by('-id').first()
    if hotel is None:
        hotel = trip.hotels.create(
            hotel_name=normalized.get('hotel_name', ''),
            booking_reference=normalized.get('booking_reference', ''),
            location=normalized.get('location', ''),
            checkin_date=timezone.now().date(),
            checkout_date=timezone.now().date(),
            total_cost=0,
        )

    check_in = normalized.get('checkin_date')
    check_out = normalized.get('checkout_date')
    if check_in:
        try:
            check_in = date.fromisoformat(str(check_in))
        except ValueError:
            check_in = timezone.now().date()
    else:
        check_in = timezone.now().date()

    if check_out:
        try:
            check_out = date.fromisoformat(str(check_out))
        except ValueError:
            check_out = timezone.now().date()
    else:
        check_out = timezone.now().date()

    hotel.hotel_name = normalized.get('hotel_name', hotel.hotel_name)
    hotel.booking_reference = normalized.get('booking_reference', hotel.booking_reference)
    hotel.location = normalized.get('location', hotel.location)
    hotel.checkin_date = check_in
    hotel.checkout_date = check_out
    hotel.total_cost = normalized.get('total_cost') or hotel.total_cost or 0
    hotel.save()
    return hotel


def _upsert_itinerary_item_for_trip(trip, item_data):
    if not item_data or not isinstance(item_data, dict):
        return None

    place_name = item_data.get('place_name') or item_data.get('title') or 'Saved Place'
    description = item_data.get('description') or ''
    category = item_data.get('category') or 'attraction'
    day_number = item_data.get('day_number') or (trip.itineraries.count() + 1)
    latitude = item_data.get('latitude')
    longitude = item_data.get('longitude')

    existing_item = trip.itineraries.filter(category=category, place_name=place_name, day_number=day_number).order_by('-id').first()
    if existing_item is None and latitude is not None and longitude is not None:
        existing_item = trip.itineraries.filter(category='map_place', latitude=latitude, longitude=longitude).order_by('-id').first()

    if existing_item is not None:
        existing_item.place_name = place_name
        existing_item.description = description
        existing_item.category = category
        existing_item.day_number = day_number
        existing_item.latitude = latitude
        existing_item.longitude = longitude
        existing_item.save(update_fields=['place_name', 'description', 'category', 'day_number', 'latitude', 'longitude'])
        return existing_item

    return ItineraryItem.objects.create(
        trip=trip,
        day_number=day_number,
        place_name=place_name,
        category=category,
        description=description,
        latitude=latitude,
        longitude=longitude,
    )


def _save_pending_trip_wizard_data(trip, request):
    if trip is None:
        return

    pending_flight = request.session.get('trip_wizard_pending_flight', {}) or {}
    pending_hotel = request.session.get('trip_wizard_pending_hotel', {}) or {}
    pending_itinerary = request.session.get('trip_wizard_pending_itinerary', []) or []

    if pending_flight:
        _upsert_flight_for_trip(trip, {k: v for k, v in pending_flight.items() if v not in (None, '')})
    if pending_hotel:
        _upsert_hotel_for_trip(trip, {k: v for k, v in pending_hotel.items() if v not in (None, '')})

    if isinstance(pending_itinerary, dict):
        pending_itinerary = [pending_itinerary]
    for item in pending_itinerary:
        _upsert_itinerary_item_for_trip(trip, item)

    request.session.pop('trip_wizard_pending_flight', None)
    request.session.pop('trip_wizard_pending_hotel', None)
    request.session.pop('trip_wizard_pending_itinerary', None)


@login_required
def trip_wizard_step2(request):
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    hotel_search_results = None

    if request.method == "POST":

        # ------------------------------------------------------------
        # 1. AJAX request — fired automatically when a file input changes
        # ------------------------------------------------------------
        if is_ajax:
            flight_data, hotel_data = {}, {}

            if request.FILES.get("flight_file"):
                flight_data = _extract_uploaded_file(request.FILES["flight_file"], extract_flight_info)
                request.session["extracted_flight"] = _json_safe_session_value(flight_data)
                request.session["trip_wizard_pending_flight"] = _json_safe_session_value(flight_data)

            if request.FILES.get("hotel_file"):
                hotel_data = _extract_uploaded_file(request.FILES["hotel_file"], extract_hotel_info)
                request.session["extracted_hotel"] = _json_safe_session_value(hotel_data)
                request.session["trip_wizard_pending_hotel"] = _json_safe_session_value(hotel_data)

            return JsonResponse({"success": True, "flight": flight_data, "hotel": hotel_data})

        # ------------------------------------------------------------
        # 2. Regular (non-AJAX) button submits
        # ------------------------------------------------------------
        if "upload_flight" in request.POST and request.FILES.get("flight_file"):
            data = _extract_uploaded_file(request.FILES["flight_file"], extract_flight_info)
            request.session["extracted_flight"] = _json_safe_session_value(data)
            request.session["trip_wizard_pending_flight"] = _json_safe_session_value(data)

        elif "upload_hotel" in request.POST and request.FILES.get("hotel_file"):
            data = _extract_uploaded_file(request.FILES["hotel_file"], extract_hotel_info)
            request.session["extracted_hotel"] = _json_safe_session_value(data)
            request.session["trip_wizard_pending_hotel"] = _json_safe_session_value(data)

        elif "search_hotels" in request.POST:
            query = request.POST.get("hotel_search", "")
            # Plug in your existing hotel/place search function, e.g.:
            # hotel_search_results, _ = search_places(f"hotel {query}")
            hotel_search_results = []  # placeholder until you wire in real search

        elif "save_details" in request.POST:
            flight_form = FlightDetailForm(request.POST)
            hotel_form = HotelDetailForm(request.POST)
            if flight_form.is_valid() and hotel_form.is_valid():
                request.session["trip_wizard_pending_flight"] = _json_safe_session_value(flight_form.cleaned_data)
                request.session["trip_wizard_pending_hotel"] = _json_safe_session_value(hotel_form.cleaned_data)
                request.session.pop("extracted_flight", None)
                request.session.pop("extracted_hotel", None)
                return redirect("homepage:trip_wizard_step3")

    # ------------------------------------------------------------
    # 3. Build the forms for both GET and any POST branch that falls
    #    through to re-rendering the page (upload/search actions above)
    # ------------------------------------------------------------
    upload_form = BookingUploadForm(request.POST or None, request.FILES or None)
    flight_form = FlightDetailForm(request.POST or None, initial=request.session.get("extracted_flight", {}))
    hotel_form = HotelDetailForm(request.POST or None, initial=request.session.get("extracted_hotel", {}))

    context = {
        "upload_form": upload_form,
        "flight_form": flight_form,
        "hotel_form": hotel_form,
        "extracted_flight": json.dumps(request.session.get("extracted_flight", {})),
        "extracted_hotel": json.dumps(request.session.get("extracted_hotel", {})),
        "hotel_search_results": hotel_search_results,
    }
    return render(request, "trip_wizard_step2.html", context)


def _extract_uploaded_file(uploaded_file, extractor_fn):
    """Write the in-memory upload to a temp file, run extraction, clean up."""
    suffix = "." + uploaded_file.name.rsplit(".", 1)[-1] if "." in uploaded_file.name else ""
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        for chunk in uploaded_file.chunks():
            tmp.write(chunk)
        tmp_path = tmp.name
    try:
        return extractor_fn(tmp_path)
    finally:
        os.unlink(tmp_path)


def _extract_uploaded_file(uploaded_file, extractor_fn):
    """Write the in-memory upload to a temp file, run extraction, clean up."""
    suffix = "." + uploaded_file.name.rsplit(".", 1)[-1] if "." in uploaded_file.name else ""
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        for chunk in uploaded_file.chunks():
            tmp.write(chunk)
        tmp_path = tmp.name
    try:
        return extractor_fn(tmp_path)
    finally:
        import os
        os.unlink(tmp_path)


@login_required
def trip_wizard_step3(request):
    trip_id = request.session.get('trip_wizard_trip_id')
    if not trip_id:
        return redirect('homepage:trip_wizard_step1')

    trip = get_object_or_404(Trip, id=trip_id, user=request.user)
    itinerary = list(trip.itineraries.order_by('day_number').all())

    if request.method == 'POST':
        generated = _generate_ai_itinerary(trip)
        trip.itineraries.all().delete()
        for item in generated:
            ItineraryItem.objects.create(
                trip=trip,
                day_number=item.get('day_number', 1),
                place_name=item.get('place_name', f'Day {item.get("day_number", 1)}'),
                category=item.get('category', 'attraction'),
                description=item.get('description', ''),
            )
        itinerary = list(trip.itineraries.order_by('day_number').all())
        messages.success(request, 'Your AI itinerary has been generated.')

    return render(
        request,
        'trip_wizard_step3.html',
        {
            'trip': trip,
            'itinerary': itinerary,
            'google_maps_key': os.getenv('GOOGLE_MAPS_API_KEY', ''),
        },
    )


@login_required
def trip_wizard_step4(request):
    trip_id = request.session.get('trip_wizard_trip_id')
    if not trip_id:
        return redirect('homepage:trip_wizard_step1')

    trip = get_object_or_404(Trip, id=trip_id, user=request.user)

    pending_flight = request.session.get('trip_wizard_pending_flight', {})
    pending_hotel = request.session.get('trip_wizard_pending_hotel', {})

    _save_pending_trip_wizard_data(trip, request)

    flights = trip.flights.all()
    hotels = trip.hotels.all()
    itinerary = trip.itineraries.order_by('day_number')

    return render(
        request,
        'trip_wizard_step4.html',
        {
            'trip': trip,
            'flights': flights,
            'hotels': hotels,
            'itinerary': itinerary,
        },
    )


@login_required
def trip_wizard_finish(request):
    trip_id = request.session.get('trip_wizard_trip_id')
    trip = get_object_or_404(Trip, id=trip_id, user=request.user) if trip_id else None

    if trip is not None:
        _save_pending_trip_wizard_data(trip, request)
        trip.status = trip.determine_status()
        trip.save(update_fields=['status', 'updated_at'])

    request.session.pop('trip_wizard_trip_id', None)
    request.session.pop('extracted_flight', None)
    request.session.pop('extracted_hotel', None)
    request.session.pop('trip_wizard_pending_flight', None)
    request.session.pop('trip_wizard_pending_hotel', None)
    request.session.pop('trip_wizard_pending_itinerary', None)
    messages.success(request, 'Trip saved successfully.')
    return redirect('homepage:dashboard')


@login_required
def trip_wizard_save_place(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST required'}, status=405)

    trip_id = request.session.get('trip_wizard_trip_id')
    if not trip_id:
        return JsonResponse({'success': False, 'message': 'Trip not found'}, status=400)

    trip = get_object_or_404(Trip, id=trip_id, user=request.user)
    place_name = request.POST.get('place_name') or 'Saved Place'
    description = request.POST.get('description') or 'Saved from map selection.'
    latitude = request.POST.get('latitude')
    longitude = request.POST.get('longitude')

    latitude_value = float(latitude) if latitude not in (None, '', 'None') else None
    longitude_value = float(longitude) if longitude not in (None, '', 'None') else None

    existing_item = trip.itineraries.filter(category='map_place', place_name=place_name).order_by('-id').first()
    if existing_item is None and latitude_value is not None and longitude_value is not None:
        existing_item = trip.itineraries.filter(
            category='map_place',
            latitude=latitude_value,
            longitude=longitude_value,
        ).order_by('-id').first()

    if existing_item is not None:
        existing_item.place_name = place_name
        existing_item.description = description
        existing_item.latitude = latitude_value
        existing_item.longitude = longitude_value
        existing_item.save(update_fields=['place_name', 'description', 'latitude', 'longitude'])
        item = existing_item
    else:
        item = ItineraryItem.objects.create(
            trip=trip,
            day_number=(trip.itineraries.count() + 1),
            place_name=place_name,
            category='map_place',
            description=description,
            latitude=latitude_value,
            longitude=longitude_value,
        )

    return JsonResponse({'success': True, 'id': item.id, 'place_name': item.place_name})


@login_required
def trip_delete(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id, user=request.user)
    if request.method == 'POST':
        trip.delete()
        messages.success(request, 'Trip deleted successfully.')
    return redirect('homepage:dashboard')


@login_required
def trip_detail(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id, user=request.user)
    return render(request, 'trip_detail.html', {'trip': trip})


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
 
    return render(
        request,
        "trip_form.html",
        {"form": form}
    )


@login_required
def flight_create(request):
    form = FlightForm(request.POST or None, user=request.user)

    if request.method == 'POST' and form.is_valid():
        flight = form.save(commit=False)
        flight.trip = form.cleaned_data.get('trip') or Trip.objects.filter(user=request.user).first()
        flight.save()
        if flight.trip:
            return redirect('homepage:trip_detail', flight.trip.id)
        return redirect('homepage:dashboard')

    return render(request, 'flight_form.html', {'form': form})


@login_required
def hotel_create(request):
    form = HotelBookingForm(request.POST or None, user=request.user)

    if request.method == 'POST' and form.is_valid():
        hotel = form.save(commit=False)
        hotel.trip = form.cleaned_data.get('trip') or Trip.objects.filter(user=request.user).first()
        hotel.save()
        if hotel.trip:
            return redirect('homepage:trip_detail', hotel.trip.id)
        return redirect('homepage:dashboard')

    return render(request, 'hotel_form.html', {'form': form})


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
        request.POST or None,
        user=request.user,
    )
 
    if request.method == "POST":
 
        if form.is_valid():
 
            form.save()
 
            return redirect(
                "homepage:event_list"
            )
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


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('homepage:dashboard')
    else:
        form = AuthenticationForm()

    return render(request, 'login.html', {'form': form})


def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            return redirect('homepage:dashboard')
    else:
        form = RegistrationForm()

    return render(request, 'register.html', {'form': form})

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


# tasks.py (or management command run daily)
@login_required
def virtual_assistant_chat(request):
  if request.method != 'POST':
    return JsonResponse({'error': 'Invalid request method.'}, status=400)

  # Check premium status
  is_premium = getattr(request.user, 'is_premium', True)
  if not is_premium:
    return JsonResponse(
        {'error': 'Virtual Assistant is available exclusively to Premium users.'},
        status=403,
    )

  try:
    data = json.loads(request.body)
    user_message = data.get('message', '').strip()
    trip_destination = data.get('destination', '')

    if not user_message:
      return JsonResponse({'error': 'Message cannot be empty.'}, status=400)

    # Call function from llm.py
    bot_reply = ask_travel_assistant(
        user_message=user_message, trip_destination=trip_destination
    )

    return JsonResponse({'reply': bot_reply})

  except Exception as e:
    return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)


@login_required
def add_ai_suggestion_event(request):
  if request.method != 'POST':
    return JsonResponse({'error': 'Invalid method.'}, status=400)

  try:
    data = json.loads(request.body)
    trip_id = data.get('trip_id')
    raw_title = data.get('title', '')
    category = data.get('category', 'Activity')

    # Convert unicode escape sequences like \u0026 back to &
    title = html.unescape(raw_title)

    trip = get_object_or_404(Trip, id=trip_id, user=request.user)

    if hasattr(trip, 'start_date') and trip.start_date:
      start_dt = timezone.make_aware(
          timezone.datetime.combine(
              trip.start_date, timezone.datetime.min.time()
          )
      )
    else:
      start_dt = timezone.now()

    end_dt = start_dt + timezone.timedelta(hours=2)

    event = CalendarEvent.objects.create(
        trip=trip,
        event_type=category,
        title=title,  # Cleaned title saved here
        start_datetime=start_dt,
        end_datetime=end_dt,
        color_code='#3b82f6',
    )

    return JsonResponse({'success': True, 'event_id': event.id})
  except Exception as e:
    return JsonResponse({'error': str(e)}, status=500)