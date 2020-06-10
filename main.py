import logging
import random
import os
import telebot
from telebot import apihelper, types
from collections import defaultdict
import utils
import json
import requests
import datetime, time
import os
from flask import Flask, request

apihelper.proxy = {
    'https': 'socks5://104.248.63.18:30588'
}

START, REPEAT, REPEAT_TYPE, REPEAT_DURATION, DATE, DURATION, CONFIRMATION, GETMASTER, GETCLIENT, DELETECLIENT, DELETEMASTER, EVENTRESERVE, SHOWRESERVED, SHOWAPPLICATIONS, APPROVEAPPLICATIONS = range(
    15)

bot = telebot.TeleBot(os.environ["TOKEN"], threaded=False)

USER_STATE = defaultdict(lambda: START)

CHOSEN_EVENT = defaultdict(lambda: 1)

MASTER_EVENT = {}


def get_state(message):
    return USER_STATE[message.chat.id]


def update_state(message, state):
    USER_STATE[message.chat.id] = state

def get_event(message):
    return CHOSEN_EVENT[message.chat.id]

def update_event(message, state):
    CHOSEN_EVENT[message.chat.id] = state

@bot.message_handler(commands=['start'])
def get_schedule(message):
    # Формируем разметку
    id = message.chat.id
    if id == os.environ["CHAT"]:
        role = 'MASTER'
    else:
        role = 'USER'
    username = ""
    if message.from_user.first_name:
        username = message.from_user.first_name
        if message.from_user.last_name:
            username += " " + message.from_user.last_name
    response = requests.post('https://pilka.herokuapp.com/authorization',
                             json={'username': username,
                                   'phoneNumber': "", 'telegramId': id,  'role': role})
    if (response.status_code == 200):
        bot.send_message(message.chat.id, 'Добро пожаловать в бот!')
    else:
        bot.send_message(message.chat.id, 'Мы уже знакомы с вами:)')



####################################################
# get schedule for client and master
@bot.message_handler(commands=['get_schedule'])
def get_schedule(message):
    markup = utils.generate_markup_to_get_schedule()
    bot.send_message(message.chat.id, 'Выбери сервис', reply_markup=markup)
    id = message.chat.id
    if id == os.environ["CHAT"]:
        update_state(message, GETMASTER)
    else:
        update_state(message, GETCLIENT)

####################################################
# put master's event
@bot.message_handler(commands=['put_schedule'])
def get_schedule(message):
    print('put_schedule')
    markup = utils.generate_markup_to_put_schedule()
    id = message.chat.id
    if id == os.environ["CHAT"]:
        bot.send_message(message.chat.id, 'Выбери сервис', reply_markup=markup)
        MASTER_EVENT['mul'] = 1
        MASTER_EVENT['interval'] = 1
        MASTER_EVENT['freq'] = 'DAILY'
        MASTER_EVENT['count'] = 1
        MASTER_EVENT['byweekday'] = ""
        update_state(message, REPEAT)
    else:
        bot.send_message(message.chat.id, 'Вам не разрешено данное дейтсвие', reply_markup=markup)

####################################################
# show reserved events
@bot.message_handler(commands=['show_reserved'])
def get_schedule(message):
    id = message.chat.id
    if id == os.environ["CHAT"]:
        bot.send_message(message.chat.id, "Вам недоступно это действие")
        return
    response = requests.get('https://pilka.herokuapp.com/rest/event/get/clientEvents', params={"clientTelegramId": id})
    print(response.text)
    if len(response.text) <= 2:
        bot.send_message(message.chat.id, "Сеансов не найдено")
    else:
        keyboard = types.InlineKeyboardMarkup()
        update_state(message, SHOWRESERVED)
        for item in json.loads(response.text):
            date_start = datetime.datetime.fromtimestamp(item['dateStart'])
            print(date_start)
            date_end = datetime.datetime.fromtimestamp(item['dateEnd'])
            print(date_end)
            if item['eventStatus'] == "APPROVED":
                callback_button = types.InlineKeyboardButton(
                    text="Подтвержден\n" + date_start.strftime('%d.%m.%y %H:%M') +
                         " - " + date_end.strftime('%H:%M'), callback_data=item['id'])
            else:
                callback_button = types.InlineKeyboardButton(text="Не подтвержден\n" + date_start.strftime('%d.%m.%y %H:%M') +
                                                                  " - " + date_end.strftime('%H:%M'),
                                                             callback_data=item['id'])
            keyboard.add(callback_button)
        bot.send_message(message.chat.id, "Ваши сеансы", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: get_state(call.message) == SHOWRESERVED)
