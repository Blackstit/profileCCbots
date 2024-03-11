import telebot
from telebot import types
import sqlite3 as sql
from datetime import datetime
import random
import string
import media

# База данных
con = sql.connect("data.db", check_same_thread=False)
cur = con.cursor()
cur.execute('''CREATE TABLE IF NOT EXISTS users
             (id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, last_name TEXT, registration_date TEXT, referrals INTEGER, referral_code TEXT, referrer_id INTEGER, reputation INTEGER DEFAULT 0)''')

cur.execute('''CREATE TABLE IF NOT EXISTS completed_tasks (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    task_name TEXT,
    UNIQUE(user_id, task_name)
);''')

# Ваш бот
token = "6536069812:AAGnGeg6oXtsvl7CcRZgb0PfV5CyhSb3pyI"
bot = telebot.TeleBot(token)

# ID вашего канала
chan_id = -1001850988863

# Клавиатура для проверки подписки
клавиатура_inline = telebot.types.InlineKeyboardMarkup()
подписаться = telebot.types.InlineKeyboardButton(text="Подписаться", url="https://t.me/agavacrypto")
вступить_в_чат = telebot.types.InlineKeyboardButton(text="Вступить в чат", url="https://t.me/+TIBhBif_kQYxZjM0")
проверить = telebot.types.InlineKeyboardButton(text="Проверить", callback_data="check")
клавиатура_inline.add(подписаться)
клавиатура_inline.add(вступить_в_чат)
клавиатура_inline.add(проверить)


# Клавиатура для профиля
клавиатура_профиля = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
кнопка_профиль = telebot.types.KeyboardButton("Профиль 👤")
кнопка_о_нас = telebot.types.KeyboardButton("О нас 🌐")  # Используем подходящий эмодзи для кнопки "О нас"
клавиатура_профиля.row(кнопка_профиль, кнопка_о_нас)


