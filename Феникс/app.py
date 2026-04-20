from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2
import psycopg2.extras
import hashlib
import os
from functools import wraps
from datetime import date

app = Flask(__name__)
app.secret_key = 'секретный_ключ_феникс_2024'

# ========== ПОДКЛЮЧЕНИЕ К БД ==========
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            port=os.environ.get('DB_PORT', '5432'),
            database=os.environ.get('DB_NAME', 'feniks_db'),
            user=os.environ.get('DB_USER', 'feniks_user'),
            password=os.environ.get('DB_PASSWORD', 'password')
        )
        return conn
    except Exception as e:
        print(f"Ошибка БД: {e}")
        return None

# ========== ПРОВЕРКА ПОДКЛЮЧЕНИЯ ПРИ ЗАПУСКЕ ==========
print("="*50)
print("🚀 ЗАПУСК ПРИЛОЖЕНИЯ ФЕНИКС")
print("="*50)

# Проверяем подключение к БД
conn = get_db_connection()
if conn:
    print("✅ PostgreSQL: подключено успешно")
    conn.close()
else:
    print("❌ PostgreSQL: ошибка подключения")
    print("   Проверьте переменные окружения:")
    print(f"   DB_HOST={os.environ.get('DB_HOST', 'не задан')}")
    print(f"   DB_NAME={os.environ.get('DB_NAME', 'не задан')}")
    print(f"   DB_USER={os.environ.get('DB_USER', 'не задан')}")

print("="*50)

# ========== ПРОСТОЙ МАРШРУТ ДЛЯ ПРОВЕРКИ ==========
@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>ФЕНИКС</title>
        <style>
            body { font-family: Arial; text-align: center; padding: 50px; background: linear-gradient(135deg, #0a0f1a, #1a1f2e); color: white; }
            h1 { color: #ff8c00; font-size: 48px; }
            .status { background: rgba(255,140,0,0.2); padding: 20px; border-radius: 20px; display: inline-block; margin-top: 20px; }
            .ok { color: #4ade80; }
            .error { color: #ff6b6b; }
        </style>
    </head>
    <body>
        <h1>🐦‍🔥 ФЕНИКС</h1>
        <div class="status">
            <h2>Сервер работает!</h2>
            <p>Flask + Gunicorn + PostgreSQL</p>
            <hr>
    '''

@app.route('/health')
def health():
    return {"status": "ok", "timestamp": str(date.today())}

@app.route('/test-db')
def test_db():
    conn = get_db_connection()
    if not conn:
        return {"error": "Не удалось подключиться к БД", "status": "fail"}
    
    cur = conn.cursor()
    cur.execute("SELECT NOW()")
    now = cur.fetchone()
    cur.close()
    conn.close()
    
    return {"status": "ok", "server_time": str(now[0]), "message": "База данных работает!"}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
