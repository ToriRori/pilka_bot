import random
import telebot
from telebot import apihelper, types
from collections import defaultdict
import utils
import json
import requests
import datetime, time
import os

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
    if message.from_user.username == os.environ["ADMIN"]:
        role = 'MASTER'
    else:
        role = 'USER'
    response = requests.post('https://pilka.herokuapp.com/authorization',
                             json={'username': message.from_user.username, 'role': role})
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
    if message.from_user.username == os.environ['ADMIN']:
        update_state(message, GETMASTER)
    else:
        update_state(message, GETCLIENT)


@bot.message_handler(func=lambda message: get_state(message) == GETCLIENT)
def choose_type_repeat(message):
    if message.text == 'Расписание на сегодня':
        keyboard_hider = types.ReplyKeyboardRemove()
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
                    "masterUsername": os.environ["ADMIN"]}

    if message.text == 'Расписание на завтра':
        keyboard_hider = types.ReplyKeyboardRemove()
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
                    "masterUsername":  os.environ["ADMIN"]}

    if message.text == 'Расписание на неделю':
        keyboard_hider = types.ReplyKeyboardRemove()
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
                    "masterUsername":  os.environ["ADMIN"]}

    if message.text == 'Расписание на месяц':
        keyboard_hider = types.ReplyKeyboardRemove()
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
                    "masterUsername":  os.environ["ADMIN"]}
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
    if message.text == 'Расписание на сегодня':
        keyboard_hider = types.ReplyKeyboardRemove()
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
                    "masterUsername": message.from_user.username}

    if message.text == 'Расписание на завтра':
        keyboard_hider = types.ReplyKeyboardRemove()
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
                    "masterUsername": message.from_user.username}

    if message.text == 'Расписание на неделю':
        keyboard_hider = types.ReplyKeyboardRemove()
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
                    "masterUsername": message.from_user.username}

    if message.text == 'Расписание на месяц':
        keyboard_hider = types.ReplyKeyboardRemove()
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
                    "masterUsername": message.from_user.username}
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
            if item['clientUsername']:
                callback_button = types.InlineKeyboardButton(
                    text=item['clientUsername'] + "\n" + date_start.strftime('%d.%m.%y %H:%M') +
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
    bot.send_message(call.message.chat.id, 'Хотите удалить событие?', reply_markup=markup)
    update_event(call.message, call.data)
    update_state(call.message, DELETEMASTER)

@bot.callback_query_handler(func=lambda call: get_state(call.message) == GETCLIENT)
def callback_inline(call):
    markup = utils.generate_markup_agree()
    bot.send_message(call.message.chat.id, 'Хотите записаться на сеанс?', reply_markup=markup)
    update_event(call.message, call.data)
    update_state(call.message, EVENTRESERVE)

@bot.message_handler(func=lambda message: get_state(message) == EVENTRESERVE)
def choose_type_repeat(message):
    if message.text == 'Да':
        keyboard_hider = types.ReplyKeyboardRemove()
        response = requests.put('https://pilka.herokuapp.com/rest/event/engage', json={"eventId": get_event(message), "clientUsername": message.from_user.username})
        if response.status_code == 200:
            bot.send_message(message.chat.id, 'Сеанс успешно забронирован', reply_markup=keyboard_hider)
            bot.send_message(os.environ["CHAT"], "У вас новая заявка!")
        else:
            bot.send_message(message.chat.id, 'Произошла ошибка при бронировании сеанса', reply_markup=keyboard_hider)
        # отправить уведомление мастеру

    if message.text == 'Нет':
        keyboard_hider = types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id, "Сеанс не был забронирован", reply_markup=keyboard_hider)

@bot.message_handler(func=lambda message: get_state(message) == DELETECLIENT)
def choose_type_repeat(message):
    if message.text == 'Да':
        keyboard_hider = types.ReplyKeyboardRemove()
        response = requests.put('https://pilka.herokuapp.com/rest/event/cancelEvent', json={"eventId":str(get_event(message)), "clientUsername": message.from_user.username})
        if response.status_code == 200:
            bot.send_message(message.chat.id, 'Сеанс успешно отменен', reply_markup=keyboard_hider)
        else:
            bot.send_message(message.chat.id, 'Произошла ошибка при отмене сеанса', reply_markup=keyboard_hider)
        # отправить уведомление мастеру

    if message.text == 'Нет':
        keyboard_hider = types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id, 'Сеанс не был удален', reply_markup=keyboard_hider)