def callback_inline(call):
    markup = utils.generate_markup_agree()
    response = requests.get('https://pilka.herokuapp.com/rest/event/get',
                            params={"eventId": call.data})
    answer = response.json()

    date_start = datetime.datetime.fromtimestamp(answer['dateStart'])
    date_end = datetime.datetime.fromtimestamp(answer['dateEnd'])

    bot.send_message(call.message.chat.id, 'Хотите отменить сеанс ' + date_start.strftime('%d.%m.%y %H:%M') +
                                                " - " + date_end.strftime('%H:%M') + '?', reply_markup=markup)
    update_event(call.message, call.data)
    update_state(call.message, DELETECLIENT)

####################################################
# show events applications
@bot.message_handler(commands=['show_applications'])
def get_schedule(message):
    id = message.chat.id
    if id != os.environ["CHAT"]:
        bot.send_message(message.chat.id, "Вам недоступно это действие")
        return
    response = requests.get('https://pilka.herokuapp.com/rest/event/get/review',
                            params={"masterTelegramId": os.environ["CHAT"]})
    print(response.text)
    if len(response.text) <= 2:
        bot.send_message(message.chat.id, "Заявок не найдено")
    else:
        keyboard = types.InlineKeyboardMarkup()
        update_state(message, SHOWAPPLICATIONS)
        for item in json.loads(response.text):
            date_start = datetime.datetime.fromtimestamp(item['dateStart'])
            print(date_start)
            date_end = datetime.datetime.fromtimestamp(item['dateEnd'])
            print(date_end)
            callback_button = types.InlineKeyboardButton(
                    text=item["client"]['username']+"\n" + date_start.strftime('%d.%m.%y %H:%M') +
                         " - " + date_end.strftime('%H:%M'), callback_data=item['id'])
            keyboard.add(callback_button)
        bot.send_message(message.chat.id, "Ваши заявки", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: get_state(call.message) == SHOWAPPLICATIONS)
def callback_inline(call):
    markup = utils.generate_markup_agree()

    response = requests.get('https://pilka.herokuapp.com/rest/event/get',
                            params={"eventId": call.data})
    answer = response.json()

    date_start = datetime.datetime.fromtimestamp(answer['dateStart'])
    date_end = datetime.datetime.fromtimestamp(answer['dateEnd'])

    bot.send_message(call.message.chat.id, 'Подтверждаете сеанс ' + date_start.strftime('%d.%m.%y %H:%M') +
                     " - " + date_end.strftime('%H:%M') + '?', reply_markup=markup)
    update_event(call.message, call.data)
    update_state(call.message, APPROVEAPPLICATIONS)

@bot.message_handler(func=lambda message: get_state(message) == APPROVEAPPLICATIONS)
def choose_type_repeat(message):
    response = requests.get('https://pilka.herokuapp.com/rest/event/get',
                            params={"eventId": get_event(message)})
    answer = response.json()
    date_start = datetime.datetime.fromtimestamp(answer['dateStart'])
    date_end = datetime.datetime.fromtimestamp(answer['dateEnd'])

    if message.text == 'Да':
        keyboard_hider = types.ReplyKeyboardRemove()
        response = requests.put('https://pilka.herokuapp.com/rest/event/approve', json={"eventId": str(get_event(message)), "approval": "APPROVAL"})

        if response.status_code == 200:
            bot.send_message(message.chat.id, 'Сеанс ' + date_start.strftime('%d.%m.%y %H:%M') +
                     " - " + date_end.strftime('%H:%M') + ' успешно подтвержден', reply_markup=keyboard_hider)
            bot.send_message(answer['client']['telegramId'], "Cеанс " + date_start.strftime('%d.%m.%y %H:%M') +
                     " - " + date_end.strftime('%H:%M') + " был подтвержен")
        else:
            bot.send_message(message.chat.id, 'Произошла ошибка при подстверждении сеанса ' + date_start.strftime('%d.%m.%y %H:%M') +
                     " - " + date_end.strftime('%H:%M'), reply_markup=keyboard_hider)

    if message.text == 'Нет':
        keyboard_hider = types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id, 'Заявка ' + date_start.strftime('%d.%m.%y %H:%M') +
                     " - " + date_end.strftime('%H:%M') + ' была отклонена', reply_markup=keyboard_hider)
        bot.send_message(answer['client']['telegramId'], "Cеанс " + date_start.strftime('%d.%m.%y %H:%M') +
                     " - " + date_end.strftime('%H:%M') + " не был подтвержен")
    update_state(message, START)

