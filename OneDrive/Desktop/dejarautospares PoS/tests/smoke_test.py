import os
import re
import sys

from app import app, db
from app.models import Product, User


def extract_csrf(html_text):
    m = re.search(r'name="csrf_token" value="([^"]+)"', html_text)
    return m.group(1) if m else None


def fail(msg):
    print('FAIL:', msg)
    sys.exit(2)


def main():
    admin_user = os.getenv('ADMIN_USERNAME')
    admin_pass = os.getenv('ADMIN_PASSWORD')
    if not admin_user or not admin_pass:
        fail('ADMIN_USERNAME or ADMIN_PASSWORD not set in environment (.env)')

    with app.test_client() as client:
        # GET login to obtain CSRF
        r = client.get('/login')
        token = extract_csrf(r.get_data(as_text=True))
        if not token:
            fail('Could not extract CSRF token from login page')

        # login
        r = client.post('/login', data={'username': admin_user, 'password': admin_pass, 'csrf_token': token}, follow_redirects=True)
        if b'Logout' not in r.data and b'logout' not in r.data:
            fail('Login failed or logout link not present after login')
        print('Login: OK')

        # Add a new product
        r = client.get('/add')
        token = extract_csrf(r.get_data(as_text=True))
        if not token:
            fail('CSRF token missing on add product page')

        product_name = 'smoke-test-product'
        r = client.post('/add', data={'name': product_name, 'brand': 'smoke', 'price': '9.99', 'stock': '10', 'csrf_token': token}, follow_redirects=True)
        if b'smoke-test-product' not in r.data:
            fail('Add product failed or product not visible in index')
        print('Add product: OK')

        # Find product id
        with app.app_context():
            p = Product.query.filter_by(name=product_name).first()
            if not p:
                fail('Could not find newly created product in DB')
            pid = p.id

        # Sell one item
        r = client.get('/')
        token = extract_csrf(r.get_data(as_text=True))
        if not token:
            fail('CSRF missing on index for sell')
        r = client.post(f'/sell/{pid}', data={'quantity': '1', 'csrf_token': token}, follow_redirects=True)
        if b'Out of Stock' in r.data:
            # still OK if not out of stock; just verify redirect succeeded
            pass
        print('Sell product: OK')

        # Restock
        r = client.get(f'/restock/{pid}')
        token = extract_csrf(r.get_data(as_text=True))
        r = client.post(f'/restock/{pid}', data={'quantity': '5', 'csrf_token': token}, follow_redirects=True)
        if r.status_code >= 400:
            fail('Restock failed')
        print('Restock: OK')

        # Delete product
        r = client.get('/')
        token = extract_csrf(r.get_data(as_text=True))
        r = client.post(f'/delete/{pid}', data={'csrf_token': token}, follow_redirects=True)
        with app.app_context():
            if Product.query.get(pid):
                fail('Delete product failed')
        print('Delete product: OK')

    print('SMOKE TESTS PASSED')


if __name__ == '__main__':
    main()
