from django import forms

from .models import BookingImport, Trip, Flight, HotelBooking, CalendarEvent


class BookingImportForm(forms.ModelForm):
    class Meta:
        model = BookingImport
        fields = ['trip', 'file']
        widgets = {
            'trip': forms.Select(attrs={'class': 'form-select'}),
        }


class TripForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = [
            'trip_name',
            'destination',
            'start_date',
            'end_date',
            'status',
        ]


class FlightForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user is not None:
            self.fields['trip'].queryset = Trip.objects.filter(user=self.user)

    class Meta:
        model = Flight
        fields = [
            'trip',
            'airline',
            'flight_number',
            'booking_reference',
            'departure_airport',
            'arrival_airport',
            'departure_datetime',
            'arrival_datetime',
            'seat_number',
        ]
        widgets = {
            'departure_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'arrival_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        }


class HotelBookingForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user is not None:
            self.fields['trip'].queryset = Trip.objects.filter(user=self.user)

    class Meta:
        model = HotelBooking
        fields = [
            'trip',
            'hotel_name',
            'booking_reference',
            'location',
            'checkin_date',
            'checkout_date',
            'total_cost',
        ]
        widgets = {
            'checkin_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'checkout_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }


class CalendarEventForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user is not None:
            self.fields['trip'].queryset = Trip.objects.filter(user=self.user)

    class Meta:
        model = CalendarEvent
        fields = ['trip', 'event_type', 'title', 'start_datetime', 'end_datetime', 'color_code']
        widgets = {
            'start_datetime': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_datetime': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'London Sightseeing Tour'}),
            'event_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tour'}),
            'color_code': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
        }
