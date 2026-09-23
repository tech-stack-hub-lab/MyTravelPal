"""
Extracts structured flight/hotel details from an uploaded file (PDF or
image) using Groq. Field names match exactly what trip_wizard_step2.html
expects, so the JSON returned here can be dropped straight into the
JS autoPopulateFlightData() / autoPopulateHotelData() functions.
"""

import base64
import json
import logging
import mimetypes
import os

logger = logging.getLogger(__name__)

IMAGE_MIME_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp", "image/gif"}
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

# Current Groq models (2026) - llama-3.3-70b-versatile is Enterprise-only now.
TEXT_MODEL_CANDIDATES = ["openai/gpt-oss-120b", "openai/gpt-oss-20b"]
VISION_MODEL_CANDIDATES = ["qwen/qwen3.6-27b", "meta-llama/llama-4-maverick-17b-128e-instruct"]
import os
from django.conf import settings
from groq import Groq

# Initialize client using environment variable or Django settings
GROQ_API_KEY = (getattr(settings, 'GROQ_API_KEY', '') or os.getenv('GROQ_API_KEY', '') or '').strip()
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None


def _groq_client():
    api_key = (getattr(settings, 'GROQ_API_KEY', '') or os.environ.get("GROQ_API_KEY") or '').strip()
    if not api_key:
        logger.warning("GROQ_API_KEY not set - skipping extraction.")
        return None
    return Groq(api_key=api_key)


def ask_travel_assistant(
    user_message: str, trip_destination: str = ''
) -> str:
    """Calls Groq API to act as a virtual assistant for travel recommendations."""
    system_prompt = (
        "You are an expert AI Travel Assistant for a premium travel app. "
        "You provide recommendations for local food attractions, scenic/beauty spots, "
        "hidden gems, hotels, residential areas, and tourist places. "
        "Keep responses structured, engaging, and clear using bullet points and emojis. "
        "Provide clear, well-structured travel recommendations. "
        "Do NOT use Markdown tables or raw HTML tags like <br>. "
        "Use clean bullet points with emojis instead."
        f"Context Destination: {trip_destination if trip_destination else 'General Travel'}."
     )
    client = _groq_client()
    if client is None:
        logger.warning("GROQ_API_KEY not set - skipping extraction.")
        return "Sorry, I cannot provide recommendations at this time."
    try:
        completion = client.chat.completions.create(
            model=TEXT_MODEL_CANDIDATES[0],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.7,
            max_tokens=1024,
        )
        return completion.choices[0].message.content
    except Exception as e:
        return (
            "Sorry, I encountered an issue retrieving recommendations: "
            f"{str(e)}"
        )

  
def _pdf_to_text(file_path, max_chars=12000):
    from pypdf import PdfReader
    try:
        reader = PdfReader(file_path)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return text[:max_chars]
    except Exception:
        logger.exception("Failed to read PDF %s", file_path)
        return ""


def _is_model_not_found(exc):
    msg = str(exc).lower()
    return "model_not_found" in msg or "does not exist" in msg or "404" in msg


def _chat_with_fallback(client, messages, candidates):
    """Try each model in order; only move to the next on a 'model not
    found' error, and force valid JSON output via response_format."""
    last_exc = None
    for model in candidates:
        try:
            response = client.chat.completions.create(
                model=model,
                max_tokens=1024,
                messages=messages,
                response_format={"type": "json_object"},  # <-- forces valid JSON, fixes the parse-error issue
            )
            return response.choices[0].message.content
        except Exception as exc:
            last_exc = exc
            if _is_model_not_found(exc):
                logger.warning("Model %s unavailable, trying next candidate", model)
                continue
            raise
    raise last_exc


FLIGHT_PROMPT = """Extract details from this travel ticket/confirmation
(flight, train, bus, or event). Return ONLY a JSON object with exactly
these keys (use "" for anything not found):

{
  "title": "short label e.g. 'Flight to Paris' or 'Train to Rome'",
  "airline": "airline / operator name",
  "flight_number": "flight/train/bus number",
  "booking_reference": "PNR or confirmation code",
  "departure_airport": "departure airport/station code or name",
  "arrival_airport": "arrival airport/station code or name",
  "departure_datetime": "ISO 8601 datetime, e.g. 2026-09-20T14:30",
  "arrival_datetime": "ISO 8601 datetime",
  "seat_number": "seat, if present",
  "location": "destination city, for calendar/map display"
}
Return valid JSON only, no markdown fences, no commentary."""

