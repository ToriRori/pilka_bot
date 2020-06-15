import random
import codecs
import telebot
from telebot import apihelper, types
from collections import defaultdict
import utils
import json
import requests
import datetime, time
import os
import logging

apihelper.proxy = {
    'https': 'socks5://104.248.63.18:30588'
}

START, REPEAT, REPEAT_TYPE, REPEAT_DURATION, DATE, DURATION, CONFIRMATION, GETMASTER, GETCLIENT, \
DELETECLIENT, DELETEMASTER, EVENTRESERVE, SHOWRESERVED, SHOWAPPLICATIONS, APPROVEAPPLICATIONS, \
DELETEORENGAGE, CLIENTNAME = range(17)

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
    logging.info(str(message.chat.id)+":start")
    update_state(message, START)
    user_id = str(message.chat.id)
    if user_id == os.environ["CHAT"]:
        role = 'MASTER'
    else:
        role = 'USER'
    logging.info(user_id + ":role:"+role+" master_id:"+os.environ["CHAT"])
    username = ""
    if message.from_user.first_name:
        username = message.from_user.first_name
        if message.from_user.last_name:
            username += " " + message.from_user.last_name
    response = requests.post('https://pilka.herokuapp.com/authorization',
                             json={'username': username,
                                   'phoneNumber': "", 'telegramId': user_id, 'role': role})
    if response.status_code == 200:
        logging.info(str(message.chat.id) + ":new user success")
        bot.send_message(message.chat.id, 'Добро пожаловать в бот!')
    else:
        logging.info(str(message.chat.id) + ":new user bad")
        bot.send_message(message.chat.id, 'Мы уже знакомы с вами:)')


####################################################
# get schedule for client and master
@bot.message_handler(commands=['get_schedule'])
def get_schedule(message):
    logging.info(str(message.chat.id)+":get_schedule")
    update_state(message, START)
    markup = utils.generate_markup_to_get_schedule()
    user_id = str(message.chat.id)
    if user_id == os.environ["CHAT"]:
        update_state(message, GETMASTER)
    else:
        update_state(message, GETCLIENT)
    bot.send_message(message.chat.id, 'Выбери сервис', reply_markup=markup)


####################################################
# put master's event
@bot.message_handler(commands=['put_schedule'])
def get_schedule(message):
    logging.info(str(message.chat.id)+":get_schedule")
    update_state(message, START)
    user_id = str(message.chat.id)
    if user_id == os.environ["CHAT"]:
        markup = utils.generate_markup_to_put_schedule()
        MASTER_EVENT['mul'] = 1
        MASTER_EVENT['interval'] = 1
        MASTER_EVENT['freq'] = 'DAILY'
        MASTER_EVENT['count'] = 1
        MASTER_EVENT['byweekday'] = ""
        update_state(message, REPEAT)
        bot.send_message(message.chat.id, 'Выбери сервис', reply_markup=markup)
    else:
        bot.send_message(message.chat.id, 'Вам не разрешено данное действие')


####################################################
# show reserved events
@bot.message_handler(commands=['show_reserved'])
def get_schedule(message):
    logging.info(str(message.chat.id)+":show_reserved")
    update_state(message, START)
    user_id = str(message.chat.id)
    if user_id == os.environ["CHAT"]:
        bot.send_message(message.chat.id, "Вам недоступно это действие")
        return
    response = requests.get('https://pilka.herokuapp.com/rest/event/get/clientEvents', params={"clientTelegramId": user_id})
    if response.status_code != 200:
        logging.error(str(message.chat.id) + ":no id")
        bot.send_message(message.chat.id, "Не удалось выполнить действие")
        return
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
                callback_button = types.InlineKeyboardButton(
                    text="Не подтвержден\n" + date_start.strftime('%d.%m.%y %H:%M') +
                         " - " + date_end.strftime('%H:%M'),
                    callback_data=item['id'])
            keyboard.add(callback_button)
        bot.send_message(message.chat.id, "Ваши назначенные сеансы", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: get_state(call.message) == SHOWRESERVED)
