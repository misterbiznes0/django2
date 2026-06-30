from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from mainKUA import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('profile/', views.profile, name='profile'),
    path('', views.register, name='register'),
    path('login/', views.loginf, name='login'),
    path('logout/', views.logoutf, name='logout'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)