from flask import Flask, jsonify, render_template, request, send_from_directory, send_file, redirect, url_for, session
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
import os
from pathlib import Path
import random
import string
import math
import io
import sqlite3
import ollama
import pyttsx3
import base64
import logging



app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Add a secret key for session
CORS(app)  # Enable CORS for all routes

# Ensure template and static folders are properly set
app.template_folder = os.path.abspath('templates')
app.static_folder = os.path.abspath('static')

# Database configurations
EDUCATION_DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Dhakar@2002',
    'database': 'education_site'
}

RUBIX_DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Dhakar@2002',
    'database': 'rubix'
}

PICTURE_GAME_DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Dhakar@2002',
    'auth_plugin': 'mysql_native_password',
    'database': 'picture_game'
}

# Database connection functions
def verify_template_exists(template_name):
    template_path = os.path.join(app.template_folder, template_name)
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template not found: {template_path}")
    return True

def get_education_db_connection():
    return mysql.connector.connect(**EDUCATION_DB_CONFIG)

def get_rubix_db_connection():
    return mysql.connector.connect(**RUBIX_DB_CONFIG)

def get_picture_game_db_connection():
    try:
        connection = mysql.connector.connect(**PICTURE_GAME_DB_CONFIG)
        return connection
    except mysql.connector.Error as err:
        print(f"Database Connection Error: {err}")
        return None

# Game Logic Classes
class MemoryMatchGame:
    def __init__(self):
        self.current_level = 1
        self.score = 0
        self.matched_positions = set()
        self.current_game_emojis = []
        self.levels = {
            1: {'grid': 4, 'emojis': ['🐶', '🐱', '🐭', '🐹', '🐰', '🦊', '🐻', '🐼']},
            2: {'grid': 4, 'emojis': ['🍎', '🍌', '🍓', '🍉', '🍇', '🍊', '🍋', '🍍']},
            3: {'grid': 6, 'emojis': ['🚗', '🚕', '🚌', '🚓', '🚑', '🚒', '🚂', '🚁', '🚢', '⛵', '🚀', '🚲', '🚍', '🚘', '🚖', '🏎️', '🚚', '🚛']},
        }
        self.setup_level(self.current_level)
    
    def setup_level(self, level):
        if level > len(self.levels):
            level = 1  # Reset to level 1 if we've gone through all levels
        
        self.matched_positions = set()
        level_config = self.levels[level]
        grid_size = level_config['grid']
        available_emojis = level_config['emojis']
        
        num_pairs = (grid_size * grid_size) // 2
        selected_emojis = random.sample(available_emojis, min(num_pairs, len(available_emojis)))
        
        emoji_pairs = selected_emojis * 2
        
        while len(emoji_pairs) < (grid_size * grid_size):
            additional = random.choice(available_emojis)
            emoji_pairs.extend([additional, additional])
        
        random.shuffle(emoji_pairs)
        self.current_game_emojis = emoji_pairs[:grid_size * grid_size]
    
    def get_level_config(self):
        level_config = self.levels[self.current_level]
        grid_size = level_config['grid']
        
        hidden_grid = ['❓'] * (grid_size * grid_size)
        
        return {
            'level': self.current_level,
            'grid_size': grid_size,
            'cards': hidden_grid,
            'score': self.score
        }
    
    def record_match(self, pos1, pos2):
        self.matched_positions.add(pos1)
        self.matched_positions.add(pos2)
    
    def positions_matched(self):
        return len(self.matched_positions) == len(self.current_game_emojis)

# Initialize game instance
game = MemoryMatchGame()

# Helper Functions for Math Game
def generate_complex_operation():
    easy_operations = [
        ('+', lambda a, b: (f"{a} + {b}", a + b)),
        ('-', lambda a, b: (f"{a} - {b}", a - b)),
        ('*', lambda a, b: (f"{a} * {b}", a * b))
    ]
    hard_operations = [
        ('/', lambda a, b: (f"{a} / {b}", a / b) if b != 0 else (f"{a} / 1", a)),
        ('square', lambda a, b: (f"{a}²", a ** 2)),
        ('cube', lambda a, b: (f"{a}³", a ** 3)),
        ('sqrt', lambda a, b: (f"√{a*a}", a)),
        ('power', lambda a, b: (f"{a}^{b}", a ** b))
    ]
    return easy_operations if random.random() < 0.7 else hard_operations

