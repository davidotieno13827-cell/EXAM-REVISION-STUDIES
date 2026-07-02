import os
from pathlib import Path

# Remove existing persistent DB before importing app so SQLAlchemy builds fresh schema
project_root = Path(__file__).resolve().parents[1]
db_path = project_root / 'instance' / 'app.db'
if db_path.exists():
    try:
        os.remove(db_path)
    except Exception:
        pass

from app import app, db
from app.models import Product, User

def run_smoke_tests():
    with app.app_context():
        db.create_all()

        # create a test user
        if not User.query.filter_by(username='test').first():
            u = User(username='test')
            u.set_password('pass')
            db.session.add(u)
            db.session.commit()

        # create a product
        p = Product(sku='TST123', name='Test Product', brand='BrandX', price=10.0, stock=5)
        db.session.add(p)
        db.session.commit()

        client = app.test_client()

        results = []

        # GET login page
        rv = client.get('/login')
        results.append(('/login GET', rv.status_code))

        # login
        rv = client.post('/login', data={'username': 'test', 'password': 'pass'}, follow_redirects=True)
        results.append(('/login POST', rv.status_code))

        # index
        rv = client.get('/')
        results.append(('/ GET', rv.status_code))

        # add page
        rv = client.get('/add')
        results.append(('/add GET', rv.status_code))

        # quick sell (by name)
        rv = client.post('/quick_sell', data={'product_search': 'Test Product', 'quantity': '1'}, follow_redirects=True)
        results.append(('/quick_sell POST', rv.status_code))

        # export sales
        rv = client.get('/export/sales')
        results.append(('/export/sales GET', rv.status_code))

        # export inventory
        rv = client.get('/export/inventory')
        results.append(('/export/inventory GET', rv.status_code))

        # history
        rv = client.get('/history')
        results.append(('/history GET', rv.status_code))

        # edit (GET)
        rv = client.get(f'/edit/{p.id}')
        results.append((f'/edit/{p.id} GET', rv.status_code))

        # restock (GET)
        rv = client.get(f'/restock/{p.id}')
        results.append((f'/restock/{p.id} GET', rv.status_code))

        # logout
        rv = client.get('/logout', follow_redirects=True)
        results.append(('/logout GET', rv.status_code))

        # Print results
        for route, status in results:
            print(route, status)

        # Show a small sample of exported sales CSV
        rv = client.get('/export/sales')
        print('\nSales CSV sample:')
        print(rv.data.decode('utf-8'))

if __name__ == '__main__':
    run_smoke_tests()
