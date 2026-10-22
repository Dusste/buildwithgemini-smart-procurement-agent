import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "procurement.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create Vendors table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vendors (
        vendor_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        tax_id TEXT,
        payment_terms TEXT
    )
    """)
    
    # Create Purchase Orders table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS purchase_orders (
        po_number TEXT PRIMARY KEY,
        vendor_id TEXT NOT NULL,
        vendor_name TEXT NOT NULL,
        po_date TEXT NOT NULL,
        total_amount REAL NOT NULL,
        status TEXT DEFAULT 'OPEN',
        FOREIGN KEY (vendor_id) REFERENCES vendors (vendor_id)
    )
    """)
    
    # Create PO Line Items table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS po_line_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        po_number TEXT NOT NULL,
        item_id TEXT NOT NULL,
        description TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price REAL NOT NULL,
        line_total REAL NOT NULL,
        FOREIGN KEY (po_number) REFERENCES purchase_orders (po_number)
    )
    """)
    
    # Create Goods Receipt Notes (GRN) table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS goods_receipt_notes (
        grn_number TEXT PRIMARY KEY,
        po_number TEXT NOT NULL,
        received_date TEXT NOT NULL,
        item_id TEXT NOT NULL,
        received_quantity INTEGER NOT NULL,
        FOREIGN KEY (po_number) REFERENCES purchase_orders (po_number)
    )
    """)
    
    # Create Invoice Match Audit & Log table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS invoice_match_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_number TEXT NOT NULL,
        po_number TEXT NOT NULL,
        vendor_name TEXT NOT NULL,
        match_status TEXT NOT NULL,
        price_variance REAL DEFAULT 0.0,
        qty_variance INTEGER DEFAULT 0,
        details TEXT,
        erp_payment_staged INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Seed data if tables are empty
    cursor.execute("SELECT COUNT(*) FROM purchase_orders")
    if cursor.fetchone()[0] == 0:
        _seed_data(cursor)
        
    conn.commit()
    conn.close()

def _seed_data(cursor):
    # Vendors
    vendors = [
        ("VEND-001", "Acme Office Supplies", "XX-XXXX123", "Net 30"),
        ("VEND-002", "TechCorp Logistics", "XX-XXXX456", "Net 15"),
        ("VEND-003", "Global Hardware Ltd", "XX-XXXX789", "Net 30"),
        ("VEND-004", "CloudServices Inc", "XX-XXXX999", "Due on Receipt"),
    ]
    cursor.executemany("INSERT INTO vendors VALUES (?, ?, ?, ?)", vendors)
    
    # Purchase Orders
    pos = [
        ("PO-1001", "VEND-001", "Acme Office Supplies", "2026-10-01", 1500.00, "OPEN"),
        ("PO-1002", "VEND-002", "TechCorp Logistics", "2026-10-05", 1500.00, "OPEN"),
        ("PO-1003", "VEND-003", "Global Hardware Ltd", "2026-10-10", 1600.00, "OPEN"),
        ("PO-1004", "VEND-004", "CloudServices Inc", "2026-10-15", 5000.00, "OPEN"),
    ]
    cursor.executemany("INSERT INTO purchase_orders VALUES (?, ?, ?, ?, ?, ?)", pos)
    
    # PO Line Items
    po_items = [
        # PO-1001
        ("PO-1001", "ITEM-CHAIR-01", "Ergonomic Mesh Office Chair", 10, 150.00, 1500.00),
        # PO-1002
        ("PO-1002", "ITEM-MON-27", "27-inch 4K Monitor", 5, 300.00, 1500.00),
        # PO-1003
        ("PO-1003", "ITEM-KB-MECH", "Tactile Mechanical Keyboard", 20, 80.00, 1600.00),
        # PO-1004
        ("PO-1004", "ITEM-SAAS-ANNUAL", "Annual Cloud Enterprise Subscription", 1, 5000.00, 5000.00),
    ]
    cursor.executemany("INSERT INTO po_line_items (po_number, item_id, description, quantity, unit_price, line_total) VALUES (?, ?, ?, ?, ?, ?)", po_items)
    
    # Goods Receipt Notes (GRNs)
    grns = [
        ("GRN-1001", "PO-1001", "2026-10-08", "ITEM-CHAIR-01", 10),
        ("GRN-1002", "PO-1002", "2026-10-12", "ITEM-MON-27", 4), # 4 received out of 5 ordered!
        ("GRN-1003", "PO-1003", "2026-10-15", "ITEM-KB-MECH", 20),
        ("GRN-1004", "PO-1004", "2026-10-16", "ITEM-SAAS-ANNUAL", 1),
    ]
    cursor.executemany("INSERT INTO goods_receipt_notes VALUES (?, ?, ?, ?, ?)", grns)

if __name__ == "__main__":
    init_db()
    print("Database initialized and seeded successfully.")
