import os
import random
import time
import config
import telebot
from telebot import apihelper, types
from collections import defaultdict
import utils
from SQLighter import SQLighter

# inline keyboard for buttons in chat
apihelper.proxy = {
    'https': 'socks5://217.182.230.15:4485'
}

START, REPEAT, REPEAT_TYPE, REPEAT_DURATION, DATE, DURATION, CONFIRMATION, GETMASTER, GETCLIENT, DELETECLIENT, DELETEMASTER= range(11)

bot = telebot.TeleBot(config.token, threaded=False)

USER_STATE = defaultdict(lambda: START)


def get_state(message):
    return USER_STATE[message.chat.id]


def update_state(message, state):
    USER_STATE[message.chat.id] = state


@bot.message_handler(commands=['start'])
def get_schedule(message):
    # Формируем разметку
    bot.send_message(message.chat.id, 'Добро пожаловать в бот!')

####################################################
# get schedule for client and master
@bot.message_handler(commands=['get_schedule'])
def get_schedule(message):
    markup = utils.generate_markup_to_get_schedule()
    bot.send_message(message.chat.id, 'Выбери сервис', reply_markup=markup)
    if message.from_user.username == config.admin:
        update_state(message, GETMASTER)
    else:
        update_state(message, GETCLIENT)


@bot.message_handler(func=lambda message: get_state(message) == GETCLIENT)
def choose_type_repeat(message):
    if message.text == 'Расписание на сегодня':
        keyboard_hider = types.ReplyKeyboardRemove()

    if message.text == 'Расписание на завтра':
        keyboard_hider = types.ReplyKeyboardRemove()

    if message.text == 'Расписание на неделю':
        keyboard_hider = types.ReplyKeyboardRemove()

    if message.text == 'Расписание на месяц':
        keyboard_hider = types.ReplyKeyboardRemove()

    list = ['event1', 'event2', 'event3']
    keyboard = types.InlineKeyboardMarkup()
    for item in list:
        callback_button = types.InlineKeyboardButton(text=item, callback_data=item)
        keyboard.add(callback_button)
    bot.send_message(message.chat.id, "Свободные окна", reply_markup=keyboard)


@bot.message_handler(func=lambda message: get_state(message) == GETMASTER)
def choose_type_repeat(message):
    if message.text == 'Расписание на сегодня':
        keyboard_hider = types.ReplyKeyboardRemove()

    if message.text == 'Расписание на завтра':
        keyboard_hider = types.ReplyKeyboardRemove()

    if message.text == 'Расписание на неделю':
        keyboard_hider = types.ReplyKeyboardRemove()

    if message.text == 'Расписание на месяц':
        keyboard_hider = types.ReplyKeyboardRemove()

    bot.send_message(message.chat.id, message.text, reply_markup=keyboard_hider)
    list = ['event3', 'event2', 'event1']
    keyboard = types.InlineKeyboardMarkup()
    for item in list:
        callback_button = types.InlineKeyboardButton(text=item, callback_data=item)
        keyboard.add(callback_button)
    bot.send_message(message.chat.id, "Ваши размещенные сеансы", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    #if call.message:
    markup = utils.generate_markup_agree()
    bot.send_message(call.message.chat.id, 'Хотите удалить событие '+call.data+'?', reply_markup=markup)
    if get_state(call.message) == GETCLIENT:
        update_state(call.message, DELETECLIENT)
    if get_state(call.message) == GETMASTER:
        update_state(call.message, DELETEMASTER)

@bot.message_handler(func=lambda message: get_state(message) == DELETECLIENT)
def choose_type_repeat(message):
    if message.text == 'Да':
        keyboard_hider = types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id, 'Сеанс успешно отменен', reply_markup=keyboard_hider)
        #отправить уведомление мастеру

    if message.text == 'Нет':
        keyboard_hider = types.ReplyKeyboardRemove()

@bot.message_handler(func=lambda message: get_state(message) == DELETEMASTER)
def choose_type_repeat(message):
    if message.text == 'Да':
        keyboard_hider = types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id, 'Сеанс успешно отменен', reply_markup=keyboard_hider)
        #проверка свободно ли, если нет, отправить уведомление клиенту

    if message.text == 'Нет':
        keyboard_hider = types.ReplyKeyboardRemove()

####################################################
# show reserved events
# @bot.message_handler(commands=['show_reserved'])
# def get_schedule(message):


####################################################
# show reserved events
# @bot.message_handler(commands=['show_applications'])
# def get_schedule(message):


####################################################
# put master's event
@bot.message_handler(commands=['put_schedule'])
def get_schedule(message):
    markup = utils.generate_markup_to_put_schedule()
    bot.send_message(message.chat.id, 'Выбери сервис', reply_markup=markup)
    update_state(message, REPEAT)


@bot.message_handler(func=lambda message: get_state(message) == REPEAT)
def choose_type_repeat(message):
    if message.text == 'Одиночное окно':
        keyboard_hider = types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id, 'Напиши дату и время начала окна', reply_markup=keyboard_hider)
        update_state(message, DATE)
    if message.text == 'Повторяющееся окно':
        markup = utils.generate_markup_to_get_type_of_repeat()
        bot.send_message(message.chat.id, 'Выбери как будет повторяться окно', reply_markup=markup)
        update_state(message, REPEAT_TYPE)


@bot.message_handler(func=lambda message: get_state(message) == REPEAT_TYPE)
def choose_type_repeat(message):
    # if valid message
    markup = utils.generate_markup_to_get_duration_of_repeat()
    bot.send_message(message.chat.id, 'Выбери как долго окно будет повторяться', reply_markup=markup)
    update_state(message, REPEAT_DURATION)


@bot.message_handler(func=lambda message: get_state(message) == REPEAT_DURATION)
def choose_type_repeat(message):
    # if valid message
    keyboard_hider = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, 'Напиши дату и время начала окна', reply_markup=keyboard_hider)
    update_state(message, DATE)


@bot.message_handler(func=lambda message: get_state(message) == DATE)
def choose_type_repeat(message):
    # if valid message
    bot.send_message(message.chat.id, 'Напиши длительность окна в минутах')
    update_state(message, DURATION)


@bot.message_handler(func=lambda message: get_state(message) == DURATION)
def choose_type_repeat(message):
    # if valid message
    markup = utils.generate_markup_agree()
    bot.send_message(message.chat.id, 'Добавить такое-то событие?', reply_markup=markup)
    update_state(message, CONFIRMATION)


@bot.message_handler(func=lambda message: get_state(message) == CONFIRMATION)
def choose_type_repeat(message):
    # if valid message
    keyboard_hider = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, 'Окно успешно добавлено', reply_markup=keyboard_hider)
    update_state(message, START)


####################################################
@bot.message_handler(func=lambda message: True, content_types=['text'])
def check_answer(message):
    answer = message
    print(answer)
    if not answer:
        bot.send_message(message.chat.id, 'Чтобы начать выберите команду /getschedule /putschedule')
    else:
        keyboard_hider = types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id, 'Так точно!', reply_markup=keyboard_hider)


if __name__ == '__main__':
    print('start')
    while True:
        try:
            # utils.count_rows()
            random.seed()
            bot.polling(none_stop=True)
        except:
            time.sleep(3)
