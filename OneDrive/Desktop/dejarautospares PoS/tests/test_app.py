import os
import re

import pytest
from app import app, db
from app.models import Product, User


def extract_csrf(html_text):
    m = re.search(r'name="csrf_token" value="([^"]+)"', html_text)
    return m.group(1) if m else None


@pytest.fixture(scope='session')
def app_client():
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    os.environ['FLASK_ENV'] = 'testing'
    app.config.update({'TESTING': True, 'WTF_CSRF_ENABLED': True})
    with app.app_context():
        db.drop_all()
        db.create_all()
        user = User(username='test')
        user.set_password('pass')
        db.session.add(user)
        db.session.commit()
    with app.test_client() as client:
        yield client


def test_login_logout(app_client):
    r = app_client.get('/login')
    token = extract_csrf(r.get_data(as_text=True))
    assert token
    r = app_client.post('/login', data={'username': 'test', 'password': 'pass', 'csrf_token': token}, follow_redirects=True)
    assert r.status_code == 200
    assert 'Logout' in r.get_data(as_text=True)
    r = app_client.post('/logout', data={'csrf_token': extract_csrf(app_client.get('/login').get_data(as_text=True))}, follow_redirects=True)
    assert r.status_code == 200


def test_add_edit_restock_delete_product(app_client):
    # login first
    r = app_client.get('/login')
    token = extract_csrf(r.get_data(as_text=True))
    app_client.post('/login', data={'username': 'test', 'password': 'pass', 'csrf_token': token}, follow_redirects=True)

    r = app_client.get('/add')
    token = extract_csrf(r.get_data(as_text=True))
    assert token
    r = app_client.post('/add', data={'name': 'pytest product', 'brand': 'Brand', 'price': '5.50', 'stock': '3', 'csrf_token': token}, follow_redirects=True)
    assert r.status_code == 200
    assert b'pytest product' in r.data

    with app.app_context():
        p = Product.query.filter_by(name='pytest product').first()
        assert p
        pid = p.id

    r = app_client.get('/')
    token = extract_csrf(r.get_data(as_text=True))
    r = app_client.post(f'/sell/{pid}', data={'quantity': '1', 'csrf_token': token}, follow_redirects=True)
    assert r.status_code == 200

    r = app_client.get(f'/restock/{pid}')
    token = extract_csrf(r.get_data(as_text=True))
    r = app_client.post(f'/restock/{pid}', data={'quantity': '2', 'csrf_token': token}, follow_redirects=True)
    assert r.status_code == 200

    r = app_client.get('/')
    token = extract_csrf(r.get_data(as_text=True))
    r = app_client.post(f'/delete/{pid}', data={'csrf_token': token}, follow_redirects=True)
    assert r.status_code == 200

    with app.app_context():
        assert Product.query.get(pid) is None


def test_import_export_history_routes(app_client):
    # login first
    r = app_client.get('/login')
    token = extract_csrf(r.get_data(as_text=True))
    app_client.post('/login', data={'username': 'test', 'password': 'pass', 'csrf_token': token}, follow_redirects=True)

    # check import page GET
    r = app_client.get('/import')
    assert r.status_code == 200
    token = extract_csrf(r.get_data(as_text=True))
    assert token

    # check export routes
    r = app_client.get('/export/sales')
    assert r.status_code == 200
    assert b'ID,Product SKU,Product Name' in r.data

    r = app_client.get('/export/inventory')
    assert r.status_code == 200
    assert b'SKU,Name,Brand,Price' in r.data

    # history route
    r = app_client.get('/history')
    assert r.status_code == 200

    # logout route using CSRF token from authenticated page
    r = app_client.get('/')
    token = extract_csrf(r.get_data(as_text=True))
    assert token
    r = app_client.post('/logout', data={'csrf_token': token}, follow_redirects=True)
    assert r.status_code == 200
