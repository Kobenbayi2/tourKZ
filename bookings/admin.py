
from django.contrib import admin
from django.utils.html import format_html
from .models import City, TourCategory, Tour, TourDate, RoutePoint, UserProfile, Booking, Review, BackupLog, SystemMetric


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ['name', 'country', 'tours_count']
    search_fields = ['name', 'country']
    list_filter = ['country']
    
    def tours_count(self, obj):
        return obj.tours.count()
    tours_count.short_description = 'Количество туров'


@admin.register(TourCategory)
class TourCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'tours_count']
    search_fields = ['name']
    
    def tours_count(self, obj):
        return obj.tours.count()
    tours_count.short_description = 'Количество туров'


class RoutePointInline(admin.TabularInline):
    model = RoutePoint
    extra = 1
    ordering = ['order']


class TourDateInline(admin.TabularInline):
    model = TourDate
    extra = 1
    ordering = ['start_date']


@admin.register(Tour)
class TourAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'destination_city', 'duration_days', 'price', 'difficulty', 'is_active', 'created_at']
    list_filter = ['category', 'destination_city', 'difficulty', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [TourDateInline, RoutePointInline]
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'category', 'destination_city')
        }),
        ('Параметры тура', {
            'fields': ('duration_days', 'price', 'max_participants', 'difficulty')
        }),
        ('Медиа', {
            'fields': ('image',)
        }),
        ('Статус', {
            'fields': ('is_active', 'created_at', 'updated_at')
        }),
    )


@admin.register(TourDate)
class TourDateAdmin(admin.ModelAdmin):
    list_display = ['tour', 'start_date', 'end_date', 'is_available', 'bookings_count']
    list_filter = ['is_available', 'start_date', 'tour__category']
    search_fields = ['tour__name']
    date_hierarchy = 'start_date'
    
    def bookings_count(self, obj):
        return obj.bookings.filter(status__in=['pending', 'confirmed']).count()
    bookings_count.short_description = 'Бронирований'


@admin.register(RoutePoint)
class RoutePointAdmin(admin.ModelAdmin):
    list_display = ['tour', 'order', 'city', 'duration_hours']
    list_filter = ['tour', 'city']
    search_fields = ['tour__name', 'city__name', 'description']
    ordering = ['tour', 'order']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'city', 'date_of_birth', 'created_at']
    list_filter = ['city', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone', 'passport_number']
    readonly_fields = ['created_at']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'tour_name', 'tour_date', 'number_of_people', 'total_price', 'status_badge', 'created_at']
    list_filter = ['status', 'created_at', 'tour_date__tour__category']
    search_fields = ['user__username', 'user__email', 'tour_date__tour__name']
    readonly_fields = ['created_at', 'updated_at', 'total_price']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Информация о бронировании', {
            'fields': ('user', 'tour_date', 'number_of_people', 'total_price')
        }),
        ('Статус и примечания', {
            'fields': ('status', 'notes')
        }),
        ('Временные метки', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def tour_name(self, obj):
        return obj.tour_date.tour.name
    tour_name.short_description = 'Тур'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#FFA500',
            'confirmed': '#28A745',
            'cancelled': '#DC3545',
            'completed': '#6C757D',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, '#6C757D'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Статус'


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['booking', 'rating_stars', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['booking__user__username', 'booking__tour_date__tour__name', 'comment']
    readonly_fields = ['created_at']
    
    def rating_stars(self, obj):
        return '⭐' * obj.rating
    rating_stars.short_description = 'Рейтинг'


@admin.register(BackupLog)
class BackupLogAdmin(admin.ModelAdmin):
    list_display = ['backup_type', 'status_badge', 'file_size_mb', 'started_at', 'duration']
    list_filter = ['backup_type', 'status', 'started_at']
    search_fields = ['file_path', 'error_message']
    readonly_fields = ['started_at', 'completed_at', 'file_size']
    date_hierarchy = 'started_at'
    
    def status_badge(self, obj):
        colors = {
            'in_progress': '#007BFF',
            'completed': '#28A745',
            'failed': '#DC3545',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, '#6C757D'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Статус'
    
    def file_size_mb(self, obj):
        return f"{obj.file_size / (1024 * 1024):.2f} МБ"
    file_size_mb.short_description = 'Размер'
    
    def duration(self, obj):
        if obj.completed_at:
            delta = obj.completed_at - obj.started_at
            return f"{delta.total_seconds():.1f} сек"
        return "В процессе"
    duration.short_description = 'Длительность'


@admin.register(SystemMetric)
class SystemMetricAdmin(admin.ModelAdmin):
    list_display = ['metric_name', 'metric_value', 'timestamp']
    list_filter = ['metric_name', 'timestamp']
    search_fields = ['metric_name']
    date_hierarchy = 'timestamp'
    readonly_fields = ['timestamp']

