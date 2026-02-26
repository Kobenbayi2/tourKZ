from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Настройки админки
admin.site.site_header = "Панель управления туристическими турами"
admin.site.site_title = "Управление турами"
admin.site.index_title = "Добро пожаловать в панель управления"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("bookings.urls")),
    path("", include("django_prometheus.urls")),  
]

# Подключение медиа (для фото туров)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
