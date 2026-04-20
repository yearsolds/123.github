from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello, World! Сервер ФЕНИКС работает!'

@app.route('/test')
def test():
    return 'Тестовая страница работает!'
