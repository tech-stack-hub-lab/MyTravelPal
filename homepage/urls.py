from django.urls import path
# from django.contrib.auth.views import LogoutView
from . import views

app_name = 'homepage'

urlpatterns = [
    path('', views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('trips/wizard/', views.trip_wizard_step1, name='trip_wizard_step1'),
    path('trips/wizard/upload/', views.trip_wizard_step2, name='trip_wizard_step2'),
    path('trips/wizard/itinerary/', views.trip_wizard_step3, name='trip_wizard_step3'),
    path('trips/wizard/summary/', views.trip_wizard_step4, name='trip_wizard_step4'),
    path('trips/wizard/finish/', views.trip_wizard_finish, name='trip_wizard_finish'),
    path('trips/wizard/save-place/', views.trip_wizard_save_place, name='trip_wizard_save_place'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('trips/', views.trip_list, name='trip_list'),
    path('trips/create/', views.trip_create, name='trip_create'),
    path('trips/<int:trip_id>/', views.trip_detail, name='trip_detail'),
    path('trips/<int:trip_id>/delete/', views.trip_delete, name='trip_delete'),
    path('flights/', views.flight_list, name='flight_list'),
    path('flights/create/', views.flight_create, name='flight_create'),
    path('hotels/', views.hotel_list, name='hotel_list'),
    path('hotels/create/', views.hotel_create, name='hotel_create'),
    path('events/', views.event_list, name='event_list'),
    path('events/create/', views.event_create, name='event_create'),
    path('assistant/chat/', views.virtual_assistant_chat, name='virtual_assistant_chat'),
    path("calendar/events/",views.calendar_events, name="calendar_events"),
    path('uploads/', views.uploaded_files, name='uploaded_files'),
    path('uploads/new/', views.upload_booking, name='upload_booking'),
    path('chat/api/', views.chat_api, name='chat_api'),
    path(
        'ajax/add-ai-event/',
        views.add_ai_suggestion_event,
        name='add_ai_suggestion_event',
    ),
]

