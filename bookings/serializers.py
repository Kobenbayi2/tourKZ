from rest_framework import serializers
from django.contrib.auth.models import User
from .models import City, TourCategory, Tour, TourDate, RoutePoint, UserProfile, Booking, Review


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ['id', 'name', 'country', 'description']


class TourCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TourCategory
        fields = ['id', 'name', 'description']


class RoutePointSerializer(serializers.ModelSerializer):
    city = CitySerializer(read_only=True)
    city_id = serializers.PrimaryKeyRelatedField(
        queryset=City.objects.all(),
        source='city',
        write_only=True
    )
    
    class Meta:
        model = RoutePoint
        fields = ['id', 'order', 'city', 'city_id', 'description', 'duration_hours']


class TourDateSerializer(serializers.ModelSerializer):
    available_spots = serializers.SerializerMethodField()
    
    class Meta:
        model = TourDate
        fields = ['id', 'start_date', 'end_date', 'is_available', 'available_spots']
    
    def get_available_spots(self, obj):
        from django.db.models import Sum
        booked = Booking.objects.filter(
            tour_date=obj,
            status__in=['pending', 'confirmed']
        ).aggregate(total=Sum('number_of_people'))['total'] or 0
        return obj.tour.max_participants - booked


class TourListSerializer(serializers.ModelSerializer):
    category = TourCategorySerializer(read_only=True)
    destination_city = CitySerializer(read_only=True)
    
    class Meta:
        model = Tour
        fields = ['id', 'name', 'category', 'destination_city', 'duration_days', 
                  'price', 'difficulty', 'image', 'is_active']


class TourDetailSerializer(serializers.ModelSerializer):
    category = TourCategorySerializer(read_only=True)
    destination_city = CitySerializer(read_only=True)
    route_points = RoutePointSerializer(many=True, read_only=True)
    tour_dates = TourDateSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()
    reviews_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Tour
        fields = ['id', 'name', 'description', 'category', 'destination_city', 
                  'duration_days', 'price', 'max_participants', 'difficulty', 
                  'image', 'is_active', 'route_points', 'tour_dates', 
                  'average_rating', 'reviews_count', 'created_at', 'updated_at']
    
    def get_average_rating(self, obj):
        from django.db.models import Avg
        bookings = Booking.objects.filter(tour_date__tour=obj)
        avg = Review.objects.filter(booking__in=bookings).aggregate(avg=Avg('rating'))['avg']
        return round(avg, 1) if avg else None
    
    def get_reviews_count(self, obj):
        bookings = Booking.objects.filter(tour_date__tour=obj)
        return Review.objects.filter(booking__in=bookings).count()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    city = CitySerializer(read_only=True)
    city_id = serializers.PrimaryKeyRelatedField(
        queryset=City.objects.all(),
        source='city',
        write_only=True,
        required=False
    )
    
    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'phone', 'city', 'city_id', 'date_of_birth', 
                  'passport_number', 'created_at']
        read_only_fields = ['created_at']


class BookingSerializer(serializers.ModelSerializer):
    tour_date_detail = TourDateSerializer(source='tour_date', read_only=True)
    tour_detail = TourListSerializer(source='tour_date.tour', read_only=True)
    user_detail = UserSerializer(source='user', read_only=True)
    
    class Meta:
        model = Booking
        fields = ['id', 'user', 'user_detail', 'tour_date', 'tour_date_detail', 
                  'tour_detail', 'number_of_people', 'total_price', 'status', 
                  'notes', 'created_at', 'updated_at']
        read_only_fields = ['total_price', 'created_at', 'updated_at']
    
    def validate(self, data):
        tour_date = data.get('tour_date')
        number_of_people = data.get('number_of_people')
        
        if tour_date and number_of_people:
            from django.db.models import Sum
            booked = Booking.objects.filter(
                tour_date=tour_date,
                status__in=['pending', 'confirmed']
            ).aggregate(total=Sum('number_of_people'))['total'] or 0
            
            available = tour_date.tour.max_participants - booked
            
            if self.instance:
                available += self.instance.number_of_people
            
            if number_of_people > available:
                raise serializers.ValidationError(
                    f'Недостаточно мест. Доступно: {available}'
                )
        
        return data


class ReviewSerializer(serializers.ModelSerializer):
    booking_detail = BookingSerializer(source='booking', read_only=True)
    
    class Meta:
        model = Review
        fields = ['id', 'booking', 'booking_detail', 'rating', 'comment', 'created_at']
        read_only_fields = ['created_at']
    
    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError('Рейтинг должен быть от 1 до 5')
        return value

