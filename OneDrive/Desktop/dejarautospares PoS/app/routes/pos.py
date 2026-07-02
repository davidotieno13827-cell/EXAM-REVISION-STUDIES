import os
from datetime import datetime, timedelta
from pathlib import Path
import csv
import io

import openpyxl
from flask import Blueprint, Response, flash, redirect, render_template, request, url_for
from flask_login import login_user, logout_user, login_required
from sqlalchemy import func, or_
from urllib.parse import urlparse

from app import db, limiter
from app.models import Product, Sale, User

bp = Blueprint('pos', __name__)
project_root = Path(__file__).resolve().parents[1]
PRICE_LIST_PATH = Path(os.getenv('PRICE_LIST_PATH', project_root / 'Dejar_Auto_Spares_Lubricants_Price_List.xlsx'))
ITEMS_PER_PAGE = 20


def read_price_list():
    if not PRICE_LIST_PATH.exists():
        return [], []
    try:
        workbook = openpyxl.load_workbook(PRICE_LIST_PATH, data_only=True)
        sheet = workbook.active
        rows = [row for row in sheet.iter_rows(values_only=True)]
        if not rows:
            return [], []
        header = [cell if cell is not None else '' for cell in rows[0]]
        data = [
            [cell if cell is not None else '' for cell in row]
            for row in rows[1:]
            if any(cell is not None for cell in row)
        ]
        return header, data
    except Exception:
        return [], []


def build_sales_query(start_date, end_date, search_term=None):
    query = Sale.query
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Sale.timestamp >= start_dt)
        except ValueError:
            flash('Start date must be YYYY-MM-DD.', 'danger')
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Sale.timestamp < end_dt)
        except ValueError:
            flash('End date must be YYYY-MM-DD.', 'danger')
    if search_term:
        query = query.filter(
            or_(
                Sale.product_name.ilike(f'%{search_term}%'),
                Sale.product_sku.ilike(f'%{search_term}%')
            )
        )
    return query


def _escape_for_excel(value):
    value = '' if value is None else str(value)
    if value and value[0] in ('=', '+', '-', '@'):
        return "'" + value
    return value


@bp.route('/')
@login_required
def index():
    query = request.args.get('q', '').strip()
    low_stock_threshold = request.args.get('low_stock', 5)
    page = request.args.get('page', 1)

    try:
        low_stock_threshold = int(low_stock_threshold)
    except ValueError:
        low_stock_threshold = 5

    try:
        page = int(page)
        if page < 1:
            page = 1
    except ValueError:
        page = 1

    product_query = Product.query
    if query:
        product_query = product_query.filter(
            or_(
                Product.name.ilike(f'%{query}%'),
                Product.brand.ilike(f'%{query}%'),
                Product.sku.ilike(f'%{query}%')
            )
        )

    product_pagination = product_query.order_by(Product.name).paginate(page=page, per_page=ITEMS_PER_PAGE, error_out=False)
    products = product_pagination.items

    product_ids = [product.id for product in products]
    if product_ids:
        last_sale_rows = db.session.query(
            Sale.product_id,
            func.max(Sale.timestamp)
        ).filter(Sale.product_id.in_(product_ids)).group_by(Sale.product_id).all()
        last_sold_map = {product_id: last_timestamp for product_id, last_timestamp in last_sale_rows}
    else:
        last_sold_map = {}

    total_products, total_stock, inventory_value = db.session.query(
        func.count(Product.id),
        func.coalesce(func.sum(Product.stock), 0),
        func.coalesce(func.sum(Product.stock * Product.price), 0.0)
    ).one()

    low_stock_products = Product.query.filter(Product.stock <= low_stock_threshold).order_by(Product.stock).all()

    total_sales, total_revenue = db.session.query(
        func.count(Sale.id),
        func.coalesce(func.sum(Sale.total_price), 0.0)
    ).one()

    return render_template(
        'index.html',
        products=products,
        pagination=product_pagination,
        total_products=total_products,
        total_stock=total_stock,
        inventory_value=inventory_value,
        low_stock_products=low_stock_products,
        total_sales=total_sales,
        total_revenue=total_revenue,
        query=query,
        low_stock_threshold=low_stock_threshold,
        last_sold_map=last_sold_map,
    )


