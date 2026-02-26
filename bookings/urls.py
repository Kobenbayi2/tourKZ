from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'cities', views.CityViewSet)
router.register(r'categories', views.TourCategoryViewSet)
router.register(r'tours', views.TourViewSet)
router.register(r'bookings', views.BookingViewSet, basename='booking')
router.register(r'reviews', views.ReviewViewSet, basename='review')
router.register(r'profiles', views.UserProfileViewSet, basename='profile')

urlpatterns = [
    path('', views.index, name='index'),
    path('tour/<int:pk>/', views.tour_detail, name='tour_detail'),
    path('booking/create/<int:tour_date_id>/', views.create_booking, name='create_booking'),
    path('booking/<int:pk>/', views.booking_detail, name='booking_detail'),
    path('booking/<int:pk>/cancel/', views.cancel_booking, name='cancel_booking'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('review/create/<int:booking_id>/', views.create_review, name='create_review'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('api/', include(router.urls)),
]

