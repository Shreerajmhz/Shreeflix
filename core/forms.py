from django import forms
from .models import Profile

AVATAR_CHOICES = [
    ('avatar1.png', 'Avatar 1'),
    ('avatar2.jpg', 'Avatar 2'),
    ('avatar3.jpg', 'Avatar 3'),
    ('avatar4.jpg', 'Avatar 4'),
    ('avatar5.jpg', 'Avatar 5'),
]

class ProfileForm(forms.ModelForm):
    avatar = forms.ChoiceField(
        choices=AVATAR_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'avatar-radio'
        })
    )
    
    class Meta:
        model = Profile
        fields = ['name','avatar']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full p-3 rounded-md text-white text-lg border mt-2',
                'placeholder': 'Enter profile name'
            }),
        }