@bp.route('/restock/<int:product_id>', methods=['GET', 'POST'])
@login_required
def restock_product(product_id):
    product = Product.query.get_or_404(product_id)
    if request.method == 'POST':
        try:
            quantity = int(request.form.get('quantity', 0))
        except ValueError:
            flash('Enter a valid stock quantity.', 'danger')
            return render_template('restock_product.html', product=product)

        if quantity <= 0:
            flash('Quantity must be greater than zero.', 'danger')
            return render_template('restock_product.html', product=product)

        product.stock += quantity
        db.session.commit()
        flash(f'{quantity} units added to {product.name}.', 'success')
        return redirect(url_for('pos.index'))

    return render_template('restock_product.html', product=product)


@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_product():
    price_list_header, price_list_rows = read_price_list()
    price_list_path = PRICE_LIST_PATH
    price_list_exists = price_list_path.exists()

    if request.method == 'POST':
        sku = request.form.get('sku', '').strip() or None
        name = request.form.get('name', '').strip()
        brand = request.form.get('brand', '').strip()
        try:
            price = float(request.form.get('price', 0))
            stock = int(request.form.get('stock', 0))
        except ValueError:
            flash('Please enter valid numeric values for price and stock.', 'danger')
            return render_template(
                'add_product.html',
                price_list_header=price_list_header,
                price_list_rows=price_list_rows,
                price_list_path=price_list_path,
                price_list_exists=price_list_exists,
            )
        if not name or not brand:
            flash('Product name and brand are required.', 'danger')
            return render_template(
                'add_product.html',
                price_list_header=price_list_header,
                price_list_rows=price_list_rows,
                price_list_path=price_list_path,
                price_list_exists=price_list_exists,
            )

        if sku and Product.query.filter(Product.sku == sku).first():
            flash('A product with that SKU already exists.', 'danger')
            return render_template(
                'add_product.html',
                price_list_header=price_list_header,
                price_list_rows=price_list_rows,
                price_list_path=price_list_path,
                price_list_exists=price_list_exists,
            )

        new_product = Product(sku=sku, name=name, brand=brand, price=price, stock=stock)
        db.session.add(new_product)
        db.session.commit()
        return redirect(url_for('pos.index'))

    return render_template(
        'add_product.html',
        price_list_header=price_list_header,
        price_list_rows=price_list_rows,
        price_list_path=price_list_path,
        price_list_exists=price_list_exists,
    )


@bp.route('/quick_sell', methods=['POST'])
@login_required
def quick_sell():
    product_search = request.form.get('product_search', '').strip()
    try:
        quantity = int(request.form.get('quantity', 1))
    except ValueError:
        quantity = 1

    if not product_search:
        flash('Enter a product name or brand to sell.', 'danger')
        return redirect(url_for('pos.index'))

    if quantity <= 0:
        flash('Quantity must be at least 1.', 'danger')
        return redirect(url_for('pos.index'))

    product = None
    if product_search:
        product = Product.query.filter(
            or_(
                Product.sku.ilike(product_search),
                Product.sku.ilike(f'%{product_search}%')
            )
        ).order_by(Product.stock.desc()).first()

    if not product:
        product = Product.query.filter(
            or_(
                Product.name.ilike(product_search),
                Product.brand.ilike(product_search),
                Product.name.ilike(f'%{product_search}%'),
                Product.brand.ilike(f'%{product_search}%')
            )
        ).order_by(Product.stock.desc()).first()

    if not product:
        flash('No product found matching that name, brand, or SKU.', 'danger')
        return redirect(url_for('pos.index'))

    if quantity > product.stock:
        flash(f'Only {product.stock} unit(s) of {product.name} are available.', 'danger')
        return redirect(url_for('pos.index'))

    product.stock -= quantity
    sale_total = product.price * quantity
    new_sale = Sale(product=product, product_sku=product.sku, product_name=product.name, price=product.price, quantity=quantity, total_price=sale_total)
    db.session.add(new_sale)
    db.session.commit()
    flash(f'Sold {quantity} unit(s) of {product.name}.', 'success')
    return redirect(url_for('pos.index'))


