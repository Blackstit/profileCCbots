from telegram.ext import Updater, MessageHandler, Filters
import sqlite3
import datetime

# Подключение к базе данных SQLite
conn = sqlite3.connect('data.db')
cursor = conn.cursor()

# Создание таблицы user_stats, если она не существует
cursor.execute('''CREATE TABLE IF NOT EXISTS user_stats (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    username TEXT,
                    message_count INTEGER DEFAULT 0,
                    message_date TEXT
                  )''')

# Сохраняем изменения и закрываем соединение с базой данных
conn.commit()
conn.close()

# Функция для обработки входящих сообщений из определенного чата и сохранения статистики сообщений по пользователям
def message_handler(update, context):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    message_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Подключение к базе данных SQLite
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()

    # Проверка, существует ли уже запись о пользователе в базе данных
    cursor.execute("SELECT * FROM user_stats WHERE user_id = ?", (user_id,))
    user_data = cursor.fetchone()

    if user_data:
        # Если запись о пользователе существует, обновляем количество сообщений и дату последнего сообщения
        cursor.execute("UPDATE user_stats SET message_count = message_count + 1, message_date = ? WHERE user_id = ?", (message_date, user_id,))
    else:
        # Если запись о пользователе отсутствует, добавляем новую запись
        cursor.execute("INSERT INTO user_stats (user_id, username, message_count, message_date) VALUES (?, ?, 1, ?)", (user_id, username, message_date))

    # Получаем текущее количество сообщений пользователя
    cursor.execute("SELECT message_count FROM user_stats WHERE user_id = ?", (user_id,))
    message_count = cursor.fetchone()[0]

    # Если количество сообщений кратно 10, начисляем 1 очко репутации
    if message_count % 10 == 0:
        # Получаем текущее количество очков репутации пользователя
        cursor.execute("SELECT reputation FROM users WHERE id = ?", (user_id,))
        reputation = cursor.fetchone()[0]
        
        # Увеличиваем репутацию на 1 и обновляем запись в базе данных
        new_reputation = reputation + 1
        cursor.execute("UPDATE users SET reputation = ? WHERE id = ?", (new_reputation, user_id))

    # Применяем изменения к базе данных
    conn.commit()

    # Закрываем соединение с базой данных
    conn.close()

# Токен вашего бота
TOKEN = '6908271386:AAGps8jBks7fxN84EmK7H4OzHRipK4PhJHU'

# Создаем объект updater и передаем ему токен вашего бота
updater = Updater(token=TOKEN, use_context=True)

# Получаем из него диспетчер сообщений
dispatcher = updater.dispatcher

# Регистрируем обработчик сообщений для конкретного чата
dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), message_handler))

# Запускаем бота
updater.start_polling()
updater.idle()
