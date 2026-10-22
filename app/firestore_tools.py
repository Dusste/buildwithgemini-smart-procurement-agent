import json
from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-03-2e7293c6ceea"

def get_firestore_client():
    return firestore.Client(project=PROJECT_ID)

def seed_firestore_data() -> str:
    """Seeds sample vendor items and catalog into Firestore DB.
    
    Returns:
        Confirmation string.
    """
    db = get_firestore_client()
    vendor_collection = db.collection("vendor_catalog")
    
    sample_items = [
        {
            "item_id": "ITEM-CHAIR-01",
            "vendor_name": "Acme Office Supplies",
            "description": "Ergonomic Mesh Office Chair",
            "unit_price": 150.00,
            "stock_quantity": 45,
            "category": "Furniture"
        },
        {
            "item_id": "ITEM-MON-27",
            "vendor_name": "TechCorp Logistics",
            "description": "27-inch 4K Monitor",
            "unit_price": 300.00,
            "stock_quantity": 18,
            "category": "Electronics"
        },
        {
            "item_id": "ITEM-KB-MECH",
            "vendor_name": "Global Hardware Ltd",
            "description": "Tactile Mechanical Keyboard",
            "unit_price": 80.00,
            "stock_quantity": 60,
            "category": "Peripherals"
        },
        {
            "item_id": "ITEM-SAAS-ANNUAL",
            "vendor_name": "CloudServices Inc",
            "description": "Annual Cloud Enterprise Subscription",
            "unit_price": 5000.00,
            "stock_quantity": 999,
            "category": "Software"
        }
    ]
    
    for item in sample_items:
        vendor_collection.document(item["item_id"]).set(item)
        
    return json.dumps({"status": "SUCCESS", "message": "Seeded 4 catalog documents in Firestore collection 'vendor_catalog'."})


def get_vendor_catalog_from_firestore() -> str:
    """Queries Firestore database for live vendor catalog items and stock levels.
    
    Returns:
        JSON string listing vendor catalog items.
    """
    db = get_firestore_client()
    docs = db.collection("vendor_catalog").stream()
    items = [doc.to_dict() for doc in docs]
    return json.dumps({"vendor_catalog": items}, indent=2)


def update_vendor_inventory_in_firestore(item_id: str, new_stock_quantity: int) -> str:
    """Updates stock quantity for a vendor catalog item in Firestore.
    
    Args:
        item_id: Catalog item ID (e.g. 'ITEM-CHAIR-01')
        new_stock_quantity: Updated integer stock count
        
    Returns:
        JSON string confirming Firestore document update.
    """
    db = get_firestore_client()
    doc_ref = db.collection("vendor_catalog").document(item_id)
    doc = doc_ref.get()
    
    if not doc.exists:
        return json.dumps({"error": f"Item {item_id} not found in Firestore catalog."})
        
    doc_ref.update({"stock_quantity": new_stock_quantity})
    return json.dumps({
        "status": "SUCCESS",
        "item_id": item_id,
        "updated_stock_quantity": new_stock_quantity,
        "message": f"Successfully updated {item_id} stock to {new_stock_quantity} in Firestore."
    }, indent=2)
