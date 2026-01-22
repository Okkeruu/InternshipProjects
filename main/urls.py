from django.contrib import admin
from django.urls import path, include
from . import views
from .views import upload_excel, show_people, SignUpView, autocomplete_title, autocomplete_ekdoths



urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('people/', views.show_people, name='show_people'),
    path('upload/', views.upload_excel, name='upload_excel'),
    path('duplicates/', views.resolve_duplicates, name='resolve_duplicates'),
    
    path('duplicates/resolve/', views.resolve_duplicates, name='resolve_duplicates'),
    path('duplicates/replace-all/', views.replace_all_duplicates, name='replace_all_duplicates'),
    path('duplicates/skip-all/', views.skip_all_duplicates, name='skip_all_duplicates'),
    
    path('skip-all-duplicates/', views.skip_all_duplicates, name='skip_all_duplicates'),
    path('add-person/', views.add_person, name='add_person'),
    path('ajax/autocomplete/title/', views.autocomplete_title, name='autocomplete_title'),
    path('ajax/autocomplete/ekdoths/', views.autocomplete_ekdoths, name='autocomplete_ekdoths'),
    path('incomplete-records/', views.incomplete_records, name='incomplete_records'),
    path('people/edit/<int:ari8mos>/', views.edit_person, name='edit_person'),
    path('people/delete/<int:ari8mos>/', views.delete_person, name='delete_person'),
    path('print-range/', views.print_range, name='print_range'),
    path('print-range/data/', views.print_range_data, name='print_range_data'),

    

]
