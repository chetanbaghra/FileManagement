"""
modules/attachments.py
File upload and download for work order documents.
"""
import os
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from db import get_db

bp = Blueprint('attachments', __name__)

@bp.route('/<int:wo_id>', methods=['GET'])
def get_all(wo_id):
    with get_db() as (conn, cur):
        cur.execute('SELECT * FROM attachments WHERE wo_id=%s ORDER BY uploaded_at DESC', [wo_id])
        rows = []
        for r in cur.fetchall():
            r = dict(r)
            r['uploaded_at'] = r['uploaded_at'].isoformat()
            rows.append(r)
        return jsonify(rows)

@bp.route('/<int:wo_id>', methods=['POST'])
def upload(wo_id):
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    f        = request.files['file']
    category = request.form.get('category', 'general')
    notes    = request.form.get('notes', '')
    filename = secure_filename(f.filename)
    folder   = os.path.join(current_app.config['UPLOAD_FOLDER'], str(wo_id))
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, filename)
    f.save(filepath)
    with get_db() as (conn, cur):
        cur.execute("""
            INSERT INTO attachments (wo_id, category, file_name, file_path, file_size, mime_type, notes)
            VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING *
        """, [wo_id, category, f.filename, filepath, os.path.getsize(filepath), f.content_type, notes])
        cur.execute(
            'INSERT INTO wo_activity_log (wo_id, user_name, action, detail) VALUES (%s,%s,%s,%s)',
            [wo_id, 'System', 'File Uploaded', f'{category}: {f.filename}']
        )
        row = dict(cur.fetchone())
        row['uploaded_at'] = row['uploaded_at'].isoformat()
        return jsonify(row)

@bp.route('/file/<int:id>', methods=['DELETE'])
def delete(id):
    with get_db() as (conn, cur):
        cur.execute('SELECT file_path FROM attachments WHERE id=%s', [id])
        row = cur.fetchone()
        if row and os.path.exists(row['file_path']):
            os.remove(row['file_path'])
        cur.execute('DELETE FROM attachments WHERE id=%s', [id])
        return jsonify({'ok': True})
