from django.urls import path
from . import views

app_name = 'payment'

urlpatterns = [
    path("pricing-page-view/", views.pricing, name="pricing"),
    path("checkout/", views.create_checkout_session, name="checkout"),
    path("success/", views.success, name="success"),
    path("cancel/", views.cancel, name="cancel"),
]