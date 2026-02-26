
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class City(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='Название города')
    country = models.CharField(max_length=100, default='Казахстан', verbose_name='Страна')
    description = models.TextField(blank=True, verbose_name='Описание')
    
    class Meta:
        verbose_name = 'Город'
        verbose_name_plural = 'Города'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name}, {self.country}"


class TourCategory(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='Название категории')
    description = models.TextField(blank=True, verbose_name='Описание')
    
    class Meta:
        verbose_name = 'Категория тура'
        verbose_name_plural = 'Категории туров'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Tour(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Легкий'),
        ('medium', 'Средний'),
        ('hard', 'Сложный'),
    ]
    
    name = models.CharField(max_length=200, verbose_name='Название тура')
    description = models.TextField(verbose_name='Описание')
    category = models.ForeignKey(TourCategory, on_delete=models.PROTECT, related_name='tours', verbose_name='Категория')
    destination_city = models.ForeignKey(City, on_delete=models.PROTECT, related_name='tours', verbose_name='Город назначения')
    duration_days = models.PositiveIntegerField(validators=[MinValueValidator(1)], verbose_name='Длительность (дней)')
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], verbose_name='Цена (тенге)')
    max_participants = models.PositiveIntegerField(validators=[MinValueValidator(1)], verbose_name='Макс. участников')
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='medium', verbose_name='Сложность')
    image = models.ImageField(upload_to='tours/', blank=True, null=True, verbose_name='Изображение')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создан')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлен')
    
    class Meta:
        verbose_name = 'Тур'
        verbose_name_plural = 'Туры'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['destination_city', 'is_active']),
            models.Index(fields=['category', 'is_active']),
        ]
    
    def __str__(self):
        return self.name
    
    def get_available_spots(self, tour_date_id):
        try:
            tour_date = self.tour_dates.get(id=tour_date_id)
            booked = Booking.objects.filter(
                tour_date=tour_date,
                status__in=['pending', 'confirmed']
            ).aggregate(total=models.Sum('number_of_people'))['total'] or 0
            return self.max_participants - booked
        except TourDate.DoesNotExist:
            return 0


class TourDate(models.Model):
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name='tour_dates', verbose_name='Тур')
    start_date = models.DateField(verbose_name='Дата начала')
    end_date = models.DateField(verbose_name='Дата окончания')
    is_available = models.BooleanField(default=True, verbose_name='Доступна')
    
    class Meta:
        verbose_name = 'Дата тура'
        verbose_name_plural = 'Даты туров'
        ordering = ['start_date']
        unique_together = ['tour', 'start_date']
    
    def __str__(self):
        return f"{self.tour.name} - {self.start_date.strftime('%d.%m.%Y')}"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError('Дата окончания не может быть раньше даты начала')


class RoutePoint(models.Model):
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name='route_points', verbose_name='Тур')
    order = models.PositiveIntegerField(verbose_name='Порядок')
    city = models.ForeignKey(City, on_delete=models.PROTECT, verbose_name='Город')
    description = models.TextField(verbose_name='Описание точки маршрута')
    duration_hours = models.PositiveIntegerField(default=0, verbose_name='Длительность (часов)')
    
    class Meta:
        verbose_name = 'Точка маршрута'
        verbose_name_plural = 'Точки маршрута'
        ordering = ['tour', 'order']
        unique_together = ['tour', 'order']
    
    def __str__(self):
        return f"{self.tour.name} - {self.order}. {self.city.name}"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name='Пользователь')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон')
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Город')
    date_of_birth = models.DateField(null=True, blank=True, verbose_name='Дата рождения')
    passport_number = models.CharField(max_length=20, blank=True, verbose_name='Номер паспорта')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создан')
    
    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'
    
    def __str__(self):
        return f"Профиль {self.user.username}"


class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'В ожидании'),
        ('confirmed', 'Подтверждено'),
        ('cancelled', 'Отменено'),
        ('completed', 'Завершено'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings', verbose_name='Пользователь')
    tour_date = models.ForeignKey(TourDate, on_delete=models.PROTECT, related_name='bookings', verbose_name='Дата тура')
    number_of_people = models.PositiveIntegerField(validators=[MinValueValidator(1)], verbose_name='Количество человек')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Общая стоимость')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Статус')
    notes = models.TextField(blank=True, verbose_name='Примечания')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')
    
    class Meta:
        verbose_name = 'Бронирование'
        verbose_name_plural = 'Бронирования'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['tour_date', 'status']),
        ]
    
    def __str__(self):
        return f"Бронирование #{self.id} - {self.user.username}"
    
    def save(self, *args, **kwargs):
        if not self.total_price:
            self.total_price = self.tour_date.tour.price * self.number_of_people
        
        if self.pk:
            old_booking = Booking.objects.get(pk=self.pk)
            if old_booking.status != self.status:
                logger.info(f"Booking {self.id} status changed from {old_booking.status} to {self.status}")
        
        super().save(*args, **kwargs)


class Review(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='review', verbose_name='Бронирование')
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name='Оценка')
    comment = models.TextField(verbose_name='Комментарий')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создан')
    
    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Отзыв на {self.booking.tour_date.tour.name} - {self.rating}/5"


class BackupLog(models.Model):
    BACKUP_TYPE_CHOICES = [
        ('full', 'Полное'),
        ('incremental', 'Инкрементное'),
        ('differential', 'Дифференциальное'),
    ]
    
    STATUS_CHOICES = [
        ('in_progress', 'В процессе'),
        ('completed', 'Завершено'),
        ('failed', 'Ошибка'),
    ]
    
    backup_type = models.CharField(max_length=20, choices=BACKUP_TYPE_CHOICES, verbose_name='Тип резервной копии')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress', verbose_name='Статус')
    file_path = models.CharField(max_length=500, verbose_name='Путь к файлу')
    file_size = models.BigIntegerField(default=0, verbose_name='Размер файла (байт)')
    started_at = models.DateTimeField(auto_now_add=True, verbose_name='Начало')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Завершение')
    error_message = models.TextField(blank=True, verbose_name='Сообщение об ошибке')
    
    class Meta:
        verbose_name = 'Лог резервной копии'
        verbose_name_plural = 'Логи резервных копий'
        ordering = ['-started_at']
    
    def __str__(self):
        return f"Backup {self.backup_type} - {self.started_at.strftime('%d.%m.%Y %H:%M')}"


class SystemMetric(models.Model):
    metric_name = models.CharField(max_length=100, verbose_name='Название метрики')
    metric_value = models.FloatField(verbose_name='Значение')
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='Время')
    
    class Meta:
        verbose_name = 'Системная метрика'
        verbose_name_plural = 'Системные метрики'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['metric_name', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.metric_name}: {self.metric_value}"