def callback_inline(call):
    logging.info(str(call.message.chat.id) + ":inline show reserved:"+str(call.data))
    markup = utils.generate_markup_agree()
    response = requests.get('https://pilka.herokuapp.com/rest/event/get',
                            params={"eventId": call.data})
    if response.status_code != 200:
        logging.error(str(call.message.chat.id) + ":no id")
        bot.send_message(call.message.chat.id, "Не удалось выполнить действие")
        return

    answer = response.json()

    date_start = datetime.datetime.fromtimestamp(answer['dateStart'])
    date_end = datetime.datetime.fromtimestamp(answer['dateEnd'])

    update_event(call.message, call.data)
    update_state(call.message, DELETECLIENT)
    bot.send_message(call.message.chat.id, 'Хотите отменить сеанс ' + date_start.strftime('%d.%m.%y %H:%M') +
                     " - " + date_end.strftime('%H:%M') + '?', reply_markup=markup)


####################################################
# show events applications
@bot.message_handler(commands=['show_applications'])
def get_schedule(message):
    logging.info(str(message.chat.id) + ":show_applications")
    update_state(message, START)
    user_id = str(message.chat.id)
    if user_id != os.environ["CHAT"]:
        bot.send_message(message.chat.id, "Вам недоступно это действие")
        return
    response = requests.get('https://pilka.herokuapp.com/rest/event/get/review',
                            params={"masterTelegramId": os.environ["CHAT"]})
    if response.status_code != 200:
        logging.error(str(message.chat.id) + ":no id")
        bot.send_message(message.chat.id, "Не удалось выполнить действие")
        return

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
                text=item["client"]['username'] + "\n" + date_start.strftime('%d.%m.%y %H:%M') +
                     " - " + date_end.strftime('%H:%M'), callback_data=item['id'])
            keyboard.add(callback_button)
        bot.send_message(message.chat.id, "Заявки на предстоящие сеансы", reply_markup=keyboard)


@bot.message_handler(commands=['info'])
def get_schedule(message):
    logging.info(str(message.chat.id) + ":info")
    update_state(message, START)
    f = codecs.open("readme.md", encoding='utf-8')
    text = f.readlines()
    for i in range(0, 5):
        text[i] = ""
    bot.send_message(message.chat.id, "".join(text))


@bot.callback_query_handler(func=lambda call: get_state(call.message) == SHOWAPPLICATIONS)
def callback_inline(call):
    logging.info(str(call.message.chat.id) + ":inline show applications:" + str(call.data))
    markup = utils.generate_markup_agree()

    response = requests.get('https://pilka.herokuapp.com/rest/event/get',
                            params={"eventId": call.data})
    if response.status_code != 200:
        update_state(call.message, START)
        logging.error(str(call.message.chat.id) + ":no id")
        bot.send_message(call.message.chat.id, "Не удалось выполнить действие")
        return

    answer = response.json()

    date_start = datetime.datetime.fromtimestamp(answer['dateStart'])
    date_end = datetime.datetime.fromtimestamp(answer['dateEnd'])

    update_event(call.message, call.data)
    update_state(call.message, APPROVEAPPLICATIONS)
    bot.send_message(call.message.chat.id, 'Подтверждаете сеанс ' + date_start.strftime('%d.%m.%y %H:%M') +
                     " - " + date_end.strftime('%H:%M') + '?', reply_markup=markup)


