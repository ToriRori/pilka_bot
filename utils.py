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
#
#
# def set_user_game(chat_id, estimated_answer):
#     with shelve.open(shelve_name) as storage:
#         storage[str(chat_id)] = estimated_answer
#
#
# def finish_user_game(chat_id):
#     with shelve.open(shelve_name) as storage:
#         del storage[str(chat_id)]
#
#
# def get_answer_for_user(chat_id):
#     with shelve.open(shelve_name) as storage:
#         try:
#             answer = storage[str(chat_id)]
#             return answer
#         except KeyError:
#             return None
#
#
# def generate_markup(right_answer, wrong_answers):
#     markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
#     # Склеиваем правильный ответ с неправильными
#     all_answers = '{},{}'.format(right_answer, wrong_answers)
#     # Создаем лист (массив) и записываем в него все элементы
#     list_items = []
#     for item in all_answers.split(','):
#         list_items.append(item)
#     # Хорошенько перемешаем все элементы
#     shuffle(list_items)
#     # Заполняем разметку перемешанными элементами
#     for item in list_items:
#         markup.add(item)
#     return markup


def generate_markup_to_get_schedule():
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    list_items = ['Расписание на сегодня', 'Расписание на завтра', 'Расписание на неделю', 'Расписание на месяц']
    # Заполняем разметку перемешанными элементами
    for item in list_items:
        markup.add(item)
    return markup

def generate_markup_to_put_schedule():
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    list_items = ['Одиночное окно', 'Повторяющееся окно']
    # Заполняем разметку перемешанными элементами
    for item in list_items:
        markup.add(item)
    return markup