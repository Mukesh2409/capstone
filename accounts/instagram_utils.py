import requests
import random
from django.conf import settings
from django.utils import timezone
from .models import InstagramProfile

def fetch_instagram_data(username):
    """Mock function - replace with real API calls"""
    # This would be replaced with actual Instagram API calls
    return {
        'is_verified': username.lower().endswith(('official', 'real')),
        'follower_count': len(username) * 1000,
        'following_count': len(username) * 200,
        'is_private': False,
        'post_count': len(username) * 50
    }

def connect_instagram_profile(user, username):
    ig_data = fetch_instagram_data(username)
    
    profile, created = InstagramProfile.objects.update_or_create(
        user=user,
        defaults={
            'username': username,
            'is_verified': ig_data['is_verified'],
            'follower_count': ig_data['follower_count'],
            'following_count': ig_data['following_count'],
            'last_synced': timezone.now()
        }
    )
    
    # Update user's social media status
    user.social_media_linked = True
    user.save()
    
    return profile

def perform_instagram_scan(user):
    if not hasattr(user, 'instagram'):
        return None
        
    ig_profile = user.instagram
    indicators = {}
    
    # Check 1: Follower ratio
    if ig_profile.follower_ratio > 10:  # Following way more than followers
        indicators['high_following_ratio'] = True
    
    # Check 2: Verified status
    if user.is_verified and not ig_profile.is_verified:
        indicators['verification_mismatch'] = True
    
    # Check 3: New account with high followers
    account_age = (timezone.now() - user.date_joined).days
    if account_age < 30 and ig_profile.follower_count > 10000:
        indicators['suspicious_growth'] = True
    
    risk_score = min(100, len(indicators) * 25 + random.uniform(0, 15))
    
    scan = ProfileScan.objects.create(
        user=user,
        scan_type='INSTA',
        risk_score=risk_score,
        indicators=indicators
    )
    
    return scan