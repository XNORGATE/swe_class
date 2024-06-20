from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_socketio import SocketIO, emit, join_room, leave_room
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

# 存儲線上用戶的資料
online_users = {}

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
        return jsonify({'success': True, 'userName': user_name, 'classroom': classroom[1], 'role': 'host' if user_name == classroom[1] else 'student'})
    return jsonify({'success': False}), 404

@app.route('/get_classes', methods=['GET'])
def get_classes():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT name, code, total_rating, rating_count FROM classes')
    classes = cursor.fetchall()
    cursor.close()
    conn.close()
    class_list = []
    for row in classes:
        if row[3] > 0:
            average_rating = row[2] / row[3]
        else:
            average_rating = 0
        class_list.append({
            'name': row[0], 
            'code': row[1], 
            'average_rating': average_rating,
            'rating_count': row[3]  # 確保包含 rating_count
        })
    return jsonify(class_list)

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


# Socket.IO 事件
@socketio.on('join')
def on_join(data):
    user_name = data['user_name']
    class_code = data['class_code']
    join_room(class_code)
    if class_code not in online_users:
        online_users[class_code] = []
    if user_name not in online_users[class_code]:
        online_users[class_code].append(user_name)
    emit('user_list', online_users[class_code], room=class_code)

@socketio.on('leave')
def on_leave(data):
    user_name = data['user_name']
    class_code = data['class_code']
    leave_room(class_code)
    if class_code in online_users:
        online_users[class_code].remove(user_name)
        emit('user_list', online_users[class_code], room=class_code)


@socketio.on('send_message')
def handle_send_message(data):
    data['id'] = str(uuid.uuid4())  # Generate a unique ID for each message
    emit('receive_message', data, broadcast=True, room=data['class_code'])

@app.route('/rate_class', methods=['POST'])
def rate_class():
    data = request.json
    class_code = data.get('classCode')
    rating = data.get('rating')
    
    if not class_code or not rating:
        return jsonify({'success': False, 'message': 'Class code and rating are required'}), 400

    try:
        rating = int(rating)  # 確保 rating 是整數，如果需要浮點數，可以使用 float(rating)
    except ValueError:
        return jsonify({'success': False, 'message': 'Rating must be a number'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT total_rating, rating_count FROM classes WHERE code = %s', (class_code,))
    class_info = cursor.fetchone()
    
    if class_info:
        total_rating = class_info[0] + rating
        rating_count = class_info[1] + 1
        cursor.execute('UPDATE classes SET total_rating = %s, rating_count = %s WHERE code = %s',
                       (total_rating, rating_count, class_code))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True})
    else:
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'message': 'Class not found'}), 404



if __name__ == '__main__':
    socketio.run(app, debug=True)
