"""
generate_data.py
Creates / overwrites data/finance.db with mock GL entries, vendor invoices,
and reconciliation records for the ERP reconciliation dashboard.
"""
import sqlite3
import os
from datetime import datetime, timedelta

# ----------------------------------------------------------------------
# 1. Setup
# ----------------------------------------------------------------------
os.makedirs("data", exist_ok=True)
DB_PATH = "data/finance.db"

# Use a fixed "today" so the data is deterministic regardless of when you run it
TODAY = datetime(2026, 8, 11)   # match the date in your project (or set dynamically if you prefer)

# ----------------------------------------------------------------------
# 2. Helper: database connection
# ----------------------------------------------------------------------
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

# ----------------------------------------------------------------------
# 3. Create tables and views
# ----------------------------------------------------------------------
def create_schema(cursor):
    cursor.executescript("""
        DROP VIEW IF EXISTS discrepancies;
        DROP TABLE IF EXISTS reconciliation;
        DROP TABLE IF EXISTS vendor_invoices;
        DROP TABLE IF EXISTS gl_entries;

        CREATE TABLE gl_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_date TEXT NOT NULL,
            account_code TEXT,
            description TEXT,
            debit REAL DEFAULT 0,
            credit REAL DEFAULT 0,
            reconciled INTEGER DEFAULT 0
        );

        CREATE TABLE vendor_invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_date TEXT NOT NULL,
            due_date TEXT NOT NULL,
            vendor_name TEXT,
            invoice_number TEXT UNIQUE,
            amount REAL NOT NULL,
            status TEXT DEFAULT 'open',   -- 'open','paid','disputed'
            gl_entry_id INTEGER,
            FOREIGN KEY (gl_entry_id) REFERENCES gl_entries(id)
        );

        CREATE TABLE reconciliation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gl_entry_id INTEGER NOT NULL,
            invoice_id INTEGER NOT NULL,
            match_date TEXT,
            FOREIGN KEY (gl_entry_id) REFERENCES gl_entries(id),
            FOREIGN KEY (invoice_id) REFERENCES vendor_invoices(id)
        );

        CREATE VIEW discrepancies AS
        SELECT
            vi.id AS invoice_id,
            vi.invoice_number,
            vi.vendor_name,
            vi.amount AS invoice_amount,
            gl.credit AS gl_amount,
            CASE
                WHEN gl.id IS NULL THEN 'No matching GL'
                WHEN ABS(vi.amount - gl.amount) > 0.01 THEN 'Amount mismatch'
                ELSE NULL
            END AS issue
        FROM vendor_invoices vi
        LEFT JOIN gl_entries gl ON vi.gl_entry_id = gl.id
        WHERE vi.status != 'paid'
          AND (gl.id IS NULL OR ABS(vi.amount - gl.amount) > 0.01);
    """)

