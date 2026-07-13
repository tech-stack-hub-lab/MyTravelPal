from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


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
    trip_name = models.CharField(max_length=150)
    destination = models.CharField(max_length=150)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.trip_name} — {self.destination}'


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
    airline = models.CharField(max_length=100)
    flight_number = models.CharField(max_length=30)
    booking_reference = models.CharField(max_length=50, blank=True)
    departure_airport = models.CharField(max_length=10)
    arrival_airport = models.CharField(max_length=10)
    departure_datetime = models.DateTimeField()
    arrival_datetime = models.DateTimeField()
    seat_number = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.airline} {self.flight_number}'


class HotelBooking(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='hotels')
    hotel_name = models.CharField(max_length=150)
    booking_reference = models.CharField(max_length=50, blank=True)
    location = models.CharField(max_length=150)
    checkin_date = models.DateField()
    checkout_date = models.DateField()
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
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
