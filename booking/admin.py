
from django.contrib import admin
from django.utils.html import format_html
from .models import Client, Route, Tour, Booking, Review, BackupLog


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'phone', 'city', 'created_at']
    list_filter = ['city', 'created_at']
    search_fields = ['full_name', 'email', 'phone', 'iin']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'full_name', 'email', 'phone')
        }),
        ('Документы', {
            'fields': ('iin', 'passport_number', 'date_of_birth')
        }),
        ('Адрес', {
            'fields': ('address', 'city')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_location', 'end_location', 'total_distance', 'difficulty_level', 'created_at']
    list_filter = ['difficulty_level', 'created_at']
    search_fields = ['name', 'start_location', 'end_location']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Tour)
class TourAdmin(admin.ModelAdmin):
    list_display = ['name', 'tour_type', 'price_display', 'duration_days', 'available', 'rating', 'created_at']
    list_filter = ['tour_type', 'available', 'season', 'created_at']
    search_fields = ['name', 'description', 'route__name']
    readonly_fields = ['created_at', 'updated_at', 'available_spots']
    list_editable = ['available']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'route', 'tour_type', 'season')
        }),
        ('Ценообразование', {
            'fields': ('price', 'duration_days')
        }),
        ('Участники', {
            'fields': ('min_participants', 'max_participants', 'available_spots')
        }),
        ('Услуги', {
            'fields': ('included_services', 'excluded_services', 'accommodation_type', 'meals_included')
        }),
        ('Медиа и рейтинг', {
            'fields': ('image', 'rating', 'available')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def price_display(self, obj):
        return f"{obj.price:,.0f} ₸"
    price_display.short_description = 'Цена'


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = [
        'booking_number', 'client_name', 'tour_name', 'start_date', 
        'status_badge', 'total_price_display', 'created_at'
    ]
    list_filter = ['status', 'payment_method', 'created_at', 'start_date']
    search_fields = ['booking_number', 'client__full_name', 'tour__name']
    readonly_fields = ['booking_number', 'created_at', 'updated_at']
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Информация о бронировании', {
            'fields': ('booking_number', 'tour', 'client', 'status')
        }),
        ('Даты', {
            'fields': ('start_date', 'end_date', 'number_of_participants')
        }),
        ('Оплата', {
            'fields': ('total_price', 'payment_method', 'payment_date')
        }),
        ('Дополнительно', {
            'fields': ('special_requests',)
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def client_name(self, obj):
        return obj.client.full_name
    client_name.short_description = 'Клиент'

    def tour_name(self, obj):
        return obj.tour.name
    tour_name.short_description = 'Тур'

    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'confirmed': '#17a2b8',
            'paid': '#28a745',
            'completed': '#6c757d',
            'cancelled': '#dc3545'
        }
        color = colors.get(obj.status, '#000')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Статус'

    def total_price_display(self, obj):
        return f"{obj.total_price:,.0f} ₸"
    total_price_display.short_description = 'Сумма'


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['tour', 'client', 'rating_stars', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['tour__name', 'client__full_name', 'comment']
    readonly_fields = ['created_at']

    def rating_stars(self, obj):
        return '⭐' * obj.rating
    rating_stars.short_description = 'Оценка'


@admin.register(BackupLog)
class BackupLogAdmin(admin.ModelAdmin):
    list_display = ['backup_date', 'status_badge', 'backup_size_display', 'backup_file']
    list_filter = ['status', 'backup_date']
    readonly_fields = ['backup_date', 'backup_file', 'backup_size', 'status', 'error_message']
    
    def has_add_permission(self, request):
        return False

    def status_badge(self, obj):
        color = '#28a745' if obj.status == 'success' else '#dc3545'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Статус'

    def backup_size_display(self, obj):
        size_mb = obj.backup_size / (1024 * 1024)
        return f"{size_mb:.2f} МБ"
    backup_size_display.short_description = 'Размер'

