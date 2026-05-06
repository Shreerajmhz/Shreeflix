from django.urls import path
from . import views     
from core.views import index

urlpatterns = [
    path('',index.as_view(),name='index'),
    path('signup/',views.signup,name='signup'),
    path('login/',views.signin,name='login'),
    path('logout/',views.logout_view,name='logout'),


    path('homepage/',views.home,name='home'),
    path('player/<int:movie_id>/', views.player, name='player'),

    #profile urls
    path('profiles/',views.profiles_view,name='profiles'),
    path('profiles/manage/', views.manage_profiles, name='manage_profiles'),
    path('profiles/select/<int:profile_id>/', views.select_profile, name='select_profile'),
    path('profiles/create/', views.create_profile, name='create_profile'),
    path('profiles/manage/edit/<int:profile_id>/', views.manage_edit_profile, name='manage_edit_profile'),
    path('profiles/delete/<int:profile_id>/', views.delete_profile, name='delete_profile'),
    path('category/<str:category>/', views.movies_by_category, name='movies_by_category'),


]