# Функция для генерации случайного реферрального кода
def generate_referral_code():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.chat.id
    username = message.chat.username
    first_name = message.chat.first_name
    last_name = message.chat.last_name
    registration_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Проверяем, передан ли реферальный код в команде "/start"
    referer_code = None
    parts = message.text.split()
    if len(parts) > 1:
        referer_code = parts[1]

    print(f"{username} - Реферральный код: {referer_code} мессадж: {message.text}")

    # Проверяем, зарегистрирован ли уже пользователь
    user_data = cur.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    print(f"{username} - Старт. юзер дата: {user_data}")
    if not user_data:
        # Генерируем уникальный реферральный код
        referral_code = generate_referral_code()
        print(f"{username} - Старт. реф код ген: {referral_code}")
        # Поиск пользователя с реферральным кодом
        referrer_id = None
        if referral_code:
            referrer_data = cur.execute("SELECT id FROM users WHERE referral_code = ?", (referer_code,)).fetchone()
            if referrer_data:
                referrer_id = referrer_data[0]

        # Добавляем пользователя в базу данных
        cur.execute("INSERT INTO users (id, username, first_name, last_name, registration_date, referrals, referral_code, referrer_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (user_id, username, first_name, last_name, registration_date, 0, referral_code, referrer_id))
        # Вставляем запись в таблицу user_stats
        cur.execute("INSERT INTO user_stats (user_id, username, message_count) VALUES (?, ?, 0)", (user_id, username))
        con.commit()

        # Отправляем сообщение о подписке и кнопку профиля
        bot.send_message(user_id, f"Добро пожаловать в мир AGAVA CRYPTO!", reply_markup=клавиатура_профиля)
        bot.send_message(user_id, """Приветствуем тебя в нашем комьюнити крипто-энтузиастов!

Мы ищем активных участников, готовых вкладывать свое время и энергию в наше сообщество, чтобы вместе стремиться к успеху!

Прежде чем присоединиться к нам, подпишись на наш Telegram-канал и создай свой профиль в этом боте.

Здесь ты сможешь отслеживать свой прогресс, получать награды и поощрения от AGAVA CRYPTO! Давай двигаться к успеху вместе!""", reply_markup=клавиатура_inline)
    else:
        # Отправляем приветственное сообщение
        bot.send_message(user_id, "С возвращением!", reply_markup=клавиатура_профиля)



@bot.callback_query_handler(func=lambda call: call.data == "check")
def c_listener(call):
    user_id = call.message.chat.id
    x = bot.get_chat_member(chan_id, user_id)

    if x.status in ["member", "creator", "administrator"]:
        user_data = cur.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        print(f"Чек, юзер дата: {user_data}")
        if user_data:
            # Получаем ID реферрера
            referrer_id = user_data[7]
            if referrer_id is not None:
                # Увеличиваем счетчик рефералов
                cur.execute("UPDATE users SET referrals = referrals + 1 WHERE id = ?", (referrer_id,))
                con.commit()
                # Отправка уведомления рефереру о новом реферале
                referrer_data = cur.execute("SELECT first_name, username, referrals FROM users WHERE id = ?", (referrer_id,)).fetchone()
                if referrer_data:
                    referrer_name = referrer_data[0]
                    referrer_username = referrer_data[1]
                    referrals_count = referrer_data[2]
                    message_text = f"""🎉 У вас новый реферал! {referrer_name} (@{referrer_username})

                    Вам начислено +10 $AGAVA!!!!
                    Всего рефералов: {referrals_count}"""
                    bot.send_message(referrer_id, message_text)

                # Начисление 10 очков репутации за нового реферала
                cur.execute("UPDATE users SET reputation = reputation + 10 WHERE id = ?", (referrer_id,))
                con.commit()

        # Удаление кнопки "Проверить"
        bot.edit_message_text(chat_id=user_id, message_id=call.message.message_id, text="Спасибо за подписку! Добро пожаловать!", reply_markup=None)
    else:
        # Удаление сообщения с запросом подписаться и отправка нового сообщения
        bot.edit_message_text(chat_id=user_id, message_id=call.message.message_id, text="Чтобы продолжить, сначала подпишитесь на наш канал и на наш чат", reply_markup=клавиатура_inline)

# Обработчик нажатия на кнопку "О нас"
@bot.message_handler(func=lambda message: message.text == "О нас 🌐")
def about_us(message):
    # Текст приветствия и информация о сообществе
    about_text = ("Приветствуем тебя в нашем комьюнити крипто-энтузиастов!\n\n"
                  "Мы ищем активных участников, готовых вкладывать свое время и энергию в наше сообщество, чтобы вместе стремиться к успеху!\n\n"
                  "Прежде чем присоединиться к нам, подпишись на наш Telegram-канал и создай свой профиль в этом боте.\n\n"
                  "Здесь ты сможешь отслеживать свой прогресс, получать награды и поощрения от AGAVA CRYPTO! Давай двигаться к успеху вместе!")

    # Создание инлайн кнопок
    keyboard = types.InlineKeyboardMarkup()
    btn_agava_crypto = types.InlineKeyboardButton("AGAVA CRYPTO", url="https://t.me/agavacrypto")
    btn_agava_crypto_chat = types.InlineKeyboardButton("AGAVA CRYPTO CHAT", url="https://t.me/agavacryptochat")
    
    # Добавление кнопок на клавиатуру
    keyboard.row(btn_agava_crypto)
    keyboard.row(btn_agava_crypto_chat)

    # Отправка сообщения с текстом и инлайн кнопками
    bot.send_message(message.chat.id, about_text, reply_markup=keyboard)

from telebot import types

@bot.message_handler(func=lambda message: message.text == "Профиль 👤")
def profile(message):
    user_id = message.chat.id
    user_data = cur.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    if user_data:
        referrals_count = user_data[5]
        referral_code = user_data[6]
        username = user_data[1] if user_data[1] else "Нет"
        first_name = user_data[2] if user_data[2] else "Нет"
        last_name = user_data[3] if user_data[3] else "Нет"
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
        if referrer_id:
            referrer_data = cur.execute("SELECT first_name, username FROM users WHERE id = ?", (referrer_id,)).fetchone()
            if referrer_data:
                referrer_name = referrer_data[0]
                referrer_username = referrer_data[1]
                referrer_info = f"Вас пригласил: {referrer_name} (@{referrer_username})\n"

        # Получаем количество сообщений пользователя из таблицы user_stats
        message_count = cur.execute("SELECT message_count FROM user_stats WHERE user_id = ?", (user_id,)).fetchone()
        message_count = message_count[0] if message_count else 0

        # Получаем дату последней активности пользователя из таблицы user_stats
        last_activity_date = cur.execute("SELECT last_message_date FROM user_stats WHERE user_id = ? ORDER BY last_message_date DESC LIMIT 1", (user_id,)).fetchone()
        last_activity_date = last_activity_date[0] if last_activity_date else "Нет данных"

        # Формируем сообщение профиля с учетом количества сообщений, репутации и информации о пригласившем пользователе
        profile_message = f"Имя: {first_name}\nФамилия: {last_name}\nИмя пользователя: @{username}\nДней в боте: {days_since_registration}\nПоследняя активность: {last_activity_date}\nРеферралы: {referrals_count}\nКоличество сообщений: {message_count}\n$AGAVA: {reputation}\n\n{referrer_info}Ваша реферальная ссылка: t.me/Cyndycate_invaterbot?start={referral_code}"

        # Создаем клавиатуру для заданий
        tasks_keyboard = types.InlineKeyboardMarkup(row_width=1)
        task_button = types.InlineKeyboardButton("Задания 🎯 ", callback_data="profile_tasks")
        tasks_keyboard.add(task_button)

        bot.send_photo(user_id, media.profile_img, caption=profile_message, reply_markup=tasks_keyboard)
    else:
        bot.send_message(user_id, "Вы еще не зарегистрированы")




@bot.callback_query_handler(func=lambda call: call.data == "profile_tasks")
def profile_tasks_handler(call):
    # Создаем клавиатуру для заданий
    tasks_keyboard = types.InlineKeyboardMarkup(row_width=1)
    
    # Кнопка для проверки 10 сообщений в чате
    button_10_messages = types.InlineKeyboardButton("10 сообщений в чате", callback_data="check_10_messages")
    tasks_keyboard.add(button_10_messages)
    
    # Кнопка для проверки 30 сообщений в чате
    button_30_messages = types.InlineKeyboardButton("30 сообщений в чате", callback_data="check_30_messages")
    tasks_keyboard.add(button_30_messages)
    
    # Кнопка для проверки 5 рефералов
    button_5_referrals = types.InlineKeyboardButton("5 реффералов", callback_data="check_5_referrals")
    tasks_keyboard.add(button_5_referrals)
    
    # Кнопка для закрытия сообщения
    button_close = types.InlineKeyboardButton("Закрыть", callback_data="close")
    tasks_keyboard.add(button_close)

    # Отправляем сообщение пользователю
    bot.send_message(call.message.chat.id, "Выполняй задания и зарабатывай $AGAVA", reply_markup=tasks_keyboard)


def add_completed_task(user_id, task_name):
    cur.execute("INSERT OR IGNORE INTO completed_tasks (user_id, task_name) VALUES (?, ?)", (user_id, task_name))
    con.commit()

def check_task_completed(user_id, task_name):
    cur.execute("SELECT * FROM completed_tasks WHERE user_id = ? AND task_name = ?", (user_id, task_name))
    return cur.fetchone() is not None



@bot.callback_query_handler(func=lambda call: call.data == "check_10_messages")
def check_10_messages_handler(call):
    user_id = call.from_user.id
    message_count = cur.execute("SELECT message_count FROM user_stats WHERE user_id = ?", (user_id,)).fetchone()[0]

    if message_count >= 10 and not check_task_completed(user_id, "check_10_messages"):
        cur.execute("UPDATE users SET reputation = reputation + 50 WHERE id = ?", (user_id,))
        con.commit()
        add_completed_task(user_id, "check_10_messages")  # Добавляем задание в список выполненных
        bot.answer_callback_query(call.id, text="Вы получили +50 очков репутации", show_alert=True)
    elif check_task_completed(user_id, "check_10_messages"):
        bot.answer_callback_query(call.id, text="Это задание уже выполнено", show_alert=True)
    else:
        bot.answer_callback_query(call.id, text="У вас недостаточно сообщений в чате")

@bot.callback_query_handler(func=lambda call: call.data == "check_30_messages")
def check_30_messages_handler(call):
    user_id = call.from_user.id
    message_count = cur.execute("SELECT message_count FROM user_stats WHERE user_id = ?", (user_id,)).fetchone()[0]

    if message_count >= 30 and not check_task_completed(user_id, "check_30_messages"):
        cur.execute("UPDATE users SET reputation = reputation + 200 WHERE id = ?", (user_id,))
        con.commit()
        add_completed_task(user_id, "check_30_messages")  # Добавляем задание в список выполненных
        bot.answer_callback_query(call.id, text="Вы получили +200 очков репутации", show_alert=True)
    elif check_task_completed(user_id, "check_30_messages"):
        bot.answer_callback_query(call.id, text="Это задание уже выполнено", show_alert=True)
    else:
        bot.answer_callback_query(call.id, text="У вас недостаточно сообщений в чате")

@bot.callback_query_handler(func=lambda call: call.data == "check_5_referrals")
def check_5_referrals_handler(call):
    user_id = call.from_user.id
    referrals_count = cur.execute("SELECT referrals FROM users WHERE id = ?", (user_id,)).fetchone()[0]

    if referrals_count >= 5 and not check_task_completed(user_id, "check_5_referrals"):
        cur.execute("UPDATE users SET reputation = reputation + 200 WHERE id = ?", (user_id,))
        con.commit()
        add_completed_task(user_id, "check_5_referrals")  # Добавляем задание в список выполненных
        bot.answer_callback_query(call.id, text="Вы получили +200 очков репутации", show_alert=True)
    elif check_task_completed(user_id, "check_5_referrals"):
        bot.answer_callback_query(call.id, text="Это задание уже выполнено", show_alert=True)
    else:
        bot.answer_callback_query(call.id, text="У вас недостаточно реферралов")

@bot.callback_query_handler(func=lambda call: call.data == "close")
def close_handler(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)




if __name__ == "__main__":
    bot.polling()
