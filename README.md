# Inventory & Barcode Management System

Web app to manage products, stock levels, barcodes and reports.

## Features
- Product add, edit, delete, search
- Auto-generated Code128 barcodes
- Scan page (works with USB barcode scanners)
- Stock in/out history, low-stock report, CSV export
- Login-protected pages

## Tech stack
Python, Django, SQLite, python-barcode, Pillow

## Run locally
python -m venv myenv
myenv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver