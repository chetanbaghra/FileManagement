"""modules/delivery_ext.py — Delivery date extensions"""
from flask import Blueprint, request, jsonify
from db import get_db

bp = Blueprint('delivery_ext', __name__)

@bp.route('/<int:wo_id>', methods=['GET'])
def get_all(wo_id):
    with get_db() as (conn, cur):
        cur.execute('SELECT * FROM delivery_extensions WHERE wo_id=%s ORDER BY created_at', [wo_id])
        rows = []
        for r in cur.fetchall():
            r = dict(r)
            r['created_at']    = r['created_at'].isoformat()
            r['original_date'] = str(r['original_date']) if r['original_date'] else None
            r['extended_date'] = str(r['extended_date']) if r['extended_date'] else None
            rows.append(r)
        return jsonify(rows)

@bp.route('/<int:wo_id>', methods=['POST'])
def create(wo_id):
    d = request.json
    with get_db() as (conn, cur):
        cur.execute("""
            INSERT INTO delivery_extensions (wo_id, original_date, extended_date, reason, approved_by)
            VALUES (%s,%s,%s,%s,%s) RETURNING *
        """, [wo_id, d.get('original_date'), d.get('extended_date'), d.get('reason'), d.get('approved_by')])
        cur.execute(
            'INSERT INTO wo_activity_log (wo_id,user_name,action,detail) VALUES (%s,%s,%s,%s)',
            [wo_id, d.get('userName','System'), 'Delivery Extended',
             f"Extended to: {d.get('extended_date')}. Reason: {d.get('reason','')}"]
        )
        row = dict(cur.fetchone())
        row['created_at']    = row['created_at'].isoformat()
        row['original_date'] = str(row['original_date']) if row['original_date'] else None
        row['extended_date'] = str(row['extended_date']) if row['extended_date'] else None
        return jsonify(row)

@bp.route('/<int:id>', methods=['DELETE'])
def delete(id):
    with get_db() as (conn, cur):
        cur.execute('DELETE FROM delivery_extensions WHERE id=%s', [id])
        return jsonify({'ok': True})
