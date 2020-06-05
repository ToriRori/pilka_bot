import shelve
from random import shuffle

from telebot import types

from SQLighter import SQLighter
from config import shelve_name, database_name

# def count_rows():
#     db = SQLighter(database_name)
#     rowsnum = db.count_rows()
#     with shelve.open(shelve_name) as storage:
#         storage['rows_count'] = rowsnum
#
#
# def get_rows_count():
#     with shelve.open(shelve_name) as storage:
#         rowsnum = storage['rows_count']
#     return rowsnum


def get_answer_for_user(chat_id):
    with shelve.open(shelve_name) as storage:
        try:
            answer = storage[str(chat_id)]
            return answer
        except KeyError:
            return None

def generate_markup_to_get_schedule():
    list_items = ['Расписание на сегодня', 'Расписание на завтра', 'Расписание на неделю', 'Расписание на месяц']
    return generate_markup(list_items)

def generate_markup_to_put_schedule():
    list_items = ['Одиночное окно', 'Повторяющееся окно']
    return generate_markup(list_items)

def generate_markup_to_get_type_of_repeat():
    list_items = ['Каждый день (без выходных)', 'Каждый день (с выходными сб, вс)', 'Каждую неделю']
    return generate_markup(list_items)

def generate_markup_to_get_duration_of_repeat():
    list_items = ['Неделю', 'До конца месяца', 'Месяц']
    return generate_markup(list_items)

def generate_markup_agree():
    list_items = ['Да', 'Нет']
    return generate_markup(list_items)

def generate_markup(list_items):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    for item in list_items:
        markup.add(item)
    return markup
