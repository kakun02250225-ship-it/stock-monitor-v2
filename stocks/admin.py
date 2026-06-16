from django.contrib import admin

from .models import Stock


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    # 管理画面の一覧で見せる列
    list_display = ("name", "ticker", "market", "shares", "cost", "owner")
    list_filter = ("market",)
    search_fields = ("name", "ticker")
