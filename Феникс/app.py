from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
import sqlite3
from datetime import date, datetime
import hashlib
from functools import wraps
import os

app = Flask(__name__)
app.secret_key = 'секретный_ключ_феникс_2024'

DB_NAME = "Feniks.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT UNIQUE,
            password TEXT,
            full_name TEXT,
            rank TEXT,
            unit TEXT DEFAULT '3 отделение',
            role_template TEXT DEFAULT 'soldier',
            nickname TEXT DEFAULT '',
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
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS chat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            user_name TEXT,
            user_nickname TEXT,
            user_unit TEXT,
            message TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS reprimands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date DATE,
            reason TEXT,
            issued_by TEXT
        )
    ''')
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS lateness (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date DATE,
            minutes INTEGER,
            reason TEXT,
            noted_by TEXT
        )
    ''')
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS flag_duty (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE UNIQUE,
            first_user_id INTEGER,
            second_user_id INTEGER,
            assigned_by TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE,
            time TEXT,
            title TEXT,
            description TEXT,
            location TEXT,
            assigned_by TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Тех админ
    cur.execute("SELECT * FROM users WHERE login = 'tech_admin'")
    if not cur.fetchone():
        cur.execute('''
            INSERT INTO users (login, password, full_name, rank, unit, role_template, nickname,
                              can_chat_write, can_view_all_reprimands, can_issue_reprimands,
                              can_view_all_lateness, can_manage_users, can_change_unit, 
                              can_manage_flag, can_manage_schedule)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('tech_admin', hashlib.sha256('S#215-3152'.encode()).hexdigest(),
              'Технический администратор', 'Тех. админ', 'Управление', 'admin', 'Феникс',
              1, 1, 1, 1, 1, 1, 1, 1))
    
    # Руководитель
    cur.execute("SELECT * FROM users WHERE login = 'rukovoditel'")
    if not cur.fetchone():
        cur.execute('''
            INSERT INTO users (login, password, full_name, rank, unit, role_template, nickname,
                              can_chat_write, can_view_all_reprimands, can_issue_reprimands,
                              can_view_all_lateness, can_manage_users, can_change_unit, 
                              can_manage_flag, can_manage_schedule)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('rukovoditel', hashlib.sha256('123'.encode()).hexdigest(),
              'Руководитель', 'Руководитель', 'Без отделения', 'leader', 'Шеф',
              1, 1, 1, 1, 0, 1, 1, 1))
    
    # Командиры отделений
    commanders = [
        ('kom1', 'Командир 1 отделения', 'Командир отделения', '1 отделение', 'Беркут'),
        ('kom2', 'Командир 2 отделения', 'Командир отделения', '2 отделение', 'Орел'),
        ('kom3', 'Командир 3 отделения', 'Командир отделения', '3 отделение', 'Сокол'),
    ]
    
    for login, full_name, rank, unit, nickname in commanders:
        cur.execute("SELECT * FROM users WHERE login = ?", (login,))
        if not cur.fetchone():
            cur.execute('''
                INSERT INTO users (login, password, full_name, rank, unit, role_template, nickname,
                                  can_chat_write, can_view_all_reprimands, can_issue_reprimands,
                                  can_view_all_lateness, can_manage_users, can_change_unit, 
                                  can_manage_flag, can_manage_schedule)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (login, hashlib.sha256('123'.encode()).hexdigest(),
                  full_name, rank, unit, 'commander', nickname,
                  1, 0, 0, 1, 0, 1, 0, 0))
    
    # Рядовые
    soldiers = [
        ("babenko", "Артём Бабенков", "Батя"),
        ("karpeev", "Максим Карпеев", "Карп"),
        ("max", "Макс", "Макс"),
        ("viharev", "Яков Вихарев", "Яша"),
        ("tsukanov", "Saveliy Tsukanov", "Цука"),
        ("martoshev", "Максим Мартошев", "Март"),
        ("alina", "Алина", "Аля"),
        ("artem", "Артём", "Тема"),
        ("elina", "Элина", "Эля"),
        ("borovikova", "Наталья Боровикова", "Натаха"),
        ("avdey", "Авдей", "Авдей"),
        ("khalturin", "Кирилл Халтурин", "Халт"),
        ("gazizov", "Данис Газизов", "Газик"),
        ("zahar", "Захар", "Захар"),
        ("potapov", "Константин Потапов", "Потап"),
        ("khachatryan", "Маршак Хачатрян", "Маршак"),
        ("orlov", "Иван Орлов", "Орел"),
        ("borovikova_p", "Полина Боровикова", "Поля"),
        ("dima", "Дима", "Димон"),
        ("kornilov", "Родион Корнилов", "Корнил"),
        ("brotan", "Brotan", "Бро"),
        ("sultanov", "Артур Султанов", "Султан"),
        ("beloysov", "Gleb Beloysov", "Глеб")
    ]
    
    for login, full_name, nickname in soldiers:
        cur.execute("SELECT * FROM users WHERE login = ?", (login,))
        if not cur.fetchone():
            cur.execute('''
                INSERT INTO users (login, password, full_name, rank, unit, role_template, nickname,
                                  can_chat_write, can_view_all_reprimands, can_issue_reprimands,
                                  can_view_all_lateness, can_manage_users, can_change_unit, 
                                  can_manage_flag, can_manage_schedule)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (login, hashlib.sha256('123'.encode()).hexdigest(),
                  full_name, 'Рядовой', '3 отделение', 'soldier', nickname,
                  0, 1, 0, 1, 0, 0, 0, 0))
    
    conn.commit()
    conn.close()

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
        
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute('''
            SELECT id, full_name, rank, unit, role_template, nickname,
                   can_chat_write, can_view_all_reprimands, can_issue_reprimands,
                   can_view_all_lateness, can_manage_users, can_change_unit, 
                   can_manage_flag, can_manage_schedule
            FROM users
            WHERE login = ? AND password = ?
        ''', (login, password))
        user = cur.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            session['user_rank'] = user[2]
            session['user_unit'] = user[3]
            session['role_template'] = user[4]
            session['user_nickname'] = user[5] if user[5] else user[1]
            session['can_chat_write'] = user[6]
            session['can_view_all_reprimands'] = user[7]
            session['can_issue_reprimands'] = user[8]
            session['can_view_all_lateness'] = user[9]
            session['can_manage_users'] = user[10]
            session['can_change_unit'] = user[11]
            session['can_manage_flag'] = user[12]
            session['can_manage_schedule'] = user[13]
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
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    if request.method == 'POST' and session.get('can_chat_write'):
        message = request.form['message']
        if message.strip():
            cur.execute('''
                INSERT INTO chat (user_id, user_name, user_nickname, user_unit, message)
                VALUES (?, ?, ?, ?, ?)
            ''', (session['user_id'], session['user_name'], session.get('user_nickname', session['user_name']), 
                  session.get('user_unit', ''), message.strip()))
            conn.commit()
    cur.execute('''
        SELECT user_name, user_nickname, user_unit, message, timestamp 
        FROM chat 
        ORDER BY timestamp DESC LIMIT 100
    ''')
    messages = cur.fetchall()[::-1]
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
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    if request.method == 'POST':
        nickname = request.form.get('nickname', '')
        cur.execute("UPDATE users SET nickname = ? WHERE id = ?", (nickname, session['user_id']))
        conn.commit()
        session['user_nickname'] = nickname if nickname else session['user_name']
        return redirect(url_for('profile'))
        
    cur.execute("SELECT full_name, rank, unit, nickname FROM users WHERE id = ?", (session['user_id'],))
    user = cur.fetchone()
    conn.close()
    
    return render_template('profile.html',
                         user=user,
                         user_nickname=session.get('user_nickname'))

@app.route('/reprimands')
@login_required
def reprimands():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    if session.get('can_view_all_reprimands'):
        cur.execute('''
            SELECT reprimands.*, users.full_name, users.rank, users.unit, users.nickname
            FROM reprimands 
            JOIN users ON reprimands.user_id = users.id
            ORDER BY date DESC
        ''')
    else:
        cur.execute('''
            SELECT reprimands.*, users.full_name, users.rank, users.unit, users.nickname
            FROM reprimands 
            JOIN users ON reprimands.user_id = users.id
            WHERE user_id = ? 
            ORDER BY date DESC
        ''', (session['user_id'],))
    reprimands_list = cur.fetchall()
    
    soldiers = []
    if session.get('can_issue_reprimands'):
        cur.execute("SELECT id, full_name, rank, unit, nickname FROM users")
        soldiers = cur.fetchall()
    
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
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO reprimands (user_id, date, reason, issued_by)
        VALUES (?, ?, ?, ?)
    ''', (user_id, date.today(), reason, session['user_name']))
    conn.commit()
    conn.close()
    return redirect(url_for('reprimands'))

@app.route('/lateness')
@login_required
def lateness():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    if session.get('can_view_all_lateness'):
        cur.execute('''
            SELECT lateness.*, users.full_name, users.rank, users.unit, users.nickname
            FROM lateness 
            JOIN users ON lateness.user_id = users.id
            ORDER BY date DESC
        ''')
    else:
        cur.execute('''
            SELECT lateness.*, users.full_name, users.rank, users.unit, users.nickname
            FROM lateness 
            JOIN users ON lateness.user_id = users.id
            WHERE user_id = ? 
            ORDER BY date DESC
        ''', (session['user_id'],))
    
    lateness_list = cur.fetchall()
    
    soldiers = []
    if session.get('can_view_all_lateness'):
        cur.execute("SELECT id, full_name, rank, unit, nickname FROM users")
        soldiers = cur.fetchall()
    elif session.get('can_change_unit'):
        cur.execute("SELECT id, full_name, rank, unit, nickname FROM users WHERE unit = ?", (session.get('user_unit'),))
        soldiers = cur.fetchall()
    
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
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO lateness (user_id, date, minutes, reason, noted_by)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, date.today(), minutes, reason, session['user_name']))
    conn.commit()
    conn.close()
    return redirect(url_for('lateness'))

@app.route('/users')
@login_required
@has_permission('can_manage_users')
def users():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        SELECT id, login, full_name, rank, unit, role_template, nickname,
               can_chat_write, can_view_all_reprimands, can_issue_reprimands,
               can_view_all_lateness, can_manage_users, can_change_unit, 
               can_manage_flag, can_manage_schedule
        FROM users
    ''')
    users_list = cur.fetchall()
    conn.close()
    return render_template('users.html', users=users_list)

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@has_permission('can_manage_users')
def edit_user(user_id):
    conn = sqlite3.connect(DB_NAME)
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
                can_chat_write = ?,
                can_view_all_reprimands = ?,
                can_issue_reprimands = ?,
                can_view_all_lateness = ?,
                can_manage_users = ?,
                can_change_unit = ?,
                can_manage_flag = ?,
                can_manage_schedule = ?,
                unit = ?,
                rank = ?,
                nickname = ?
            WHERE id = ?
        ''', (can_chat_write, can_view_all_reprimands, can_issue_reprimands,
              can_view_all_lateness, can_manage_users, can_change_unit, 
              can_manage_flag, can_manage_schedule, unit, rank, nickname, user_id))
        conn.commit()
        return redirect(url_for('users'))
    
    cur.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cur.fetchone()
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
        
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        try:
            cur.execute('''
                INSERT INTO users (login, password, full_name, rank, unit, role_template, nickname,
                                  can_chat_write, can_view_all_reprimands, can_issue_reprimands,
                                  can_view_all_lateness, can_manage_users, can_change_unit, 
                                  can_manage_flag, can_manage_schedule)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (login, password, full_name, rank, unit, 'custom', nickname,
                  can_chat_write, can_view_all_reprimands, can_issue_reprimands,
                  can_view_all_lateness, can_manage_users, can_change_unit, 
                  can_manage_flag, can_manage_schedule))
            conn.commit()
        except sqlite3.IntegrityError:
            pass
        conn.close()
        return redirect(url_for('users'))
    
    return render_template('add_user.html')

