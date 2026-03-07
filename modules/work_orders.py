import io
import csv
from flask import Blueprint, request, jsonify, Response
from db import get_db

bp = Blueprint('work_orders', __name__)

def _log(cur, wo_id, user_name, action, detail=None):
    try:
        cur.execute(
            'INSERT INTO wo_activity_log (wo_id, user_name, action, detail) VALUES (%s,%s,%s,%s)',
            [wo_id, user_name or 'System', action, detail]
        )
    except Exception:
        pass  # logging is non-critical

# GET all — dashboard list (no heavy form_data)
@bp.route('/', methods=['GET'])
def get_all():
    with get_db() as (conn, cur):
        cur.execute("""
            SELECT
                id, ref_no, work_name, div_code, financial_year, serial_no,
                budget_type, budget_head, estimated_cost, delivery_value, delivery_unit,
                progress, saved_at, updated_at,
                (SELECT COUNT(*) FROM attachments a WHERE a.wo_id = work_orders.id) AS attachment_count
            FROM work_orders
            ORDER BY saved_at DESC
        """)
        rows = cur.fetchall()
        # Convert decimals/dates to JSON-safe types
        result = []
        for r in rows:
            r = dict(r)
            r['estimated_cost'] = float(r['estimated_cost']) if r['estimated_cost'] else 0
            r['saved_at']   = r['saved_at'].isoformat()   if r['saved_at']   else None
            r['updated_at'] = r['updated_at'].isoformat() if r['updated_at'] else None
            r['attachment_count'] = int(r['attachment_count'])
            result.append(r)
        return jsonify(result)

# GET single with full form_data
@bp.route('/<int:id>', methods=['GET'])
def get_one(id):
    with get_db() as (conn, cur):
        cur.execute('SELECT * FROM work_orders WHERE id = %s', [id])
        row = cur.fetchone()
        if not row:
            return jsonify({'error': 'Not found'}), 404
        row = dict(row)
        row['estimated_cost'] = float(row['estimated_cost']) if row['estimated_cost'] else 0
        row['saved_at']   = row['saved_at'].isoformat()   if row['saved_at']   else None
        row['updated_at'] = row['updated_at'].isoformat() if row['updated_at'] else None
        return jsonify(row)

# POST create
@bp.route('/', methods=['POST'])
def create():
    d    = request.json
    form = d.get('form', {})
    div  = d.get('divCode', '')
    ref  = f"{div}/{form.get('financialYear','')}/{form.get('serialNo','__')}"
    with get_db() as (conn, cur):
        cur.execute("""
            INSERT INTO work_orders
              (ref_no, work_name, div_code, financial_year, serial_no, budget_type,
               budget_head, estimated_cost, delivery_value, delivery_unit, form_data, progress)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING id, ref_no, work_name, saved_at, updated_at
        """, [
            ref, form.get('workName'), div, form.get('financialYear'), form.get('serialNo'),
            form.get('budgetType'), form.get('budgetHead'),
            float(form.get('estimatedCost') or 0),
            form.get('deliveryValue'), form.get('deliveryUnit'),
            psycopg2_json(form), psycopg2_json(d.get('progress', {}))
        ])
        row = cur.fetchone()
        _log(cur, row['id'], d.get('userName'), 'Created', f'WO created: {ref}')
        row = dict(row)
        row['saved_at']   = row['saved_at'].isoformat()
        row['updated_at'] = row['updated_at'].isoformat()
        return jsonify(row)

# PUT update form data
@bp.route('/<int:id>', methods=['PUT'])
def update(id):
    d    = request.json
    form = d.get('form', {})
    div  = d.get('divCode', '')
    ref  = f"{div}/{form.get('financialYear','')}/{form.get('serialNo','__')}"
    with get_db() as (conn, cur):
        cur.execute("""
            UPDATE work_orders SET
              ref_no=%s, work_name=%s, div_code=%s, financial_year=%s, serial_no=%s,
              budget_type=%s, budget_head=%s, estimated_cost=%s,
              delivery_value=%s, delivery_unit=%s, form_data=%s, updated_at=NOW()
            WHERE id=%s
            RETURNING id, ref_no, work_name, saved_at, updated_at
        """, [
            ref, form.get('workName'), div, form.get('financialYear'), form.get('serialNo'),
            form.get('budgetType'), form.get('budgetHead'),
            float(form.get('estimatedCost') or 0),
            form.get('deliveryValue'), form.get('deliveryUnit'),
            psycopg2_json(form), id
        ])
        row = dict(cur.fetchone())
        _log(cur, id, d.get('userName'), 'Updated', 'Form data updated')
        row['saved_at']   = row['saved_at'].isoformat()
        row['updated_at'] = row['updated_at'].isoformat()
        return jsonify(row)

# PATCH progress only
@bp.route('/<int:id>/progress', methods=['PATCH'])
def update_progress(id):
    d = request.json
    with get_db() as (conn, cur):
        cur.execute(
            'UPDATE work_orders SET progress=%s, updated_at=NOW() WHERE id=%s RETURNING progress',
            [psycopg2_json(d.get('progress', {})), id]
        )
        row = cur.fetchone()
        done = d.get('done', True)
        _log(cur, id, d.get('userName'),
             'Stage Completed' if done else 'Stage Reopened',
             f"{d.get('stepLabel','')} marked {'Done' if done else 'Pending'}")
        return jsonify(dict(row))

# DELETE
@bp.route('/<int:id>', methods=['DELETE'])
def delete(id):
    with get_db() as (conn, cur):
        cur.execute('DELETE FROM work_orders WHERE id = %s', [id])
        return jsonify({'ok': True})

# GET activity log
@bp.route('/<int:id>/activity', methods=['GET'])
def activity(id):
    with get_db() as (conn, cur):
        cur.execute(
            'SELECT * FROM wo_activity_log WHERE wo_id=%s ORDER BY created_at DESC LIMIT 50', [id]
        )
        rows = []
        for r in cur.fetchall():
            r = dict(r)
            r['created_at'] = r['created_at'].isoformat()
            rows.append(r)
        return jsonify(rows)

# GET CSV export
@bp.route('/export/csv', methods=['GET'])
def export_csv():
    with get_db() as (conn, cur):
        cur.execute("""
            SELECT ref_no, work_name, budget_type, budget_head, estimated_cost,
                   delivery_value, delivery_unit, saved_at, updated_at
            FROM work_orders ORDER BY saved_at DESC
        """)
        rows = cur.fetchall()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Ref No', 'Work Name', 'Budget Type', 'Budget Head',
                     'Estimated Cost (Rs)', 'Delivery Value', 'Delivery Unit',
                     'Created On', 'Last Updated'])
    for r in rows:
        writer.writerow([
            r['ref_no'], r['work_name'], r['budget_type'], r['budget_head'],
            r['estimated_cost'], r['delivery_value'], r['delivery_unit'],
            r['saved_at'].strftime('%d/%m/%Y') if r['saved_at'] else '',
            r['updated_at'].strftime('%d/%m/%Y') if r['updated_at'] else '',
        ])
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=work_orders.csv'}
    )


def psycopg2_json(obj):
    """Helper — convert dict to psycopg2 JSON wrapper."""
    import json
    from psycopg2.extras import Json
    return Json(obj)
