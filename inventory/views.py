import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import DecimalField, ExpressionWrapper, F, Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ProductForm, StockForm
from .models import Product, StockMovement


@login_required
def dashboard(request):
    value = ExpressionWrapper(
        F("price") * F("quantity"),
        output_field=DecimalField(max_digits=14, decimal_places=2))
    totals = Product.objects.aggregate(units=Sum("quantity"),
                                       value=Sum(value))
    context = {
        "total_products": Product.objects.count(),
        "total_units": totals["units"] or 0,
        "stock_value": totals["value"] or 0,
        "low_count": Product.objects.filter(
            quantity__lte=F("reorder_level")).count(),
        "recent": StockMovement.objects.select_related("product")[:8],
    }
    return render(request, "inventory/dashboard.html", context)


@login_required
def product_list(request):
    q = request.GET.get("q", "").strip()
    products = Product.objects.select_related("category")
    if q:
        products = products.filter(
            Q(name__icontains=q) | Q(barcode_number__icontains=q))
    return render(request, "inventory/product_list.html",
                  {"products": products, "q": q})


@login_required
def product_add(request):
    form = ProductForm(request.POST or None)
    if form.is_valid():
        product = form.save()
        if product.quantity > 0:
            StockMovement.objects.create(
                product=product, movement_type="IN",
                quantity=product.quantity, note="Opening stock",
                created_by=request.user)
        messages.success(request, "Product added. Barcode created.")
        return redirect("product_detail", pk=product.pk)
    return render(request, "inventory/product_form.html",
                  {"form": form, "title": "Add product"})


@login_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = ProductForm(request.POST or None, instance=product)
    if form.is_valid():
        form.save()
        messages.success(request, "Product updated.")
        return redirect("product_detail", pk=product.pk)
    return render(request, "inventory/product_form.html",
                  {"form": form, "title": "Edit product"})


@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        product.delete()
        messages.success(request, "Product deleted.")
        return redirect("product_list")
    return render(request, "inventory/product_confirm_delete.html",
                  {"product": product})


@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = StockForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        move = form.save(commit=False)
        if move.movement_type == "OUT" and move.quantity > product.quantity:
            form.add_error("quantity", "Not enough stock available.")
        else:
            if move.movement_type == "IN":
                product.quantity += move.quantity
            else:
                product.quantity -= move.quantity
            product.save()
            move.product = product
            move.created_by = request.user
            move.save()
            messages.success(request, "Stock updated.")
            return redirect("product_detail", pk=product.pk)
    return render(request, "inventory/product_detail.html", {
        "product": product, "form": form,
        "movements": product.movements.all()[:15]})


@login_required
def scan(request):
    code = request.GET.get("code", "").strip()
    if code:
        product = Product.objects.filter(barcode_number=code).first()
        if product:
            return redirect("product_detail", pk=product.pk)
        messages.error(request, f"No product found for barcode {code}")
    return render(request, "inventory/scan.html")


@login_required
def low_stock(request):
    products = Product.objects.filter(quantity__lte=F("reorder_level"))
    return render(request, "inventory/low_stock.html",
                  {"products": products})


@login_required
def export_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="inventory.csv"'
    writer = csv.writer(response)
    writer.writerow(["Name", "Category", "Barcode", "Price", "Quantity",
                     "Reorder level"])
    for p in Product.objects.select_related("category"):
        writer.writerow([p.name, p.category or "", p.barcode_number,
                         p.price, p.quantity, p.reorder_level])
    return response