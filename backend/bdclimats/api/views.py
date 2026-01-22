from django.shortcuts import render
from rest_framework import viewsets
from catalog.models import Indicator
from api.serializers import IndicatorSerializer

class IndicatorViewSet(viewsets.ModelViewSet):
    queryset = Indicator.objects.all().order_by("code")
    serializer_class = IndicatorSerializer