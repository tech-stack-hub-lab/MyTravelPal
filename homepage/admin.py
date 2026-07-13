from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import BookingImport, CalendarEvent, Flight, HotelBooking, Trip, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'subscription_plan', 'subscription_status', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('Travel Profile', {
            'fields': (
                'phone_number',
                'preferred_airport',
                'preferred_airline',
                'preferred_currency',
                'notification_enabled',
            )
        }),
        ('Subscription', {
            'fields': (
                'subscription_plan',
                'billing_cycle',
                'subscription_status',
                'subscription_start',
                'subscription_end',
            )
        }),
    )


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ('trip_name', 'destination', 'status', 'start_date', 'end_date', 'user')
    search_fields = ('trip_name', 'destination')


@admin.register(BookingImport)
class BookingImportAdmin(admin.ModelAdmin):
    list_display = ('file', 'trip', 'user', 'import_status', 'created_at')
    list_filter = ('import_status',)


@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):
    list_display = ('trip', 'airline', 'flight_number', 'departure_airport', 'arrival_airport')


@admin.register(HotelBooking)
class HotelBookingAdmin(admin.ModelAdmin):
    list_display = ('trip', 'hotel_name', 'location', 'checkin_date', 'checkout_date')


@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    list_display = ('trip', 'title', 'start_datetime', 'end_datetime')
