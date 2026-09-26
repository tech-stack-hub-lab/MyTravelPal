from django import forms

from .models import BookingImport, Trip, Flight, HotelBooking, CalendarEvent


class TripWizardForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = [
            'title',
            'category',
            'destination',
            'start_date',
            'end_date',
            'budget',
            'status',
            'notes',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': ''}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'destination': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Paris, France'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'budget': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Travel notes, preferences, must-see places...'}),
        }


class TripUploadForm(forms.Form):
    flight_file = forms.FileField(required=False, label='Flight confirmation (PDF/JPG/PNG)')
    hotel_file = forms.FileField(required=False, label='Hotel confirmation (PDF/JPG/PNG)')


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
            'category',
            'start_date',
            'end_date',
            'status',
        ]
        widgets = {
                    'category': forms.Select(attrs={'class': 'form-select'}),
                    # ... other widgets ...
                  }
        

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


class BookingUploadForm(forms.Form):
    """Handles the two file uploads + hotel search box at the top of the wizard."""

    flight_file = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={"class": "form-control", "accept": ".pdf,.png,.jpg,.jpeg,.webp"}),
    )
    hotel_file = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={"class": "form-control", "accept": ".pdf,.png,.jpg,.jpeg,.webp"}),
    )
    hotel_search = forms.CharField(
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. hotels near Eiffel Tower"}),
    )

    MAX_SIZE_BYTES = 5 * 1024 * 1024
    ALLOWED_EXTENSIONS = (".pdf", ".png", ".jpg", ".jpeg", ".webp")

    def _validate_file(self, file):
        if file.size > self.MAX_SIZE_BYTES:
            raise forms.ValidationError("File is too large (max 5 MB).")
        if not file.name.lower().endswith(self.ALLOWED_EXTENSIONS):
            raise forms.ValidationError("Unsupported file type. Please upload a PDF or image.")
        return file

    def clean_flight_file(self):
        file = self.cleaned_data.get("flight_file")
        return self._validate_file(file) if file else file

    def clean_hotel_file(self):
        file = self.cleaned_data.get("hotel_file")
        return self._validate_file(file) if file else file


class FlightDetailForm(forms.Form):
    """Field names must match exactly what the JS autoPopulateFlightData()
    writes into — see setFieldValue() calls in the template."""

    title = forms.CharField(
        required=False, max_length=255,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Flight to Paris"}),
    )
    airline = forms.CharField(
        required=False, max_length=255,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    flight_number = forms.CharField(
        required=False, max_length=50,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    booking_reference = forms.CharField(
        required=False, max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    departure_airport = forms.CharField(
        required=False, max_length=255,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    arrival_airport = forms.CharField(
        required=False, max_length=255,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    departure_datetime = forms.CharField(
        required=False,
        widget=forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
    )
    arrival_datetime = forms.CharField(
        required=False,
        widget=forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
    )
    seat_number = forms.CharField(
        required=False, max_length=20,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    location = forms.CharField(
        required=False, max_length=255,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )


class HotelDetailForm(forms.Form):
    """Field names must match exactly what the JS autoPopulateHotelData()
    writes into."""

    hotel_name = forms.CharField(
        required=False, max_length=255,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    booking_reference = forms.CharField(
        required=False, max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    location = forms.CharField(
        required=False, max_length=255,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    checkin_date = forms.CharField(
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
    checkout_date = forms.CharField(
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
    total_cost = forms.DecimalField(
        required=False, max_digits=10, decimal_places=2,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
    )


class TripUpdateForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = ['title', 'destination', 'start_date', 'end_date']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'destination': forms.TextInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }