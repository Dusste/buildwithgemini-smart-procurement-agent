# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.genai import types

from app.database import init_db
from app.tools import (
    list_pending_invoices,
    fetch_invoice_details,
    lookup_purchase_order,
    lookup_goods_receipt_note,
    perform_3way_matching,
    stage_erp_payment_draft,
    flag_discrepancy_for_human_review,
)
from app.firestore_tools import (
    seed_firestore_data,
    get_vendor_catalog_from_firestore,
    update_vendor_inventory_in_firestore,
)
from app.image_tool import generate_vendor_item_image
from app.a2ui_utils import a2ui_callback

# Ensure local database schema and tables are initialized on agent startup
init_db()

MODEL = "gemini-3.8-flash"

SYSTEM_INSTRUCTION = """You are the Smart Procurement & Invoice Matching Agent for the Vendor Management System (VMS).

Your core responsibility is to automate vendor invoice audit and 3-way matching between:
1. Vendor Invoices (extracted from Google Drive / Ingestion)
2. Purchase Orders (PO) in the local ERP database
3. Goods Receipt Notes (GRN) from warehouse receiving logs
4. Live Vendor Catalog & Inventory in Google Cloud Firestore

Workflow Protocol:
1. When asked to check pending invoices, use `list_pending_invoices` to list incoming files.
2. For an invoice, use `fetch_invoice_details` to inspect line items, vendor name, PO number, and grand total.
3. Use `perform_3way_matching(invoice_number)` to perform an automated line-item comparison against PO unit prices and GRN received quantities.
4. If the match result is `100% MATCHED` and `can_auto_approve` is True:
   - Call `stage_erp_payment_draft` with the invoice number, PO number, and grand total.
   - Summarize the successful match and ERP staging confirmation clearly.
5. If a discrepancy is detected (`DISCREPANCY_PRICE`, `DISCREPANCY_QTY`, `MISSING_PO`, `MISSING_GRN`):
   - Call `flag_discrepancy_for_human_review` with the detailed variance breakdown.
   - Present a clear, structured breakdown report highlighting exact unit price or quantity variances for human procurement manager review.
6. Use `get_vendor_catalog_from_firestore` or `update_vendor_inventory_in_firestore` to interact with live vendor records.
7. Use `generate_vendor_item_image` when a visual receipt or product item image is requested.

Maintain high accuracy, flag all financial variances, and never auto-stage payments for mismatched invoices.
"""

root_agent = Agent(
    name="smart_procurement_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=SYSTEM_INSTRUCTION,
    tools=[
        list_pending_invoices,
        fetch_invoice_details,
        lookup_purchase_order,
        lookup_goods_receipt_note,
        perform_3way_matching,
        stage_erp_payment_draft,
        flag_discrepancy_for_human_review,
        seed_firestore_data,
        get_vendor_catalog_from_firestore,
        update_vendor_inventory_in_firestore,
        generate_vendor_item_image,
    ],
    code_executor=AgentEngineSandboxCodeExecutor(),
    after_model_callback=a2ui_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
