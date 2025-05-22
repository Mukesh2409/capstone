# accounts/scan_utils.py
import random
from .models import ProfileScan

def analyze_profile(user):
    """Analyze user profile for fake indicators"""
    indicators = {}
    
    # Profile Completeness Check
    completeness = user.get_profile_completeness()
    if completeness < 70:
        indicators['low_completeness'] = True
    
    # Profile Picture Check
    if not user.profile_pic:
        indicators['no_profile_pic'] = True
    
    # Username Analysis
    if any(char.isdigit() for char in user.username[:3]):
        indicators['numeric_username'] = True
    
    # Instagram Checks (if connected)
    if hasattr(user, 'instagram'):
        if user.instagram.follower_ratio > 10:
            indicators['high_following_ratio'] = True
        if user.is_verified and not user.instagram.is_verified:
            indicators['verification_mismatch'] = True
    
    # Calculate Risk Score (0-100)
    risk_score = min(100, 
        (0.4 * (100 - completeness) + 
         0.3 * len(indicators) * 20 +
         0.3 * random.uniform(0, 20)))  # Small randomness
    
    # Save scan results
    scan = ProfileScan.objects.create(
        user=user,
        scan_type='FULL',
        risk_score=risk_score,
        indicators=indicators
    )
    
    return scan