# ----------------------------------------------------------------------
# 4. Insert GL entries (~50, with exact values)
# ----------------------------------------------------------------------
def insert_gl_entries(cursor):
    """Insert a mix of reconciled and unreconciled GL entries."""
    entries = [
        # (days_offset_from_today, account_code, description, debit, credit, reconciled)
        # Negative days = in the past
        (-180, '4000-AP', 'Office supplies', 0, 1200.00, 0),
        (-175, '1000-CASH', 'Bank deposit', 5000.00, 0, 0),
        (-170, '4000-AP', 'Consulting - Accenture', 0, 8500.00, 1),
        (-165, '4000-AP', 'Software license', 0, 3200.00, 0),
        (-160, '4000-AP', 'Travel - Delta', 0, 1450.50, 0),
        (-155, '4000-AP', 'Marketing materials', 0, 890.00, 0),
        (-150, '2000-AR', 'Client payment - ABC', 7500.00, 0, 0),
        (-145, '4000-AP', 'Hardware - Dell', 0, 2200.00, 1),
        (-140, '4000-AP', 'Cleaning services', 0, 450.00, 0),
        (-135, '4000-AP', 'Internet - Comcast', 0, 299.99, 0),
        (-130, '1000-CASH', 'Cash withdrawal', 0, 2000.00, 0),
        (-125, '4000-AP', 'Legal fees', 0, 5600.00, 0),
        (-120, '4000-AP', 'Subscription - Salesforce', 0, 1200.00, 1),
        (-115, '4000-AP', 'Utilities - Edison', 0, 780.30, 0),
        (-110, '2000-AR', 'Client payment - XYZ', 4300.00, 0, 0),
        (-105, '4000-AP', 'Training - Coursera', 0, 399.00, 0),
        (-100, '4000-AP', 'Office rent - WeWork', 0, 15000.00, 1),
        (-95, '4000-AP', 'Courier - FedEx', 0, 125.75, 0),
        (-90, '4000-AP', 'Insurance - AIG', 0, 3400.00, 0),
        (-85, '4000-AP', 'Recruitment fee', 0, 2500.00, 0),
        (-80, '2000-AR', 'Client payment - GlobalTech', 12000.00, 0, 0),
        (-75, '4000-AP', 'Cloud hosting - AWS', 0, 2300.50, 1),
        (-70, '4000-AP', 'Repairs - Handyman', 0, 680.00, 0),
        (-65, '4000-AP', 'Membership - SHRM', 0, 210.00, 0),
        (-60, '4000-AP', 'Tax consultancy - PwC', 0, 4800.00, 0),
        (-55, '1000-CASH', 'Petty cash', 0, 500.00, 0),
        (-50, '4000-AP', 'Employee gifts', 0, 950.00, 0),
        (-45, '4000-AP', 'Software - Adobe', 0, 599.99, 1),
        (-40, '4000-AP', 'Maintenance - HVAC', 0, 1100.00, 0),
        (-35, '4000-AP', 'Travel - Marriott', 0, 3200.00, 0),
        (-30, '2000-AR', 'Client payment - Acme', 9800.00, 0, 0),
        (-25, '4000-AP', 'Supplies - Office Depot', 0, 230.45, 0),
        (-20, '4000-AP', 'Consulting - Deloitte', 0, 7200.00, 0),
        (-15, '4000-AP', 'Advertising - Google Ads', 0, 1500.00, 0),
        (-10, '4000-AP', 'Late payment interest', 0, 45.00, 0),
        (-5,  '4000-AP', 'Misc expense', 0, 99.00, 0),
        # Additional entries to reach ~50
        (-178, '5000-EXP', 'Depreciation', 2000.00, 0, 1),
        (-172, '5000-EXP', 'Meals & entertainment', 0, 350.00, 0),
        (-168, '2000-AR', 'Invoice #1001', 1800.00, 0, 1),
        (-162, '1000-CASH', 'Bank charges', 0, 30.00, 0),
        (-158, '4000-AP', 'Water delivery', 0, 80.00, 0),
        (-152, '5000-EXP', 'Charity donation', 0, 500.00, 0),
        (-148, '2000-AR', 'Invoice #1002', 2500.00, 0, 1),
        (-142, '4000-AP', 'Telephone - AT&T', 0, 410.00, 0),
        (-136, '5000-EXP', 'Office renovation', 0, 12000.00, 1),
        (-128, '2000-AR', 'Refund from vendor', 800.00, 0, 0),
        (-122, '4000-AP', 'Security monitoring', 0, 99.00, 0),
        (-116, '4000-AP', 'Courier - UPS', 0, 67.35, 0),
        (-108, '5000-EXP', 'Training materials', 0, 275.00, 0),
        (-98, '2000-AR', 'Invoice #1003', 4100.00, 0, 1),
    ]

    for days_ago, acct, desc, debit, credit, reconciled in entries:
        entry_date = (TODAY + timedelta(days=days_ago)).strftime('%Y-%m-%d')
        cursor.execute(
            "INSERT INTO gl_entries (entry_date, account_code, description, debit, credit, reconciled) VALUES (?,?,?,?,?,?)",
            (entry_date, acct, desc, debit, credit, reconciled)
        )

