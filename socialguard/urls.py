from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda request: redirect('dashboard/')),
    path('', include('accounts.urls')),
    path('profile-checker/', include('profile_checker.urls', namespace='profile_checker')),
] + static(settings.WHOLEDATA_URL, document_root=settings.WHOLEDATA_ROOT)
