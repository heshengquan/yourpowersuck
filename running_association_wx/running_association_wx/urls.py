"""running_association_wx URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
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
from django.urls import path, include
from utils.admin_site import admin_site
from utils.access_token import GenerateQRCodeView
from . import index_view

urlpatterns = [
    path('your-power-suck-admin/', admin_site.urls),
    path('share/generate-QRcode/', GenerateQRCodeView.as_view()),
    path('', index_view.index),
    path('', include('me.urls')),
    path('', include('appointment.urls')),
    path('', include('running.urls')),
    path('', include('association.urls')),
    path('', include('marathon_spider.urls')),
    path('', include('pay.urls')),
    path('', include('poll.urls')),
    path('', include('ourRace.urls')),
]
