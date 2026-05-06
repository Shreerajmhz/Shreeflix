from django.db import models
from django.contrib.auth.models import User

AVATAR_CHOICES = [
    ('avatar1.png', 'Avatar 1'),
    ('avatar2.jpg', 'Avatar 2'),
    ('avatar3.jpg', 'Avatar 3'),
    ('avatar4.jpg', 'Avatar 4'),
    ('avatar5.jpg', 'Avatar 5'),
]


class Profile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name="profiles")
    name = models.CharField(max_length=50)
    avatar = models.CharField(max_length=50, choices=AVATAR_CHOICES, default="avatar1.png")
    def __str__(self):
        return f"{self.name} ({self.user.email})"
    
class Movie(models.Model):
    CATEGORY_CHOICES = [
    ('random', 'random'),
    ('vlog', 'vlog'),
    ('cultural', 'cultural'),
    ('family', 'family'),
]
    title=models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='random')
    video_id = models.CharField(max_length=500,default="",blank=True)
    release_date=models.DateField()
    poster = models.ImageField(upload_to='posters/')
    created_at= models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title