# My agent: Smart Procurement & Vendor Management Agent
One-liner: A conversational agent that helps procurement managers audit vendor invoices, perform 3-way matching, track vendor catalogs, and stage payment approvals.

Tool coverage:
- Memory: Remembers vendor payment terms, manager approval thresholds, and preferred procurement policies across sessions.
- Tools: list_pending_invoices, fetch_invoice_details, perform_3way_matching, stage_erp_payment_draft, flag_discrepancy_for_human_review.
- Catalog/UI: Vendor catalog, Purchase Orders, and 3-Way Match Audit Reports rendered as A2UI rich cards and tables.
- Image gen: Generates vendor product previews and receipt visuals using gemini-3.1-flash-lite-image.
- Sandbox: Audits complex line-item math, tax calculations, and price variance percentages using AgentEngineSandboxCodeExecutor.

Recommended for every project: memory, storage, tools, image generation, A2UI
Agent-specific / stretch: Code sandbox for variance calculations, Firestore for persistent vendor records, Cloud Storage for assets, A2UI rich cards.