@bot.message_handler(func=lambda message: get_state(message) == GETCLIENT)
def choose_type_repeat(message):
    json_req = {}
    keyboard_hider = types.ReplyKeyboardRemove()
    if message.text == 'Расписание на сегодня':
        today = datetime.datetime.today()
        start = datetime.datetime(year=today.year,
                                  month=today.month,
                                  day=today.day,
                                  hour=0,
                                  minute=0,
                                  second=0)
        end = datetime.datetime(year=today.year,
                                month=today.month,
                                day=today.day,
                                hour=23,
                                minute=59,
                                second=59)
        json_req = {"dateStart": time.mktime(start.timetuple()), "dateEnd": time.mktime(end.timetuple()),
                    "masterTelegramId":  os.environ["CHAT"]}

    if message.text == 'Расписание на завтра':
        tomorrow = datetime.datetime.today() + datetime.timedelta(days=1)
        start = datetime.datetime(year=tomorrow.year,
                                  month=tomorrow.month,
                                  day=tomorrow.day,
                                  hour=0,
                                  minute=0,
                                  second=0)
        end = datetime.datetime(year=tomorrow.year,
                                month=tomorrow.month,
                                day=tomorrow.day,
                                hour=23,
                                minute=59,
                                second=59)
        json_req = {"dateStart": time.mktime(start.timetuple()), "dateEnd": time.mktime(end.timetuple()),
                    "masterTelegramId":  os.environ["CHAT"]}

    if message.text == 'Расписание на неделю':
        start = datetime.datetime.today()
        end = start + datetime.timedelta(days=7)
        start = datetime.datetime(year=start.year,
                                  month=start.month,
                                  day=start.day,
                                  hour=0,
                                  minute=0,
                                  second=0)
        end = datetime.datetime(year=end.year,
                                month=end.month,
                                day=end.day,
                                hour=23,
                                minute=59,
                                second=59)
        json_req = {"dateStart": time.mktime(start.timetuple()), "dateEnd": time.mktime(end.timetuple()),
                    "masterTelegramId":  os.environ["CHAT"]}

    if message.text == 'Расписание на месяц':
        start = datetime.datetime.today()
        end = start + datetime.timedelta(days=30)
        start = datetime.datetime(year=start.year,
                                  month=start.month,
                                  day=start.day,
                                  hour=0,
                                  minute=0,
                                  second=0)
        end = datetime.datetime(year=end.year,
                                month=end.month,
                                day=end.day,
                                hour=23,
                                minute=59,
                                second=59)
        json_req = {"dateStart": time.mktime(start.timetuple()), "dateEnd": time.mktime(end.timetuple()),
                    "masterTelegramId":  os.environ["CHAT"]}
    response = requests.post('https://pilka.herokuapp.com/rest/event/free', json=json_req)
    print(response.text)
    if len(response.text) <= 2:
        bot.send_message(message.chat.id, "Сеансов не найдено", reply_markup=keyboard_hider)
    else:
        bot.send_message(message.chat.id, message.text, reply_markup=keyboard_hider)
        keyboard = types.InlineKeyboardMarkup()
        for item in json.loads(response.text):
            date_start = datetime.datetime.fromtimestamp(item['dateStart'])
            print(date_start)
            date_end = datetime.datetime.fromtimestamp(item['dateEnd'])
            print(date_end)
            callback_button = types.InlineKeyboardButton(text= date_start.strftime('%d.%m.%y %H:%M') +
                                                                  " - " + date_end.strftime('%H:%M'),
                                                             callback_data=item['id'])
            keyboard.add(callback_button)
        bot.send_message(message.chat.id, "Cвободные окна", reply_markup=keyboard)


