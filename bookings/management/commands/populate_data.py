from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from bookings.models import City, TourCategory, Tour, TourDate, RoutePoint, UserProfile
from datetime import datetime, timedelta
from decimal import Decimal


class Command(BaseCommand):
    help = 'Заполнение базы данных тестовыми данными'

    def handle(self, *args, **options):
        self.stdout.write('Создание тестовых данных...')
        
        cities_data = [
            {'name': 'Алматы', 'country': 'Казахстан', 'description': 'Южная столица Казахстана'},
            {'name': 'Астана', 'country': 'Казахстан', 'description': 'Столица Казахстана'},
            {'name': 'Шымкент', 'country': 'Казахстан', 'description': 'Третий по величине город'},
            {'name': 'Караганда', 'country': 'Казахстан', 'description': 'Промышленный центр'},
            {'name': 'Актобе', 'country': 'Казахстан', 'description': 'Западный Казахстан'},
            {'name': 'Тараз', 'country': 'Казахстан', 'description': 'Древний город'},
            {'name': 'Павлодар', 'country': 'Казахстан', 'description': 'Промышленный город'},
            {'name': 'Усть-Каменогорск', 'country': 'Казахстан', 'description': 'Восточный Казахстан'},
            {'name': 'Семей', 'country': 'Казахстан', 'description': 'Исторический город'},
            {'name': 'Атырау', 'country': 'Казахстан', 'description': 'Нефтяная столица'},
            {'name': 'Кокшетау', 'country': 'Казахстан', 'description': 'Курортная зона'},
            {'name': 'Туркестан', 'country': 'Казахстан', 'description': 'Древняя столица'},
        ]
        
        cities = {}
        for city_data in cities_data:
            city, created = City.objects.get_or_create(
                name=city_data['name'],
                defaults=city_data
            )
            cities[city.name] = city
            if created:
                self.stdout.write(f'Создан город: {city.name}')
        
        categories_data = [
            {'name': 'Горные туры', 'description': 'Походы в горы и альпинизм'},
            {'name': 'Экскурсионные туры', 'description': 'Культурно-познавательные туры'},
            {'name': 'Активный отдых', 'description': 'Спортивные и приключенческие туры'},
            {'name': 'Экотуризм', 'description': 'Туры на природу'},
            {'name': 'Паломнические туры', 'description': 'Религиозные туры'},
            {'name': 'Зимние туры', 'description': 'Лыжи и зимний отдых'},
        ]
        
        categories = {}
        for cat_data in categories_data:
            category, created = TourCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
            categories[category.name] = category
            if created:
                self.stdout.write(f'Создана категория: {category.name}')
        
        tours_data = [
            {
                'name': 'Большое Алматинское озеро',
                'description': 'Живописное озеро в горах Заилийского Алатау. Высота 2511 метров над уровнем моря. Кристально чистая вода бирюзового цвета.',
                'category': categories['Горные туры'],
                'destination_city': cities['Алматы'],
                'duration_days': 1,
                'price': Decimal('15000'),
                'max_participants': 15,
                'difficulty': 'easy',
            },
            {
                'name': 'Чарынский каньон',
                'description': 'Уникальный природный памятник. "Долина замков" - удивительные скальные образования красного песчаника.',
                'category': categories['Экотуризм'],
                'destination_city': cities['Алматы'],
                'duration_days': 1,
                'price': Decimal('18000'),
                'max_participants': 20,
                'difficulty': 'easy',
            },
            {
                'name': 'Кольсайские озера',
                'description': 'Три горных озера в ущелье Кольсай. Изумрудная вода, хвойные леса, горные пики. Жемчужина Казахстана.',
                'category': categories['Горные туры'],
                'destination_city': cities['Алматы'],
                'duration_days': 2,
                'price': Decimal('35000'),
                'max_participants': 12,
                'difficulty': 'medium',
            },
            {
                'name': 'Тур в Туркестан',
                'description': 'Посещение мавзолея Ходжи Ахмеда Ясави - объект всемирного наследия ЮНЕСКО. Знакомство с историей древнего города.',
                'category': categories['Паломнические туры'],
                'destination_city': cities['Туркестан'],
                'duration_days': 2,
                'price': Decimal('40000'),
                'max_participants': 25,
                'difficulty': 'easy',
            },
            {
                'name': 'Боровое - жемчужина Казахстана',
                'description': 'Курортная зона Бурабай. Озеро Боровое, скала Жумбактас, гора Кокшетау. Чистый воздух соснового леса.',
                'category': categories['Экотуризм'],
                'destination_city': cities['Кокшетау'],
                'duration_days': 3,
                'price': Decimal('55000'),
                'max_participants': 20,
                'difficulty': 'easy',
            },
            {
                'name': 'Восхождение на пик Талгар',
                'description': 'Высочайшая вершина Заилийского Алатау (4979 м). Техническое восхождение для опытных альпинистов.',
                'category': categories['Горные туры'],
                'destination_city': cities['Алматы'],
                'duration_days': 7,
                'price': Decimal('120000'),
                'max_participants': 8,
                'difficulty': 'hard',
            },
            {
                'name': 'Экскурсия по Алматы',
                'description': 'Обзорная экскурсия по городу. Зеленый базар, Парк 28 панфиловцев, Медео, Шымбулак.',
                'category': categories['Экскурсионные туры'],
                'destination_city': cities['Алматы'],
                'duration_days': 1,
                'price': Decimal('12000'),
                'max_participants': 30,
                'difficulty': 'easy',
            },
            {
                'name': 'Тур в Астану',
                'description': 'Знакомство со столицей. Байтерек, Хан-Шатыр, мечеть Хазрет Султан, ЭКСПО-2017.',
                'category': categories['Экскурсионные туры'],
                'destination_city': cities['Астана'],
                'duration_days': 2,
                'price': Decimal('45000'),
                'max_participants': 25,
                'difficulty': 'easy',
            },
            {
                'name': 'Лыжный тур на Шымбулак',
                'description': 'Горнолыжный курорт мирового уровня. Трассы разной сложности. Современная инфраструктура.',
                'category': categories['Зимние туры'],
                'destination_city': cities['Алматы'],
                'duration_days': 3,
                'price': Decimal('60000'),
                'max_participants': 15,
                'difficulty': 'medium',
            },
            {
                'name': 'Алтын-Эмель',
                'description': 'Национальный парк. Поющий бархан, горы Актау и Катутау. Уникальные ландшафты и древние петроглифы.',
                'category': categories['Экотуризм'],
                'destination_city': cities['Алматы'],
                'duration_days': 2,
                'price': Decimal('32000'),
                'max_participants': 18,
                'difficulty': 'medium',
            },
        ]
        
        for tour_data in tours_data:
            tour, created = Tour.objects.get_or_create(
                name=tour_data['name'],
                defaults=tour_data
            )
            if created:
                self.stdout.write(f'Создан тур: {tour.name}')
                
                start_date = datetime.now().date() + timedelta(days=7)
                for i in range(5):
                    date_offset = timedelta(days=i * 14)
                    tour_date = TourDate.objects.create(
                        tour=tour,
                        start_date=start_date + date_offset,
                        end_date=start_date + date_offset + timedelta(days=tour.duration_days),
                        is_available=True
                    )
                    self.stdout.write(f'  Создана дата: {tour_date.start_date}')
        
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser(
                username='admin',
                email='admin@tourkz.kz',
                password='admin123',
                first_name='Администратор',
                last_name='Системы'
            )
            UserProfile.objects.create(
                user=admin,
                phone='+7 (777) 123-45-67',
                city=cities['Алматы']
            )
            self.stdout.write('Создан суперпользователь: admin / admin123')
        
        if not User.objects.filter(username='testuser').exists():
            user = User.objects.create_user(
                username='testuser',
                email='test@tourkz.kz',
                password='test123',
                first_name='Тестовый',
                last_name='Пользователь'
            )
            UserProfile.objects.create(
                user=user,
                phone='+7 (777) 999-99-99',
                city=cities['Алматы'],
                passport_number='N 12345678'
            )
            self.stdout.write('Создан тестовый пользователь: testuser / test123')
        
        self.stdout.write(self.style.SUCCESS('Тестовые данные успешно созданы!'))

