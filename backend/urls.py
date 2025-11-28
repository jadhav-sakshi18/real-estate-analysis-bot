from django.contrib import admin
from django.urls import path
from api.views import analyze, upload_file

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/analyze/', analyze, name='analyze'),
    path('api/upload/', upload_file, name='upload_file'),
    
]