@bot.message_handler(func=lambda message: get_state(message) == APPROVEAPPLICATIONS)
def choose_type_repeat(message):
    logging.info(str(message.chat.id) + ":approve")
    response = requests.get('https://pilka.herokuapp.com/rest/event/get',
                            params={"eventId": get_event(message)})
    if response.status_code != 200:
        logging.error(str(message.chat.id) + ":no id")
        bot.send_message(message.chat.id, "Не удалось выполнить действие")
        return
    answer = response.json()
    date_start = datetime.datetime.fromtimestamp(answer['dateStart'])
    date_end = datetime.datetime.fromtimestamp(answer['dateEnd'])

    if message.text == 'Да':
        keyboard_hider = types.ReplyKeyboardRemove()
        response = requests.put('https://pilka.herokuapp.com/rest/event/approve',
                                json={"eventId": str(get_event(message)), "approval": "APPROVAL"})

        if response.status_code == 200:
            update_state(message, START)
            bot.send_message(message.chat.id, 'Сеанс ' + date_start.strftime('%d.%m.%y %H:%M') +
                             " - " + date_end.strftime('%H:%M') + ' успешно подтвержден', reply_markup=keyboard_hider)
            bot.send_message(answer['client']['telegramId'], "Cеанс " + date_start.strftime('%d.%m.%y %H:%M') +
                             " - " + date_end.strftime('%H:%M') + " был подтвержен")
        else:
            update_state(message, START)
            bot.send_message(message.chat.id,
                             'Произошла ошибка при подстверждении сеанса ' + date_start.strftime('%d.%m.%y %H:%M') +
                             " - " + date_end.strftime('%H:%M'), reply_markup=keyboard_hider)

    if message.text == 'Нет':
        keyboard_hider = types.ReplyKeyboardRemove()
        update_state(message, START)
        bot.send_message(message.chat.id, 'Заявка ' + date_start.strftime('%d.%m.%y %H:%M') +
                         " - " + date_end.strftime('%H:%M') + ' была отклонена', reply_markup=keyboard_hider)
        bot.send_message(answer['client']['telegramId'], "Cеанс " + date_start.strftime('%d.%m.%y %H:%M') +
                         " - " + date_end.strftime('%H:%M') + " не был подтвержен")


@bot.message_handler(func=lambda message: get_state(message) == GETCLIENT or get_state(message) == GETMASTER)
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
                    "masterTelegramId": os.environ["CHAT"]}

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
                    "masterTelegramId": os.environ["CHAT"]}

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
                    "masterTelegramId": os.environ["CHAT"]}

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
                    "masterTelegramId": os.environ["CHAT"]}

    if get_state(message) == GETCLIENT:
        response = requests.post('https://pilka.herokuapp.com/rest/event/free', json=json_req)
    else:
        response = requests.post('https://pilka.herokuapp.com/rest/event/get_all', json=json_req)

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
            if get_state(message) == GETMASTER:
                if item['client'] and item['eventStatus'] == 'APPROVED':
                    callback_button = types.InlineKeyboardButton(
                        text=item['client']['username'] + "\n" + date_start.strftime('%d.%m.%y %H:%M') +
                             " - " + date_end.strftime('%H:%M'), callback_data=item['id'])
                else:
                    callback_button = types.InlineKeyboardButton(
                        text="Cвободно\n" + date_start.strftime('%d.%m.%y %H:%M') +
                             " - " + date_end.strftime('%H:%M'),
                        callback_data=item['id'])
            else:
                callback_button = types.InlineKeyboardButton(text=date_start.strftime('%d.%m.%y %H:%M') +
                                                                  " - " + date_end.strftime('%H:%M'),
                                                             callback_data=item['id'])
            keyboard.add(callback_button)
        if get_state(message) == GETMASTER:
            bot.send_message(message.chat.id, "Ваши размещенные сеансы", reply_markup=keyboard)
        else:
            bot.send_message(message.chat.id, "Cвободные окна мастера", reply_markup=keyboard)


@bot.callback_query_handler(
    func=lambda call: get_state(call.message) == GETMASTER or get_state(call.message) == GETCLIENT)
def callback_inline(call):
    response = requests.get('https://pilka.herokuapp.com/rest/event/get',
                            params={"eventId": call.data})
    answer = response.json()

    date_start = datetime.datetime.fromtimestamp(answer['dateStart'])
    date_end = datetime.datetime.fromtimestamp(answer['dateEnd'])

    update_event(call.message, call.data)
    if get_state(call.message) == GETMASTER:
        markup = utils.generate_markup_delete_or_engage()
        update_state(call.message, DELETEORENGAGE)
        bot.send_message(call.message.chat.id, 'Выберите действие с сеансом  '+ date_start.strftime('%d.%m.%y %H:%M') +
                         " - " + date_end.strftime('%H:%M') + '?', reply_markup=markup)

    else:
        markup = utils.generate_markup_agree()
        update_state(call.message, EVENTRESERVE)
        bot.send_message(call.message.chat.id, 'Хотите записаться на сеанс ' + date_start.strftime('%d.%m.%y %H:%M') +
                         " - " + date_end.strftime('%H:%M') + '?', reply_markup=markup)