@bp.route('/import', methods=['GET', 'POST'])
@login_required
def import_products():
    if request.method == 'POST':
        uploaded_file = request.files.get('file')
        if not uploaded_file or uploaded_file.filename == '':
            flash('Please select a CSV file to import.', 'danger')
            return render_template('import_products.html')

        if not uploaded_file.filename.lower().endswith('.csv'):
            flash('Only CSV files are accepted.', 'danger')
            return render_template('import_products.html')

        try:
            stream = io.TextIOWrapper(uploaded_file.stream, encoding='utf-8', errors='replace')
            reader = csv.DictReader(stream)
            if not reader.fieldnames:
                raise ValueError('CSV file must include a header row.')

            imported = 0
            updated = 0
            skipped = 0
            def _csv_safe_cell(val):
                # Prevent CSV/Excel formula injection by prefixing dangerous leading chars
                if val is None:
                    return ''
                s = str(val)
                if s and s[0] in ('=', '+', '-', '@'):
                    return "'" + s
                return s

            for row in reader:
                sku = (row.get('sku') or row.get('code') or '').strip()
                name = (row.get('name') or row.get('product_name') or '').strip()
                brand = (row.get('brand') or row.get('make') or '').strip()
                price_raw = row.get('price') or row.get('unit_price') or ''
                stock_raw = row.get('stock') or row.get('quantity') or row.get('stock_quantity') or '0'

                if not name or not brand:
                    skipped += 1
                    continue

                try:
                    price = float(price_raw)
                    stock = int(float(stock_raw))
                except (ValueError, TypeError):
                    skipped += 1
                    continue

                existing = None
                if sku:
                    existing = Product.query.filter_by(sku=sku).first()
                if not existing:
                    existing = Product.query.filter_by(name=name, brand=brand).first()

                # sanitize values for storage/display
                sku = _csv_safe_cell(sku)
                name = _csv_safe_cell(name)
                brand = _csv_safe_cell(brand)

                if existing:
                    existing.price = price
                    existing.stock += stock
                    if sku and not existing.sku:
                        existing.sku = sku
                    updated += 1
                else:
                    db.session.add(Product(sku=sku or None, name=name, brand=brand, price=price, stock=stock))
                    imported += 1

            db.session.commit()
            flash(f'Imported {imported} products and updated {updated} existing product(s). Skipped {skipped} rows.', 'success')
            return redirect(url_for('pos.index'))
        except Exception as exc:
            flash(f'Error importing CSV: {exc}', 'danger')
            return render_template('import_products.html')

    return render_template('import_products.html')


@bp.route('/sell/<int:product_id>', methods=['POST'])
@login_required
def sell(product_id):
    product = Product.query.get_or_404(product_id)
    try:
        quantity = int(request.form.get('quantity', 1))
    except ValueError:
        quantity = 1

    if quantity <= 0:
        flash('Quantity must be at least 1.', 'danger')
        return redirect(url_for('pos.index'))

    if quantity > product.stock:
        flash(f'Only {product.stock} unit(s) of {product.name} are available.', 'danger')
        return redirect(url_for('pos.index'))

    product.stock -= quantity
    sale_total = product.price * quantity
    new_sale = Sale(product=product, product_sku=product.sku, product_name=product.name, price=product.price, quantity=quantity, total_price=sale_total)
    db.session.add(new_sale)
    db.session.commit()
    flash(f'Sold {quantity} unit(s) of {product.name}.', 'success')
    return redirect(url_for('pos.index'))


