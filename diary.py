import telebot
from telebot import types
import sqlite3

token = "TOKEN"
bot = telebot.TeleBot(token)

def database():
    row = sqlite3.connect("schedule.db")
    cursor = row.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day TEXT,
            name TEXT,
            time TEXT
        )
    """)

    row.close()


database()

@bot.message_handler(commands = ['start'])
def start(message):
    keyboard = types.ReplyKeyboardMarkup()
    button_1 = types.KeyboardButton(text='Додати подію')
    button_2 = types.KeyboardButton(text='Видалити подію')
    button_3 = types.KeyboardButton(text='Редагувати події')
    button_4 = types.KeyboardButton(text='Переглянути події')
    keyboard.add(button_1, button_2)
    keyboard.add(button_3, button_4)

    bot.send_message(message.chat.id, "Привіт у власному щоденнику!", reply_markup = keyboard)




@bot.message_handler(func= lambda message: message.text == 'Додати подію')
def add_lesson(message):
    msg = bot.send_message(message.chat.id, "Введи день події")

    bot.register_next_step_handler(msg, get_day)

def get_day(message):
    day = message.text

    msg = bot.send_message(message.chat.id, "Введи назву події:")
    bot.register_next_step_handler(msg, get_name, day)

def get_name(message, day):
    name = message.text

    msg = bot.send_message(message.chat.id, "Введи час події")
    bot.register_next_step_handler(msg, save_event, day, name, )

def save_event(message, day, name):
    time = message.text

    row = sqlite3.connect("schedule.db")
    cursor = row.cursor()

    cursor.execute("""INSERT INTO schedule (day, name, time) VALUES(?, ?, ?)""",
                   (day, name, time))
    row.commit()
    row.close()

    bot.send_message(message.chat.id, f"Подію додано!\n\n"
        f"День: {day}\n"
        f"Подія: {name}\n"
        f"Час: {time}")

@bot.message_handler(func = lambda message: message.text == "Переглянути події")
def show_lessons(message):
    row = sqlite3.connect("schedule.db")
    cursor = row.cursor()

    cursor.execute("SELECT * FROM schedule")
    result = cursor.fetchall()
    row.close()

    for row in result:
        bot.send_message(
            message.chat.id,
            f"День: {row[1]}\n"
            f"Подія: {row[2]}\n"
            f"Час: {row[3]}"
        )


    if len(result) == 0:
        bot.send_message(message.chat.id, "Не знайдено записів")

@bot.message_handler(func = lambda message: message.text == 'Видалити подію')
def delete_less_step1(message):
    keyboard2 = types.InlineKeyboardMarkup()
    button_1 = types.InlineKeyboardButton('Видалити одну подію', callback_data = "one")
    button_2 = types.InlineKeyboardButton('Видалити події на день', callback_data = "two")
    keyboard2.add(button_1, button_2)

    bot.send_message(message.chat.id, "Виберіть що ви хочкете видалити",  reply_markup = keyboard2)

@bot.callback_query_handler(func = lambda call: call.data == 'one')
def delete_less_step2(call):
    bot.send_message(call.message.chat.id, 'Введіть id запису, який потрібно видалити:')

    bot.register_next_step_handler(call.message, delete_by_id)

def delete_by_id(message):
    try:
        event_id = int(message.text)

        row = sqlite3.connect('schedule.db')
        cursor = row.cursor()

        cursor.execute("DELETE FROM schedule WHERE time = ?", (event_id,))

        if cursor.rowcount == 0:
            bot.send_message(message.chat.id, "Такої події не знайдено")
        else:
            row.commit()
            bot.send_message(message.chat.id, "Подію успішно видалено!")

        row.close()

    except ValueError:
        bot.send_message(message.chat.id(message.chat.id, "ID має бути числом."))

@bot.callback_query_handler(func = lambda call: call.data == 'two')
def delete_day(call):
    bot.send_message(call.message.chat.id, "Введіть день")

    bot.register_next_step_handler(call.message, delete_day_final)

def delete_day_final(message):
    try:
        event_day = str(message.text)

        row = sqlite3.connect('schedule.db')
        cursor = row.cursor()

        cursor.execute("DELETE FROM schedule WHERE day = ?", (event_day,))

        if cursor.rowcount == 0:
            bot.send_message(message.chat.id, "Такої події не знайдено")
        else:
            row.commit()
            bot.send_message(message.chat.id, "Подію успішно видалено!")

        row.close()

    except ValueError:
        bot.send_message(message.chat.id(message.chat.id, "Введіть день тижня."))

@bot.message_handler(func=lambda message: message.text == "Редагувати події")
def remake_lessons(message):
    msg = bot.send_message(
        message.chat.id,
        "Напишіть час старої події, яку треба відредагувати"
    )
    bot.register_next_step_handler(msg, remake_lessons_step2)


def remake_lessons_step2(message):
    old_time = message.text

    msg = bot.send_message(message.chat.id, "Напишіть нову назву події")
    bot.register_next_step_handler(msg, remake_lesson_step3, old_time)


def remake_lesson_step3(message, old_time):
    name = message.text

    msg = bot.send_message(message.chat.id, "Напишіть нову дату")
    bot.register_next_step_handler(
        msg, remake_lesson_step4, old_time, name
    )


def remake_lesson_step4(message, old_time, name):
    date = message.text

    msg = bot.send_message(message.chat.id, "Введіть новий час події")
    bot.register_next_step_handler(
        msg, remake_lesson_final_step, old_time, name, date
    )


def remake_lesson_final_step(message, old_time, name, date):
    new_time = message.text

    row = sqlite3.connect("schedule.db")
    cursor = row.cursor()

    cursor.execute("""
        UPDATE schedule
        SET day = ?, name = ?, time = ?
        WHERE time = ?
    """, (date, name, new_time, old_time))

    updated_rows = cursor.rowcount
    row.commit()
    row.close()

    if updated_rows > 0:
        bot.send_message(
            message.chat.id,
            f"Подію відредаговано!\n"
            f"День: {date}\n"
            f"Подія: {name}\n"
            f"Час: {new_time}"
        )
    else:
        bot.send_message(
            message.chat.id,
            "Подію з таким старим часом не знайдено.")


bot.polling()