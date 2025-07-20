# klayons/urls.py
from django.contrib import admin
from django.urls import path, include
from accounts.views import api_documentation

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('', api_documentation, name='home'),
]
