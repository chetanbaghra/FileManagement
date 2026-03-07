from flask import Blueprint, request, jsonify
from db import get_db

bp = Blueprint('budget_heads', __name__)

@bp.route('/', methods=['GET'])
def get_all():
    with get_db() as (conn, cur):
        cur.execute('SELECT * FROM budget_heads ORDER BY type, label')
        return jsonify(cur.fetchall())

@bp.route('/', methods=['POST'])
def create():
    d = request.json
    with get_db() as (conn, cur):
        cur.execute(
            'INSERT INTO budget_heads (type,label,bh,proj,hoa) VALUES (%s,%s,%s,%s,%s) RETURNING *',
            [d.get('type'), d.get('label'), d.get('bh'), d.get('proj'), d.get('hoa')]
        )
        return jsonify(cur.fetchone())

@bp.route('/<int:id>', methods=['DELETE'])
def delete(id):
    with get_db() as (conn, cur):
        cur.execute('DELETE FROM budget_heads WHERE id = %s', [id])
        return jsonify({'ok': True})
