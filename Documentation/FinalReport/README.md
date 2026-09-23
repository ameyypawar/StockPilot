# Final Report

`InventoryManagementSystem_FinalReport.docx` is the full project report for
**StockPilot — Inventory Management System**: title page, abstract, a
table-of-contents field, and chapters on Introduction, Requirements, Design
(architecture, ER diagram, data dictionary, routes), Implementation
(console/ASP.NET/PWA), Testing (from the actual test run results),
Setup and Conclusion & Future Scope, plus references. It is generated, not
hand-edited — after opening it in Word, press **F9** (or right-click the
table of contents → **Update Field**) to fill in the TOC page numbers.
Regenerate the document itself after any change to the code, the seed data,
`tools/doc_config.py` or `tools/test_results.json` with:

```
tools/.venv/bin/python tools/build_docs.py
```