@bp.route('/history')
@login_required
def history():
    start_date = request.args.get('start_date', '').strip()
    end_date = request.args.get('end_date', '').strip()
    search = request.args.get('search', '').strip()
    sales_query = build_sales_query(start_date, end_date, search)
    sales = sales_query.order_by(Sale.timestamp.desc()).all()
    total_revenue = sum(sale.total_price for sale in sales)
    return render_template(
        'sales_history.html',
        sales=sales,
        total=total_revenue,
        start_date=start_date,
        end_date=end_date,
        search=search,
    )


@bp.route('/export/sales')
@login_required
def export_sales():
    start_date = request.args.get('start_date', '').strip()
    end_date = request.args.get('end_date', '').strip()
    search = request.args.get('search', '').strip()
    sales_query = build_sales_query(start_date, end_date, search)
    sales = sales_query.order_by(Sale.timestamp.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Product SKU', 'Product Name', 'Price', 'Quantity', 'Total Price', 'Timestamp'])

    for sale in sales:
        writer.writerow([
            sale.id,
            _escape_for_excel(sale.product_sku or ''),
            _escape_for_excel(sale.product_name),
            sale.price,
            sale.quantity,
            sale.total_price,
            sale.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        ])

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=sales_history.csv'},
    )


@bp.route('/export/inventory')
@login_required
def export_inventory():
    products = Product.query.order_by(Product.name).all()
    product_ids = [product.id for product in products]
    last_sold_map = {}
    if product_ids:
        last_sale_rows = db.session.query(
            Sale.product_id,
            func.max(Sale.timestamp)
        ).filter(Sale.product_id.in_(product_ids)).group_by(Sale.product_id).all()
        last_sold_map = {product_id: last_timestamp for product_id, last_timestamp in last_sale_rows}

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'SKU', 'Name', 'Brand', 'Price', 'Stock', 'Stock Value', 'Last Sold'])
    for product in products:
        def _fmt_last_sold(pid):
            ts = last_sold_map.get(pid)
            return ts.strftime('%Y-%m-%d %H:%M:%S') if ts else ''

        writer.writerow([
            product.id,
            _escape_for_excel(product.sku or ''),
            _escape_for_excel(product.name),
            _escape_for_excel(product.brand),
            product.price,
            product.stock,
            product.price * product.stock,
            _fmt_last_sold(product.id),
        ])

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=inventory.csv'},
    )


@bp.route('/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    if request.method == 'POST':
        sku = request.form.get('sku', product.sku or '').strip() or None
        product.name = request.form.get('name', product.name).strip()
        product.brand = request.form.get('brand', product.brand).strip()
        try:
            product.price = float(request.form.get('price', product.price))
            product.stock = int(request.form.get('stock', product.stock))
        except ValueError:
            flash('Please enter valid numeric values for price and stock.', 'danger')
            return render_template('edit_product.html', product=product)

        if sku and Product.query.filter(Product.sku == sku, Product.id != product.id).first():
            flash('Another product already uses that SKU.', 'danger')
            return render_template('edit_product.html', product=product)

        product.sku = sku
        db.session.commit()
        flash('Product updated successfully.', 'success')
        return redirect(url_for('pos.index'))
    return render_template('edit_product.html', product=product)


@bp.route('/delete/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)

    # Perform deletion on POST only to prevent CSRF via simple GET
    Sale.query.filter(Sale.product_id == product.id).delete(synchronize_session=False)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully.', 'success')
    return redirect(url_for('pos.index'))


@bp.route('/login', methods=['GET', 'POST'])
@limiter.limit('6 per minute')
def login():
    next_page = request.args.get('next')
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            if next_page and urlparse(next_page).netloc == '':
                return redirect(next_page)
            return redirect(url_for('pos.index'))
        flash('Invalid username or password.', 'danger')
    return render_template('login.html', next_page=next_page)


@bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('pos.index'))
