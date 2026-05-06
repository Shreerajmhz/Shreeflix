from django.shortcuts import get_object_or_404, render,redirect
from django.urls import reverse_lazy
from django.views import View
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login as auth_login,logout
from django.contrib.auth import views as auth_views
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from .models import Profile,Movie
from .forms import ProfileForm
from django.contrib.auth.decorators import login_required

class index(View):
    def get(self, request):
        trending_movies = Movie.objects.all()[:10]
        return render(request, 'core/index.html', {
            'show_signin': True,
            'trending_movies': trending_movies
        })

    def post(self, request):
        email = request.POST.get('email', '').strip()

        if not email:
            messages.error(request, "Please enter your email")
            return redirect('index')

        if User.objects.filter(username=email).exists():
            messages.error(request, "Email already exists. Login instead")
            return redirect('index')

        # New user → send them to signup page with email in GET
        return redirect(f'/signup/?email={email}')
        

def signup(request):
    email = request.GET.get('email', '').strip()  # Get email from url

    if request.method == "POST":
        password = request.POST.get('password', '').strip()

        if not password:
            messages.error(request, "Password is required")
            return redirect(f'/signup/?email={email}')

        user = User.objects.create_user(username=email, email=email, password=password)
        user.save()
        auth_login(request, user)  # Auto-login after signup
        return redirect('plans')

    return render(request, 'core/signup.html', {'email': email})


def signin(request):
    if request.method=="POST":
        email=request.POST.get('email','').strip()
        password=request.POST.get('password','').strip()

        if not email or not password:
            messages.error(request,"Both email and password are required")
            return redirect('login')
        
        user = authenticate(request,username=email,password=password)

        if user is not None:
            auth_login(request,user)
            return redirect('profiles')
        else:
            messages.error(request,"Invalid email or password")
            return redirect('login')
    return render(request,'core/signin.html')

@login_required  
def profiles_view(request):
    profiles = request.user.profiles.all()
    if not profiles.exists():
        return redirect('create_profile')  # Send them to create one

    return render(request,'core/profiles.html',{
        'profiles':profiles,
    })

@login_required
def create_profile(request):
    user_profiles_count = request.user.profiles.count()
    profile_limit = 5
    
    if user_profiles_count >= profile_limit:
        messages.error(request, f"You can only create a maximum of {profile_limit} profiles")
        return redirect('manage_profiles')
    
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES)
        if form.is_valid():
            profile= form.save(commit=False)
            profile.user = request.user
            profile.save()
            request.session['profile_id'] = profile.id
            return redirect('profiles')
    else:
        form = ProfileForm()
    
    return render(request, 'core/create_profile.html', {
        'form': form,
        'profile_count': user_profiles_count,
        'profile_limit': profile_limit
    })

@login_required
def select_profile(request, profile_id):
    profile = get_object_or_404(Profile, id=profile_id, user=request.user)
    request.session['profile_id'] = profile.id 
    if not request.session.get('profile_id'): # store for homepage
        return redirect('profiles')
    return redirect('home')  # now homepage knows which profile is active

@login_required   
def manage_profiles(request):
    """Display all profiles for management"""
    profiles = Profile.objects.filter(user=request.user)
    return render(request, 'core/manage_profiles.html', {'profiles': profiles})

@login_required
def manage_edit_profile(request, profile_id):
    """Edit a specific profile from manage profiles page"""
    profile = get_object_or_404(Profile, id=profile_id, user=request.user)

    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('manage_profiles')
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'core/manage_edit_profile.html', {
        'form': form,
        'profile': profile
    })

@login_required
def delete_profile(request, profile_id):
    profile = get_object_or_404(Profile, id=profile_id, user=request.user)

    if request.method == "POST":
        profile.delete()
        return redirect('profiles')

    return redirect('profiles')


@login_required
def home(request):    # Check if user has an active subscription
    try:
        subscription = request.user.subscription
        if not subscription.is_valid():
            messages.error(request, "Your subscription has expired. Please renew your subscription.")
            return redirect('plans')
    except:
        # User doesn't have any subscription
        messages.error(request, "Please choose a subscription plan to access the content.")
        return redirect('plans')
    profile_id = request.session.get('profile_id')

    if not profile_id:
        return redirect('profiles')  # Who’s watching?

    profile = get_object_or_404(Profile, id=profile_id, user=request.user)

    movies = Movie.objects.all()
    user_profiles = request.user.profiles.all()

    return render(request, 'core/home.html', {
        'movies': movies,
        'profile': profile,
        'user_profiles': user_profiles,
        'active_category': 'all',
        'categories': Movie.CATEGORY_CHOICES,
    })


@login_required
def player(request, movie_id):
    # Check if user has an active subscription
    try:
        subscription = request.user.subscription
        if not subscription.is_valid():
            messages.error(request, "Your subscription has expired. Please renew your subscription.")
            return redirect('plans')
    except:
        # User doesn't have any subscription
        messages.error(request, "Please choose a subscription plan to access the content.")
        return redirect('plans')
    
    # Get the profile from session
    profile_id = request.session.get('profile_id')
    profile = None
    if profile_id:
        profile = get_object_or_404(Profile, id=profile_id, user=request.user)

    # Get the main movie
    movie = get_object_or_404(Movie, id=movie_id)

    # Get the category from query params (default to movie's category)
    category = request.GET.get('category', movie.category)

    movies = Movie.objects.filter(category=category).exclude(id=movie.id)

    # Get all user profiles
    user_profiles = request.user.profiles.all()

    return render(request, 'core/player.html', {
        'movie': movie,
        'movies': movies,
        'profile': profile,
        'user_profiles': user_profiles,
        'categories': Movie.CATEGORY_CHOICES,
    })


def login_view(request):
    return render(request,"accounts/login.html")

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

class CustomPasswordChangeView(SuccessMessageMixin,auth_views.PasswordChangeView):
    success_message = "Your password was changed successfully."

def movies_by_category(request, category):
    # Check if user has an active subscription
    try:
        subscription = request.user.subscription
        if not subscription.is_valid():
            messages.error(request, "Your subscription has expired. Please renew your subscription.")
            return redirect('plans')
    except:
        # User doesn't have any subscription
        messages.error(request, "Please choose a subscription plan to access the content.")
        return redirect('plans')
    
    # Get profile from session
    profile_id = request.session.get('profile_id')
    profile = None
    if profile_id:
        profile = get_object_or_404(Profile, id=profile_id, user=request.user)

    movies = Movie.objects.filter(category=category)
    return render(request, 'core/home.html', {
        'movies': movies, 
        'user_profiles': request.user.profiles.all(),
        'active_category': category,
        'profile': profile
    })