@bot.message_handler(func=lambda message: get_state(message) == DELETEMASTER)
def choose_type_repeat(message):
    if message.text == 'Да':
        keyboard_hider = types.ReplyKeyboardRemove()
        response = requests.delete('https://pilka.herokuapp.com/rest/event/delete?'+"eventId="+str(get_event(message)))
        if response.status_code == 200:
            bot.send_message(message.chat.id, 'Сеанс успешно отменен', reply_markup=keyboard_hider)
        else:
            bot.send_message(message.chat.id, 'Произошла ошибка при отмене сеанса', reply_markup=keyboard_hider)
        # отправить уведомление мастеру

    if message.text == 'Нет':
        keyboard_hider = types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id, 'Сеанс не был удален', reply_markup=keyboard_hider)


####################################################
# show reserved events
@bot.message_handler(commands=['show_reserved'])
def get_schedule(message):
    if message.from_user.username == os.environ["ADMIN"]:
        bot.send_message(message.chat.id, "Вам недоступно это действие")
        return
    response = requests.get('https://pilka.herokuapp.com/rest/event/get/clientEvents', params={"clientUsername": message.from_user.username})
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
    bot.send_message(call.message.chat.id, 'Хотите удалить сеанс?', reply_markup=markup)
    update_event(call.message, call.data)
    update_state(call.message, DELETECLIENT)

####################################################
# show events applications
@bot.message_handler(commands=['show_applications'])
def get_schedule(message):
    if message.from_user.username != os.environ["ADMIN"]:
        bot.send_message(message.chat.id, "Вам недоступно это действие")
        return
    response = requests.get('https://pilka.herokuapp.com/rest/event/get/review',
                            params={"masterUsername": os.environ["ADMIN"]})
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
                    text=item["clientUsername"]+"\n" + date_start.strftime('%d.%m.%y %H:%M') +
                         " - " + date_end.strftime('%H:%M'), callback_data=item['id'])
            keyboard.add(callback_button)
        bot.send_message(message.chat.id, "Ваши заявки", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: get_state(call.message) == SHOWAPPLICATIONS)
def callback_inline(call):
    markup = utils.generate_markup_agree()
    bot.send_message(call.message.chat.id, 'Подтверждаете сеанс?', reply_markup=markup)
    update_event(call.message, call.data)
    update_state(call.message, APPROVEAPPLICATIONS)

@bot.message_handler(func=lambda message: get_state(message) == APPROVEAPPLICATIONS)
def choose_type_repeat(message):
    if message.text == 'Да':
        keyboard_hider = types.ReplyKeyboardRemove()
        response = requests.put('https://pilka.herokuapp.com/rest/event/approve', json={"eventId": str(get_event(message)), "approval": "APPROVAL"})
        if response.status_code == 200:
            bot.send_message(message.chat.id, 'Сеанс успешно подтвержден', reply_markup=keyboard_hider)
        else:
            bot.send_message(message.chat.id, 'Произошла ошибка при подстверждении сеанса', reply_markup=keyboard_hider)
        # отправить уведомление мастеру

    if message.text == 'Нет':
        keyboard_hider = types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id, 'Заявка была отклонена', reply_markup=keyboard_hider)

####################################################
# put master's event
@bot.message_handler(commands=['put_schedule'])
def get_schedule(message):
    print('put_schedule')
    markup = utils.generate_markup_to_put_schedule()
    if message.from_user.username == os.environ["ADMIN"]:
        bot.send_message(message.chat.id, 'Выбери сервис', reply_markup=markup)
        MASTER_EVENT['mul'] = 1
        MASTER_EVENT['interval'] = 1
        MASTER_EVENT['freq'] = 'DAILY'
        MASTER_EVENT['count'] = 1
        MASTER_EVENT['byweekday'] = ""
        update_state(message, REPEAT)
    else:
        bot.send_message(message.chat.id, 'Вам не разрешено данное дейтсвие', reply_markup=markup)


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
        MASTER_EVENT['duration'] = duration*60
        markup = utils.generate_markup_agree()
        bot.send_message(message.chat.id, 'Добавить такое-то событие?', reply_markup=markup)
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
        json = {'username': message.from_user.username, "duration": MASTER_EVENT['duration'],
                "rrule": rrule, "dateStart": MASTER_EVENT['date_start']}
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
            print('polling')
            bot.polling(none_stop=True)
        except:
            time.sleep(3)
