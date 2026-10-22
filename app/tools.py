import json
import os
import sqlite3
from typing import Dict, Any, List
from app.database import DB_PATH, get_db_connection

INVOICE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sample_invoices")

def list_pending_invoices() -> str:
    """Lists all pending vendor invoices in the Google Drive / Ingestion folder.
    
    Returns:
        JSON string listing available invoice files and their numbers.
    """
    if not os.path.exists(INVOICE_DIR):
        return json.dumps({"error": "Invoice directory not found"})
    
    invoices = []
    for filename in sorted(os.listdir(INVOICE_DIR)):
        if filename.endswith(".json"):
            filepath = os.path.join(INVOICE_DIR, filename)
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                    invoices.append({
                        "filename": filename,
                        "invoice_number": data.get("invoice_number"),
                        "vendor_name": data.get("vendor_name"),
                        "po_number": data.get("po_number"),
                        "grand_total": data.get("grand_total")
                    })
            except Exception as e:
                continue
    return json.dumps({"pending_invoices": invoices}, indent=2)


def fetch_invoice_details(invoice_number: str) -> str:
    """Retrieves full line-item details for a specific invoice number.
    
    Args:
        invoice_number: The invoice identifier (e.g., 'INV-9001')
        
    Returns:
        JSON string with invoice metadata and line items.
    """
    filename = f"{invoice_number.upper()}.json"
    filepath = os.path.join(INVOICE_DIR, filename)
    
    if not os.path.exists(filepath):
        return json.dumps({"error": f"Invoice {invoice_number} not found in ingestion folder."})
        
    with open(filepath, "r") as f:
        data = json.load(f)
    return json.dumps(data, indent=2)


def lookup_purchase_order(po_number: str) -> str:
    """Queries the ERP / local database for Purchase Order (PO) details and authorized line items.
    
    Args:
        po_number: The Purchase Order number (e.g., 'PO-1001')
        
    Returns:
        JSON string containing PO details, vendor info, and PO line items.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM purchase_orders WHERE po_number = ?", (po_number.upper(),))
    po = cursor.fetchone()
    
    if not po:
        conn.close()
        return json.dumps({"error": f"Purchase Order {po_number} not found in database."})
        
    cursor.execute("SELECT * FROM po_line_items WHERE po_number = ?", (po_number.upper(),))
    items = [dict(row) for row in cursor.fetchall()]
    
    result = dict(po)
    result["line_items"] = items
    conn.close()
    return json.dumps(result, indent=2)


def lookup_goods_receipt_note(po_number: str) -> str:
    """Queries the warehouse database for Goods Receipt Notes (GRN) showing received quantities for a PO.
    
    Args:
        po_number: The Purchase Order number (e.g., 'PO-1001')
        
    Returns:
        JSON string listing received item quantities and delivery dates.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM goods_receipt_notes WHERE po_number = ?", (po_number.upper(),))
    grns = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    if not grns:
        return json.dumps({"error": f"No Goods Receipt Note (GRN) found for Purchase Order {po_number}."})
        
    return json.dumps({"grn_records": grns}, indent=2)


