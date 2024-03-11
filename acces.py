from telegram.ext import Updater, MessageHandler, Filters
import sqlite3
import media
from telebot import types
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler
import telebot
import random
from datetime import datetime

# Подключение к базе данных SQLite
conn = sqlite3.connect('data.db')
cursor = conn.cursor()

# Создание таблицы user_stats, если она не существует
cursor.execute('''CREATE TABLE IF NOT EXISTS user_stats (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    username TEXT,
                    message_count INTEGER DEFAULT 0,
                    last_message_date TEXT
                  )''')


# Сохраняем изменения и закрываем соединение с базой данных
conn.commit()
conn.close()

def message_handler(update, context):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    message_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Текущая дата и время

    # Подключение к базе данных SQLite
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()

    # Проверка, существует ли уже запись о пользователе в базе данных
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user_data = cursor.fetchone()

    if user_data:
        # Если запись о пользователе существует, обновляем количество сообщений и дату последнего сообщения
        cursor.execute("UPDATE user_stats SET message_count = message_count + 1, last_message_date = ? WHERE user_id = ?", (message_date, user_id,))
    else:
        # Если запись о пользователе отсутствует, удаляем сообщение пользователя
        context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id)

        # Отправляем сообщение о регистрации и приглашение зарегистрироваться
        invite_message = f"@{username}, салют!\n\nЧтобы писать сообщения в чате, тебе сначала нужно зарегистрироваться в нашем боте. Это не займет у тебя больше минуты."
        keyboard = [[InlineKeyboardButton("Зарегистрироваться", url="t.me/Cyndycate_invaterbot?start=yjkqU3t1U8")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.send_message(chat_id=chat_id, text=invite_message, reply_markup=reply_markup)

        conn.close()
        return

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


# Функция обработки команды /me
def me(update, context):
    # Получаем идентификатор пользователя, отправившего сообщение
    user_id = update.message.from_user.id

    # Подключение к базе данных SQLite
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()

    user_data = cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    if user_data:
        referrals_count = user_data[5]
        referral_code = user_data[6]
        username = user_data[1] if user_data[1] else "Нет"
        first_name = user_data[2] if user_data[2] else "Нет"
        registration_date = user_data[4]
        referrer_id = user_data[7]
        reputation = user_data[8]

        # Получаем дату регистрации пользователя
        registration_date = user_data[4]
        registration_datetime = datetime.strptime(registration_date, "%Y-%m-%d %H:%M:%S")

        # Вычисляем разницу в днях между текущей датой и датой регистрации
        days_since_registration = (datetime.now() - registration_datetime).days

        # Получаем информацию о пригласившем пользователе
        referrer_info = ""
        referrer_username = "-"
        if referrer_id:
            referrer_data = cursor.execute("SELECT first_name, username FROM users WHERE id = ?", (referrer_id,)).fetchone()
            if referrer_data:
                referrer_name = referrer_data[0]
                referrer_username = referrer_data[1]
                referrer_info = f"Вас пригласил: {referrer_name} (@{referrer_username})\n"
            else:
                referrer_info = "Вас пригласил: -\n"
                referrer_username = "-"

        # Получаем количество сообщений пользователя из таблицы user_stats
        message_count = cursor.execute("SELECT message_count FROM user_stats WHERE user_id = ?", (user_id,)).fetchone()
        message_count = message_count[0] if message_count else 0

        # Получаем дату последней активности пользователя из таблицы user_stats
        last_activity_date = cursor.execute("SELECT last_message_date FROM user_stats WHERE user_id = ? ORDER BY last_message_date DESC LIMIT 1", (user_id,)).fetchone()

        # Проверяем, что дата не пустая
        if last_activity_date:
            last_activity_date_str = last_activity_date[0]  # Преобразуем кортеж в строку

            # Преобразуем строку в объект datetime
            last_activity_datetime = datetime.strptime(last_activity_date_str, "%Y-%m-%d %H:%M:%S")

            # Форматируем дату в нужный формат "d.m.Y"
            last_activity_formatted = last_activity_datetime.strftime("%d.%m.%Y")

            print(last_activity_formatted)  # Выводим отформатированную дату
        else:
            print('Дата не работает')
            last_activity_formatted = "Нет данных"

        # Формируем сообщение профиля с учетом количества сообщений, репутации и информации о пригласившем пользователе
        profile_message = f"Имя пользователя: @{username}\nДней в боте: {days_since_registration}\nПоследняя активность: {last_activity_formatted}\nРеферралы: {referrals_count}\nКоличество сообщений: {message_count}\nБаланс: {reputation}\n\n{referrer_info}"

        # Отправляем сообщение с профилем пользователя, используя реплай на сообщение, которое вызвало команду /me
        context.bot.send_message(chat_id=update.message.chat_id, text=profile_message, reply_to_message_id=update.message.message_id)
    else:
        context.bot.send_message(chat_id=update.message.chat_id, text="Вы еще не зарегистрированы")

    # Применяем изменения к базе данных
    conn.commit()

    # Закрываем соединение с базой данных
    conn.close()



# Функция обработки команды /top
def top(update, context):
    # Подключение к базе данных SQLite
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()

    # Получаем топ-10 пользователей по количеству репутации
    cursor.execute("SELECT username, reputation FROM users ORDER BY reputation DESC LIMIT 10")
    top_users = cursor.fetchall()

    if top_users:
        # Формируем сообщение с топ-10 пользователями
        top_message = "Топ 10 холдеров $AGAVA:\n\n"
        for index, user in enumerate(top_users, start=1):
            username = user[0]
            reputation = user[1]
            top_message += f"{index}. @{username} - {reputation} $AGAVA\n"

        # Отправляем сообщение с топ-10 пользователями
        context.bot.send_message(chat_id=update.message.chat_id, text=top_message)
    else:
        context.bot.send_message(chat_id=update.message.chat_id, text="Пока нет пользователей с репутацией")

    # Закрываем соединение с базой данных
    conn.close()

# Функция обработки команды /give
def give(update, context):
    # Подключение к базе данных SQLite
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()

    # Получаем ID пользователя, отправившего команду
    sender_user_id = update.message.from_user.id

    # Получаем количество токенов, которое отправляется
    if len(context.args) == 1:
        try:
            tokens_to_give = int(context.args[0])
        except ValueError:
            context.bot.send_message(chat_id=update.message.chat_id, text="Некорректное количество токенов.")
            return
    else:
        context.bot.send_message(chat_id=update.message.chat_id, text="Укажите количество токенов для передачи.")
        return

    # Получаем баланс отправителя
    cursor.execute("SELECT reputation FROM users WHERE id = ?", (sender_user_id,))
    sender_balance = cursor.fetchone()[0]

    # Проверяем, достаточно ли у пользователя баланса для передачи токенов
    if sender_balance >= tokens_to_give:
        # Выбираем случайного пользователя для начисления токенов
        cursor.execute("SELECT id, reputation FROM users WHERE id != ?", (sender_user_id,))
        all_users = cursor.fetchall()
        random_user_id, _ = random.choice(all_users)

        # Начисляем токены случайному пользователю
        cursor.execute("UPDATE users SET reputation = reputation + ? WHERE id = ?", (tokens_to_give, random_user_id))

        # Списываем токены у отправителя
        cursor.execute("UPDATE users SET reputation = reputation - ? WHERE id = ?", (tokens_to_give, sender_user_id))
        conn.commit()

        # Получаем username случайного пользователя
        cursor.execute("SELECT username FROM users WHERE id = ?", (random_user_id,))
        random_username = cursor.fetchone()[0]

        # Получаем username пользователя, отправившего команду
        sender_username = update.message.from_user.username

        # Формируем сообщение
        message_text = f"@{random_username}, вам случайным образом @{sender_username} начислил +{tokens_to_give} $AGAVA"

        # Отправляем сообщение
        context.bot.send_message(chat_id=update.message.chat_id, text=message_text)
    else:
        context.bot.send_message(chat_id=update.message.chat_id, text="Недостаточно токенов на балансе.")

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

# Регистрируем обработчик команды /me
me_handler = CommandHandler('me', me)
dispatcher.add_handler(me_handler)

# Регистрируем обработчик команды /top
top_handler = CommandHandler('top', top)
dispatcher.add_handler(top_handler)

# Регистрируем обработчик команды /give
give_handler = CommandHandler('give', give)
dispatcher.add_handler(give_handler)

# Запускаем бота
updater.start_polling()
updater.idle()
