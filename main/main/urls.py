from django.urls import path
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from app import views

urlpatterns = [
    path('admin/', admin.site.urls),

    path('equipment/', views.equipment, name='equipment'),
    path('equipment/add_equipment/', views.add_equipment),
    path('catalog/', views.catalog, name='catalog'),
    path('edit/', views.edit, name='edit'),
    path('profile/', views.profile, name='profile'),
    path('repairs/', views.repairs, name='repairs'),
    path('signin/', views.signin, name='signin'),
    path('signup/', views.signup, name='signup'),
    path('signin_staff/', views.signin_staff, name='signin_staff'),
    path('signup_staff/', views.signup_staff, name='signup_staff'),
    path('statement/', views.statement, name='statement'),

    path('', views.index, name='index'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)