@bot.message_handler(func=lambda message: get_state(message) == DELETEORENGAGE)
def choose_type_repeat(message):
    response = requests.get('https://pilka.herokuapp.com/rest/event/get',
                            params={"eventId": get_event(message)})
    answer = response.json()

    date_start = datetime.datetime.fromtimestamp(answer['dateStart'])
    date_end = datetime.datetime.fromtimestamp(answer['dateEnd'])

    if message.text == 'Записать клиента':
        keyboard_hider = types.ReplyKeyboardRemove()
        update_state(message, CLIENTNAME)
        bot.send_message(message.chat.id, "Напишите имя клиента", reply_markup=keyboard_hider)


    if message.text == 'Удалить':
        markup = utils.generate_markup_agree()
        update_state(message, DELETEMASTER)
        bot.send_message(message.chat.id, 'Хотите удалить сеанс ' + date_start.strftime('%d.%m.%y %H:%M') +
                      " - " + date_end.strftime('%H:%M') + '?', reply_markup=markup)


    if message.text == 'Отмена':
        keyboard_hider = types.ReplyKeyboardRemove()
        update_state(message, START)
        bot.send_message(message.chat.id, "Отмена", reply_markup=keyboard_hider)

@bot.message_handler(func=lambda message: get_state(message) == CLIENTNAME)
def choose_type_repeat(message):
    response = requests.get('https://pilka.herokuapp.com/rest/event/get',
                            params={"eventId": get_event(message)})
    answer = response.json()

    date_start = datetime.datetime.fromtimestamp(answer['dateStart'])
    date_end = datetime.datetime.fromtimestamp(answer['dateEnd'])

    response = requests.put('https://pilka.herokuapp.com/rest/event/engage',
                            json={"eventId": get_event(message), "clientUsername": message.text,
                                  "engagerUserTelegramId": message.chat.id, "phoneNumber": ""})
    if response.status_code == 200:
        update_state(message, START)
        bot.send_message(message.chat.id, 'Сеанс ' + date_start.strftime('%d.%m.%y %H:%M') +
                         " - " + date_end.strftime('%H:%M') + ' успешно забронирован')
    else:
        update_state(message, START)
        bot.send_message(message.chat.id,
                         'Произошла ошибка при бронировании сеанса ' + date_start.strftime('%d.%m.%y %H:%M') +
                         " - " + date_end.strftime('%H:%M'))

@bot.message_handler(func=lambda message: get_state(message) == EVENTRESERVE)
def choose_type_repeat(message):
    response = requests.get('https://pilka.herokuapp.com/rest/event/get',
                            params={"eventId": get_event(message)})
    answer = response.json()

    date_start = datetime.datetime.fromtimestamp(answer['dateStart'])
    date_end = datetime.datetime.fromtimestamp(answer['dateEnd'])

    if message.text == 'Да':
        keyboard_hider = types.ReplyKeyboardRemove()
        response = requests.put('https://pilka.herokuapp.com/rest/event/engage',
                                json={"eventId": get_event(message), "clientTelegramId": message.chat.id, "engagerUserTelegramId": message.chat.id})
        if response.status_code == 200:
            update_state(message, START)
            bot.send_message(message.chat.id, 'Сеанс ' + date_start.strftime('%d.%m.%y %H:%M') +
                             " - " + date_end.strftime('%H:%M') + ' успешно забронирован', reply_markup=keyboard_hider)
            bot.send_message(os.environ["CHAT"], "У вас новая заявка на " + date_start.strftime('%d.%m.%y %H:%M') +
                             " - " + date_end.strftime('%H:%M') + "!")
        else:
            update_state(message, START)
            bot.send_message(message.chat.id,
                             'Произошла ошибка при бронировании сеанса ' + date_start.strftime('%d.%m.%y %H:%M') +
                             " - " + date_end.strftime('%H:%M'), reply_markup=keyboard_hider)

    if message.text == 'Нет':
        keyboard_hider = types.ReplyKeyboardRemove()
        update_state(message, START)
        bot.send_message(message.chat.id, "Сеанс " + date_start.strftime('%d.%m.%y %H:%M') +
                         " - " + date_end.strftime('%H:%M') + " не был забронирован", reply_markup=keyboard_hider)




