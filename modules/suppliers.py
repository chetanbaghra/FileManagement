from flask import Blueprint, request, jsonify
from db import get_db

bp = Blueprint('suppliers', __name__)

@bp.route('/', methods=['GET'])
def get_all():
    with get_db() as (conn, cur):
        cur.execute('SELECT * FROM suppliers ORDER BY name')
        return jsonify(cur.fetchall())

@bp.route('/', methods=['POST'])
def create():
    d = request.json
    with get_db() as (conn, cur):
        cur.execute(
            'INSERT INTO suppliers (name,contact,email,address,gstin) VALUES (%s,%s,%s,%s,%s) RETURNING *',
            [d.get('name'), d.get('contact'), d.get('email'), d.get('address'), d.get('gstin')]
        )
        return jsonify(cur.fetchone())

@bp.route('/<int:id>', methods=['PUT'])
def update(id):
    d = request.json
    with get_db() as (conn, cur):
        cur.execute(
            'UPDATE suppliers SET name=%s,contact=%s,email=%s,address=%s,gstin=%s WHERE id=%s RETURNING *',
            [d.get('name'), d.get('contact'), d.get('email'), d.get('address'), d.get('gstin'), id]
        )
        return jsonify(cur.fetchone())

@bp.route('/<int:id>', methods=['DELETE'])
def delete(id):
    with get_db() as (conn, cur):
        cur.execute('DELETE FROM suppliers WHERE id = %s', [id])
        return jsonify({'ok': True})
