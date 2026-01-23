from django.shortcuts import render
from rest_framework import viewsets
from catalog.models import Indicator, Dataset, ComputationRule
from api.serializers import IndicatorSerializer, DatasetSerializer, ComputationRuleSerializer

class IndicatorViewSet(viewsets.ModelViewSet):
    queryset = Indicator.objects.all().order_by("code")
    serializer_class = IndicatorSerializer

class DatasetViewSet(viewsets.ModelViewSet):
    queryset = Dataset.objects.all().order_by("code")
    serializer_class = DatasetSerializer

class ComputationRuleViewSet(viewsets.ModelViewSet):
    queryset = ComputationRule.objects.all().order_by("version").order_by("indicator")
    serializer_class = ComputationRuleSerializer
    