@bot.message_handler(func=lambda message: get_state(message) == DELETECLIENT)
def choose_type_repeat(message):
    response = requests.get('https://pilka.herokuapp.com/rest/event/get',
                            params={"eventId": get_event(message)})
    answer = response.json()
    date_start = datetime.datetime.fromtimestamp(answer['dateStart'])
    date_end = datetime.datetime.fromtimestamp(answer['dateEnd'])

    if message.text == 'Да':
        keyboard_hider = types.ReplyKeyboardRemove()
        response = requests.put('https://pilka.herokuapp.com/rest/event/cancelEvent',
                                json={"eventId": str(get_event(message)), "clientTelegramId": message.chat.id})
        if response.status_code == 200:
            update_state(message, START)
            bot.send_message(message.chat.id, 'Сеанс ' + date_start.strftime('%d.%m.%y %H:%M') +
                             " - " + date_end.strftime('%H:%M') + ' успешно отменен', reply_markup=keyboard_hider)
            if answer['eventStatus'] == 'APPROVED':
                bot.send_message(os.environ["CHAT"], "Cеанс " + date_start.strftime('%d.%m.%y %H:%M') +
                                 " - " + date_end.strftime('%H:%M') + " был отменен клиентом")
        else:
            update_state(message, START)
            bot.send_message(message.chat.id,
                             'Произошла ошибка при отмене сеанса ' + date_start.strftime('%d.%m.%y %H:%M') +
                             " - " + date_end.strftime('%H:%M'), reply_markup=keyboard_hider)

    if message.text == 'Нет':
        keyboard_hider = types.ReplyKeyboardRemove()
        update_state(message, START)
        bot.send_message(message.chat.id, 'Сеанс ' + date_start.strftime('%d.%m.%y %H:%M') +
                         " - " + date_end.strftime('%H:%M') + ' не был отменен', reply_markup=keyboard_hider)




@bot.message_handler(func=lambda message: get_state(message) == DELETEMASTER)
def choose_type_repeat(message):
    response = requests.get('https://pilka.herokuapp.com/rest/event/get',
                            params={"eventId": get_event(message)})
    answer = response.json()
    date_start = datetime.datetime.fromtimestamp(answer['dateStart'])
    date_end = datetime.datetime.fromtimestamp(answer['dateEnd'])

    if message.text == 'Да':
        keyboard_hider = types.ReplyKeyboardRemove()
        response = requests.delete(
            'https://pilka.herokuapp.com/rest/event/delete?' + "eventId=" + str(get_event(message)))
        if response.status_code == 200:
            update_state(message, START)
            bot.send_message(message.chat.id, 'Сеанс ' + date_start.strftime('%d.%m.%y %H:%M') +
                             " - " + date_end.strftime('%H:%M') + ' успешно отменен', reply_markup=keyboard_hider)
            if answer['eventStatus'] == 'APPROVED':
                bot.send_message(answer['client']['telegramId'], "Ваш сеанс " + date_start.strftime('%d.%m.%y %H:%M') +
                                 " - " + date_end.strftime('%H:%M') + " был отменен")
        else:
            update_state(message, START)
            bot.send_message(message.chat.id,
                             'Произошла ошибка при отмене сеанса ' + date_start.strftime('%d.%m.%y %H:%M') +
                             " - " + date_end.strftime('%H:%M'), reply_markup=keyboard_hider)

    if message.text == 'Нет':
        keyboard_hider = types.ReplyKeyboardRemove()
        update_state(message, START)
        bot.send_message(message.chat.id, 'Сеанс ' + date_start.strftime('%d.%m.%y %H:%M') +
                         " - " + date_end.strftime('%H:%M') + ' не был удален', reply_markup=keyboard_hider)


