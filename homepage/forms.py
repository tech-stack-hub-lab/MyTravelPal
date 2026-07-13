from django import forms

from .models import BookingImport, Trip
from django import forms
from .models import (
    Trip,
    Flight,
    HotelBooking,
    CalendarEvent
)




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
                "trip_name",
                "destination",
                "start_date",
                "end_date",
                "status"
            ]
    
    
class FlightForm(forms.ModelForm):
    
        class Meta:
            model = Flight
            fields = "__all__"
    
    
class HotelBookingForm(forms.ModelForm):
    
        class Meta:
            model = HotelBooking
            fields = "__all__"
    
    
class CalendarEventForm(forms.ModelForm):
    
        class Meta:
            model = CalendarEvent
            fields = "__all__"
            
            widgets = {
            "start_datetime": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "type": "datetime-local"
                }
            ),
            "end_datetime": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "type": "datetime-local"
                }
            ),
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "London Sightseeing Tour"
                }
            ),
            "location": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "London"
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4
                }
            )
        }
