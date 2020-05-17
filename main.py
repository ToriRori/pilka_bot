import os
import random
import time
import config
import telebot
from telebot import apihelper, types

import utils
from SQLighter import SQLighter

apihelper.proxy = {
    'https':'socks5://217.182.230.15:4485'
}

bot = telebot.TeleBot(config.token, threaded=False)

# @bot.message_handler(commands=['test'])
# def find_file_ids(message):
#     for file in os.listdir('music/'):
#         if file.split('.')[-1] == 'ogg':
#             f = open('music/'+file, 'rb')
#             msg = bot.send_voice(message.chat.id, f, None)
#             # А теперь отправим вслед за файлом его file_id
#             bot.send_message(message.chat.id, msg.voice.file_id, reply_to_message_id=msg.message_id)
#         time.sleep(3)

# @bot.message_handler(commands=['game'])
# def game(message):
#     # Подключаемся к БД
#     db_worker = SQLighter(config.database_name)
#     # Получаем случайную строку из БД
#     row = db_worker.select_single(random.randint(1, utils.get_rows_count()))
#     # Формируем разметку
#     markup = utils.generate_markup(row[2], row[3])
#     # Отправляем аудиофайл с вариантами ответа
#     bot.send_voice(message.chat.id, row[1], reply_markup=markup)
#     # Включаем "игровой режим"
#     utils.set_user_game(message.chat.id, row[2])
#     # Отсоединяемся от БД
#     db_worker.close()

@bot.message_handler(commands=['get_schedule'])
def get_schedule(message):
    # Формируем разметку
    markup = utils.generate_markup_to_get_schedule()
    bot.send_message(message.chat.id, 'Выбери сервис', reply_markup=markup)

@bot.message_handler(commands=['put_schedule'])
def get_schedule(message):
    # Формируем разметку
    markup = utils.generate_markup_to_put_schedule()
    bot.send_message(message.chat.id, 'Выбери сервис', reply_markup=markup)


@bot.message_handler(func=lambda message: True, content_types=['text'])
def check_answer(message):
    # Если функция возвращает None -> Человек не в игре
    # answer = utils.get_answer_for_user(message.chat.id)
    # # Как Вы помните, answer может быть либо текст, либо None
    # # Если None:
    # if not answer:
    #     bot.send_message(message.chat.id, 'Чтобы начать игру, выберите команду /game')
    # else:
        # Уберем клавиатуру с вариантами ответа.
    keyboard_hider = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, 'Так точно!', reply_markup=keyboard_hider)
        # Если ответ правильный/неправильный
        # if message.text == answer:
        #     bot.send_message(message.chat.id, 'Верно!', reply_markup=keyboard_hider)
        # else:
        #     bot.send_message(message.chat.id, 'Увы, Вы не угадали. Попробуйте ещё раз!', reply_markup=keyboard_hider)
        # # Удаляем юзера из хранилища (игра закончена)
        # utils.finish_user_game(message.chat.id)

if __name__ == '__main__':
    while (True):
        try:
            utils.count_rows()
            random.seed()
            bot.polling(none_stop=True)
        except:
            time.sleep(3)
