from django.contrib import admin

from .models import Category, Product, StockMovement

admin.site.register(Category)
admin.site.register(StockMovement)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "barcode_number", "category", "price", "quantity")
    search_fields = ("name", "barcode_number")