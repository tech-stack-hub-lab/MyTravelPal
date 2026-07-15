from django.urls import path
# from django.contrib.auth.views import LogoutView
from . import views

app_name = 'homepage'

urlpatterns = [
    path('', views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    # path('logout/', LogoutView.as_view(), name='logout'),
    path('trips/', views.trip_list, name='trip_list'),
    path('trips/create/', views.trip_create, name='trip_create'),
    path('trips/<int:trip_id>/', views.trip_detail, name='trip_detail'),
    path('flights/', views.flight_list, name='flight_list'),
    path('flights/create/', views.flight_create, name='flight_create'),
    path('hotels/', views.hotel_list, name='hotel_list'),
    path('hotels/create/',views.hotel_create, name="hotel_create"),
    path('events/', views.event_list, name="event_list"),
    path('events/create/',views.event_create, name="event_create"),
    path("calendar/events/",views.calendar_events, name="calendar_events"),
    path('uploads/', views.uploaded_files, name='uploaded_files'),
    path('uploads/new/', views.upload_booking, name='upload_booking'),
    path('chat/api/', views.chat_api, name='chat_api'),
    
]
