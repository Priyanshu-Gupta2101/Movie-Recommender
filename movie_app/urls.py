from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name = "start"),
    path('login', views.login, name = 'login'),
    path('googlelogin', views.google_login, name = 'google-login'),
    path('callback', views.google_callback, name = 'google-callback'),
    path('logout', views.logout, name = 'logout'),
    path('signup', views.signUp, name = 'signup'),
    path('datas/', views.show_pop_data, name='popular movies'),
    path('datas/home', views.home, name='home'),
    path('data/', views.show_pop_series, name='popular series'),
    path('data/home', views.home, name='home'),
    path('data/logout', views.logout, name='logout'),
    path('datas/logout', views.logout, name='logout'),
    path('search/', views.show, name='search_results'),
    path('search/data/', views.data, name='data_fetch'),
    path('search/logout', views.logout, name='logout'),
    path('home',views.home, name='home'),
]
