"""modules/reports.py — Summary stats and reports"""
from flask import Blueprint, jsonify
from db import get_db

bp = Blueprint('reports', __name__)

@bp.route('/summary', methods=['GET'])
def summary():
    with get_db() as (conn, cur):
        cur.execute('SELECT COUNT(*) as total FROM work_orders')
        total = cur.fetchone()['total']

        cur.execute('SELECT budget_type, COUNT(*) as count FROM work_orders GROUP BY budget_type')
        by_budget = cur.fetchall()

        cur.execute('SELECT financial_year, COUNT(*) as count FROM work_orders GROUP BY financial_year ORDER BY financial_year DESC')
        by_year = cur.fetchall()

        cur.execute('SELECT SUM(estimated_cost) as total, AVG(estimated_cost) as avg FROM work_orders')
        cost = cur.fetchone()

        return jsonify({
            'total': total,
            'by_budget': [dict(r) for r in by_budget],
            'by_year':   [dict(r) for r in by_year],
            'total_cost': float(cost['total'] or 0),
            'avg_cost':   float(cost['avg']   or 0),
        })

@bp.route('/cost-summary', methods=['GET'])
def cost_summary():
    with get_db() as (conn, cur):
        cur.execute("""
            SELECT budget_head, budget_type,
                   COUNT(*) as wo_count,
                   SUM(estimated_cost) as total_cost
            FROM work_orders
            WHERE budget_head IS NOT NULL AND budget_head != ''
            GROUP BY budget_head, budget_type
            ORDER BY total_cost DESC
        """)
        rows = []
        for r in cur.fetchall():
            r = dict(r)
            r['total_cost'] = float(r['total_cost'] or 0)
            rows.append(r)
        return jsonify(rows)

@bp.route('/stage-wise', methods=['GET'])
def stage_wise():
    with get_db() as (conn, cur):
        cur.execute('SELECT id, progress FROM work_orders')
        stages = {}
        for row in cur.fetchall():
            prog = row['progress'] or {}
            for k, v in prog.items():
                if v is True or v == 'true':
                    stages[k] = stages.get(k, 0) + 1
        return jsonify(stages)
