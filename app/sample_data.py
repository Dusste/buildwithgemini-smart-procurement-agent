import json
import os

INVOICE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sample_invoices")

def create_sample_invoices():
    os.makedirs(INVOICE_DIR, exist_ok=True)
    
    invoices = [
        {
            "filename": "INV-9001.json",
            "invoice_number": "INV-9001",
            "invoice_date": "2026-10-18",
            "vendor_name": "Acme Office Supplies",
            "po_number": "PO-1001",
            "payment_terms": "Net 30",
            "line_items": [
                {
                    "item_id": "ITEM-CHAIR-01",
                    "description": "Ergonomic Mesh Office Chair",
                    "quantity": 10,
                    "unit_price": 150.00,
                    "line_total": 1500.00
                }
            ],
            "subtotal": 1500.00,
            "tax": 0.00,
            "grand_total": 1500.00
        },
        {
            "filename": "INV-9002.json",
            "invoice_number": "INV-9002",
            "invoice_date": "2026-10-19",
            "vendor_name": "TechCorp Logistics",
            "po_number": "PO-1002",
            "payment_terms": "Net 15",
            "line_items": [
                {
                    "item_id": "ITEM-MON-27",
                    "description": "27-inch 4K Monitor",
                    "quantity": 5,
                    "unit_price": 300.00,
                    "line_total": 1500.00
                }
            ],
            "subtotal": 1500.00,
            "tax": 0.00,
            "grand_total": 1500.00
        },
        {
            "filename": "INV-9003.json",
            "invoice_number": "INV-9003",
            "invoice_date": "2026-10-20",
            "vendor_name": "Global Hardware Ltd",
            "po_number": "PO-1003",
            "payment_terms": "Net 30",
            "line_items": [
                {
                    "item_id": "ITEM-KB-MECH",
                    "description": "Tactile Mechanical Keyboard",
                    "quantity": 20,
                    "unit_price": 95.00,  # PO was 80.00
                    "line_total": 1900.00
                }
            ],
            "subtotal": 1900.00,
            "tax": 0.00,
            "grand_total": 1900.00
        },
        {
            "filename": "INV-9004.json",
            "invoice_number": "INV-9004",
            "invoice_date": "2026-10-21",
            "vendor_name": "Unknown Services LLC",
            "po_number": "PO-9999", # Invalid PO
            "payment_terms": "Due on Receipt",
            "line_items": [
                {
                    "item_id": "ITEM-CONSULTING",
                    "description": "Unapproved Consulting Services",
                    "quantity": 1,
                    "unit_price": 2500.00,
                    "line_total": 2500.00
                }
            ],
            "subtotal": 2500.00,
            "tax": 0.00,
            "grand_total": 2500.00
        }
    ]

    for inv in invoices:
        filename = inv.pop("filename")
        filepath = os.path.join(INVOICE_DIR, filename)
        with open(filepath, "w") as f:
            json.dump(inv, f, indent=2)

    print(f"Created {len(invoices)} sample invoice files in {INVOICE_DIR}")

if __name__ == "__main__":
    create_sample_invoices()