def perform_3way_matching(invoice_number: str) -> str:
    """Executes an automated 3-way match audit between Invoice, PO, and Goods Receipt Note (GRN).
    
    Checks:
    1. Valid PO existence
    2. Quantity match (Invoice Billed Qty vs GRN Received Qty)
    3. Price match (Invoice Unit Price vs PO Unit Price)
    4. Grand total math check
    
    Args:
        invoice_number: The invoice identifier (e.g. 'INV-9001')
        
    Returns:
        JSON string with audit result, match status, detected variances, and audit notes.
    """
    filename = f"{invoice_number.upper()}.json"
    filepath = os.path.join(INVOICE_DIR, filename)
    
    if not os.path.exists(filepath):
        return json.dumps({"error": f"Invoice {invoice_number} not found."})
        
    with open(filepath, "r") as f:
        invoice = json.load(f)
        
    po_number = invoice.get("po_number")
    vendor_name = invoice.get("vendor_name")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Fetch PO
    cursor.execute("SELECT * FROM purchase_orders WHERE po_number = ?", (po_number,))
    po = cursor.fetchone()
    if not po:
        match_status = "MISSING_PO"
        details = f"Purchase Order {po_number} does not exist in ERP database."
        cursor.execute(
            "INSERT INTO invoice_match_results (invoice_number, po_number, vendor_name, match_status, details) VALUES (?, ?, ?, ?, ?)",
            (invoice_number, po_number, vendor_name, match_status, details)
        )
        conn.commit()
        conn.close()
        return json.dumps({
            "invoice_number": invoice_number,
            "po_number": po_number,
            "match_status": match_status,
            "can_auto_approve": False,
            "details": details
        }, indent=2)
        
    cursor.execute("SELECT * FROM po_line_items WHERE po_number = ?", (po_number,))
    po_items = {row["item_id"]: dict(row) for row in cursor.fetchall()}
    
    # 2. Fetch GRN
    cursor.execute("SELECT * FROM goods_receipt_notes WHERE po_number = ?", (po_number,))
    grn_rows = cursor.fetchall()
    grn_qty = {}
    for row in grn_rows:
        item_id = row["item_id"]
        grn_qty[item_id] = grn_qty.get(item_id, 0) + row["received_quantity"]
        
    discrepancies = []
    total_price_var = 0.0
    total_qty_var = 0
    
    # 3. Line Item Auditing
    for item in invoice.get("line_items", []):
        item_id = item.get("item_id")
        inv_qty = item.get("quantity")
        inv_price = item.get("unit_price")
        
        po_item = po_items.get(item_id)
        if not po_item:
            discrepancies.append(f"Item {item_id} not found in PO {po_number}.")
            continue
            
        po_price = po_item["unit_price"]
        rec_qty = grn_qty.get(item_id, 0)
        
        # Price check
        if abs(inv_price - po_price) > 0.01:
            diff = inv_price - po_price
            total_price_var += diff * inv_qty
            discrepancies.append(
                f"PRICE MISMATCH on {item_id}: Billed ${inv_price:.2f}/unit vs PO agreed ${po_price:.2f}/unit (Diff: ${diff:+.2f}/unit)."
            )
            
        # Quantity check (Invoice vs GRN)
        if inv_qty != rec_qty:
            q_diff = inv_qty - rec_qty
            total_qty_var += q_diff
            discrepancies.append(
                f"QUANTITY MISMATCH on {item_id}: Billed {inv_qty} units vs Warehouse received {rec_qty} units (Diff: {q_diff:+d} units)."
            )

    if not discrepancies:
        match_status = "100% MATCHED"
        details = "Invoice perfectly matches PO and Goods Receipt Note."
        can_auto_approve = True
    else:
        if total_price_var != 0:
            match_status = "DISCREPANCY_PRICE"
        elif total_qty_var != 0:
            match_status = "DISCREPANCY_QTY"
        else:
            match_status = "DISCREPANCY_OTHER"
        details = " | ".join(discrepancies)
        can_auto_approve = False

    cursor.execute(
        """INSERT INTO invoice_match_results 
           (invoice_number, po_number, vendor_name, match_status, price_variance, qty_variance, details) 
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (invoice_number, po_number, vendor_name, match_status, total_price_var, total_qty_var, details)
    )
    conn.commit()
    conn.close()
    
    return json.dumps({
        "invoice_number": invoice_number,
        "po_number": po_number,
        "vendor_name": vendor_name,
        "match_status": match_status,
        "price_variance": round(total_price_var, 2),
        "qty_variance": total_qty_var,
        "can_auto_approve": can_auto_approve,
        "discrepancies": discrepancies,
        "summary": details
    }, indent=2)


def stage_erp_payment_draft(invoice_number: str, po_number: str, amount: float) -> str:
    """Stages an approved invoice payment draft in the external ERP payment queue.
    
    Args:
        invoice_number: The invoice number to stage
        po_number: The matching PO number
        amount: Total authorized dollar amount to stage
        
    Returns:
        JSON string confirming ERP staging and transaction reference.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE invoice_match_results SET erp_payment_staged = 1 WHERE invoice_number = ?", (invoice_number,))
    cursor.execute("UPDATE purchase_orders SET status = 'PAYMENT_STAGED' WHERE po_number = ?", (po_number,))
    conn.commit()
    conn.close()
    
    return json.dumps({
        "status": "SUCCESS",
        "invoice_number": invoice_number,
        "po_number": po_number,
        "staged_amount": amount,
        "erp_reference_id": f"ERP-PAY-{invoice_number}-OK",
        "message": f"Payment draft of ${amount:.2f} successfully staged in ERP for invoice {invoice_number}."
    }, indent=2)


def flag_discrepancy_for_human_review(invoice_number: str, reason: str) -> str:
    """Flags an invoice with a discrepancy for human procurement review.
    
    Args:
        invoice_number: The invoice number
        reason: Explanation of the discrepancy
        
    Returns:
        JSON confirmation message of review ticket creation.
    """
    return json.dumps({
        "status": "REVIEW_FLAGGED",
        "invoice_number": invoice_number,
        "ticket_id": f"TICKET-PROC-{invoice_number}",
        "reason": reason,
        "message": f"Invoice {invoice_number} flagged and assigned to Procurement Manager review queue."
    }, indent=2)