def generate_problem(difficulty=1):
    operations = generate_complex_operation()
    operation_type, operation_func = random.choice(operations)

    if difficulty == 1:
        if operation_type in ['+', '-']:
            a, b = random.randint(1, 20), random.randint(1, 10)
        elif operation_type == '*':
            a, b = random.randint(2, 9), random.randint(2, 5)
        else:
            a, b = random.randint(1, 5), random.randint(1, 3)
    else:
        if operation_type in ['+', '-']:
            a, b = random.randint(50, 200), random.randint(25, 100)
        elif operation_type == '*':
            a, b = random.randint(10, 30), random.randint(5, 15)
        elif operation_type == '/':
            b = random.randint(2, 12)
            a = b * random.randint(5, 20)
        elif operation_type in ['square', 'cube']:
            a = random.randint(8, 15)
        elif operation_type == 'sqrt':
            a = random.randint(5, 12)
            a = a * a
        else:
            a, b = random.randint(2, 10), random.randint(2, 4)

    expression, result = operation_func(a, b)

    numbers = list(str(a) + (str(b) if operation_type in ['+', '-', '*', '/', 'power'] else ''))
    unique_numbers = list(set(numbers))
    letters = random.sample(string.ascii_uppercase, len(unique_numbers))
    mapping = dict(zip(unique_numbers, letters))

    if operation_type in ['+', '-', '*', '/']:
        parts = expression.split()
        a_letters = ''.join(mapping[d] for d in str(parts[0]))
        b_letters = ''.join(mapping[d] for d in str(parts[2]))
        letter_expression = f"{a_letters} {parts[1]} {b_letters}"
    elif operation_type in ['square', 'cube']:
        a_letters = ''.join(mapping[d] for d in str(a))
        letter_expression = f"{a_letters}{expression[-1]}"
    elif operation_type == 'sqrt':
        a_letters = ''.join(mapping[d] for d in str(a*a))
        letter_expression = f"√{a_letters}"
    else:
        a_letters = ''.join(mapping[d] for d in str(a))
        b_letters = ''.join(mapping[d] for d in str(b))
        letter_expression = f"{a_letters}^{b_letters}"

    hints = [
        "Break down the problem into smaller parts",
        "Look for patterns in the letter combinations",
        "Consider the relationship between the numbers"
    ] if difficulty == 2 else [
        "Start by finding the most common letter in the problem",
        "Try solving the easiest operation first"
    ]

    return {
        'expression': letter_expression,
        'operation_type': operation_type,
        'mapping': {v: k for k, v in mapping.items()},
        'result': round(result),
        'hints': hints
    }
    
current_dir = os.path.dirname(os.path.abspath(__file__))
app.template_folder = os.path.join(current_dir, 'templates')
app.static_folder = os.path.join(current_dir, 'static')

# Cache control
@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.expires = 0
    response.cache_control.public = False
    return response

# Main application routes
@app.route('/')
def home():
    try:
        verify_template_exists('interface.html')
        return render_template('interface.html')
    except FileNotFoundError as e:
        return str(e), 500

# Authentication Routes
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    try:
        connection = get_rubix_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()
        
        if user:
            session['user'] = username
            print(f"Login successful for user: {username}")
            return jsonify({"success": True, "message": "Login successful!"}), 200
        else:
            print(f"Login failed for user: {username}")
            return 'Login Failed', 401
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Main Navigation Routes
@app.route('/webpagerubix1')
def webpagerubix():
    if 'user' in session:
        return render_template('webpagerubix1.html')
    else:
        return redirect(url_for('home'))

@app.route('/picture_game')
def picture_game():
    return render_template('iiii.html')

@app.route('/parent')
def parent():
    return render_template('parent.html')

@app.route('/chat')
def chat():
    return render_template('main1.4.html')

@app.route('/subjects')
def subjects():
    return render_template('index.html')

@app.route('/webpage')
def webpage():
    return render_template('webpage.html')

@app.route('/memorymatch')
def memorymatch():
    return render_template('memorymatchgame.html')

@app.route('/numbergame')
def numbergame():
    return render_template('numbergame.html')

@app.route('/superstudent')
def superstudent():
    return render_template('superstudent.html')

@app.route('/iiii')
def picturerecognition():
    return render_template('iiii.html')

# Game State API Routes for Memory Match
@app.route('/api/game-state')
def game_state():
    return jsonify(game.get_level_config())

@app.route('/api/check-match/<int:pos1>/<int:pos2>')
def check_match(pos1, pos2):
    if pos1 == pos2:
        return jsonify({'error': 'Cannot match same position'}), 400
    
    emojis = game.current_game_emojis
    
    if 0 <= pos1 < len(emojis) and 0 <= pos2 < len(emojis):
        is_match = emojis[pos1] == emojis[pos2]
        
        if is_match:
            game.score += 1
            game.record_match(pos1, pos2)
            
            level_complete = game.positions_matched()
            if level_complete:
                game.current_level += 1
            
            return jsonify({
                'match': True,
                'score': game.score,
                'level': game.current_level,
                'levelComplete': level_complete
            })
        
        return jsonify({
            'match': False,
            'score': game.score,
            'level': game.current_level
        })
    
    return jsonify({'error': 'Invalid positions'}), 400

# Math Game Routes
@app.route('/get_problem')
def get_problem():
    difficulty = int(request.args.get('difficulty', 1))
    problem = generate_problem(difficulty)
    return jsonify(problem)

