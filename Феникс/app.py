from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
import psycopg2
import psycopg2.extras
from datetime import date, datetime
import hashlib
from functools import wraps
import os

app = Flask(__name__)
app.secret_key = 'секретный_ключ_феникс_2024'

# ========== НАСТРОЙКИ ПОДКЛЮЧЕНИЯ К БАЗЕ ДАННЫХ ==========
# ЭТИ ДАННЫЕ НУЖНО ЗАМЕНИТЬ НА СВОИ ИЗ ЛИЧНОГО КАБИНЕТА TIMEWEB
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "feniks_db"
DB_USER = "feniks_user"
DB_PASSWORD = "твой_пароль"

def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # ========== СОЗДАНИЕ ТАБЛИЦ ==========
    
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
    
    # ========== ВСЕ ПОЛЬЗОВАТЕЛИ ИЗ ТВОЕГО СПИСКА ==========
    
    # Очищаем таблицу users (чтобы пересоздать всех заново)
    cur.execute("DELETE FROM users")
    
    users_data = [
        # Администраторы и руководители
        ("tech_admin", "S#215-3152", "Технический администратор", "Тех. админ", "Управление", "admin", "Феникс", 1,1,1,1,1,1,1,1),
        ("rukovoditel", "123", "Руководитель", "Руководитель", "Без отделения", "leader", "Шеф", 1,1,1,1,0,1,1,1),
        
        # Командиры отделений
        ("kom1", "123", "Командир 1 отделения", "Командир отделения", "1 отделение", "commander", "Беркут", 1,0,0,1,0,1,0,0),
        ("kom2", "123", "Командир 2 отделения", "Командир отделения", "2 отделение", "commander", "Орел", 1,0,0,1,0,1,0,0),
        ("kom3", "123", "Командир 3 отделения", "Командир отделения", "3 отделение", "commander", "Сокол", 1,0,0,1,0,1,0,0),
        
        # Все рядовые из списка
        ("babenko", "123", "Артём Бабенков", "Рядовой", "3 отделение", "soldier", "Батя", 0,1,0,1,0,0,0,0),
        ("karpeev", "123", "Максим Карпеев", "Рядовой", "3 отделение", "soldier", "Карп", 0,1,0,1,0,0,0,0),
        ("max", "123", "Макс", "Рядовой", "3 отделение", "soldier", "Макс", 0,1,0,1,0,0,0,0),
        ("viharev", "123", "Яков Вихарев", "Рядовой", "3 отделение", "soldier", "Яша", 0,1,0,1,0,0,0,0),
        ("tsukanov", "123", "Савелий Цуканов", "Рядовой", "3 отделение", "soldier", "Цука", 0,1,0,1,0,0,0,0),
        ("martoshev", "123", "Максим Мартошев", "Рядовой", "3 отделение", "soldier", "Март", 0,1,0,1,0,0,0,0),
        ("alina", "123", "Алина Макаева", "Рядовой", "3 отделение", "soldier", "Аля", 0,1,0,1,0,0,0,0),
        ("artem", "123", "Артём", "Рядовой", "3 отделение", "soldier", "Тема", 0,1,0,1,0,0,0,0),
        ("elina", "123", "Элина Фатауза", "Рядовой", "3 отделение", "soldier", "Эля", 0,1,0,1,0,0,0,0),
        ("borovikova", "123", "Наталья Боровикова", "Рядовой", "3 отделение", "soldier", "Натаха", 0,1,0,1,0,0,0,0),
        ("avdey", "123", "Авдей", "Рядовой", "3 отделение", "soldier", "Авдей", 0,1,0,1,0,0,0,0),
        ("khalturin", "123", "Кирилл Халтурин", "Рядовой", "3 отделение", "soldier", "Халт", 0,1,0,1,0,0,0,0),
        ("gazizov", "123", "Данис Газизов", "Рядовой", "3 отделение", "soldier", "Газик", 0,1,0,1,0,0,0,0),
        ("zahar", "123", "Захар", "Рядовой", "3 отделение", "soldier", "Захар", 0,1,0,1,0,0,0,0),
        ("potapov", "123", "Константин Потапов", "Рядовой", "3 отделение", "soldier", "Потап", 0,1,0,1,0,0,0,0),
        ("khachatryan", "123", "Мариям Хачатрян", "Рядовой", "3 отделение", "soldier", "Маршак", 0,1,0,1,0,0,0,0),
        ("orlov", "123", "Иван Орлов", "Рядовой", "3 отделение", "soldier", "Орел", 0,1,0,1,0,0,0,0),
        ("borovikova_p", "123", "Полина Боровикова", "Рядовой", "3 отделение", "soldier", "Поля", 0,1,0,1,0,0,0,0),
        ("dima", "123", "Дима", "Рядовой", "3 отделение", "soldier", "Димон", 0,1,0,1,0,0,0,0),
        ("komilov", "123", "Родион Корнилов", "Рядовой", "3 отделение", "soldier", "Корнил", 0,1,0,1,0,0,0,0),
        ("brotan", "123", "Brotan", "Рядовой", "3 отделение", "soldier", "Бро", 0,1,0,1,0,0,0,0),
        ("sultanov", "123", "Артур Султанов", "Рядовой", "3 отделение", "soldier", "Султан", 0,1,0,1,0,0,0,0),
        ("beloyov", "123", "Gleb Beloyov", "Рядовой", "3 отделение", "soldier", "Глеб", 0,1,0,1,0,0,0,0),
        
        # Дополнительные пользователи из списка
        ("karyavskiy", "123", "Максим Карявский", "Рядовой", "3 отделение", "soldier", "Каряв", 0,1,0,1,0,0,0,0),
        ("tests", "123", "Мария Белоносова", "Рядовой", "3 отделение", "soldier", "Тест", 0,1,0,1,0,0,0,0),
        ("tst", "123", "Максим Мартышев", "Рядовой", "3 отделение", "soldier", "Март", 0,1,0,1,0,0,0,0),
        ("darinabeloysova", "123", "Дарина Белоусова", "Рядовой", "3 отделение", "soldier", "Дарина", 0,1,0,1,0,0,0,0),
        ("Katyapiotnikova", "123", "Екатерина Плотникова", "Рядовой", "3 отделение", "soldier", "Катя", 0,1,0,1,0,0,0,0),
        ("YakovViharev", "123", "Яков Вихарев Игоревич", "Рядовой", "3 отделение", "soldier", "Яков", 0,1,0,1,0,0,0,0),
        ("NikitaBorovikov", "123", "Никита Боровиков", "Рядовой", "3 отделение", "soldier", "Никита", 0,1,0,1,0,0,0,0),
        ("SemenSivkov", "123", "Семен Сивков", "Рядовой", "3 отделение", "soldier", "Сивков", 0,1,0,1,0,0,0,0),
        ("Ketsirinova", "123", "Екатерина Сиринкова", "Рядовой", "3 отделение", "soldier", "Сиринкова", 0,1,0,1,0,0,0,0),
        ("DaryaYdarceva", "123", "Дарья Ударцева", "Рядовой", "3 отделение", "soldier", "Дарья", 0,1,0,1,0,0,0,0),
        ("babenkov", "123", "Артём Бабенков", "Рядовой", "3 отделение", "soldier", "Бабенков", 0,1,0,1,0,0,0,0),
        ("sts", "123", "Стас", "Рядовой", "3 отделение", "soldier", "Стас", 0,1,0,1,0,0,0,0),
        ("1", "123", "Яков Вихарев Игоревич", "Рядовой", "3 отделение", "soldier", "Яков1", 0,1,0,1,0,0,0,0),
    ]
    
    for login, password, full_name, rank, unit, role_template, nickname, can_chat, can_view_repr, can_issue, can_view_lat, can_manage, can_change, can_flag, can_sched in users_data:
        cur.execute('''
            INSERT INTO users (login, password, full_name, rank, unit, role_template, nickname,
                              can_chat_write, can_view_all_reprimands, can_issue_reprimands,
                              can_view_all_lateness, can_manage_users, can_change_unit, 
                              can_manage_flag, can_manage_schedule)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (login, hashlib.sha256(password.encode()).hexdigest(),
              full_name, rank, unit, role_template, nickname,
              can_chat, can_view_repr, can_issue, can_view_lat, can_manage, can_change, can_flag, can_sched))
    
    conn.commit()
    cur.close()
    conn.close()
    print("✅ База данных инициализирована со всеми пользователями!")

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

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form['login']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute('''
            SELECT id, full_name, rank, unit, role_template, nickname,
                   can_chat_write, can_view_all_reprimands, can_issue_reprimands,
                   can_view_all_lateness, can_manage_users, can_change_unit, 
                   can_manage_flag, can_manage_schedule
            FROM users
            WHERE login = %s AND password = %s
        ''', (login, password))
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
            return render_template('login.html', error='Неверный логин или пароль')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == 'POST' and session.get('can_chat_write'):
        message = request.form['message']
        if message.strip():
            cur.execute('''
                INSERT INTO chat (user_id, user_name, user_nickname, user_unit, message)
                VALUES (%s, %s, %s, %s, %s)
            ''', (session['user_id'], session['user_name'], session.get('user_nickname', session['user_name']), 
                  session.get('user_unit', ''), message.strip()))
            conn.commit()
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
                         can_write=session.get('can_chat_write'),
                         user_name=session['user_name'],
                         user_nickname=session.get('user_nickname'),
                         user_rank=session['user_rank'],
                         user_unit=session['user_unit'])

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    conn = get_db_connection()
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
                         user_nickname=session.get('user_nickname'))

@app.route('/reprimands')
@login_required
def reprimands():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if session.get('can_view_all_reprimands'):
        cur.execute('''
            SELECT r.*, u.full_name, u.rank, u.unit, u.nickname
            FROM reprimands r
            JOIN users u ON r.user_id = u.id
            ORDER BY r.date DESC
        ''')
    else:
        cur.execute('''
            SELECT r.*, u.full_name, u.rank, u.unit, u.nickname
            FROM reprimands r
            JOIN users u ON r.user_id = u.id
            WHERE r.user_id = %s
            ORDER BY r.date DESC
        ''', (session['user_id'],))
    reprimands_list = cur.fetchall()
    
    soldiers = []
    if session.get('can_issue_reprimands'):
        cur.execute("SELECT id, full_name, rank, unit, nickname FROM users")
        soldiers = cur.fetchall()
    
    cur.close()
    conn.close()
    return render_template('reprimands.html', 
                         reprimands=reprimands_list,
                         soldiers=soldiers,
                         can_issue=session.get('can_issue_reprimands'),
                         can_view_all=session.get('can_view_all_reprimands'))

@app.route('/add_reprimand', methods=['POST'])
@login_required
@has_permission('can_issue_reprimands')
def add_reprimand():
    user_id = request.form['user_id']
    reason = request.form['reason']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO reprimands (user_id, date, reason, issued_by)
        VALUES (%s, %s, %s, %s)
    ''', (user_id, date.today(), reason, session['user_name']))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('reprimands'))

