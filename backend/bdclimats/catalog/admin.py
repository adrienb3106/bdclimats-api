from django.contrib import admin
from .models import Indicator, ComputationRule, Dataset


class ComputationRuleInline(admin.TabularInline):
    model = ComputationRule
    extra = 0
    fields = ("version", "operation", "is_active")
    ordering = ("-is_active", "-version")


@admin.register(Indicator)
class IndicatorAdmin(admin.ModelAdmin):
    inlines = [ComputationRuleInline]
    search_fields = ("code", "name")
    list_display = ("code", "name", "dataset", "unit")
    list_filter = ("dataset",)
    list_select_related = ("dataset",)
    ordering = ("code",)


@admin.register(ComputationRule)
class ComputationRuleAdmin(admin.ModelAdmin):
    list_display = ("indicator", "version", "operation", "is_active")
    list_filter = ("operation", "is_active", "indicator__dataset")
    search_fields = ("indicator__code", "indicator__name")
    list_select_related = ("indicator", "indicator__dataset")
    ordering = ("indicator__code", "-version")


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    search_fields = ("code", "name")
    list_display = ("code", "name", "source_url", "created_at")
    ordering = ("code",)
