"""modules/payments.py — Payment documents (completion cert, invoices, vouchers)"""
from flask import Blueprint, request, jsonify
from psycopg2.extras import Json
from db import get_db

bp = Blueprint('payments', __name__)

@bp.route('/<int:wo_id>', methods=['GET'])
def get_all(wo_id):
    with get_db() as (conn, cur):
        cur.execute('SELECT * FROM payment_documents WHERE wo_id=%s ORDER BY created_at', [wo_id])
        rows = []
        for r in cur.fetchall():
            r = dict(r)
            r['created_at'] = r['created_at'].isoformat()
            r['updated_at'] = r['updated_at'].isoformat()
            rows.append(r)
        return jsonify(rows)

@bp.route('/<int:wo_id>', methods=['POST'])
def create(wo_id):
    d = request.json
    with get_db() as (conn, cur):
        cur.execute("""
            INSERT INTO payment_documents (wo_id, doc_type, doc_data, status)
            VALUES (%s,%s,%s,'draft') RETURNING *
        """, [wo_id, d.get('doc_type'), Json(d.get('doc_data', {}))])
        row = dict(cur.fetchone())
        row['created_at'] = row['created_at'].isoformat()
        row['updated_at'] = row['updated_at'].isoformat()
        return jsonify(row)

@bp.route('/doc/<int:id>', methods=['PUT'])
def update(id):
    d = request.json
    with get_db() as (conn, cur):
        cur.execute(
            'UPDATE payment_documents SET doc_data=%s, updated_at=NOW() WHERE id=%s RETURNING *',
            [Json(d.get('doc_data', {})), id]
        )
        row = dict(cur.fetchone())
        row['created_at'] = row['created_at'].isoformat()
        row['updated_at'] = row['updated_at'].isoformat()
        return jsonify(row)

@bp.route('/doc/<int:id>/status', methods=['PATCH'])
def update_status(id):
    d = request.json
    with get_db() as (conn, cur):
        cur.execute(
            'UPDATE payment_documents SET status=%s, updated_at=NOW() WHERE id=%s RETURNING wo_id, status',
            [d.get('status'), id]
        )
        row = cur.fetchone()
        cur.execute(
            'INSERT INTO wo_activity_log (wo_id,user_name,action,detail) VALUES (%s,%s,%s,%s)',
            [row['wo_id'], d.get('userName','System'), 'Payment Doc Status', f"→ {d.get('status')}"]
        )
        return jsonify({'ok': True})

@bp.route('/doc/<int:id>', methods=['DELETE'])
def delete(id):
    with get_db() as (conn, cur):
        cur.execute('DELETE FROM payment_documents WHERE id=%s', [id])
        return jsonify({'ok': True})
