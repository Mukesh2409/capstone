from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from accounts import views

urlpatterns = [
    path('batch-scan/', views.batch_scan, name='batch_scan'),
    path('generate-report/<int:scan_id>/', views.generate_report, name='generate_report'),
    path('admin/', admin.site.urls),
    path('signup/', views.signup, name='signup'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('connect-instagram/', views.connect_instagram, name='connect_instagram'),
    path('scan-instagram/', views.scan_instagram, name='scan_instagram'),
    path('scan-profile/', views.scan_profile, name='scan_profile'),
    path('predict-profile/', views.predict_profile, name='predict_profile'),
    path('scan-result/<int:scan_id>/', views.scan_result, name='scan_result'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('password-reset/', views.password_reset, name='password_reset'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('scan-profile/', views.scan_profile, name='scan_profile'),
    path('scan-history/', views.scan_history, name='scan_history'),
    path('delete-scan/<int:scan_id>/', views.delete_scan, name='delete_scan'),
    path('batch-scan/', views.batch_scan, name='batch_scan'),
    path('generate-report/<int:scan_id>/', views.generate_report, name='generate_report'),
    path('notifications/', views.notifications, name='notifications'),
    path('compare-profiles/', views.compare_profiles, name='compare_profiles'),
    path('api/scan/', views.api_scan, name='api_scan'),
    path('export-scan-history-csv/', views.export_scan_history_csv, name='export_scan_history_csv'),
    path('', RedirectView.as_view(url='/login/')),
]