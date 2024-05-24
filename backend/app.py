from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import os
import db_config
import random
import string
import uuid

app = Flask(__name__, static_folder='static', static_url_path='')
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
socketio = SocketIO(app, cors_allowed_origins="*")
CORS(app)

# Database setup
def get_db_connection():
    return db_config.get_db_connection()

def generate_class_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

@app.route('/')
def index():
    return send_file(os.path.join(app.static_folder, 'index.html'))

@app.route('/create_class', methods=['POST'])
def create_class():
    data = request.json
    class_name = data.get('classroomName')
    class_code = generate_class_code()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO classes (name, code) VALUES (%s, %s)', (class_name, class_code))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'classroomCode': class_code})

@app.route('/join_class', methods=['POST'])
def join_class():
    data = request.json
    class_code = data.get('joinCode')
    user_name = data.get('userName')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM classes WHERE code = %s', (class_code,))
    classroom = cursor.fetchone()
    cursor.close()
    conn.close()
    if classroom:
        return jsonify({'success': True, 'userName': user_name, 'role': 'host' if user_name == classroom[1] else 'student'})
    return jsonify({'success': False}), 404

@app.route('/get_classes', methods=['GET'])
def get_classes():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT name, code FROM classes')
    classes = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify([{'name': row[0], 'code': row[1]} for row in classes])

@app.route('/delete_class', methods=['POST'])
def delete_class():
    data = request.json
    class_code = data.get('classCode')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM classes WHERE code = %s', (class_code,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'success': True})

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part', 400
    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400
    if file:
        filename = file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return jsonify({'name': filename, 'url': f'/uploads/{filename}'})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@socketio.on('send_message')
def handle_send_message(data):
    data['id'] = str(uuid.uuid4())  # Generate a unique ID for each message
    emit('receive_message', data, broadcast=True)

@app.route('/test_db_connection')
def test_db_connection():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        cursor.fetchone()
        cursor.close()
        conn.close()
        return 'Database connection successful', 200
    except Exception as e:
        return f'Database connection failed: {e}', 500

if __name__ == '__main__':
    socketio.run(app, debug=True)
