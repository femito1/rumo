"""MBC monthly-closing automation (v0).

Pulls the revenue side of the MBC closing workbook live from the Juritis
LegalDesk OData API and emits a structured ``data.json`` that the dashboard
renders 1:1 against the original spreadsheet tabs.
"""

__version__ = "0.1.0"
