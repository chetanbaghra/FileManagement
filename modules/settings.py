from flask import Blueprint, request, jsonify
from db import get_db

bp = Blueprint('settings', __name__)

@bp.route('/', methods=['GET'])
def get_settings():
    with get_db() as (conn, cur):
        cur.execute('SELECT data FROM settings WHERE id = 1')
        row = cur.fetchone()
        return jsonify(row['data'] if row else {})

@bp.route('/', methods=['POST'])
def save_settings():
    with get_db() as (conn, cur):
        cur.execute("""
            INSERT INTO settings (id, data, updated_at) VALUES (1, %s, NOW())
            ON CONFLICT (id) DO UPDATE SET data = %s, updated_at = NOW()
        """, [request.json, request.json])
        return jsonify({'ok': True})
