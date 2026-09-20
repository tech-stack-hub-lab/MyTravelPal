from datetime import date

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


def _coerce_date(value):
    if value in (None, ''):
        return None
    if isinstance(value, date):
        return value
    if hasattr(value, 'date'):
        return value.date()
    value_str = str(value).strip()
    if not value_str:
        return None
    try:
        return date.fromisoformat(value_str.split('T')[0])
    except ValueError:
        return None


class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=30, blank=True)
    preferred_airport = models.CharField(max_length=10, blank=True)
    preferred_airline = models.CharField(max_length=100, blank=True)
    preferred_currency = models.CharField(max_length=3, blank=True, default='USD')
    notification_enabled = models.BooleanField(default=True)

    subscription_plan = models.CharField(max_length=50, blank=True)
    billing_cycle = models.CharField(max_length=30, blank=True)
    subscription_status = models.CharField(max_length=30, blank=True)
    subscription_start = models.DateField(null=True, blank=True)
    subscription_end = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.email or self.username

    @property
    def is_premium(self):
        """Return True when the user's subscription indicates an active/premium plan.

        This property is read-only and derived from existing fields so no migration is required.
        """
        plan = (self.subscription_plan or '').lower()
        status = (self.subscription_status or '').lower()
        if 'premium' in plan:
            return True
        if status in ('active', 'paid'):
            return True
        return False
    

class Trip(models.Model):
    CATEGORY_CHOICES = [
        ('leisure', 'Vacation / Leisure'),
        ('cultural', 'Cultural & Sightseeing'),
        ('adventure', 'Adventure & Outdoor'),
        ('business', 'Business / Work'),
        ('road_trip', 'Road Trip'),
        ('family', 'Family Trip'),
        ('solo', 'Solo Travel'),
    ]
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='trips',
    )
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='leisure')
    trip_type = models.CharField(max_length=50, blank=True, default='leisure', null=True)
    title = models.CharField(max_length=200, blank=True, default='', null=True)
    trip_name = models.CharField(max_length=150, blank=True, default='', null=True)
    destination = models.CharField(max_length=150, blank=True, default='', null=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    budget = models.DecimalField(max_digits=12, decimal_places=2, default=0, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned', blank=True, null=True)
    notes = models.TextField(blank=True, default='', null=True)
    description = models.TextField(blank=True, default='', null=True)
    is_archived = models.BooleanField(default=False)
    ai_recommendations = models.JSONField(blank=True, null=True, default=dict)
    extracted_data = models.JSONField(blank=True, null=True, default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def determine_status(self):
        today = date.today()
        status = (self.status or '').lower()

        start_date = _coerce_date(self.start_date)
        end_date = _coerce_date(self.end_date)

        if status == 'cancelled':
            return 'cancelled'

        if start_date and end_date:
            if end_date < today:
                return 'completed'
            if start_date <= today <= end_date:
                return 'active'
            if start_date > today:
                return 'planned'

        if start_date:
            if start_date > today:
                return 'planned'
            return 'active'

        if end_date:
            if end_date < today:
                return 'completed'
            return 'planned'

        if status in {'planned', 'active', 'completed'}:
            return status

        return 'planned'

    def save(self, *args, **kwargs):
        if not self.trip_type or (self.trip_type == 'leisure' and self.category and self.category != 'leisure'):
            self.trip_type = self.category or 'leisure'
        if not self.trip_name and self.title:
            self.trip_name = self.title
        if self.title and not self.title.strip():
            self.title = self.trip_name or 'My trip'
        if not self.title and self.trip_name:
            self.title = self.trip_name
        if not self.description:
            self.description = self.notes or ''
        if not self.status:
            self.status = self.determine_status()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.title or self.trip_name or "Trip"} — {self.destination}'


class BookingImport(models.Model):
    IMPORT_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='imports',
    )
    trip = models.ForeignKey(
        Trip,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='imports',
    )
    file = models.FileField(upload_to='booking_imports/')
    extracted_text = models.TextField(blank=True)
    import_status = models.CharField(max_length=20, choices=IMPORT_STATUS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name

    def extract_data(self):
        raw_content = ''
        try:
            with self.file.open('rb') as uploaded:
                raw_content = uploaded.read().decode('utf-8', errors='ignore')
        except Exception:
            raw_content = ''

        self.extracted_text = raw_content or f'Imported file {self.file.name}. No text could be extracted.'
        self.import_status = 'completed'
        self.save(update_fields=['extracted_text', 'import_status'])

        if self.trip is None:
            self.trip = Trip.objects.create(
                user=self.user,
                trip_name='Imported Trip',
                destination='Unknown',
                start_date=timezone.now().date(),
                end_date=timezone.now().date(),
            )
            self.save(update_fields=['trip'])

        if 'flight' in raw_content.lower():
            Flight.objects.create(
                trip=self.trip,
                airline='Unknown Airline',
                flight_number='AUTO',
                booking_reference='AUTO',
                departure_airport='Unknown',
                arrival_airport='Unknown',
                departure_datetime=timezone.now(),
                arrival_datetime=timezone.now(),
            )

        if 'hotel' in raw_content.lower():
            HotelBooking.objects.create(
                trip=self.trip,
                hotel_name='Unknown Hotel',
                booking_reference='AUTO',
                location='Unknown',
                checkin_date=timezone.now().date(),
                checkout_date=timezone.now().date(),
                total_cost=0,
            )


class Flight(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='flights')
    airline = models.CharField(max_length=100, blank=True)
    flight_number = models.CharField(max_length=30, blank=True)
    booking_reference = models.CharField(max_length=50, blank=True)
    departure_airport = models.CharField(max_length=100, blank=True)
    arrival_airport = models.CharField(max_length=100, blank=True)
    departure_datetime = models.DateTimeField()
    arrival_datetime = models.DateTimeField()
    seat_number = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.airline} {self.flight_number}'


class HotelBooking(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='hotels')
    hotel_name = models.CharField(max_length=150, blank=True)
    booking_reference = models.CharField(max_length=50, blank=True)
    location = models.CharField(max_length=150, blank=True)
    checkin_date = models.DateField()
    checkout_date = models.DateField()
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.hotel_name


class CalendarEvent(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=50)
    title = models.CharField(max_length=200)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    color_code = models.CharField(max_length=20, default='#3b82f6')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class ItineraryItem(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='itineraries')
    day_number = models.IntegerField()
    place_name = models.CharField(max_length=255)
    category = models.CharField(max_length=50) # attraction, food, hotel
    google_place_id = models.CharField(max_length=255, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    description = models.TextField(blank=True)


def update_trip_statuses():
    for trip in Trip.objects.all():
        trip.status = trip.determine_status()
        trip.save(update_fields=['status'])


def trip_bucket_for(trip):
    today = date.today()
    status = (trip.status or '').lower()
    start_date = _coerce_date(getattr(trip, 'start_date', None))
    end_date = _coerce_date(getattr(trip, 'end_date', None))

    if start_date and end_date:
        if end_date < today:
            return 'past'
        if start_date <= today <= end_date:
            return 'present'
        if start_date > today:
            return 'upcoming'

    if start_date:
        if start_date > today:
            return 'upcoming'
        return 'present'

    if end_date:
        if end_date < today:
            return 'past'
        return 'upcoming'

    if status == 'cancelled':
        return 'not_decided'
    if status == 'active':
        return 'present'
    if status == 'completed':
        return 'past'
    if status == 'planned':
        return 'upcoming'

    return 'not_decided'
