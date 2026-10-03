# Telegram Quiz Bot

Бот для конвертации тестовых вопросов из .docx в .txt формат.

## Функции
- Загрузка .docx файлов с вопросами
- Выбор правильного варианта через кнопки
- Автоматическая конвертация в нужный формат
- Интерактивный интерфейс

## Деплой на Render.com

### 1. Создай репозиторий на GitHub
```bash
cd telegram-quiz-bot
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/ТВОЙ_USERNAME/telegram-quiz-bot.git
git push -u origin main
```

### 2. Зарегистрируйся на Render.com
- Зайди на https://render.com
- Нажми "Get Started for Free"
- Войди через GitHub

### 3. Создай Web Service
- Нажми "New +" → "Web Service"
- Подключи свой GitHub репозиторий
- Выбери `telegram-quiz-bot`

### 4. Настройки
```
Name: telegram-quiz-bot
Region: Frankfurt (ближайший для Казахстана)
Branch: main
Runtime: Python 3
Build Command: pip install -r requirements.txt
Start Command: python bot.py
Instance Type: Free
```

### 5. Добавь переменную окружения
В разделе "Environment":
- Key: `BOT_TOKEN`
- Value: `твой токен бота`

### 6. Нажми "Deploy Web Service"

Бот будет работать 24/7 (с засыпанием после 15 мин неактивности).

## Альтернативные хостинги
- **Railway.app** — 500 часов/месяц
- **Fly.io** — постоянная работа, сложнее настроить