@bot.message_handler(func=lambda message: get_state(message) == GETMASTER)
def choose_type_repeat(message):
    keyboard_hider = types.ReplyKeyboardRemove()
    json_req={}
    if message.text == 'Расписание на сегодня':
        today = datetime.datetime.today()
        start = datetime.datetime(year=today.year,
                                  month=today.month,
                                  day=today.day,
                                  hour=0,
                                  minute=0,
                                  second=0)
        end = datetime.datetime(year=today.year,
                                month=today.month,
                                day=today.day,
                                hour=23,
                                minute=59,
                                second=59)
        json_req = {"dateStart": time.mktime(start.timetuple()), "dateEnd": time.mktime(end.timetuple()),
                    "masterTelegramId":  os.environ["CHAT"]}

    if message.text == 'Расписание на завтра':
        tomorrow = datetime.datetime.today() + datetime.timedelta(days=1)
        start = datetime.datetime(year=tomorrow.year,
                                  month=tomorrow.month,
                                  day=tomorrow.day,
                                  hour=0,
                                  minute=0,
                                  second=0)
        end = datetime.datetime(year=tomorrow.year,
                                month=tomorrow.month,
                                day=tomorrow.day,
                                hour=23,
                                minute=59,
                                second=59)
        json_req = {"dateStart": time.mktime(start.timetuple()), "dateEnd": time.mktime(end.timetuple()),
                    "masterTelegramId":  os.environ["CHAT"]}

    if message.text == 'Расписание на неделю':
        start = datetime.datetime.today()
        end = start + datetime.timedelta(days=7)
        start = datetime.datetime(year=start.year,
                                  month=start.month,
                                  day=start.day,
                                  hour=0,
                                  minute=0,
                                  second=0)
        end = datetime.datetime(year=end.year,
                                month=end.month,
                                day=end.day,
                                hour=23,
                                minute=59,
                                second=59)
        json_req = {"dateStart": time.mktime(start.timetuple()), "dateEnd": time.mktime(end.timetuple()),
                    "masterTelegramId":  os.environ["CHAT"]}

    if message.text == 'Расписание на месяц':
        start = datetime.datetime.today()
        end = start + datetime.timedelta(days=30)
        start = datetime.datetime(year=start.year,
                                  month=start.month,
                                  day=start.day,
                                  hour=0,
                                  minute=0,
                                  second=0)
        end = datetime.datetime(year=end.year,
                                month=end.month,
                                day=end.day,
                                hour=23,
                                minute=59,
                                second=59)
        json_req = {"dateStart": time.mktime(start.timetuple()), "dateEnd": time.mktime(end.timetuple()),
                    "masterTelegramId":  os.environ["CHAT"]}
    response = requests.post('https://pilka.herokuapp.com/rest/event/get_all', json=json_req)
    print(response.text)
    if len(response.text) <= 2:
        bot.send_message(message.chat.id, "Сеансов не найдено", reply_markup=keyboard_hider)
    else:
        bot.send_message(message.chat.id, message.text, reply_markup=keyboard_hider)
        keyboard = types.InlineKeyboardMarkup()
        for item in json.loads(response.text):
            date_start = datetime.datetime.fromtimestamp(item['dateStart'])
            print(date_start)
            date_end = datetime.datetime.fromtimestamp(item['dateEnd'])
            print(date_end)
            if item['client'] and item['eventStatus'] == 'APPROVED':
                callback_button = types.InlineKeyboardButton(
                    text=item['client']['username'] + "\n" + date_start.strftime('%d.%m.%y %H:%M') +
                         " - " + date_end.strftime('%H:%M'), callback_data=item['id'])
            else:
                callback_button = types.InlineKeyboardButton(text="Cвободно\n" + date_start.strftime('%d.%m.%y %H:%M') +
                                                                  " - " + date_end.strftime('%H:%M'),
                                                             callback_data=item['id'])
            keyboard.add(callback_button)
        bot.send_message(message.chat.id, "Ваши размещенные сеансы", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: get_state(call.message) == GETMASTER)