@app.route('/lateness')
@login_required
def lateness():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    if session.get('can_view_all_lateness'):
        cur.execute('''
            SELECT l.*, u.full_name, u.rank, u.unit, u.nickname
            FROM lateness l
            JOIN users u ON l.user_id = u.id
            ORDER BY l.date DESC
        ''')
    else:
        cur.execute('''
            SELECT l.*, u.full_name, u.rank, u.unit, u.nickname
            FROM lateness l
            JOIN users u ON l.user_id = u.id
            WHERE l.user_id = %s
            ORDER BY l.date DESC
        ''', (session['user_id'],))
    
    lateness_list = cur.fetchall()
    
    soldiers = []
    if session.get('can_view_all_lateness'):
        cur.execute("SELECT id, full_name, rank, unit, nickname FROM users")
        soldiers = cur.fetchall()
    elif session.get('can_change_unit'):
        cur.execute("SELECT id, full_name, rank, unit, nickname FROM users WHERE unit = %s", (session.get('user_unit'),))
        soldiers = cur.fetchall()
    
    cur.close()
    conn.close()
    return render_template('lateness.html',
                         lateness=lateness_list,
                         soldiers=soldiers,
                         can_view_all=session.get('can_view_all_lateness') or session.get('can_change_unit'))

@app.route('/add_lateness', methods=['POST'])
@login_required
@has_permission('can_view_all_lateness')
def add_lateness():
    user_id = request.form['user_id']
    minutes = request.form['minutes']
    reason = request.form['reason']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO lateness (user_id, date, minutes, reason, noted_by)
        VALUES (%s, %s, %s, %s, %s)
    ''', (user_id, date.today(), minutes, reason, session['user_name']))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('lateness'))

@app.route('/users')
@login_required
@has_permission('can_manage_users')
def users():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute('''
        SELECT id, login, full_name, rank, unit, role_template, nickname,
               can_chat_write, can_view_all_reprimands, can_issue_reprimands,
               can_view_all_lateness, can_manage_users, can_change_unit, 
               can_manage_flag, can_manage_schedule
        FROM users
    ''')
    users_list = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('users.html', users=users_list)

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@has_permission('can_manage_users')
def edit_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    if request.method == 'POST':
        can_chat_write = 1 if request.form.get('can_chat_write') else 0
        can_view_all_reprimands = 1 if request.form.get('can_view_all_reprimands') else 0
        can_issue_reprimands = 1 if request.form.get('can_issue_reprimands') else 0
        can_view_all_lateness = 1 if request.form.get('can_view_all_lateness') else 0
        can_manage_users = 1 if request.form.get('can_manage_users') else 0
        can_change_unit = 1 if request.form.get('can_change_unit') else 0
        can_manage_flag = 1 if request.form.get('can_manage_flag') else 0
        can_manage_schedule = 1 if request.form.get('can_manage_schedule') else 0
        unit = request.form.get('unit', '3 отделение')
        rank = request.form.get('rank', 'Рядовой')
        nickname = request.form.get('nickname', '')
        
        cur.execute('''
            UPDATE users SET
                can_chat_write = %s,
                can_view_all_reprimands = %s,
                can_issue_reprimands = %s,
                can_view_all_lateness = %s,
                can_manage_users = %s,
                can_change_unit = %s,
                can_manage_flag = %s,
                can_manage_schedule = %s,
                unit = %s,
                rank = %s,
                nickname = %s
            WHERE id = %s
        ''', (can_chat_write, can_view_all_reprimands, can_issue_reprimands,
              can_view_all_lateness, can_manage_users, can_change_unit, 
              can_manage_flag, can_manage_schedule, unit, rank, nickname, user_id))
        conn.commit()
        return redirect(url_for('users'))
    
    cur.execute('SELECT * FROM users WHERE id = %s', (user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('edit_user.html', user=user)

@app.route('/add_user', methods=['GET', 'POST'])
@login_required
@has_permission('can_manage_users')
def add_user():
    if request.method == 'POST':
        login = request.form['login']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        full_name = request.form['full_name']
        rank = request.form['rank']
        unit = request.form['unit']
        nickname = request.form.get('nickname', '')
        
        can_chat_write = 1 if request.form.get('can_chat_write') else 0
        can_view_all_reprimands = 1 if request.form.get('can_view_all_reprimands') else 0
        can_issue_reprimands = 1 if request.form.get('can_issue_reprimands') else 0
        can_view_all_lateness = 1 if request.form.get('can_view_all_lateness') else 0
        can_manage_users = 1 if request.form.get('can_manage_users') else 0
        can_change_unit = 1 if request.form.get('can_change_unit') else 0
        can_manage_flag = 1 if request.form.get('can_manage_flag') else 0
        can_manage_schedule = 1 if request.form.get('can_manage_schedule') else 0
        
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute('''
                INSERT INTO users (login, password, full_name, rank, unit, role_template, nickname,
                                  can_chat_write, can_view_all_reprimands, can_issue_reprimands,
                                  can_view_all_lateness, can_manage_users, can_change_unit, 
                                  can_manage_flag, can_manage_schedule)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (login, password, full_name, rank, unit, 'custom', nickname,
                  can_chat_write, can_view_all_reprimands, can_issue_reprimands,
                  can_view_all_lateness, can_manage_users, can_change_unit, 
                  can_manage_flag, can_manage_schedule))
            conn.commit()
        except Exception as e:
            print(f"Ошибка: {e}")
            pass
        cur.close()
        conn.close()
        return redirect(url_for('users'))
    
    return render_template('add_user.html')

