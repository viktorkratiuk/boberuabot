# 📹 Bober UA – Простий Telegram-бот (Aiogram 3) для завантаження відео YouTube/Instagram/TikTok

[English](README.md)

### 📌 Вимоги
- Python 3.10+

### 🛠️ Налаштування
1. Скопіюйте `.env` з `.env.dist` та додайте ваш токен:
```
BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
```

2. Встановіть залежності (рекомендовано у віртуальному середовищі):
```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. ▶️ Запуск бота:
```
python bot.py
```

### 🐳 Налаштування з Docker
1. Створіть `.env` з вашим токеном:
```
BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
```
2. Зберіть і запустіть:
```
docker compose up -d --build
```
3. Перегляд логів:
```
docker compose logs -f
```
4. Оновлення коду й перезбірка:
```
git pull
docker compose up -d --build
```

### 📥 Використання
Надішліть боту посилання на TikTok або Instagram Reels. Бот спробує видалити ваше повідомлення з посиланням і надіслати відео. У підписі буде вказано ваш Telegram username (або ім'я, якщо username відсутній)

### 👥 Використання в групах
1. У BotFather вимкніть режим приватності для бота:
   - Відправте `/setprivacy` → оберіть вашого бота → `Disable`.
2. Додайте бота до групи як адміністратора щоб надати права на видалення та надсилання повідомлень