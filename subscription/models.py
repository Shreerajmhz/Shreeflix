from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta
from django.utils import timezone

class SubscriptionPlan(models.Model):
    # Basic info
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=8, decimal_places=2)  # USD
    duration_days = models.PositiveIntegerField(default=30)  # 30 days = monthly

    # Media details
    video_sound_quality = models.CharField(max_length=100, default="Unknown")  # e.g., Fair, Good, Great, Best
    resolution = models.CharField(max_length=100, default="Unknown")           # e.g., 480p, 720p, 1080p, 4k+HDR

    # Device info
    supported_devices = models.CharField(max_length=255, default="Unknown")    # e.g., TV, Computer, Mobile, Tablet
    simultaneous_streams = models.PositiveIntegerField(default=1)
    download_devices = models.PositiveIntegerField(default=1)

    # Stripe integration
    stripe_price_id = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f"{self.name} - ${self.price}"


class UserSubscription(models.Model):
    """Track user subscription status and expiry"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="subscription")
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True, blank=True)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    stripe_session_id = models.CharField(max_length=500, blank=True, null=True)

    def __str__(self):
        return f"{self.user.email} - {self.plan.name if self.plan else 'No Plan'}"

    def is_valid(self):
        """Check if subscription is still active and not expired"""
        return self.is_active and self.end_date > timezone.now()