# ----------------------------------------------------------------------
# 5. Insert vendor invoices and create known scenarios
# ----------------------------------------------------------------------
def insert_vendor_invoices(cursor):
    """
    We'll insert invoices manually, then link them to specific GL entries
    to create three scenarios:
      - Paid + fully matched (no discrepancy, not outstanding)
      - Open + fully matched (outstanding, no discrepancy)
      - Open + amount mismatch (outstanding + discrepancy)
      - Open + no GL entry at all (outstanding + discrepancy)
    Also vary due dates to populate all aging buckets.
    """
    # First, fetch the IDs of the GL entries we want to link to.
    # We'll use known descriptions to find them reliably.
    cursor.execute("SELECT id, description FROM gl_entries")
    gl_map = {}
    for row in cursor.fetchall():
        # Use description as key; if duplicates, we'll need something else, but our descriptions are unique.
        gl_map[row[1]] = row[0] # map description -> id

    # Define invoices: (invoice_date_offset, due_date_offset, vendor, inv_num, amount, status, gl_desc_or_None)
    # gl_desc_or_None: the description of the GL entry to link, or None for no link.
    invoices = [
        # ---- Paid and fully matched (status='paid', linked to correct GL) ----
        (-170, -140, 'Accenture', 'INV-1001', 8500.00, 'paid', 'Consulting - Accenture'),
        (-145, -115, 'Dell', 'INV-1002', 2200.00, 'paid', 'Hardware - Dell'),
        (-120, -90, 'Salesforce', 'INV-1003', 1200.00, 'paid', 'Subscription - Salesforce'),
        (-100, -70, 'WeWork', 'INV-1004', 15000.00, 'paid', 'Office rent - WeWork'),
        (-75, -45, 'AWS', 'INV-1005', 2300.50, 'paid', 'Cloud hosting - AWS'),
        (-45, -15, 'Adobe', 'INV-1006', 599.99, 'paid', 'Software - Adobe'),

        # ---- Open, fully matched (linked to correct GL, amounts match) ----
        (-165, -135, 'Microsoft', 'INV-2001', 3200.00, 'open', 'Software license'),
        (-140, -110, 'Comcast', 'INV-2002', 299.99, 'open', 'Internet - Comcast'),
        (-125, -95, 'Baker McKenzie', 'INV-2003', 5600.00, 'open', 'Legal fees'),
        (-90, -60, 'AIG', 'INV-2004', 3400.00, 'open', 'Insurance - AIG'),
        (-60, -30, 'PwC', 'INV-2005', 4800.00, 'open', 'Tax consultancy - PwC'),
        (-35, -5,  'Marriott', 'INV-2006', 3200.00, 'open', 'Travel - Marriott'),
        (-20, 10,  'Deloitte', 'INV-2007', 7200.00, 'open', 'Consulting - Deloitte'),  # due 10 days from now -> 0-30 bucket
        (-15, 15,  'Google Ads', 'INV-2008', 1500.00, 'open', 'Advertising - Google Ads'), # future due date

        # ---- Open, amount mismatch (linked to GL, but amounts differ) ----
        (-180, -160, 'Staples', 'INV-3001', 1250.00, 'open', 'Office supplies'),   # GL has 1200
        (-155, -135, 'Vistaprint', 'INV-3002', 890.50, 'open', 'Marketing materials'), # GL 890.00
        (-130, -110, 'Bank Withdrawal', 'INV-3003', 2050.00, 'open', 'Cash withdrawal'), # GL 2000
        (-85, -65, 'Indeed', 'INV-3004', 2499.99, 'open', 'Recruitment fee'),      # GL 2500
        (-50, -30, 'Amazon', 'INV-3005', 1000.00, 'open', 'Employee gifts'),       # GL 950
        (-10, 5,   'Interest', 'INV-3006', 45.50, 'open', 'Late payment interest'), # GL 45.00

        # ---- Open, no GL entry at all (gl_desc = None) ----
        (-160, -140, 'Delta', 'INV-4001', 1450.50, 'open', None),       # Travel - Delta (GL exists but not linked)
        (-115, -95, 'Edison', 'INV-4002', 780.30, 'open', None),        # Utilities - Edison
        (-105, -85, 'Coursera', 'INV-4003', 399.00, 'open', None),      # Training
        (-95, -75, 'FedEx', 'INV-4004', 125.75, 'open', None),          # Courier
        (-70, -50, 'SHRM', 'INV-4005', 210.00, 'open', None),           # Membership
        (-40, -20, 'HVAC', 'INV-4006', 1100.00, 'open', None),          # Maintenance
        (-30, -10, 'Acme', 'INV-4007', 230.45, 'open', None),           # Supplies (but we have Office Depot GL, but not linked)
        # Additional to reach ~30 total: add one more no-GL
        (-5, 15, 'Misc Vendor', 'INV-4008', 99.00, 'open', None),
    ]

    for inv_days_ago, due_days_offset, vendor, inv_num, amount, status, gl_desc in invoices:
        inv_date = (TODAY + timedelta(days=inv_days_ago)).strftime('%Y-%m-%d')
        due_date = (TODAY + timedelta(days=due_days_offset)).strftime('%Y-%m-%d')
        gl_id = None
        if gl_desc is not None:
            gl_id = gl_map.get(gl_desc)   
        else:
            print(f"Warning: GL description '{gl_desc}' not found; invoice {inv_num} will have no GL link.")

        cursor.execute(
            "INSERT INTO vendor_invoices (invoice_date, due_date, vendor_name, invoice_number, amount, status, gl_entry_id) VALUES (?,?,?,?,?,?,?)",
            (inv_date, due_date, vendor, inv_num, amount, status, gl_id)
        )

# ----------------------------------------------------------------------
# 6. Insert reconciliation records for paid invoices (optional but realistic)
# ----------------------------------------------------------------------
def insert_reconciliation(cursor):
    """For every paid invoice with a gl_entry_id, create a reconciliation record."""
    cursor.execute("""
        INSERT INTO reconciliation (gl_entry_id, invoice_id, match_date)
        SELECT vi.gl_entry_id, vi.id, vi.invoice_date
        FROM vendor_invoices vi
        WHERE vi.status = 'paid' AND vi.gl_entry_id IS NOT NULL
    """)

# ----------------------------------------------------------------------
# 7. Main execution
# ----------------------------------------------------------------------
def main():
    conn = get_connection()
    cursor = conn.cursor()
    create_schema(cursor)
    insert_gl_entries(cursor)
    insert_vendor_invoices(cursor)
    insert_reconciliation(cursor)
    conn.commit()
    conn.close()
    print(f"Database created at {DB_PATH} with mock data.")

if __name__ == "__main__":
    main()