@app.route('/change_unit', methods=['GET', 'POST'])
@login_required
@has_permission('can_change_unit')
def change_unit():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    if request.method == 'POST':
        user_id = request.form['user_id']
        new_unit = request.form['new_unit']
        cur.execute("UPDATE users SET unit = ? WHERE id = ?", (new_unit, user_id))
        conn.commit()
        return redirect(url_for('change_unit'))
    
    if session.get('can_view_all_lateness'):
        cur.execute('SELECT id, full_name, rank, unit, nickname FROM users')
    else:
        cur.execute('SELECT id, full_name, rank, unit, nickname FROM users WHERE unit = ?', (session.get('user_unit'),))
    users_list = cur.fetchall()
    conn.close()
    
    return render_template('change_unit.html', users=users_list)

@app.route('/user_profile/<int:user_id>')
@login_required
def user_profile(user_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        SELECT full_name, rank, unit, role_template, nickname,
               can_chat_write, can_view_all_reprimands, can_issue_reprimands,
               can_view_all_lateness, can_manage_users, can_change_unit
        FROM users WHERE id = ?
    ''', (user_id,))
    user_info = cur.fetchone()
    cur.execute("SELECT date, reason, issued_by FROM reprimands WHERE user_id = ? ORDER BY date DESC", (user_id,))
    reprimands_user = cur.fetchall()
    cur.execute("SELECT date, minutes, reason FROM lateness WHERE user_id = ? ORDER BY date DESC", (user_id,))
    lateness_user = cur.fetchall()
    conn.close()
    return render_template('user_profile.html',
                         user=user_info,
                         reprimands=reprimands_user,
                         lateness=lateness_user,
                         can_view_all=session.get('can_view_all_reprimands'))

@app.route('/flag_duty')
@login_required
def flag_duty():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    today_date = date.today().isoformat()
    cur.execute('''
        SELECT fd.first_user_id, fd.second_user_id, u1.full_name, u1.rank, u1.unit, u1.nickname,
               u2.full_name, u2.rank, u2.unit, u2.nickname, fd.assigned_by
        FROM flag_duty fd
        LEFT JOIN users u1 ON fd.first_user_id = u1.id
        LEFT JOIN users u2 ON fd.second_user_id = u2.id
        WHERE fd.date = ?
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
    
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    cur.execute("DELETE FROM flag_duty WHERE date = ?", (today_date,))
    
    cur.execute('''
        INSERT INTO flag_duty (date, first_user_id, second_user_id, assigned_by)
        VALUES (?, ?, ?, ?)
    ''', (today_date, first_user_id, second_user_id, session['user_name']))
    
    conn.commit()
    conn.close()
    return redirect(url_for('flag_duty'))

@app.route('/schedule')
@login_required
def schedule():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        SELECT id, date, time, title, description, location, assigned_by, created_at
        FROM schedule
        ORDER BY date DESC, time DESC
    ''')
    events = cur.fetchall()
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
    
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO schedule (date, time, title, description, location, assigned_by)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (event_date, event_time, title, description, location, session['user_name']))
    conn.commit()
    conn.close()
    return redirect(url_for('schedule'))

@app.route('/delete_schedule/<int:event_id>')
@login_required
@has_permission('can_manage_schedule')
def delete_schedule(event_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("DELETE FROM schedule WHERE id = ?", (event_id,))
    conn.commit()
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
    print("🔥 СИСТЕМА ФЕНИКС ЗАПУЩЕНА!")
    print("📱 Открой браузер: http://localhost:5000")
    print("="*50)
    print("🔑 ДАННЫЕ ДЛЯ ВХОДА:")
    print("   👑 Тех. админ: tech_admin / S#215-3152")
    print("   👑 Руководитель: rukovoditel / 123")
    print("   ⭐ Командиры: kom1 / 123, kom2 / 123, kom3 / 123")
    print("   🪖 Рядовые: любой логин / 123")
    print("="*50)
    app.run(host='0.0.0.0', port=5000, debug=True)