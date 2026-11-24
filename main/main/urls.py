from django.urls import path
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from app import views

urlpatterns = [
    path('admin/', admin.site.urls),

    path('equipment/<int:pk>/', views.equipment, name='equipment'),
    path('equipment/<int:pk>/move_equipment/', views.move_equipment, name='move_equipment'),
    path('equipment/<int:pk>/write_off_equipment/', views.write_off_equipment, name='write_off_equipment'),
    path('equipment/<int:pk>/create_repair/', views.create_repair, name='create_repair'),
    path('equipment/signout/', views.signout, name='signout'),

    path('catalog/', views.catalog, name='catalog'),
    path('catalog/add_equipment/', views.add_equipment, name='add_equipment'),
    path('catalog/add_equipment/add/', views.add, name='add'),
    path('catalog/signout/', views.signout, name='signout'),

    path('equipment/<int:pk>/edit/', views.edit, name='edit'),
    path('equipment/<int:pk>/edit/save_edit/', views.save_edit, name='save_edit'),

    path('profile/', views.profile, name='profile'),
    path('profile/profile/', views.profile, name='profile'),
    path('profile/signout/', views.signout, name='signout'),
    
    path('repairs/', views.repairs, name='repairs'),
    path('repairs/close_repair/', views.close_repair, name='close_repair'),
    path('repairs/signout/', views.signout, name='signout'),

    path('signin/', views.signin, name='signin'),
    path('auth/', views.auth, name='auth'),
    path('signup/', views.signup, name='signup'),
    path('add_user/', views.add_user, name='add_user'),

    path('signin_staff/', views.signin_staff, name='signin_staff'),
    path('signup_staff/', views.signup_staff, name='signup_staff'),

    path('statement/', views.statement, name='statement'),
    path('statement/signout/', views.statement, name='statement'),

    path('', views.index, name='index'),
    path('signout/', views.signout, name='signout'),

    path('test-500/', views.test_500),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)