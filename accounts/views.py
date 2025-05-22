from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.views import PasswordResetView
from django.contrib.auth import login, authenticate, logout
from .forms import SignUpForm, LoginForm
from django.contrib.auth.decorators import login_required
from .instagram_utils import connect_instagram_profile, perform_instagram_scan
from .models import ProfileScan
from .forms import ProfileEditForm
from django.contrib import messages
from .scan_utils import analyze_profile
from .forms import ProfileScanForm
from django.http import HttpResponse
from .batch_utils import process_batch_scan, generate_pdf_report
import random
from django.shortcuts import render
from django.http import JsonResponse
import requests
import os
from django.conf import settings
import joblib
import json

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = SignUpForm()
    return render(request, 'accounts/signup.html', {'form': form})

def password_reset(request):
    return PasswordResetView.as_view()(request)

def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                return redirect('dashboard')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})

def user_logout(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    recent_scans = ProfileScan.objects.filter(scanned_by=request.user).order_by('-scan_date')[:3]
    fake_count = ProfileScan.objects.filter(scanned_by=request.user, scan_result='FAKE').count()
    real_count = ProfileScan.objects.filter(scanned_by=request.user, scan_result='REAL').count()
    total_scans = ProfileScan.objects.filter(scanned_by=request.user).count()
    stats = {
        'total_scans': total_scans,
        'real_count': real_count,
        'fake_count': fake_count,
    }
    account_data = {'labels': ['Fake', 'Real'], 'datasets': [{'data': [fake_count, real_count], 'backgroundColor': ['#dc3545', '#28a745']}]}    
    return render(request, 'accounts/dashboard.html', {
        'recent_scans': recent_scans,
        'account_data': account_data,
        'stats': stats,
    })

@login_required
def scan_profile(request):
    if request.method == 'POST':
        form = ProfileScanForm(request.POST)
        if form.is_valid():
            scan = form.save(commit=False)
            scan.scanned_by = request.user
            # Use ANN model for prediction
            from .ann_predictor import InstagramANNPredictor
            import pandas as pd
            # Suspicious username check
            suspicious_usernames = ['spam', 'fake', 'user']
            if any(s in scan.username.lower() for s in suspicious_usernames):
                scan.scan_result = 'FAKE'
                scan.confidence = 0.99
                scan.algorithm_used = 'UsernameRule'
                confidence = 0.99
            else:
                predictor = InstagramANNPredictor()
                # Prepare input as DataFrame
                input_data = pd.DataFrame([{
                    'username': scan.username,
                    'bio': scan.bio,
                    'followers_count': scan.followers_count,
                    'following_count': scan.following_count,
                    'is_private': int(scan.is_private),
                    'posts_count': scan.posts_count
                }])
                # Let the predictor handle feature engineering
                pred_class, pred_probs = predictor.predict(input_data)
                confidence = float(pred_probs[0][pred_class[0]])
                scan.scan_result = 'FAKE' if pred_class[0] == 1 else 'REAL'
                scan.confidence = confidence
                scan.algorithm_used = 'ANN'
            scan.save()
            return render(request, 'accounts/scan_result.html', {
                'scan': scan,
                'algorithms': {'ANN': confidence},
            })
    else:
        form = ProfileScanForm()
    return render(request, 'accounts/scan_profile.html', {'form': form})

@login_required
def batch_scan(request):
    if request.method == 'POST':
        usernames = request.POST.get('usernames').split('\n')
        usernames = [username.strip() for username in usernames if username.strip()]
        
        if not usernames:
            messages.error(request, 'Please enter at least one username')
            return redirect('batch_scan')
            
        results = process_batch_scan(usernames)
        return render(request, 'accounts/batch_scan.html', {'results': results})
    
    return render(request, 'accounts/batch_scan.html')

@login_required
def generate_report(request, scan_id):
    scan = get_object_or_404(ProfileScan, id=scan_id, scanned_by=request.user)
    filename = generate_pdf_report(scan)
    
    with open(filename, 'rb') as pdf:
        response = HttpResponse(pdf.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

@login_required
def scan_history(request):
    scans = ProfileScan.objects.filter(scanned_by=request.user).order_by('-scan_date')
    return render(request, 'accounts/scan_history.html', {'scans': scans})


@login_required
def connect_instagram(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        if username:
            try:
                connect_instagram_profile(request.user, username)
                return redirect('dashboard')
            except Exception as e:
                # Handle errors
                pass
    return render(request, 'accounts/connect_instagram.html')

@login_required
def scan_instagram(request):
    if hasattr(request.user, 'instagram'):
        scan = perform_instagram_scan(request.user)
        return redirect('scan_result', scan_id=scan.id)
    return redirect('connect_instagram')


@login_required
def predict_profile(request):
    """Run prediction analysis on the profile"""
    if request.method == 'POST':
        # Perform the scan and get results
        scan = analyze_profile(request.user)
        return redirect('scan_result', scan_id=scan.id)
    return redirect('scan_profile')

@login_required
def scan_result(request, scan_id):
    """Display scan results"""
    scan = get_object_or_404(ProfileScan, id=scan_id, user=request.user)
    return render(request, 'accounts/scan_result.html', {
        'scan': scan,
        'user': request.user
    })

@login_required
def delete_scan(request, scan_id):
    """Delete a scan history entry"""
    if request.method == 'POST':
        scan = get_object_or_404(ProfileScan, id=scan_id, scanned_by=request.user)
        scan.delete()
        messages.success(request, 'Scan deleted successfully.')
    return redirect('scan_history')

@login_required
def batch_scan(request):
    """Handle batch scanning of multiple profiles"""
    if request.method == 'POST':
        usernames = request.POST.getlist('usernames[]')
        if usernames:
            from .batch_utils import process_batch_scan
            results = process_batch_scan(usernames)
            return JsonResponse({'results': results})
    return render(request, 'accounts/batch_scan.html')

@login_required
def generate_report(request, scan_id):
    """Generate PDF report for a scan"""
    scan = get_object_or_404(ProfileScan, id=scan_id, scanned_by=request.user)
    from .batch_utils import generate_pdf_report
    filename = generate_pdf_report(scan)
    return FileResponse(open(filename, 'rb'), as_attachment=True)

@login_required
def notifications(request):
    """Handle real-time notifications"""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'accounts/notifications.html', {'notifications': notifications})

@login_required
def compare_profiles(request):
    """Compare multiple scanned profiles"""
    if request.method == 'POST':
        profile_ids = request.POST.getlist('profile_ids[]')
        from .batch_utils import compare_profile_metrics
        comparison = compare_profile_metrics(profile_ids)
        return JsonResponse(comparison)
    scans = ProfileScan.objects.filter(scanned_by=request.user)
    return render(request, 'accounts/compare_profiles.html', {'scans': scans})

@login_required
def api_scan(request):
    """API endpoint for third-party integrations"""
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        if username:
            scan = perform_instagram_scan(username)
            return JsonResponse({
                'scan_id': scan.id,
                'risk_score': scan.risk_score,
                'indicators': scan.indicators
            })
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = ProfileEditForm(instance=request.user)
    
    return render(request, 'accounts/edit_profile.html', {'form': form})


@login_required
def export_scan_history_csv(request):
    """Export user's scan history as a CSV file"""
    import csv
    from django.http import HttpResponse
    scans = ProfileScan.objects.filter(scanned_by=request.user).order_by('-scan_date')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="scan_history.csv"'
    writer = csv.writer(response)
    writer.writerow(['Username', 'Bio', 'Followers', 'Following', 'Private', 'Posts', 'Result', 'Confidence', 'Algorithm', 'Date'])
    for scan in scans:
        writer.writerow([
            scan.username,
            scan.bio,
            scan.followers_count,
            scan.following_count,
            'Yes' if scan.is_private else 'No',
            scan.posts_count,
            scan.scan_result,
            f"{scan.confidence:.2f}",
            scan.algorithm_used,
            scan.scan_date.strftime('%Y-%m-%d %H:%M')
        ])
    return response

@login_required
def api_social_scanner(request):
    """
    API endpoint to scan a social media profile using the Social Scanner API via RapidAPI.
    Expects a POST request with JSON body: {"username": "target_username", "platform": "instagram"}
    """
    if request.method == "POST":
        import json
        try:
            data = json.loads(request.body)
            username = data.get("username")
            platform = data.get("platform", "instagram")
            if not username:
                return JsonResponse({"error": "Username is required."}, status=400)
        except Exception:
            return JsonResponse({"error": "Invalid JSON."}, status=400)

        url = "https://social-scanner.p.rapidapi.com/scan"
        payload = {"username": username, "platform": platform}
        headers = {
            "content-type": "application/json",
            "X-RapidAPI-Key": "f253fd50ffmshbbd7b02f8601592p165c3ejsne9fb184ee8c7",
            "X-RapidAPI-Host": "instagram-scraper-ai1.p.rapidapi.com"
        }
        try:
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                return JsonResponse(response.json())
            else:
                return JsonResponse({"error": "API error", "details": response.text}, status=response.status_code)
        except Exception as e:
            return JsonResponse({"error": "Request failed", "details": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Only POST method allowed."}, status=405)

