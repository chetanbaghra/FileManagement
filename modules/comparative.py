"""modules/comparative.py — Post-bid comparative statement"""
from flask import Blueprint, request, jsonify
from psycopg2.extras import Json
from db import get_db

bp = Blueprint('comparative', __name__)

@bp.route('/<int:wo_id>', methods=['GET'])
def get_one(wo_id):
    with get_db() as (conn, cur):
        cur.execute('SELECT * FROM comparative_statements WHERE wo_id=%s ORDER BY created_at DESC LIMIT 1', [wo_id])
        row = cur.fetchone()
        if row:
            row = dict(row)
            row['created_at'] = row['created_at'].isoformat()
            row['updated_at'] = row['updated_at'].isoformat()
        return jsonify(row)

@bp.route('/<int:wo_id>', methods=['POST'])
def save(wo_id):
    d = request.json
    with get_db() as (conn, cur):
        cur.execute('SELECT id FROM comparative_statements WHERE wo_id=%s', [wo_id])
        existing = cur.fetchone()
        if existing:
            cur.execute("""
                UPDATE comparative_statements
                SET bid_data=%s, recommended=%s, notes=%s, updated_at=NOW()
                WHERE wo_id=%s RETURNING id
            """, [Json(d.get('bid_data',{})), Json(d.get('recommended')), d.get('notes'), wo_id])
        else:
            cur.execute("""
                INSERT INTO comparative_statements (wo_id, bid_data, recommended, notes)
                VALUES (%s,%s,%s,%s) RETURNING id
            """, [wo_id, Json(d.get('bid_data',{})), Json(d.get('recommended')), d.get('notes')])
        cur.execute(
            'INSERT INTO wo_activity_log (wo_id,user_name,action,detail) VALUES (%s,%s,%s,%s)',
            [wo_id, d.get('userName','System'), 'Comparative Statement Saved',
             f"L1: {d.get('bid_data',{}).get('l1Bidder','—')}"]
        )
        return jsonify({'ok': True, 'id': cur.fetchone()['id']})
