from django.shortcuts import render
from rest_framework import viewsets
from catalog.models import Indicator, Dataset
from api.serializers import IndicatorSerializer, DatasetSerializer

class IndicatorViewSet(viewsets.ModelViewSet):
    queryset = Indicator.objects.all().order_by("code")
    serializer_class = IndicatorSerializer

class DatasetViewSet(viewsets.ModelViewSet):
    queryset = Dataset.objects.all().order_by("code")
    serializer_class = DatasetSerializer