def callback_inline(call):
    markup = utils.generate_markup_agree()
    response = requests.get('https://pilka.herokuapp.com/rest/event/get',
                            params={"eventId": call.data})
    answer = response.json()

    date_start = datetime.datetime.fromtimestamp(answer['dateStart'])
    date_end = datetime.datetime.fromtimestamp(answer['dateEnd'])

    bot.send_message(call.message.chat.id, 'Хотите удалить сеанс ' + date_start.strftime('%d.%m.%y %H:%M') +
                     " - " + date_end.strftime('%H:%M') + '?', reply_markup=markup)

    update_event(call.message, call.data)
    update_state(call.message, DELETEMASTER)

@bot.callback_query_handler(func=lambda call: get_state(call.message) == GETCLIENT)
def callback_inline(call):
    markup = utils.generate_markup_agree()
    response = requests.get('https://pilka.herokuapp.com/rest/event/get',
                            params={"eventId": call.data})
    answer = response.json()

    date_start = datetime.datetime.fromtimestamp(answer['dateStart'])
    date_end = datetime.datetime.fromtimestamp(answer['dateEnd'])

    bot.send_message(call.message.chat.id, 'Хотите записаться на сеанс ' + date_start.strftime('%d.%m.%y %H:%M') +
                     " - " + date_end.strftime('%H:%M') + '?', reply_markup=markup)

    update_event(call.message, call.data)
    update_state(call.message, EVENTRESERVE)

@bot.message_handler(func=lambda message: get_state(message) == EVENTRESERVE)
def choose_type_repeat(message):
    response = requests.get('https://pilka.herokuapp.com/rest/event/get',
                            params={"eventId": get_event(message)})
    answer = response.json()

    date_start = datetime.datetime.fromtimestamp(answer['dateStart'])
    date_end = datetime.datetime.fromtimestamp(answer['dateEnd'])

    if message.text == 'Да':
        keyboard_hider = types.ReplyKeyboardRemove()
        id = message.chat.id
        response = requests.put('https://pilka.herokuapp.com/rest/event/engage', json={"eventId": get_event(message), "clientTelegramId": id})
        if response.status_code == 200:
            bot.send_message(message.chat.id, 'Сеанс ' + date_start.strftime('%d.%m.%y %H:%M') +
                     " - " + date_end.strftime('%H:%M') + ' успешно забронирован', reply_markup=keyboard_hider)
            bot.send_message(os.environ["CHAT"], "У вас новая заявка на " + date_start.strftime('%d.%m.%y %H:%M') +
                     " - " + date_end.strftime('%H:%M') + "!")
        else:
            bot.send_message(message.chat.id, 'Произошла ошибка при бронировании сеанса ' + date_start.strftime('%d.%m.%y %H:%M') +
                     " - " + date_end.strftime('%H:%M'), reply_markup=keyboard_hider)

    if message.text == 'Нет':
        keyboard_hider = types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id, "Сеанс " + date_start.strftime('%d.%m.%y %H:%M') +
                     " - " + date_end.strftime('%H:%M') + " не был забронирован", reply_markup=keyboard_hider)

    update_state(message, START)

@bot.message_handler(func=lambda message: get_state(message) == DELETECLIENT)
def choose_type_repeat(message):
    response = requests.get('https://pilka.herokuapp.com/rest/event/get',
                            params={"eventId": get_event(message)})
    answer = response.json()
    date_start = datetime.datetime.fromtimestamp(answer['dateStart'])
    date_end = datetime.datetime.fromtimestamp(answer['dateEnd'])

    if message.text == 'Да':
        keyboard_hider = types.ReplyKeyboardRemove()
        id = message.chat.id
        response = requests.put('https://pilka.herokuapp.com/rest/event/cancelEvent', json={"eventId":str(get_event(message)), "clientTelegramId": id})
        if response.status_code == 200:
            bot.send_message(message.chat.id, 'Сеанс ' + date_start.strftime('%d.%m.%y %H:%M') +
                     " - " + date_end.strftime('%H:%M') + ' успешно отменен', reply_markup=keyboard_hider)
            if (answer['eventStatus'] == 'APPROVED'):
                bot.send_message(os.environ["CHAT"], "Cеанс " + date_start.strftime('%d.%m.%y %H:%M') +
                     " - " + date_end.strftime('%H:%M') + " был отменен клиентом")
        else:
            bot.send_message(message.chat.id, 'Произошла ошибка при отмене сеанса ' + date_start.strftime('%d.%m.%y %H:%M') +
                     " - " + date_end.strftime('%H:%M'), reply_markup=keyboard_hider)
        # отправить уведомление мастеру

    if message.text == 'Нет':
        keyboard_hider = types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id, 'Сеанс ' + date_start.strftime('%d.%m.%y %H:%M') +
                     " - " + date_end.strftime('%H:%M') + ' не был отменен', reply_markup=keyboard_hider)

    update_state(message, START)

