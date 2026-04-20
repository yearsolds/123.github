from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return 'ФЕНИКС РАБОТАЕТ!'

@app.route('/test')
def test():
    return 'Сервер запущен успешно!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
