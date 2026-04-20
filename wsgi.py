# Импортируем ваш главный файл app, где создается объект 'app'
# Предполагается, что ваш файл называется app.py
from app import app as application

if __name__ == "__main__":
    application.run()