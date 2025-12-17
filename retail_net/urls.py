from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("ui.urls")),
    path("accounts/", include("django.contrib.auth.urls")), 
    
]
handler404 = "ui.views.error_404"
handler403 = "ui.views.error_403"