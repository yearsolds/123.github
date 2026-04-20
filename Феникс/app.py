from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
import psycopg2
import psycopg2.extras
from datetime import date, datetime
import hashlib
from functools import wraps
import os
import sys

# ========== СОЗДАНИЕ ПРИЛОЖЕНИЯ ==========
app = Flask(__name__)
app.secret_key = 'секретный_ключ_феникс_2024'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# ========== ПОДКЛЮЧЕНИЕ К БАЗЕ ДАННЫХ ==========
# Берем параметры из переменных окружения (их нужно добавить в панели Timeweb)
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_NAME = os.environ.get('DB_NAME', 'feniks_db')
DB_USER = os.environ.get('DB_USER', 'feniks_user')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'password')

def get_db_connection():
    """Подключение к PostgreSQL"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        print(f"Ошибка подключения к БД: {e}")
        return None

# ========== ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ ==========
def init_db():
    conn = get_db_connection()
    if not conn:
        print("❌ Не удалось подключиться к базе данных")
        return
    
    cur = conn.cursor()
    
    # Таблица пользователей
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            login VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            full_name VARCHAR(200) NOT NULL,
            rank VARCHAR(100) DEFAULT 'Рядовой',
            unit VARCHAR(100) DEFAULT '3 отделение',
            role_template VARCHAR(50) DEFAULT 'soldier',
            nickname VARCHAR(100) DEFAULT '',
            can_chat_write INTEGER DEFAULT 0,
            can_view_all_reprimands INTEGER DEFAULT 0,
            can_issue_reprimands INTEGER DEFAULT 0,
            can_view_all_lateness INTEGER DEFAULT 0,
            can_manage_users INTEGER DEFAULT 0,
            can_change_unit INTEGER DEFAULT 0,
            can_manage_flag INTEGER DEFAULT 0,
            can_manage_schedule INTEGER DEFAULT 0
        )
    ''')
    
    # Таблица чата
    cur.execute('''
        CREATE TABLE IF NOT EXISTS chat (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            user_name VARCHAR(200),
            user_nickname VARCHAR(100),
            user_unit VARCHAR(100),
            message TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Таблица выговоров
    cur.execute('''
        CREATE TABLE IF NOT EXISTS reprimands (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            date DATE,
            reason TEXT,
            issued_by VARCHAR(200)
        )
    ''')
    
    # Таблица опозданий
    cur.execute('''
        CREATE TABLE IF NOT EXISTS lateness (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            date DATE,
            minutes INTEGER,
            reason TEXT,
            noted_by VARCHAR(200)
        )
    ''')
    
    # Таблица выноса флага
    cur.execute('''
        CREATE TABLE IF NOT EXISTS flag_duty (
            id SERIAL PRIMARY KEY,
            date DATE UNIQUE,
            first_user_id INTEGER REFERENCES users(id),
            second_user_id INTEGER REFERENCES users(id),
            assigned_by VARCHAR(200),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Таблица занятий
    cur.execute('''
        CREATE TABLE IF NOT EXISTS schedule (
            id SERIAL PRIMARY KEY,
            date DATE,
            time TIME,
            title VARCHAR(200),
            description TEXT,
            location VARCHAR(200),
            assigned_by VARCHAR(200),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    
    # Проверяем, есть ли пользователи
    cur.execute("SELECT COUNT(*) FROM users")
    count = cur.fetchone()[0]
    
    if count == 0:
        # Создаём тестового пользователя для проверки
        cur.execute('''
            INSERT INTO users (login, password, full_name, rank, unit, role_template, nickname,
                              can_chat_write, can_view_all_reprimands, can_issue_reprimands,
                              can_view_all_lateness, can_manage_users, can_change_unit, 
                              can_manage_flag, can_manage_schedule)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', ('tech_admin', hashlib.sha256('S#215-3152'.encode()).hexdigest(),
              'Технический администратор', 'Тех. админ', 'Управление', 'admin', 'Феникс',
              1, 1, 1, 1, 1, 1, 1, 1))
        
        # Добавляем руководителя
        cur.execute('''
            INSERT INTO users (login, password, full_name, rank, unit, role_template, nickname,
                              can_chat_write, can_view_all_reprimands, can_issue_reprimands,
                              can_view_all_lateness, can_manage_users, can_change_unit, 
                              can_manage_flag, can_manage_schedule)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', ('rukovoditel', hashlib.sha256('123'.encode()).hexdigest(),
              'Руководитель', 'Руководитель', 'Без отделения', 'leader', 'Шеф',
              1, 1, 1, 1, 0, 1, 1, 1))
        
        # Добавляем командиров отделений
        for i, name in enumerate(['Беркут', 'Орел', 'Сокол'], 1):
            cur.execute('''
                INSERT INTO users (login, password, full_name, rank, unit, role_template, nickname,
                                  can_chat_write, can_view_all_reprimands, can_issue_reprimands,
                                  can_view_all_lateness, can_manage_users, can_change_unit, 
                                  can_manage_flag, can_manage_schedule)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (f'kom{i}', hashlib.sha256('123'.encode()).hexdigest(),
                  f'Командир {i} отделения', 'Командир отделения', f'{i} отделение', 'commander', name,
                  1, 0, 0, 1, 0, 1, 0, 0))
        
        print("✅ База данных инициализирована с тестовыми пользователями!")
    
    conn.commit()
    cur.close()
    conn.close()

# ========== ДЕКОРАТОРЫ ==========
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def has_permission(permission):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not session.get(permission, False):
                return "У вас нет прав для этого действия", 403
            return f(*args, **kwargs)
        return decorated
    return decorator

# ========== МАРШРУТЫ ==========
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        login = request.form.get('login')
        password = request.form.get('password')
        
        if not login or not password:
            error = "Введите логин и пароль"
        else:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            conn = get_db_connection()
            if conn:
                cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                cur.execute('''
                    SELECT id, full_name, rank, unit, role_template, nickname,
                           can_chat_write, can_view_all_reprimands, can_issue_reprimands,
                           can_view_all_lateness, can_manage_users, can_change_unit, 
                           can_manage_flag, can_manage_schedule
                    FROM users
                    WHERE login = %s AND password = %s
                ''', (login, password_hash))
                user = cur.fetchone()
                cur.close()
                conn.close()
                
                if user:
                    session['user_id'] = user['id']
                    session['user_name'] = user['full_name']
                    session['user_rank'] = user['rank']
                    session['user_unit'] = user['unit']
                    session['role_template'] = user['role_template']
                    session['user_nickname'] = user['nickname'] if user['nickname'] else user['full_name']
                    session['can_chat_write'] = user['can_chat_write']
                    session['can_view_all_reprimands'] = user['can_view_all_reprimands']
                    session['can_issue_reprimands'] = user['can_issue_reprimands']
                    session['can_view_all_lateness'] = user['can_view_all_lateness']
                    session['can_manage_users'] = user['can_manage_users']
                    session['can_change_unit'] = user['can_change_unit']
                    session['can_manage_flag'] = user['can_manage_flag']
                    session['can_manage_schedule'] = user['can_manage_schedule']
                    return redirect(url_for('chat'))
                else:
                    error = "Неверный логин или пароль"
            else:
                error = "Ошибка подключения к базе данных"
    
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/chat')
@login_required
def chat():
    conn = get_db_connection()
    messages = []
    if conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT user_name, user_nickname, user_unit, message, timestamp 
            FROM chat 
            ORDER BY timestamp DESC LIMIT 100
        ''')
        messages = cur.fetchall()[::-1]
        cur.close()
        conn.close()
    
    return render_template('chat.html', 
                         messages=messages,
                         can_write=session.get('can_chat_write', False),
                         user_name=session.get('user_name', ''),
                         user_nickname=session.get('user_nickname', ''),
                         user_rank=session.get('user_rank', ''),
                         user_unit=session.get('user_unit', ''))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    conn = get_db_connection()
    if not conn:
        return render_template('profile.html', user=None, user_nickname=session.get('user_nickname', ''))
    
    cur = conn.cursor()
    
    if request.method == 'POST':
        nickname = request.form.get('nickname', '')
        cur.execute("UPDATE users SET nickname = %s WHERE id = %s", (nickname, session['user_id']))
        conn.commit()
        session['user_nickname'] = nickname if nickname else session['user_name']
        return redirect(url_for('profile'))
        
    cur.execute("SELECT full_name, rank, unit, nickname FROM users WHERE id = %s", (session['user_id'],))
    user = cur.fetchone()
    cur.close()
    conn.close()
    
    return render_template('profile.html',
                         user=user,
                         user_nickname=session.get('user_nickname', ''))

# Тестовый маршрут для проверки работоспособности
@app.route('/health')
def health():
    return {"status": "ok", "message": "ФЕНИКС работает!"}

# Простой маршрут для проверки
@app.route('/test')
def test():
    return "Сервер ФЕНИКС работает! 🐦‍🔥"

# ========== ЗАПУСК ==========
if __name__ == '__main__':
    # При локальном запуске
    init_db()
    print("="*50)
    print("🔥 СИСТЕМА ФЕНИКС ЗАПУЩЕНА!")
    print("📱 Открой браузер: http://localhost:5000")
    print("="*50)
    app.run(host='0.0.0.0', port=5000, debug=True)
else:
    # При запуске на хостинге (Gunicorn)
    init_db()
    print("="*50)
    print("🔥 СИСТЕМА ФЕНИКС ЗАПУЩЕНА НА TIMEWEB!")
    print("="*50)
