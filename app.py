"""
app.py — Limited Tender Manager — Flask Server
───────────────────────────────────────────────
Run:  python app.py
Then open browser at: http://localhost:3000

HOW TO ADD A NEW MODULE IN FUTURE:
  1. Create modules/your_module.py
  2. Add two lines below in the MODULES section:
       from modules.your_module import bp as your_bp
       app.register_blueprint(your_bp)
  3. Restart the server — done. No reinstall needed.

HOW TO CHANGE DB PASSWORD:
  Edit db.py — change DB_CONFIG['password']
  Restart server.
"""

import os
import json
import socket
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from db import init_db

app = Flask(__name__, static_folder='app', static_url_path='')
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024   # 50 MB upload limit
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'app', 'uploads')

# ── MODULES ───────────────────────────────────────────────────────────────────
# To add a new feature: import its blueprint and register it (2 lines)
# ─────────────────────────────────────────────────────────────────────────────
from modules.settings          import bp as settings_bp
from modules.budget_heads      import bp as budget_heads_bp
from modules.suppliers         import bp as suppliers_bp
from modules.work_orders       import bp as work_orders_bp
from modules.attachments       import bp as attachments_bp
from modules.comparative       import bp as comparative_bp
from modules.payments          import bp as payments_bp
from modules.delivery_ext      import bp as delivery_ext_bp
from modules.reports           import bp as reports_bp

app.register_blueprint(settings_bp,      url_prefix='/api/settings')
app.register_blueprint(budget_heads_bp,  url_prefix='/api/budget-heads')
app.register_blueprint(suppliers_bp,     url_prefix='/api/suppliers')
app.register_blueprint(work_orders_bp,   url_prefix='/api/work-orders')
app.register_blueprint(attachments_bp,   url_prefix='/api/attachments')
app.register_blueprint(comparative_bp,   url_prefix='/api/comparative')
app.register_blueprint(payments_bp,      url_prefix='/api/payments')
app.register_blueprint(delivery_ext_bp,  url_prefix='/api/extensions')
app.register_blueprint(reports_bp,       url_prefix='/api/reports')
# ─────────────────────────────────────────────────────────────────────────────
# FUTURE MODULES (uncomment + create file when ready):
# from modules.users    import bp as users_bp
# from modules.email    import bp as email_bp
# from modules.reminders import bp as reminders_bp
# app.register_blueprint(users_bp,     url_prefix='/api/users')
# ─────────────────────────────────────────────────────────────────────────────

# ── HEALTH CHECK ─────────────────────────────────────────────────────────────
@app.route('/api/health')
def health():
    try:
        from db import get_db
        with get_db() as (conn, cur):
            cur.execute('SELECT 1')
        return jsonify({'status': 'ok', 'db': 'connected', 'version': '2.0.0'})
    except Exception as e:
        return jsonify({'status': 'error', 'db': 'disconnected', 'error': str(e)}), 500

# ── SERVE UPLOADED FILES ──────────────────────────────────────────────────────
@app.route('/uploads/<int:wo_id>/<path:filename>')
def uploaded_file(wo_id, filename):
    folder = os.path.join(app.config['UPLOAD_FOLDER'], str(wo_id))
    return send_from_directory(folder, filename)

# ── SERVE FRONTEND ────────────────────────────────────────────────────────────
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    return send_from_directory(app.static_folder, 'index.html')

# ── STARTUP ──────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    # Create uploads folder if missing
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialise database tables
    try:
        init_db()
    except Exception as e:
        print(f'\n❌ Database error: {e}')
        print('   Check PostgreSQL is running and password in db.py is correct.\n')
        exit(1)

    # Get local network IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        local_ip = 'YOUR-SERVER-IP'

    PORT = 3000
    print()
    print('╔══════════════════════════════════════════════════════════╗')
    print('║     Limited Tender Manager — Server is RUNNING           ║')
    print('╠══════════════════════════════════════════════════════════╣')
    print(f'║  On this PC :  http://localhost:{PORT}                      ║')
    print(f'║  Network    :  http://{local_ip}:{PORT}                 ║')
    print('║                                                          ║')
    print('║  Share the Network address with your team.               ║')
    print('║  Keep this window open while server is running.          ║')
    print('║  Press Ctrl+C to stop.                                   ║')
    print('╚══════════════════════════════════════════════════════════╝')
    print()
    print('Loaded modules:')
    print('  ✅ Settings, Budget Heads, Suppliers')
    print('  ✅ Work Orders (+ Activity Log, CSV Export)')
    print('  ✅ Attachments, Comparative, Payments')
    print('  ✅ Delivery Extensions, Reports')
    print()

    app.run(host='0.0.0.0', port=PORT, debug=False)
