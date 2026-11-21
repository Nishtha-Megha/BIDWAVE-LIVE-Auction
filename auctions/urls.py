from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
urlpatterns = [
 path('',views.home,name='home'),
 path('signup/',views.signup,name='signup'),
 path('login/',auth_views.LoginView.as_view(template_name='registration/login.html'),name='login'),
 path('logout/',auth_views.LogoutView.as_view(),name='logout'),
 path('auctions/new/',views.create_auction,name='create_auction'),
 path('auctions/<int:pk>/',views.auction_detail,name='auction_detail'),
 path('api/auctions/<int:pk>/state/',views.auction_state,name='auction_state'),
 path('api/auctions/<int:pk>/bids/',views.bid_api,name='bid_api'),
]
