from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class PaymentSuccessTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='premium-user',
            email='premium@example.com',
            password='secret123',
        )

    @patch('payment.views.stripe.checkout.Session.retrieve')
    def test_success_redirects_to_dashboard_and_marks_user_premium(self, mock_retrieve):
        self.client.force_login(self.user)
        mock_retrieve.return_value.payment_status = 'paid'

        response = self.client.get(
            reverse('payment:success') + '?session_id=test_session_123',
            follow=True,
        )

        self.user.refresh_from_db()

        self.assertEqual(response.redirect_chain[-1][0], reverse('homepage:dashboard'))
        self.assertTrue(self.user.is_premium)
        self.assertEqual(self.user.subscription_status, 'active')
        self.assertEqual(self.user.subscription_plan, 'premium')