@bot.message_handler(func=lambda message: get_state(message) == DELETEMASTER)
def choose_type_repeat(message):
    response = requests.get('https://pilka.herokuapp.com/rest/event/get',
                            params={"eventId": get_event(message)})
    answer = response.json()
    date_start = datetime.datetime.fromtimestamp(answer['dateStart'])
    date_end = datetime.datetime.fromtimestamp(answer['dateEnd'])

    if message.text == 'Да':
        keyboard_hider = types.ReplyKeyboardRemove()
        response = requests.delete('https://pilka.herokuapp.com/rest/event/delete?'+"eventId="+str(get_event(message)))
        if response.status_code == 200:
            bot.send_message(message.chat.id, 'Сеанс ' + date_start.strftime('%d.%m.%y %H:%M') +
                     " - " + date_end.strftime('%H:%M') + ' успешно отменен', reply_markup=keyboard_hider)
            if (answer['eventStatus'] == 'APPROVED'):
                bot.send_message(answer['client']['telegramId'], "Ваш сеанс " + date_start.strftime('%d.%m.%y %H:%M') +
                     " - " + date_end.strftime('%H:%M') + " был отменен")
        else:
            bot.send_message(message.chat.id, 'Произошла ошибка при отмене сеанса ' + date_start.strftime('%d.%m.%y %H:%M') +
                     " - " + date_end.strftime('%H:%M'), reply_markup=keyboard_hider)
        # отправить уведомление мастеру

    if message.text == 'Нет':
        keyboard_hider = types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id, 'Сеанс ' + date_start.strftime('%d.%m.%y %H:%M') +
                     " - " + date_end.strftime('%H:%M') + ' не был удален', reply_markup=keyboard_hider)

    update_state(message, START)


@bot.message_handler(func=lambda message: get_state(message) == REPEAT)
def choose_type_repeat(message):
    if message.text == 'Одиночное окно':
        keyboard_hider = types.ReplyKeyboardRemove()
        MASTER_EVENT['count'] = 1
        MASTER_EVENT['freq'] = 'DAILY'
        MASTER_EVENT['interval'] = 1
        bot.send_message(message.chat.id, 'Напиши дату и время начала окна', reply_markup=keyboard_hider)
        update_state(message, DATE)
    if message.text == 'Повторяющееся окно':
        markup = utils.generate_markup_to_get_type_of_repeat()
        bot.send_message(message.chat.id, 'Выбери как будет повторяться окно', reply_markup=markup)
        update_state(message, REPEAT_TYPE)


@bot.message_handler(func=lambda message: get_state(message) == REPEAT_TYPE)
def choose_type_repeat(message):
    markup = utils.generate_markup_to_get_duration_of_repeat()
    if message.text == 'Каждый день (без выходных)':
        MASTER_EVENT['freq'] = 'WEEKLY'
        MASTER_EVENT['byweekday'] = 'MO,TU,WE,TH,FR'
        MASTER_EVENT['interval'] = 1
        MASTER_EVENT['mul'] = 5
    if message.text == 'Каждый день (с выходными сб, вс)':
        MASTER_EVENT['freq'] = 'DAILY'
        MASTER_EVENT['interval'] = 1
    if message.text == 'Каждую неделю':
        MASTER_EVENT['freq'] = 'WEEKLY'
        MASTER_EVENT['interval'] = 1
    bot.send_message(message.chat.id, 'Выбери как долго окно будет повторяться', reply_markup=markup)
    update_state(message, REPEAT_DURATION)


