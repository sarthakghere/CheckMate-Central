"""
URL configuration for checkmate_central project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from users import views as user_views

urlpatterns = [
    path('', user_views.landing_page, name='landing_page'),
    path('admin/', admin.site.urls),
    path("backups/", include("backups.urls")),
    path('api/backups/', include('backups.urls')),
    path('users/', include('users.urls')),
    path('colleges/', include('colleges.urls')),
]

handler404 = 'users.views.landing_page'
