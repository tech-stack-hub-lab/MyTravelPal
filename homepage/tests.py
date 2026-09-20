from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .views import _extract_flight_details
from .models import CalendarEvent, Flight, HotelBooking, ItineraryItem, Trip, trip_bucket_for


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
                'category': 'leisure',
                'start_date': '2026-12-01',
                'end_date': '2026-12-10',
                'status': 'planned',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Trip.objects.filter(trip_name='Winter Break', user=self.user).exists())

    def test_trip_create_sets_default_legacy_trip_type(self):
        trip = Trip.objects.create(
            user=self.user,
            trip_name='Family Trip',
            destination='Mumbai',
            start_date='2026-09-09',
            end_date='2026-09-30',
            status='planned',
            category='family',
        )

        self.assertEqual(trip.trip_type, 'family')
        self.assertFalse(trip.is_archived)

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

    def test_trip_bucket_uses_dates_before_generic_status(self):
        trip = Trip.objects.create(
            user=self.user,
            trip_name='Past Trip',
            destination='Rome',
            start_date='2026-08-01',
            end_date='2026-08-10',
            status='planned',
        )

        self.assertEqual(trip.determine_status(), 'completed')
        self.assertEqual(trip_bucket_for(trip), 'past')

    def test_trip_wizard_save_place_updates_existing_map_place(self):
        self.client.force_login(self.user)
        session = self.client.session
        session['trip_wizard_trip_id'] = self.trip.id
        session.save()

        payload = {
            'place_name': 'Eiffel Tower',
            'description': 'Paris, France',
            'latitude': '48.8584',
            'longitude': '2.2945',
        }

        first_response = self.client.post(reverse('homepage:trip_wizard_save_place'), payload)
        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(ItineraryItem.objects.filter(trip=self.trip, category='map_place').count(), 1)

        payload['description'] = 'Updated address for Eiffel Tower'
        second_response = self.client.post(reverse('homepage:trip_wizard_save_place'), payload)
        self.assertEqual(second_response.status_code, 200)
        self.assertEqual(ItineraryItem.objects.filter(trip=self.trip, category='map_place').count(), 1)

        item = ItineraryItem.objects.get(trip=self.trip, category='map_place')
        self.assertEqual(item.place_name, 'Eiffel Tower')
        self.assertEqual(item.description, 'Updated address for Eiffel Tower')

    def test_trip_wizard_finish_clears_session_and_redirects_to_dashboard(self):
        self.client.force_login(self.user)
        session = self.client.session
        session['trip_wizard_trip_id'] = self.trip.id
        session['extracted_flight'] = {'flight_number': 'BA123'}
        session['trip_wizard_pending_flight'] = {'flight_number': 'BA123'}
        session.save()

        response = self.client.post(reverse('homepage:trip_wizard_finish'))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('homepage:dashboard'))
        self.assertNotIn('trip_wizard_trip_id', self.client.session)
        self.assertNotIn('extracted_flight', self.client.session)
        self.assertNotIn('trip_wizard_pending_flight', self.client.session)

    def test_trip_wizard_step2_serializes_hotel_total_cost_without_decimal_error(self):
        self.client.force_login(self.user)
        session = self.client.session
        session['trip_wizard_trip_id'] = self.trip.id
        session.save()

        response = self.client.post(
            reverse('homepage:trip_wizard_step2'),
            {
                'save_details': '1',
                'hotel_name': 'Hotel Paris',
                'booking_reference': 'HTL1',
                'location': 'Paris',
                'checkin_date': '2026-07-20',
                'checkout_date': '2026-07-27',
                'total_cost': '320.50',
            },
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn('trip_wizard_pending_hotel', self.client.session)
        self.assertIn('total_cost', self.client.session['trip_wizard_pending_hotel'])

    def test_trip_wizard_finish_persists_pending_trip_data_before_redirect(self):
        self.client.force_login(self.user)
        session = self.client.session
        session['trip_wizard_trip_id'] = self.trip.id
        session['trip_wizard_pending_flight'] = {
            'airline': 'Air France',
            'flight_number': 'AF456',
            'booking_reference': 'AF-REF-1',
            'departure_airport': 'CDG',
            'arrival_airport': 'JFK',
            'departure_datetime': '2026-07-21T08:30:00',
            'arrival_datetime': '2026-07-21T11:15:00',
            'seat_number': '12C',
        }
        session['trip_wizard_pending_hotel'] = {
            'hotel_name': 'Sky Hotel',
            'booking_reference': 'HOTEL-42',
            'location': 'New York',
            'checkin_date': '2026-07-20',
            'checkout_date': '2026-07-27',
            'total_cost': '420.00',
        }
        session.save()

        response = self.client.post(reverse('homepage:trip_wizard_finish'))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('homepage:dashboard'))
        self.trip.refresh_from_db()
        self.assertTrue(self.trip.flights.filter(flight_number='AF456').exists())
        self.assertTrue(self.trip.hotels.filter(hotel_name='Sky Hotel').exists())
        self.assertNotIn('trip_wizard_pending_flight', self.client.session)
        self.assertNotIn('trip_wizard_pending_hotel', self.client.session)

    def test_extract_flight_details_ignores_noisy_ocr_values(self):
        raw_text = '''
        Flight Emirates EK 203
        Reservation
        Booking ref: ABX987
        From Dubai to London
        Departure: 2026-09-22 22:00
        Arrival: 2026-09-23 03:10
        Seat: 12A
        '''

        extracted = _extract_flight_details(raw_text)

        self.assertEqual(extracted['booking_reference'], 'ABX987')
        self.assertEqual(extracted['departure_airport'], 'Dubai')
        self.assertEqual(extracted['arrival_airport'], 'London')
        self.assertEqual(extracted['departure_datetime'], '2026-09-22T22:00+00:00')
        self.assertEqual(extracted['arrival_datetime'], '2026-09-23T03:10+00:00')
        self.assertEqual(extracted['seat_number'], '12A')

    def test_extract_flight_details_rejects_noise_like_mer_support(self):
        raw_text = '''
        Flight Emirates EK 203
        Booking ref: ABX987
        From Dubai to Mer Support
        Departure: 2026-09-22 22:00
        Arrival: 2026-09-23 03:10
        Seat: 12A
        '''

        extracted = _extract_flight_details(raw_text)

        self.assertEqual(extracted['booking_reference'], 'ABX987')
        self.assertEqual(extracted['departure_airport'], 'Dubai')
        self.assertEqual(extracted['arrival_airport'], '')
        self.assertEqual(extracted['seat_number'], '12A')


class AuthRedirectTests(TestCase):
    def test_login_redirects_to_dashboard_for_valid_credentials(self):
        user = get_user_model().objects.create_user(
            username='tester',
            email='tester@example.com',
            password='secret123',
        )

        response = self.client.post(
            reverse('homepage:login'),
            {
                'username': user.username,
                'password': 'secret123',
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse('homepage:dashboard'))

    def test_register_redirects_to_dashboard_after_account_creation(self):
        response = self.client.post(
            reverse('homepage:register'),
            {
                'username': 'newtraveler',
                'email': 'newtraveler@example.com',
                'password1': 'StrongPass123!',
                'password2': 'StrongPass123!',
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse('homepage:dashboard'))
        self.assertTrue(get_user_model().objects.filter(username='newtraveler').exists())


