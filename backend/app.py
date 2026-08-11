"""
app.py
Flask backend for the ERP reconciliation dashboard.
Serves static frontend files and exposes three API endpoints.
"""
import sqlite3
import os
from flask import Flask, jsonify, send_from_directory

# ----------------------------------------------------------------------
# 1. App setup – point static folder to ../frontend so index.html loads
# ----------------------------------------------------------------------
app = Flask(__name__,
            static_folder='../frontend',    # serve CSS/JS from the frontend folder
            static_url_path='')             # so files are accessible at /style.css, etc.

# ----------------------------------------------------------------------
# 2. Database helper
# ----------------------------------------------------------------------
def get_db():
    """Return a connection to the SQLite database."""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'finance.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row   # allow dict-like access
    return conn

# ----------------------------------------------------------------------
# 3. API endpoints
# ----------------------------------------------------------------------
@app.route('/api/outstanding-invoices')
def outstanding_invoices():
    """Return all open vendor invoices."""
    db = get_db()
    try:
        rows = db.execute("SELECT * FROM vendor_invoices WHERE status='open'").fetchall()
        invoices = [dict(r) for r in rows]
        # Add a computed 'days_overdue' field for the frontend
        for inv in invoices:
            # If due_date is in the future, days_overdue will be negative; we'll floor to 0.
            db.execute("SELECT julianday('now') - julianday(?) AS days_overdue", (inv['due_date'],))
            inv['days_overdue'] = max(0, int(db.execute("SELECT julianday('now') - julianday(?) AS d", (inv['due_date'],)).fetchone()['d']))
        return jsonify(invoices)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/api/discrepancies')
def discrepancies():
    """Return all flagged discrepancies (no matching GL or amount mismatch)."""
    db = get_db()
    try:
        rows = db.execute("SELECT * FROM discrepancies").fetchall()
        return jsonify([dict(r) for r in rows])
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/api/aging-summary')
def aging_summary():
    """Return open invoices grouped by overdue days buckets."""
    db = get_db()
    try:
        row = db.execute("""
            SELECT
                SUM(CASE WHEN (julianday('now') - julianday(due_date)) BETWEEN 0 AND 30 THEN 1 ELSE 0 END) AS bucket_0_30,
                SUM(CASE WHEN (julianday('now') - julianday(due_date)) BETWEEN 31 AND 60 THEN 1 ELSE 0 END) AS bucket_31_60,
                SUM(CASE WHEN (julianday('now') - julianday(due_date)) BETWEEN 61 AND 90 THEN 1 ELSE 0 END) AS bucket_61_90,
                SUM(CASE WHEN (julianday('now') - julianday(due_date)) > 90 THEN 1 ELSE 0 END) AS bucket_90_plus
            FROM vendor_invoices WHERE status='open'
        """).fetchone()
        return jsonify(dict(row))
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

# ----------------------------------------------------------------------
# 4. Serve the frontend
# ----------------------------------------------------------------------
@app.route('/')
def index():
    """Serve the main dashboard page."""
    return send_from_directory(app.static_folder, 'index.html')

# ----------------------------------------------------------------------
# 5. Run the app
# ----------------------------------------------------------------------
if __name__ == '__main__':
    # debug=True reloads on changes; remove in production
    app.run(debug=True, port=5000)