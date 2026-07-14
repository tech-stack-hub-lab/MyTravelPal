from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import CalendarEvent, Flight, HotelBooking, Trip


class CreateBookingViewsTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='tester',
            email='tester@example.com',
            password='secret123',
        )
        self.trip = Trip.objects.create(
            user=self.user,
            trip_name='Summer Trip',
            destination='Paris',
            start_date='2026-07-20',
            end_date='2026-07-27',
            status='planned',
        )

    def test_trip_create_saves_trip(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('homepage:trip_create'),
            {
                'trip_name': 'Winter Break',
                'destination': 'Rome',
                'start_date': '2026-12-01',
                'end_date': '2026-12-10',
                'status': 'planned',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Trip.objects.filter(trip_name='Winter Break', user=self.user).exists())

    def test_flight_create_saves_flight(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('homepage:flight_create'),
            {
                'trip': self.trip.id,
                'airline': 'BA',
                'flight_number': 'BA123',
                'booking_reference': 'REF123',
                'departure_airport': 'LHR',
                'arrival_airport': 'CDG',
                'departure_datetime': '2026-07-20T10:00',
                'arrival_datetime': '2026-07-20T13:00',
                'seat_number': '12A',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Flight.objects.filter(flight_number='BA123', trip=self.trip).exists())

    def test_hotel_create_saves_hotel(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('homepage:hotel_create'),
            {
                'trip': self.trip.id,
                'hotel_name': 'Hotel Paris',
                'booking_reference': 'HTL1',
                'location': 'Paris',
                'checkin_date': '2026-07-20',
                'checkout_date': '2026-07-27',
                'total_cost': Decimal('320.50'),
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(HotelBooking.objects.filter(hotel_name='Hotel Paris', trip=self.trip).exists())

    def test_event_create_saves_event(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('homepage:event_create'),
            {
                'trip': self.trip.id,
                'event_type': 'tour',
                'title': 'City Tour',
                'start_datetime': '2026-07-21T09:00',
                'end_datetime': '2026-07-21T12:00',
                'color_code': '#ff0000',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(CalendarEvent.objects.filter(title='City Tour', trip=self.trip).exists())
