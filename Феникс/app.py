from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>ФЕНИКС</title>
        <style>
            body { font-family: Arial; text-align: center; padding: 50px; background: #0a0f1a; color: white; }
            h1 { color: #ff8c00; }
        </style>
    </head>
    <body>
        <h1>🐦‍🔥 ФЕНИКС</h1>
        <p>Сервер работает!</p>
        <p>Время: """ + __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
    </body>
    </html>
    """
