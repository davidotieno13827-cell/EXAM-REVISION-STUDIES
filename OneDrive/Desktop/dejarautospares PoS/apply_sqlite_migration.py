import sqlite3
from pathlib import Path

DB_PATH = Path('instance') / 'app.db'

def column_exists(conn, table, column):
    cur = conn.execute(f"PRAGMA table_info('{table}')")
    cols = [row[1] for row in cur.fetchall()]
    return column in cols

def main():
    if not DB_PATH.exists():
        print('Database not found at', DB_PATH)
        return

    conn = sqlite3.connect(str(DB_PATH))
    try:
        # Add min_stock_level to product
        if not column_exists(conn, 'product', 'min_stock_level'):
            print('Adding min_stock_level to product')
            conn.execute("ALTER TABLE product ADD COLUMN min_stock_level INTEGER NOT NULL DEFAULT 5")
        else:
            print('product.min_stock_level already exists')

        # Add product_sku to sale
        if not column_exists(conn, 'sale', 'product_sku'):
            print('Adding product_sku to sale')
            conn.execute("ALTER TABLE sale ADD COLUMN product_sku TEXT")
        else:
            print('sale.product_sku already exists')

        conn.commit()
        print('Migration applied successfully.')
    except Exception as e:
        print('Migration failed:', e)
    finally:
        conn.close()

if __name__ == '__main__':
    main()