HOTEL_PROMPT = """Extract details from this hotel bill/invoice/confirmation.
Return ONLY a JSON object with exactly these keys (use "" for anything not found):

{
  "hotel_name": "name of the hotel/property",
  "booking_reference": "confirmation/invoice number",
  "location": "city or full address",
  "checkin_date": "ISO 8601 date, e.g. 2026-09-20",
  "checkout_date": "ISO 8601 date",
  "total_cost": "numeric total amount only, e.g. 350.00"
}
Return valid JSON only, no markdown fences, no commentary."""


def _extract(file_path, prompt, empty_result):
    client = _groq_client()
    if client is None:
        logger.warning("GROQ_API_KEY not set - skipping extraction.")
        return empty_result

    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        return empty_result

    try:
        if mime_type in IMAGE_MIME_TYPES:
            with open(file_path, "rb") as fh:
                data = base64.b64encode(fh.read()).decode("utf-8")
            messages = [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{data}"}},
                ],
            }]
            text = _chat_with_fallback(client, messages, VISION_MODEL_CANDIDATES)

        elif mime_type == "application/pdf":
            pdf_text = _pdf_to_text(file_path)
            if not pdf_text.strip():
                return empty_result
            messages = [{"role": "user", "content": f"{prompt}\n\nDocument text:\n{pdf_text}"}]
            text = _chat_with_fallback(client, messages, TEXT_MODEL_CANDIDATES)

        else:
            return empty_result

        return json.loads(text)

    except Exception:
        logger.exception("Extraction failed for %s", file_path)
        return empty_result


def extract_flight_info(file_path):
    empty = {
        "title": "", "airline": "", "flight_number": "", "booking_reference": "",
        "departure_airport": "", "arrival_airport": "", "departure_datetime": "",
        "arrival_datetime": "", "seat_number": "", "location": "",
    }
    return {**empty, **_extract(file_path, FLIGHT_PROMPT, empty)}


def extract_hotel_info(file_path):
    empty = {
        "hotel_name": "", "booking_reference": "", "location": "",
        "checkin_date": "", "checkout_date": "", "total_cost": "",
    }
    return {**empty, **_extract(file_path, HOTEL_PROMPT, empty)}


def generate_trip_suggestions(
    destination: str, trip_type: str = "General"
) -> dict:
    """Generates structured travel key points as a JSON/dictionary."""
    system_prompt = (
        "You are a travel assistant for a web application dashboard. "
        "For the given destination, return a JSON object with strictly these keys: "
        '"food", "area", "shopping", "transit", "viewpoints", "religious".'
        " Provide short 1-sentence recommendations for each value without Markdown or extra keys."
    )

    client = _groq_client()
    if client is None:
        # Return fallback if API key not configured
        return {
            "food": "Try iconic local dishes & central street markets",
            "area": "Explore City Center & Old Town districts",
            "shopping": "Visit Central High Street & local artisan bazaars",
            "transit": "Use Main Central Train Station & local bus routes",
            "viewpoints": "Check out panoramic observation decks & scenic parks",
            "religious": "Visit historic cathedrals and ancient city temples",
        }

    try:
        completion = client.chat.completions.create(
            model=TEXT_MODEL_CANDIDATES[0],
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Destination: {destination}, Trip Style: {trip_type}",
                },
            ],
            temperature=0.7,
            max_tokens=400,
            response_format={"type": "json_object"},
        )
        return json.loads(completion.choices[0].message.content)
    except Exception:
        # Fallback dictionary if API call fails
        return {
            "food": "Try iconic local dishes & central street markets",
            "area": "Explore City Center & Old Town districts",
            "shopping": "Visit Central High Street & local artisan bazaars",
            "transit": "Use Main Central Train Station & local bus routes",
            "viewpoints": "Check out panoramic observation decks & scenic parks",
            "religious": "Visit historic cathedrals and ancient city temples",
        }

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
