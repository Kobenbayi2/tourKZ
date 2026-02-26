
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.contrib.auth.models import User
from decimal import Decimal


class Client(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Пользователь")
    full_name = models.CharField(max_length=200, verbose_name="ФИО")
    email = models.EmailField(unique=True, verbose_name="Email")
    phone_validator = RegexValidator(
        regex=r'^\+?7?\d{10}$',
        message="Введите корректный номер телефона Казахстана (например: +77001234567)"
    )
    phone = models.CharField(max_length=20, validators=[phone_validator], verbose_name="Телефон")
    iin = models.CharField(max_length=12, unique=True, verbose_name="ИИН", help_text="Индивидуальный идентификационный номер")
    passport_number = models.CharField(max_length=20, verbose_name="Номер паспорта")
    date_of_birth = models.DateField(verbose_name="Дата рождения")
    address = models.TextField(verbose_name="Адрес")
    city = models.CharField(max_length=100, verbose_name="Город")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата регистрации")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.full_name} ({self.phone})"


class Route(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название маршрута")
    description = models.TextField(verbose_name="Описание")
    start_location = models.CharField(max_length=200, verbose_name="Начальная точка")
    end_location = models.CharField(max_length=200, verbose_name="Конечная точка")
    intermediate_points = models.TextField(verbose_name="Промежуточные точки", help_text="Укажите через точку с запятой")
    total_distance = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Общая дистанция (км)")
    estimated_duration = models.DurationField(verbose_name="Примерная продолжительность")
    difficulty_level = models.CharField(
        max_length=20,
        choices=[
            ('easy', 'Легкий'),
            ('medium', 'Средний'),
            ('hard', 'Сложный'),
            ('extreme', 'Экстремальный')
        ],
        default='medium',
        verbose_name="Уровень сложности"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Маршрут"
        verbose_name_plural = "Маршруты"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.start_location} - {self.end_location})"


class Tour(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название тура")
    description = models.TextField(verbose_name="Описание")
    route = models.ForeignKey(Route, on_delete=models.PROTECT, related_name='tours', verbose_name="Маршрут")
    tour_type = models.CharField(
        max_length=50,
        choices=[
            ('nature', 'Природные достопримечательности'),
            ('cultural', 'Культурный туризм'),
            ('adventure', 'Приключенческий туризм'),
            ('ski', 'Горнолыжный туризм'),
            ('health', 'Оздоровительный туризм'),
            ('business', 'Деловой туризм'),
            ('eco', 'Экотуризм')
        ],
        default='nature',
        verbose_name="Тип тура"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Цена (₸)",
        help_text="Цена указывается в тенге"
    )
    duration_days = models.PositiveIntegerField(verbose_name="Длительность (дней)")
    max_participants = models.PositiveIntegerField(verbose_name="Макс. количество участников")
    min_participants = models.PositiveIntegerField(verbose_name="Мин. количество участников")
    included_services = models.TextField(verbose_name="Включенные услуги", help_text="Укажите через точку с запятой")
    excluded_services = models.TextField(verbose_name="Не включенные услуги", help_text="Укажите через точку с запятой", blank=True)
    accommodation_type = models.CharField(max_length=100, verbose_name="Тип размещения")
    meals_included = models.CharField(
        max_length=50,
        choices=[
            ('none', 'Без питания'),
            ('breakfast', 'Завтрак'),
            ('half_board', 'Полупансион'),
            ('full_board', 'Полный пансион'),
            ('all_inclusive', 'Все включено')
        ],
        default='breakfast',
        verbose_name="Питание"
    )
    available = models.BooleanField(default=True, verbose_name="Доступен для бронирования")
    season = models.CharField(
        max_length=20,
        choices=[
            ('year_round', 'Круглогодично'),
            ('summer', 'Летний сезон'),
            ('winter', 'Зимний сезон'),
            ('spring', 'Весенний сезон'),
            ('autumn', 'Осенний сезон')
        ],
        default='year_round',
        verbose_name="Сезон"
    )
    image = models.ImageField(upload_to='tours/', null=True, blank=True, verbose_name="Изображение")
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        default=0,
        verbose_name="Рейтинг"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Тур"
        verbose_name_plural = "Туры"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.duration_days} дней ({self.price} ₸)"

    @property
    def available_spots(self):
        confirmed_bookings = self.bookings.filter(status='confirmed').count()
        return self.max_participants - confirmed_bookings


class Booking(models.Model):
    tour = models.ForeignKey(Tour, on_delete=models.PROTECT, related_name='bookings', verbose_name="Тур")
    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name='bookings', verbose_name="Клиент")
    booking_number = models.CharField(max_length=20, unique=True, verbose_name="Номер бронирования")
    start_date = models.DateField(verbose_name="Дата начала тура")
    end_date = models.DateField(verbose_name="Дата окончания тура")
    number_of_participants = models.PositiveIntegerField(verbose_name="Количество участников")
    total_price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Общая стоимость (₸)")
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Ожидает подтверждения'),
            ('confirmed', 'Подтверждено'),
            ('paid', 'Оплачено'),
            ('completed', 'Завершено'),
            ('cancelled', 'Отменено')
        ],
        default='pending',
        verbose_name="Статус"
    )
    payment_method = models.CharField(
        max_length=50,
        choices=[
            ('cash', 'Наличные'),
            ('card', 'Банковская карта'),
            ('kaspi', 'Kaspi Pay'),
            ('halyk', 'Halyk Bank'),
            ('transfer', 'Банковский перевод')
        ],
        null=True,
        blank=True,
        verbose_name="Способ оплаты"
    )
    payment_date = models.DateTimeField(null=True, blank=True, verbose_name="Дата оплаты")
    special_requests = models.TextField(blank=True, verbose_name="Особые пожелания")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Бронирование"
        verbose_name_plural = "Бронирования"
        ordering = ['-created_at']

    def __str__(self):
        return f"Бронирование #{self.booking_number} - {self.client.full_name}"

    def save(self, *args, **kwargs):
        if not self.booking_number:
            import random
            import string
            self.booking_number = 'BK' + ''.join(random.choices(string.digits, k=8))
        super().save(*args, **kwargs)


class Review(models.Model):
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name='reviews', verbose_name="Тур")
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='reviews', verbose_name="Клиент")
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='review', verbose_name="Бронирование")
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Оценка"
    )
    comment = models.TextField(verbose_name="Комментарий")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        ordering = ['-created_at']

    def __str__(self):
        return f"Отзыв от {self.client.full_name} на {self.tour.name}"


class BackupLog(models.Model):
    backup_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата резервного копирования")
    backup_file = models.CharField(max_length=500, verbose_name="Файл резервной копии")
    backup_size = models.BigIntegerField(verbose_name="Размер (байты)")
    status = models.CharField(
        max_length=20,
        choices=[
            ('success', 'Успешно'),
            ('failed', 'Ошибка')
        ],
        verbose_name="Статус"
    )
    error_message = models.TextField(blank=True, verbose_name="Сообщение об ошибке")

    class Meta:
        verbose_name = "Журнал резервного копирования"
        verbose_name_plural = "Журналы резервного копирования"
        ordering = ['-backup_date']

    def __str__(self):
        return f"Резервная копия от {self.backup_date.strftime('%Y-%m-%d %H:%M')}"

