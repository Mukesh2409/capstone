import json
from datetime import datetime
from .models import ProfileScan
from .instagram_utils import fetch_instagram_data
from django.http import JsonResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors

def process_batch_scan(usernames):
    """Process multiple Instagram profiles in batch"""
    results = []
    for username in usernames:
        try:
            data = fetch_instagram_data(username)
            risk_score = calculate_risk_score(data)
            results.append({
                'username': username,
                'risk_score': risk_score,
                'indicators': get_risk_indicators(data)
            })
        except Exception as e:
            results.append({
                'username': username,
                'error': str(e)
            })
    return results

def calculate_risk_score(profile_data):
    """Calculate risk score based on profile metrics"""
    score = 0
    
    # Example scoring logic
    if profile_data['follower_count'] > 0:
        ratio = profile_data['following_count'] / profile_data['follower_count']
        if ratio > 2:
            score += 20
    
    if not profile_data['is_verified'] and profile_data['follower_count'] > 10000:
        score += 15
        
    if profile_data['is_private']:
        score += 10
        
    return min(score, 100)

def get_risk_indicators(profile_data):
    """Analyze profile data for risk indicators"""
    indicators = []
    
    if profile_data['follower_count'] > 0:
        ratio = profile_data['following_count'] / profile_data['follower_count']
        if ratio > 2:
            indicators.append('Suspicious following/follower ratio')
    
    if not profile_data['is_verified'] and profile_data['follower_count'] > 10000:
        indicators.append('High follower count without verification')
        
    if profile_data['is_private']:
        indicators.append('Private account')
        
    return indicators

def generate_pdf_report(scan):
    """Generate PDF report for a scan"""
    filename = f'scan_report_{scan.id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
    c = canvas.Canvas(filename, pagesize=letter)
    
    # Add header
    c.setFont('Helvetica-Bold', 16)
    c.drawString(50, 750, 'SocialGuard Scan Report')
    
    # Add scan details
    c.setFont('Helvetica', 12)
    c.drawString(50, 700, f'Scan ID: {scan.id}')
    c.drawString(50, 680, f'Profile: {scan.username}')
    c.drawString(50, 660, f'Scan Date: {scan.scan_date}')
    c.drawString(50, 640, f'Risk Score: {scan.risk_score}%')
    
    # Add risk indicators
    y = 600
    c.setFont('Helvetica-Bold', 12)
    c.drawString(50, y, 'Risk Indicators:')
    c.setFont('Helvetica', 12)
    for indicator in scan.indicators:
        y -= 20
        c.drawString(70, y, f'• {indicator}')
    
    c.save()
    return filename

def compare_profile_metrics(profile_ids):
    """Compare metrics between multiple profiles"""
    profiles = ProfileScan.objects.filter(id__in=profile_ids)
    comparison = {
        'risk_scores': [],
        'follower_counts': [],
        'following_counts': [],
        'common_indicators': set(),
        'unique_indicators': {}
    }
    
    for profile in profiles:
        comparison['risk_scores'].append({
            'profile': profile.username,
            'score': profile.risk_score
        })
        
        # Add indicators
        if not comparison['common_indicators']:
            comparison['common_indicators'].update(profile.indicators)
        else:
            comparison['common_indicators'].intersection_update(profile.indicators)
            
        comparison['unique_indicators'][profile.username] = [
            ind for ind in profile.indicators
            if ind not in comparison['common_indicators']
        ]
    
    return comparison