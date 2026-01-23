from rest_framework import viewsets
from catalog.models import Indicator, Dataset, ComputationRule
from api.serializers import IndicatorSerializer, DatasetSerializer, ComputationRuleSerializer


class IndicatorViewSet(viewsets.ModelViewSet):
    # CRUD complet pour Indicator.
    queryset = Indicator.objects.all().order_by("code")
    serializer_class = IndicatorSerializer


class DatasetViewSet(viewsets.ModelViewSet):
    # CRUD complet pour Dataset.
    queryset = Dataset.objects.all().order_by("code")
    serializer_class = DatasetSerializer


class ComputationRuleViewSet(viewsets.ModelViewSet):
    # CRUD complet pour ComputationRule.
    queryset = ComputationRule.objects.all().order_by("indicator", "version")
    serializer_class = ComputationRuleSerializer
