"""
URL configuration for bdclimats project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from api.views import ComputationRuleViewSet, DatasetViewSet, IndicatorViewSet, health
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView
from rest_framework.routers import DefaultRouter

api_router = DefaultRouter()
api_router.register("indicators", IndicatorViewSet, basename="indicator")
api_router.register("datasets", DatasetViewSet, basename="dataset")
api_router.register(
    "computation-rules", ComputationRuleViewSet, basename="computation-rule"
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(api_router.urls)),
    path(
        "api/help/",
        TemplateView.as_view(template_name="api/help.html"),
        name="api-help",
    ),
    path("health/", health, name="health"),
]
