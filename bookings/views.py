 
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.db.models import Q, Count, Avg
from django.core.paginator import Paginator
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
import logging

from .models import City, TourCategory, Tour, TourDate, Booking, Review, UserProfile
from .serializers import (
    CitySerializer, TourCategorySerializer, TourListSerializer, 
    TourDetailSerializer, BookingSerializer, ReviewSerializer, UserProfileSerializer
)
from .forms import BookingForm, ReviewForm, UserProfileForm

logger = logging.getLogger(__name__)


class CityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = City.objects.all()
    serializer_class = CitySerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'country']
    ordering_fields = ['name']


class TourCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TourCategory.objects.all()
    serializer_class = TourCategorySerializer
    permission_classes = [permissions.AllowAny]


class TourViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tour.objects.filter(is_active=True).select_related('category', 'destination_city')
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'destination_city', 'difficulty']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'duration_days', 'created_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TourDetailSerializer
        return TourListSerializer
    
    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        tour = self.get_object()
        bookings = Booking.objects.filter(tour_date__tour=tour)
        reviews = Review.objects.filter(booking__in=bookings).select_related('booking__user')
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)


class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Booking.objects.all().select_related('user', 'tour_date__tour')
        return Booking.objects.filter(user=user).select_related('tour_date__tour')
    
    def perform_create(self, serializer):
        booking = serializer.save(user=self.request.user)
        logger.info(f"New booking created: {booking.id} by {self.request.user.username}")
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        booking = self.get_object()
        if booking.status in ['pending', 'confirmed']:
            booking.status = 'cancelled'
            booking.save()
            logger.info(f"Booking {booking.id} cancelled by {request.user.username}")
            return Response({'status': 'cancelled'})
        return Response({'error': 'Невозможно отменить бронирование'}, status=status.HTTP_400_BAD_REQUEST)


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Review.objects.all()
        return Review.objects.filter(booking__user=user)
    
    def perform_create(self, serializer):
        review = serializer.save()
        logger.info(f"New review created for booking {review.booking.id}")


class UserProfileViewSet(viewsets.ModelViewSet):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user)


def index(request):
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    city_filter = request.GET.get('city', '')
    difficulty_filter = request.GET.get('difficulty', '')
    
    tours = Tour.objects.filter(is_active=True).select_related('category', 'destination_city')
    
    if search_query:
        tours = tours.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    if category_filter:
        tours = tours.filter(category_id=category_filter)
    
    if city_filter:
        tours = tours.filter(destination_city_id=city_filter)
    
    if difficulty_filter:
        tours = tours.filter(difficulty=difficulty_filter)
    
    tours = tours.order_by('-created_at')
    
    paginator = Paginator(tours, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = TourCategory.objects.all()
    cities = City.objects.all()
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'cities': cities,
        'search_query': search_query,
        'category_filter': category_filter,
        'city_filter': city_filter,
        'difficulty_filter': difficulty_filter,
    }
    return render(request, 'bookings/index.html', context)


def tour_detail(request, pk):
    tour = get_object_or_404(
        Tour.objects.select_related('category', 'destination_city')
        .prefetch_related('route_points__city', 'tour_dates'),
        pk=pk,
        is_active=True
    )
    
    bookings = Booking.objects.filter(tour_date__tour=tour)
    reviews = Review.objects.filter(booking__in=bookings).select_related('booking__user')
    
    context = {
        'tour': tour,
        'reviews': reviews,
    }
    return render(request, 'bookings/tour_detail.html', context)


@login_required
def create_booking(request, tour_date_id):
    tour_date = get_object_or_404(TourDate, pk=tour_date_id, is_available=True)
    
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.tour_date = tour_date
            
            try:
                booking.save()
                messages.success(request, 'Бронирование успешно создано!')
                logger.info(f"Booking created: {booking.id}")
                return redirect('booking_detail', pk=booking.id)
            except Exception as e:
                messages.error(request, f'Ошибка при создании бронирования: {str(e)}')
                logger.error(f"Booking creation failed: {str(e)}")
    else:
        form = BookingForm()
    
    context = {
        'form': form,
        'tour_date': tour_date,
    }
    return render(request, 'bookings/create_booking.html', context)


@login_required
def booking_detail(request, pk):
    booking = get_object_or_404(
        Booking.objects.select_related('tour_date__tour', 'user'),
        pk=pk
    )
    
    if not request.user.is_staff and booking.user != request.user:
        messages.error(request, 'У вас нет доступа к этому бронированию')
        return redirect('index')
    
    context = {
        'booking': booking,
    }
    return render(request, 'bookings/booking_detail.html', context)


@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user).select_related('tour_date__tour').order_by('-created_at')
    
    status_filter = request.GET.get('status', '')
    if status_filter:
        bookings = bookings.filter(status=status_filter)
    
    paginator = Paginator(bookings, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
    }
    return render(request, 'bookings/my_bookings.html', context)


@login_required
def cancel_booking(request, pk):
    booking = get_object_or_404(Booking, pk=pk, user=request.user)
    
    if booking.status in ['pending', 'confirmed']:
        booking.status = 'cancelled'
        booking.save()
        messages.success(request, 'Бронирование отменено')
        logger.info(f"Booking {booking.id} cancelled")
    else:
        messages.error(request, 'Невозможно отменить это бронирование')
    
    return redirect('booking_detail', pk=pk)


@login_required
def create_review(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
    
    if booking.status != 'completed':
        messages.error(request, 'Вы можете оставить отзыв только после завершения тура')
        return redirect('booking_detail', pk=booking_id)
    
    if hasattr(booking, 'review'):
        messages.info(request, 'Вы уже оставили отзыв на этот тур')
        return redirect('booking_detail', pk=booking_id)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.booking = booking
            review.save()
            messages.success(request, 'Спасибо за ваш отзыв!')
            logger.info(f"Review created for booking {booking.id}")
            return redirect('booking_detail', pk=booking_id)
    else:
        form = ReviewForm()
    
    context = {
        'form': form,
        'booking': booking,
    }
    return render(request, 'bookings/create_review.html', context)


def register(request):
    if request.user.is_authenticated:
        return redirect('index')
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user)
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            logger.info(f"New user registered: {username}")
            return redirect('index')
    else:
        form = UserCreationForm()
    
    return render(request, 'bookings/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('index')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Добро пожаловать, {username}!')
                logger.info(f"User logged in: {username}")
                return redirect('index')
    else:
        form = AuthenticationForm()
    
    return render(request, 'bookings/login.html', {'form': form})


@login_required
def logout_view(request):
    username = request.user.username
    logout(request)
    messages.info(request, 'Вы вышли из системы')
    logger.info(f"User logged out: {username}")
    return redirect('index')


@login_required
def profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль обновлен!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=profile)
    
    context = {
        'form': form,
        'profile': profile,
    }
    return render(request, 'bookings/profile.html', context)

