from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    profile_pic = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    bio = models.TextField(max_length=300, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

class ProfileScan(models.Model):
    SCAN_RESULTS = (
        ('REAL', 'Real'),
        ('FAKE', 'Fake'),
        ('UNKNOWN', 'Unknown'),
    )
    scanned_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    username = models.CharField(max_length=100)
    bio = models.TextField(blank=True)
    followers_count = models.IntegerField()
    following_count = models.IntegerField()
    is_private = models.BooleanField()
    posts_count = models.IntegerField()
    scan_result = models.CharField(max_length=10, choices=SCAN_RESULTS)
    confidence = models.FloatField()
    algorithm_used = models.CharField(max_length=50)
    scan_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.username} - {self.get_scan_result_display()}"
class InstagramProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='instagram')
    username = models.CharField(max_length=30)
    is_verified = models.BooleanField(default=False)
    follower_count = models.PositiveIntegerField(default=0)
    following_count = models.PositiveIntegerField(default=0)
    last_synced = models.DateTimeField(null=True, blank=True)
    
    @property
    def follower_ratio(self):
        return self.following_count / (self.follower_count or 1)
    
    def __str__(self):
        return f"@{self.username} ({self.user.username})"

    