@bot.message_handler(func=lambda message: get_state(message) == REPEAT)
def choose_type_repeat(message):
    if message.text == 'Одиночное окно':
        keyboard_hider = types.ReplyKeyboardRemove()
        MASTER_EVENT['count'] = 1
        MASTER_EVENT['freq'] = 'DAILY'
        MASTER_EVENT['interval'] = 1
        update_state(message, DATE)
        bot.send_message(message.chat.id, 'Напиши дату и время начала сеанса', reply_markup=keyboard_hider)
    if message.text == 'Повторяющееся окно':
        markup = utils.generate_markup_to_get_type_of_repeat()
        update_state(message, REPEAT_TYPE)
        bot.send_message(message.chat.id, 'Выбери как будет повторяться сеанс', reply_markup=markup)
    if message.text == 'Отмена':
        keyboard_hider = types.ReplyKeyboardRemove()
        update_state(message, START)
        bot.send_message(message.chat.id, 'Отмена добавления сеанса', reply_markup=keyboard_hider)


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
    update_state(message, REPEAT_DURATION)
    bot.send_message(message.chat.id, 'Выбери как долго окно будет повторяться', reply_markup=markup)


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
    update_state(message, DATE)
    bot.send_message(message.chat.id, 'Напиши дату и время начала окна (в формате dd.mm.yyyy hh:mm)',
                     reply_markup=keyboard_hider)

@bot.message_handler(func=lambda message: get_state(message) == DATE)
def choose_type_repeat(message):
    try:
        date = datetime.datetime.strptime(message.text, "%d.%m.%Y %H:%M").timetuple()
        MASTER_EVENT['date_start'] = time.mktime(date)
        update_state(message, DURATION)
        bot.send_message(message.chat.id, 'Напиши длительность окна в минутах')
    except:
        bot.send_message(message.chat.id, 'Неверный формат числа, попробуй еще')


@bot.message_handler(func=lambda message: get_state(message) == DURATION)
def choose_type_repeat(message):
    try:
        duration = int(message.text)
        MASTER_EVENT['duration'] = duration * 60000
        markup = utils.generate_markup_agree()
        update_state(message, CONFIRMATION)
        bot.send_message(message.chat.id, 'Добавить событие?', reply_markup=markup)
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
        json = {'userTelegramId': message.chat.id, "duration": MASTER_EVENT['duration'],
                "rrule": rrule, "dateStart": MASTER_EVENT['date_start'] * 1000}
        response = requests.post('https://pilka.herokuapp.com/rest/event/create', json=json)
        print(response)
        update_state(message, START)
        if response.status_code == 200:
            bot.send_message(message.chat.id, 'Окно успешно добавлено', reply_markup=keyboard_hider)
        else:
            bot.send_message(message.chat.id, 'Возникли ошибки при добавлении окна', reply_markup=keyboard_hider)
    else:
        update_state(message, START)
        bot.send_message(message.chat.id, 'Окно не добавлено', reply_markup=keyboard_hider)



# handlers for logic
####################################################
@bot.message_handler(func=lambda message: True, content_types=['text'])
def check_answer(message):
    f = codecs.open("readme.md", encoding='utf-8')
    text = f.readlines()
    for i in range(0, 5):
        text[i] = ""
    bot.send_message(message.chat.id, 'Выберите одну из команд\n' + "".join(text))


@bot.callback_query_handler(func=lambda call: True)
def choose_type_repeat(call):
    f = codecs.open("readme.md", encoding='utf-8')
    text = f.readlines()
    for i in range(0, 5):
        text[i] = ""
    bot.send_message(call.message.chat.id, 'Выберите одну из команд\n' + "".join(text))


if __name__ == '__main__':
    print('start')
    random.seed()
    logging.basicConfig(level=logging.DEBUG)
    while True:
        try:
            print("polling")
            bot.polling(none_stop=True)
        except:
            time.sleep(3)
