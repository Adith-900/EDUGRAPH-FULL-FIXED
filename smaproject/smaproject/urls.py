from django.contrib import admin
from django.urls import path
from smaapp import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.process_pdfs, name='upload'),
    path('results/', views.show_results, name='results'),
    path('download_results/', views.download_results_pdf, name='download_results'),  # PDF download route
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
