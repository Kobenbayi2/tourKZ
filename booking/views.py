<<<<<<< Current (Your changes)
=======
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.db.models import Q, Avg
from django.core.paginator import Paginator
from .models import Tour, Booking, Client, Route, Review
from .forms import BookingForm, ClientRegistrationForm, ReviewForm
from datetime import datetime, timedelta


def home(request):
    tours = Tour.objects.filter(available=True).select_related('route')
    
    search_query = request.GET.get('search', '')
    tour_type = request.GET.get('type', '')
    season = request.GET.get('season', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    sort = request.GET.get('sort', '-created_at')

    if search_query:
        tours = tours.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(route__name__icontains=search_query)
        )

    if tour_type:
        tours = tours.filter(tour_type=tour_type)

    if season:
        tours = tours.filter(season=season)

    if min_price:
        tours = tours.filter(price__gte=min_price)

    if max_price:
        tours = tours.filter(price__lte=max_price)

    tours = tours.order_by(sort)

    paginator = Paginator(tours, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'tour_types': Tour._meta.get_field('tour_type').choices,
        'seasons': Tour._meta.get_field('season').choices,
        'current_filters': {
            'search': search_query,
            'type': tour_type,
            'season': season,
            'min_price': min_price,
            'max_price': max_price,
            'sort': sort,
        }
    }

    return render(request, 'booking/home.html', context)


def tour_detail(request, tour_id):
    tour = get_object_or_404(Tour.objects.select_related('route'), id=tour_id)
    reviews = Review.objects.filter(tour=tour).select_related('client').order_by('-created_at')[:5]
    
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
    if avg_rating:
        tour.rating = round(avg_rating, 2)
        tour.save()

    context = {
        'tour': tour,
        'reviews': reviews,
        'included_services': tour.included_services.split(';'),
        'excluded_services': tour.excluded_services.split(';') if tour.excluded_services else [],
        'intermediate_points': tour.route.intermediate_points.split(';'),
    }

    return render(request, 'booking/tour_detail.html', context)


@login_required
def create_booking(request, tour_id):
    tour = get_object_or_404(Tour, id=tour_id, available=True)
    
    try:
        client = Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        messages.error(request, 'Пожалуйста, заполните профиль клиента.')
        return redirect('client_profile')

    if request.method == 'POST':
        form = BookingForm(request.POST, tour=tour)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.tour = tour
            booking.client = client
            
            duration = form.cleaned_data['duration_days']
            booking.end_date = booking.start_date + timedelta(days=duration)
            booking.total_price = tour.price * booking.number_of_participants
            
            if booking.number_of_participants > tour.available_spots:
                messages.error(request, 'Недостаточно свободных мест.')
                return redirect('tour_detail', tour_id=tour.id)
            
            booking.save()
            messages.success(request, f'Бронирование #{booking.booking_number} успешно создано!')
            return redirect('booking_detail', booking_id=booking.id)
    else:
        form = BookingForm(tour=tour)

    context = {
        'form': form,
        'tour': tour,
    }

    return render(request, 'booking/create_booking.html', context)


@login_required
def booking_detail(request, booking_id):
    booking = get_object_or_404(
        Booking.objects.select_related('tour', 'client'),
        id=booking_id
    )

    if booking.client.user != request.user and not request.user.is_staff:
        messages.error(request, 'У вас нет доступа к этому бронированию.')
        return redirect('home')

    context = {
        'booking': booking,
    }

    return render(request, 'booking/booking_detail.html', context)


@login_required
def my_bookings(request):
    try:
        client = Client.objects.get(user=request.user)
        bookings = Booking.objects.filter(client=client).select_related('tour').order_by('-created_at')
    except Client.DoesNotExist:
        bookings = []

    context = {
        'bookings': bookings,
    }

    return render(request, 'booking/my_bookings.html', context)


@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if booking.client.user != request.user:
        messages.error(request, 'У вас нет доступа к этому бронированию.')
        return redirect('home')

    if booking.status in ['cancelled', 'completed']:
        messages.error(request, 'Это бронирование не может быть отменено.')
        return redirect('booking_detail', booking_id=booking.id)

    if request.method == 'POST':
        booking.status = 'cancelled'
        booking.save()
        messages.success(request, 'Бронирование успешно отменено.')
        return redirect('my_bookings')

    context = {
        'booking': booking,
    }

    return render(request, 'booking/cancel_booking.html', context)


def register(request):
    if request.method == 'POST':
        form = ClientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('home')
    else:
        form = ClientRegistrationForm()

    context = {
        'form': form,
    }

    return render(request, 'booking/register.html', context)


@login_required
def client_profile(request):
    try:
        client = Client.objects.get(user=request.user)
        is_new = False
    except Client.DoesNotExist:
        client = None
        is_new = True

    if request.method == 'POST':
        from .forms import ClientProfileForm
        form = ClientProfileForm(request.POST, instance=client)
        if form.is_valid():
            client = form.save(commit=False)
            client.user = request.user
            client.save()
            messages.success(request, 'Профиль успешно обновлен!')
            return redirect('client_profile')
    else:
        from .forms import ClientProfileForm
        form = ClientProfileForm(instance=client)

    context = {
        'form': form,
        'client': client,
        'is_new': is_new,
    }

    return render(request, 'booking/client_profile.html', context)


@login_required
def add_review(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if booking.client.user != request.user:
        messages.error(request, 'У вас нет доступа к этому бронированию.')
        return redirect('home')

    if booking.status != 'completed':
        messages.error(request, 'Отзыв можно оставить только после завершения тура.')
        return redirect('booking_detail', booking_id=booking.id)

    if hasattr(booking, 'review'):
        messages.error(request, 'Вы уже оставили отзыв на этот тур.')
        return redirect('booking_detail', booking_id=booking.id)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.tour = booking.tour
            review.client = booking.client
            review.booking = booking
            review.save()
            messages.success(request, 'Спасибо за ваш отзыв!')
            return redirect('tour_detail', tour_id=booking.tour.id)
    else:
        form = ReviewForm()

    context = {
        'form': form,
        'booking': booking,
    }

    return render(request, 'booking/add_review.html', context)


def about(request):
    return render(request, 'booking/about.html')


def contacts(request):
    return render(request, 'booking/contacts.html')
>>>>>>> Incoming (Background Agent changes)