@bot.message_handler(func=lambda message: get_state(message) == REPEAT_DURATION)
def choose_type_repeat(message):
    keyboard_hider = types.ReplyKeyboardRemove()
    if message.text == 'Неделю':
        if MASTER_EVENT['freq'] == 'WEEKLY':
            MASTER_EVENT['count'] = 1
        if MASTER_EVENT['freq'] == 'DAILY':
            MASTER_EVENT['count'] = 7
    if message.text == 'Месяц':
        if MASTER_EVENT['freq'] == 'WEEKLY':
            MASTER_EVENT['count'] = 4
        if MASTER_EVENT['freq'] == 'DAILY':
            MASTER_EVENT['count'] = 30
    bot.send_message(message.chat.id, 'Напиши дату и время начала окна (в формате dd.mm.yyyy hh:mm)',
                     reply_markup=keyboard_hider)
    update_state(message, DATE)


@bot.message_handler(func=lambda message: get_state(message) == DATE)
def choose_type_repeat(message):
    try:
        date = datetime.datetime.strptime(message.text, "%d.%m.%Y %H:%M").timetuple()
        MASTER_EVENT['date_start'] = time.mktime(date)
        bot.send_message(message.chat.id, 'Напиши длительность окна в минутах')
        update_state(message, DURATION)
    except:
        bot.send_message(message.chat.id, 'Неверный формат числа, попробуй еще')


@bot.message_handler(func=lambda message: get_state(message) == DURATION)
def choose_type_repeat(message):
    try:
        duration = int(message.text)
        MASTER_EVENT['duration'] = duration*60000
        markup = utils.generate_markup_agree()
        bot.send_message(message.chat.id, 'Добавить событие?', reply_markup=markup)
        update_state(message, CONFIRMATION)
    except:
        bot.send_message(message.chat.id, 'Неверный формат даты, попробуй еще')


@bot.message_handler(func=lambda message: get_state(message) == CONFIRMATION)
def choose_type_repeat(message):
    print(MASTER_EVENT)
    keyboard_hider = types.ReplyKeyboardRemove()
    if message.text == 'Да':
        rrule = "FREQ=" + MASTER_EVENT['freq'] + ";COUNT=" + str(MASTER_EVENT['count']) + ";INTERVAL=" + str(
            MASTER_EVENT['interval']) + ";"
        if MASTER_EVENT['byweekday'] != "":
            rrule += "BYWEEKDAY=" + MASTER_EVENT['byweekday'] + ";"
        id = message.chat.id
        json = {'userTelegramId': id, "duration": MASTER_EVENT['duration'],
                "rrule": rrule, "dateStart": MASTER_EVENT['date_start']*1000}
        response = requests.post('https://pilka.herokuapp.com/rest/event/create', json=json)
        print(response)
        if response.status_code == 200:
            bot.send_message(message.chat.id, 'Окно успешно добавлено', reply_markup=keyboard_hider)
        else:
            bot.send_message(message.chat.id, 'Возникли ошибки при добавлении окна', reply_markup=keyboard_hider)
    else:
        bot.send_message(message.chat.id, 'Окно не добавлено', reply_markup=keyboard_hider)
    update_state(message, START)


####################################################
@bot.message_handler(func=lambda message: True, content_types=['text'])
def check_answer(message):
    bot.send_message(message.chat.id, 'Чтобы начать выберите одну из команд')

@bot.message_handler(func=lambda message: True)
def choose_type_repeat(message):
    bot.send_message(message.chat.id, 'Чтобы начать выберите одну из команд')

if __name__ == '__main__':
    print('start')
    random.seed()
    while True:
        try:
            if "HEROKU" in list(os.environ.keys()):
                logger = telebot.logger
                telebot.logger.setLevel(logging.INFO)

                server = Flask(__name__)


                @server.route("/bot", methods=['POST'])
                def getMessage():
                    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
                    return "!", 200


                @server.route("/")
                def webhook():
                    bot.remove_webhook()
                    bot.set_webhook(
                        url="https://pilka-bot.herokuapp.com/")
                    return "?", 200


                server.run(host="0.0.0.0", port=os.environ.get('PORT', 80))
            else:
                bot.remove_webhook()
                bot.polling(none_stop=True)
        except:
            time.sleep(3)