@app.route('/check_answer', methods=['POST'])
def check_answer():
    data = request.json
    user_answer = float(data['answer'])
    correct_answer = float(data['correct_answer'])
    remaining_time = float(data['time_taken'])
    
    base_score = 10 if data['difficulty'] == 2 else 5
    is_correct = abs(user_answer - correct_answer) < 0.01
    
    if is_correct:
        remaining_time += 5
    else:
        remaining_time -= 10
        
    remaining_time = max(0, min(50, remaining_time))
    
    if remaining_time > 50:
        time_multiplier = 0.0
    elif remaining_time >= 41 and remaining_time <= 50:
        time_multiplier = 0.2
    elif remaining_time >= 31 and remaining_time <= 40:
        time_multiplier = 0.4
    elif remaining_time >= 21 and remaining_time <= 30:
        time_multiplier = 0.6
    elif remaining_time >= 11 and remaining_time <= 20:
        time_multiplier = 0.8
    elif remaining_time >= 1 and remaining_time <= 10:
        time_multiplier = 1.0
    else:
        time_multiplier = 0.0
        
    score = int(base_score * time_multiplier)

    return jsonify({
        'score': score,
        'is_correct': is_correct,
        'remaining_time': remaining_time
    })

# Educational Content API Routes
@app.route('/api/subjects')
def get_subjects():
    try:
        connection = get_education_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM subjects")
        subjects = cursor.fetchall()
        return jsonify(subjects)
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/lessons/<int:subject_id>')
def get_lessons(subject_id):
    try:
        connection = get_education_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM lessons 
            WHERE subject_id = %s 
            ORDER BY lesson_number
        """, (subject_id,))
        lessons = cursor.fetchall()
        return jsonify(lessons)
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/topics/<int:subject_id>/<int:lesson_number>')
def get_topics(subject_id, lesson_number):
    try:
        connection = get_education_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM Topics_info 
            WHERE subject_id = %s AND lesson_number = %s
            ORDER BY Topic_id
        """, (subject_id, lesson_number))
        topics = cursor.fetchall()
        return jsonify(topics)
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/content/<int:subject_id>/<int:lesson_number>/<int:topic_id>')
def get_content(subject_id, lesson_number, topic_id):
    try:
        connection = get_education_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM Info 
            WHERE subject_id = %s AND lesson_number = %s AND Topic_id = %s
        """, (subject_id, lesson_number, topic_id))
        content = cursor.fetchone()
        return jsonify(content)
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Picture Recognition Game Routes
@app.route('/game_image/<int:image_id>')
def serve_image(image_id):
    try:
        connection = get_picture_game_db_connection()
        if not connection:
            return 'Database connection failed', 500
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute('SELECT image_data FROM game_questions WHERE id = %s', (image_id,))
        result = cursor.fetchone()
        
        if result and result['image_data']:
            return send_file(
                io.BytesIO(result['image_data']),
                mimetype='image/jpeg',
                as_attachment=False,
                download_name=f"image_{image_id}.jpg"
            )
            
        return 'Image not found', 404
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close()

@app.route('/get_game_data')
def get_game_data():
    try:
        connection = get_picture_game_db_connection()
        if not connection:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute('SELECT id, correct_answer, hint FROM game_questions')
        questions = cursor.fetchall()
            
        game_data = []
        for question in questions:
            cursor.execute('SELECT option_text FROM question_options WHERE question_id = %s', (question['id'],))
            options = [option['option_text'] for option in cursor.fetchall()]
                
            game_data.append({
                'image_path': f"/game_image/{question['id']}",
                'correct_answer': question['correct_answer'],
                'options': options,
                'hint': question['hint']
            })
                
        return jsonify(game_data)
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close()

# Static File Routes
@app.route('/static/images/<path:filename>')
def serve_image_static(filename):
    return send_from_directory('static/images', filename)

@app.route('/audio/<path:filename>')
def serve_audio(filename):
    return send_from_directory('static/audio', filename)

# Test Connection Route
@app.route('/test_connection')
def test_connection():
    """Test database connectivity for all databases."""
    education_connection = get_education_db_connection()
    picture_game_connection = get_picture_game_db_connection()
    rubix_connection = get_rubix_db_connection()
    
    status = {
        'education_db': False,
        'picture_game_db': False,
        'rubix_db': False
    }
    
    if education_connection:
        status['education_db'] = True
        education_connection.close()
    
    if picture_game_connection:
        status['picture_game_db'] = True
        picture_game_connection.close()
        
    if rubix_connection:
        status['rubix_db'] = True
        rubix_connection.close()
    
    if all(status.values()):
        return jsonify({"message": "All database connections successful", "status": status}), 200
    else:
        return jsonify({"message": "Some database connections failed", "status": status}), 500

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs(app.template_folder, exist_ok=True)
    os.makedirs(app.static_folder, exist_ok=True)
    os.makedirs(os.path.join(app.static_folder, 'images'), exist_ok=True)
    os.makedirs(os.path.join(app.static_folder, 'audio'), exist_ok=True)
    
    # You can uncomment either of these run configurations:
    
    print(f"Current directory: {os.getcwd()}")
    print(f"Template folder: {app.template_folder}")
    print(f"Template exists: {os.path.exists(os.path.join(app.template_folder, 'interface.html'))}")
    
    # For local development with debug mode:
    app.run(host='127.0.0.1', port=5000, debug=True)
    
    # For production deployment:
    # app.run(host="0.0.0.0", port=5000, debug=False)