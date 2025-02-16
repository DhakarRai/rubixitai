from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
import os
import random
import string
import math

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes



# Database connection function
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Dhakar@2002",
        database="education_site"
    )

# Game Configuration Class for Memory Match
class GameConfig:
    def __init__(self):
        self.current_level = 1
        self.score = 0
        self.matched_positions = set()
        self.emojis = [
            '🐶', '🐱', '🐼', '🐨', '🦁', '🐯', 
            '🦊', '🦝', '🐮', '🐷', '🐸', '🐙'
        ]
        self.current_game_emojis = []
    
    def get_level_config(self):
        num_boxes = self.current_level * 2
        selected_emojis = random.sample(self.emojis, num_boxes // 2)
        self.current_game_emojis = selected_emojis * 2
        random.shuffle(self.current_game_emojis)
        self.matched_positions = set()
        
        return {
            'level': self.current_level,
            'score': self.score,
            'emojis': self.current_game_emojis,
            'display_time': 10000
        }
    
    def positions_matched(self):
        total_positions = len(self.current_game_emojis)
        return len(self.matched_positions) == total_positions
    
    def record_match(self, pos1, pos2):
        self.matched_positions.add(pos1)
        self.matched_positions.add(pos2)

# Initialize game
game = GameConfig()

# Math Game Functions
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

# Cache control
@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.expires = 0
    response.cache_control.public = False
    return response

# Routes for serving static files
@app.route('/static/images/<path:filename>')
def serve_image(filename):
    return send_from_directory('static/images', filename)

@app.route('/audio/<path:filename>')
def serve_audio(filename):
    return send_from_directory('static/audio', filename)

# Main application routes
@app.route('/')
def home():
    return render_template('webpagerubix1.html')

@app.route('/parent')
def parent():
    return render_template('parent.html')

@app.route('/chat')
def chat():
    return render_template('main1.1.html')

@app.route('/subjects')
def subjects():
    return render_template('index.html')

@app.route('/webpage')
def webpage():
    return render_template('webpage.html')

# Memory Match Game Routes
@app.route('/memorymatch')
def memorymatch():
    return render_template('memorymatchgame.html')

@app.route('/numbergame')
def numbergame():
    return render_template('numbergame.html')

@app.route('/superstudent')
def superstudent():
    return render_template('superstudent.html')

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
        remaining_time += 5  # Add 5 seconds for correct answer
    else:
        remaining_time -= 10  # Subtract 10 seconds for wrong answer
        
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
        connection = get_db_connection()
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
        connection = get_db_connection()
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
        connection = get_db_connection()
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
        connection = get_db_connection()
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

if __name__ == '__main__':
    app.run(debug=True)