@app.route('/change_unit', methods=['GET', 'POST'])
@login_required
@has_permission('can_change_unit')
def change_unit():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    if request.method == 'POST':
        user_id = request.form['user_id']
        new_unit = request.form['new_unit']
        cur.execute("UPDATE users SET unit = %s WHERE id = %s", (new_unit, user_id))
        conn.commit()
        return redirect(url_for('change_unit'))
    
    if session.get('can_view_all_lateness'):
        cur.execute('SELECT id, full_name, rank, unit, nickname FROM users')
    else:
        cur.execute('SELECT id, full_name, rank, unit, nickname FROM users WHERE unit = %s', (session.get('user_unit'),))
    users_list = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template('change_unit.html', users=users_list)

@app.route('/user_profile/<int:user_id>')
@login_required
def user_profile(user_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute('''
        SELECT full_name, rank, unit, role_template, nickname,
               can_chat_write, can_view_all_reprimands, can_issue_reprimands,
               can_view_all_lateness, can_manage_users, can_change_unit
        FROM users WHERE id = %s
    ''', (user_id,))
    user_info = cur.fetchone()
    cur.execute("SELECT date, reason, issued_by FROM reprimands WHERE user_id = %s ORDER BY date DESC", (user_id,))
    reprimands_user = cur.fetchall()
    cur.execute("SELECT date, minutes, reason FROM lateness WHERE user_id = %s ORDER BY date DESC", (user_id,))
    lateness_user = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('user_profile.html',
                         user=user_info,
                         reprimands=reprimands_user,
                         lateness=lateness_user,
                         can_view_all=session.get('can_view_all_reprimands'))

@app.route('/flag_duty')
@login_required
def flag_duty():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    today_date = date.today().isoformat()
    cur.execute('''
        SELECT fd.first_user_id, fd.second_user_id, u1.full_name, u1.rank, u1.unit, u1.nickname,
               u2.full_name, u2.rank, u2.unit, u2.nickname, fd.assigned_by
        FROM flag_duty fd
        LEFT JOIN users u1 ON fd.first_user_id = u1.id
        LEFT JOIN users u2 ON fd.second_user_id = u2.id
        WHERE fd.date = %s
    ''', (today_date,))
    today_duty = cur.fetchone()
    
    cur.execute('''
        SELECT fd.date, u1.full_name, u2.full_name, fd.assigned_by
        FROM flag_duty fd
        LEFT JOIN users u1 ON fd.first_user_id = u1.id
        LEFT JOIN users u2 ON fd.second_user_id = u2.id
        ORDER BY fd.date DESC LIMIT 10
    ''')
    history = cur.fetchall()
    
    cur.execute("SELECT id, full_name, rank, unit, nickname FROM users WHERE login != 'tech_admin' ORDER BY unit, full_name")
    soldiers = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template('flag_duty.html',
                         today_duty=today_duty,
                         history=history,
                         soldiers=soldiers,
                         can_manage=session.get('can_manage_flag', False))

@app.route('/set_flag_duty', methods=['POST'])
@login_required
@has_permission('can_manage_flag')
def set_flag_duty():
    first_user_id = request.form.get('first_user_id')
    second_user_id = request.form.get('second_user_id')
    today_date = date.today().isoformat()
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("DELETE FROM flag_duty WHERE date = %s", (today_date,))
    
    cur.execute('''
        INSERT INTO flag_duty (date, first_user_id, second_user_id, assigned_by)
        VALUES (%s, %s, %s, %s)
    ''', (today_date, first_user_id, second_user_id, session['user_name']))
    
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('flag_duty'))

