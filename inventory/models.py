from io import BytesIO

import barcode
from barcode.writer import ImageWriter
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models
from django.utils.crypto import get_random_string


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL,
                                 null=True, blank=True)
    barcode_number = models.CharField(max_length=20, unique=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=5)
    barcode_image = models.ImageField(upload_to="barcodes/", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.barcode_number})"

    @property
    def is_low_stock(self):
        return self.quantity <= self.reorder_level

    def _make_barcode_number(self):
        while True:
            number = get_random_string(10, allowed_chars="0123456789")
            if not Product.objects.filter(barcode_number=number).exists():
                return number

    def _make_barcode_image(self):
        code = barcode.get_barcode_class("code128")(
            self.barcode_number, writer=ImageWriter())
        buffer = BytesIO()
        code.write(buffer)
        self.barcode_image.save(f"{self.barcode_number}.png",
                                ContentFile(buffer.getvalue()), save=False)

    def save(self, *args, **kwargs):
        if not self.barcode_number:
            self.barcode_number = self._make_barcode_number()
        if not self.barcode_image:
            self._make_barcode_image()
        super().save(*args, **kwargs)


class StockMovement(models.Model):
    IN = "IN"
    OUT = "OUT"
    TYPE_CHOICES = [(IN, "Stock In"), (OUT, "Stock Out")]

    product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                related_name="movements")
    movement_type = models.CharField(max_length=3, choices=TYPE_CHOICES)
    quantity = models.PositiveIntegerField()
    note = models.CharField(max_length=200, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                   on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.movement_type} {self.quantity} x {self.product.name}"
    