@app.route('/schedule')
@login_required
def schedule():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute('''
        SELECT id, date, time, title, description, location, assigned_by, created_at
        FROM schedule
        ORDER BY date DESC, time DESC
    ''')
    events = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('schedule.html', events=events, can_manage=session.get('can_manage_schedule', False))

@app.route('/add_schedule', methods=['POST'])
@login_required
@has_permission('can_manage_schedule')
def add_schedule():
    event_date = request.form.get('event_date')
    event_time = request.form.get('event_time')
    title = request.form.get('title')
    description = request.form.get('description', '')
    location = request.form.get('location', '')
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO schedule (date, time, title, description, location, assigned_by)
        VALUES (%s, %s, %s, %s, %s, %s)
    ''', (event_date, event_time, title, description, location, session['user_name']))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('schedule'))

@app.route('/delete_schedule/<int:event_id>')
@login_required
@has_permission('can_manage_schedule')
def delete_schedule(event_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM schedule WHERE id = %s", (event_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('schedule'))

@app.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json', mimetype='application/manifest+json')

@app.route('/sw.js')
def service_worker():
    return send_from_directory('static', 'sw.js', mimetype='application/javascript')

@app.route('/icon/<path:filename>')
def icon(filename):
    return send_from_directory('static/icons', filename)

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    init_db()
    print("="*50)
    print("🔥 СИСТЕМА ФЕНИКС ЗАПУЩЕНА С POSTGRESQL!")
    print("📱 Открой браузер: http://localhost:5000")
    print("="*50)
    print("🔑 ДАННЫЕ ДЛЯ ВХОДА:")
    print("   👑 Тех. админ: tech_admin / S#215-3152")
    print("   👑 Руководитель: rukovoditel / 123")
    print("   ⭐ Командиры: kom1 / 123, kom2 / 123, kom3 / 123")
    print("   🪖 Рядовые: любой логин / 123")
    print("="*50)
    app.run(host='0.0.0.0', port=5000, debug=True)
