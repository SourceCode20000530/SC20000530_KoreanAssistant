import telebot
import config
import random
import sqlite3

from telebot import types

import time
from datetime import datetime, timedelta

import threading

import unicodedata

from flask import Flask, request
import requests


bot = telebot.TeleBot(config.TOKEN)

# Данные ID пользователей
data_users_id = set()

# Создаем словарь для отслеживания состояний пользователей
user_states = {}

# Состояния, которые могут принимать пользователи
# [----------------------------------------------]
# Состояния для функций "Проверь себя"
# Состояние ожидания перевода
WAITING_FOR_TRANSLATION = "WAITING_FOR_TRANSLATION"

# [----------------------------------------------]
# Состояния для функции "Добавить слово"
# Состояние ожидания добавления слова
WAITING_FOR_ADD_WORD = "WAITING_FOR_ADD_WORD"
# Состояние ожидания добавления перевода
WAITING_FOR_ADD_TRANSLATION = "WAITING_FOR_ADD_TRANSLATION"
# Состояние ожидания добавления категории
WAITING_FOR_ADD_CATEGORY = "WAITING_FOR_ADD_CATEGORY"

# [----------------------------------------------]
# Состояния для функции "Найти слово"
# Состояние ожидания слова или части слова для поиска
WAITING_FOR_PARTIAL_WORD = "WAITING_FOR_PARTIAL_WORD"
# Состояние ожидания для изменения слова, перевода и категории 
WAITING_FOR_EDIT_CHOICE = "WAITING_FOR_EDIT_CHOICE"
# Состояние ожидания для замены существующего слова
WAITING_FOR_NEW_WORD = "WAITING_FOR_NEW_WORD"
# Состояние ожидания для замены существующего перевода
WAITING_FOR_NEW_TRANSLATION = "WAITING_FOR_NEW_TRANSLATION"
# Состояние ожидания для замены существующей категории
WAITING_FOR_NEW_CATEGORY = "WAITING_FOR_NEW_CATEGORY"

# [----------------------------------------------]
# Состояния для функции "Посмотреть словарь"
# Состояние ожидания выбора вывода словаря в нужной сортировке
PRINT_ALL_WORDS = "PRINT_ALL_WORDS"

# [----------------------------------------------]
# Состояния для функции "Удалить"
# Состояние ожидания удаления слова, перевода и категории
WAITING_FOR_DELETE_FULL_WORD_TRANSLATION_CATEGORY = "WAITING_FOR_DELETE_FULL_WORD_TRANSLATION_CATEGORY"


# Символы
ALLOWED_SYMBOLS = "/" + "," + "." + "" + " " + "-" + "~" + "@" + "#" + "%" + "&" + "*" + "+" + "()" + "[]" + "{}"
# [----------------------------------------------]
# Буквы русского алфавита
RUSSIAN_LETTERS = "йцуеёнгшщзхфывапролджэячсмитьъбюк" + ALLOWED_SYMBOLS

# [----------------------------------------------]
# Создаем списки для проверки слов
koreanList              = []
russianList             = []
categoryList            = []

# Кнопки
# Основные кнопки
btn_start_txt = "/start"
btn_stop_txt = "/stop"
btn_info_txt = "🗣️ /Расскажи о себе"
btn_kor_rus_test_txt = "/Проверь меня! (корейско-русский)"
btn_random_ten_words_txt = "/🎲 10 случайных слов"
btn_rus_kor_test_txt = "/Проверь меня! (русско-корейский)"
btn_add_word_txt = "/🖊️ Добавить слово"
btn_find_word_txt = "/🔍 Найти слово"
btn_all_words_txt = "/📖Посмотреть словарь"


# Кнопки функции "Найти слово"
btn_edit_word_txt = "/Изменить слово"
btn_edit_translation_txt = "/Изменить перевод"
btn_edit_category_txt = "/Изменить категорию"
btn_delete_full_word_translation_category_txt = "/Удалить"


# Кнопка "Назад" для функций "Изменить слово", "Изменить перевод" и "Изменить категорию" 
btn_back_for_find_word_functions_txt = "/Назад"


# Кнопки функции "Удалить"
btn_delete_word_yes_txt = "/Да"
btn_delete_word_no_txt = "/Нет"


# Кнопки функции "Посмотреть словарь"
btn_all_words_korean_sort_txt = "/🇰🇷По корейскому алфавиту"
btn_all_words_russian_sort_txt = "/🇷🇺По русскому алфавиту"
btn_all_words_category_sort_txt = "/📚По категориям"


# Универсальная кнопка для отмены любых действий
btn_cancel_txt = "/Отмена"


# Универсальные кнопки для перезагрузки бота
btn_restart_russian_txt = "/Перезагрузить"
btn_restart_english_txt = "/Restart"


# Кнопки категории
btn_category_society_txt            = "Общество"
btn_category_objects_txt            = "Предметы"
btn_category_animals_txt            = "Животные"
btn_category_plants_txt             = "Растения"
btn_category_education_txt          = "Образование"
btn_category_culture_txt            = "Культура"
btn_category_food_txt               = "Еда"
btn_category_religion_txt           = "Религия"

# Для выбора языка
btn_set_russian_language_txt        = "Русский язык"
btn_set_english_language_txt        = "English language"

# Создаем список, чтобы упорядочить категории
list_categories = [btn_category_society_txt, btn_category_objects_txt, btn_category_animals_txt, btn_category_plants_txt, btn_category_education_txt, btn_category_culture_txt, btn_category_food_txt, btn_category_religion_txt]


##########################################################################################
# Извлекаем слова из БД
def koreanList_instance():
    conn = sqlite3.connect('voc.db')
    cursor = conn.cursor()
    cursor.execute("SELECT korean FROM words")
    rows = cursor.fetchall()

    for row in rows:
        koreanList.append(row[0])

    conn.close()


def russianList_instance():
    conn = sqlite3.connect('voc.db')
    # Теперь заранее перевод для только что заполненного списка
    for i in range(len(koreanList)):
        cursor = conn.cursor()
        cursor.execute("SELECT russian FROM words WHERE korean = ?", (koreanList[i],))
        result = cursor.fetchone()
        russianList.append(result[0])
    conn.close()


def categoryList_instance():
    conn = sqlite3.connect('voc.db')
    # Теперь заранее категории для только что заполненного списка
    for i in range(len(koreanList)):
        cursor = conn.cursor()
        cursor.execute("SELECT category FROM words WHERE korean = ?", (koreanList[i],))
        result = cursor.fetchone()
        categoryList.append(result[0])
    conn.close()


##########################################################################################
# Получаем ID пользователей
def get_user_id():
    conn = sqlite3.connect('voc.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users")
    rows = cursor.fetchall()

    for row in rows:
        data_users_id.add(row[0])
    conn.close()


# Вызываем функции
# Заполняем списки словами
koreanList_instance()
russianList_instance()
categoryList_instance()


# Функция обновления
def lists_updates():
    koreanList.clear()
    russianList.clear()
    koreanList_instance()
    russianList_instance()


# Получаем user_id
get_user_id()


##########################################################################################
# Функции, помогающие пользователю вводить слово только на необходимом языке
# Проверяем написано ли слово русскими буквами
def hasRussianLetters(text):
    return all(char.lower() in RUSSIAN_LETTERS for char in text)


# Проверяем написано ли слово корейскими буквами
def hasKoreanLetters(text):
    for char in text:
        if 'HANGUL' not in unicodedata.name(char) and not(char in ALLOWED_SYMBOLS):
            return False
    return True


##########################################################################################
# Функция, которая сохраняет данные пользователя в БД
def save_user_data(id, first_name, last_name):
    conn = sqlite3.connect('voc.db')
    cursor = conn.cursor()

    cursor.execute('''
    INSERT OR REPLACE INTO users (id, first_name, last_name)
    VALUES (?, ?, ?)
    ''', (id, first_name, last_name))

    conn.commit()
    conn.close()


# Отдельная функция для добавления основных кнопок
# Универсальная функция для отмены всех действий
@bot.message_handler(func=lambda message: message.text.lower() == "/отмена")
def cancel_function(message):
    user_id = message.chat.id
        
    if user_states:
        if user_states[user_id] is not None:
            del user_states[user_id]
        
    bot.send_message(user_id, "Возвращаемся в главное меню.", reply_markup=create_main_menu())

# Выбор основного языка
def create_main_lang_choice_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_set_russian_language = types.KeyboardButton(btn_set_russian_language_txt)
    btn_set_english_language = types.KeyboardButton(btn_set_english_language_txt)

    markup.add(btn_set_russian_language, btn_set_english_language)
    
    return markup

# Создание основного меню
def create_main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_start = types.KeyboardButton(btn_start_txt)
    btn_stop = types.KeyboardButton(btn_stop_txt)
    btn_info = types.KeyboardButton(btn_info_txt)
    btn_kor_rus_test = types.KeyboardButton(btn_kor_rus_test_txt)
    btn_random_ten_words = types.KeyboardButton(btn_random_ten_words_txt)
    btn_rus_kor_test = types.KeyboardButton(btn_rus_kor_test_txt)
    btn_add_word = types.KeyboardButton(btn_add_word_txt)
    btn_find_word = types.KeyboardButton(btn_find_word_txt)
    btn_all_words = types.KeyboardButton(btn_all_words_txt)

    markup.add(btn_start, btn_info, btn_kor_rus_test, btn_rus_kor_test, btn_random_ten_words, btn_all_words, btn_add_word, btn_find_word)
    
    return markup


##########################################################################################
# Функция перезагрузки бота
@bot.message_handler(func=lambda message: message.text.lower() == btn_restart_russian_txt.lower() or message.text.lower() == btn_restart_english_txt.lower())
def restart(message):
    user_id = message.chat.id
    if user_states:
        if user_states[user_id] is not None:
            del user_states[user_id]
    
    get_user_id()
    lists_updates()
    
    bot.send_message(user_id, "Фуф...Спасибо, что Вы меня перезагрузили, а то я, видимо, поломался...", reply_markup=create_main_menu())


# Создание кнопки для перезагрузки
def create_restart_button():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_restart = types.KeyboardButton(btn_restart_russian_txt)

    markup.add(btn_restart)

    return markup


##########################################################################################
# Функции для реализации возможности перейти назад
# Создание кнопки для перехода назад
def create_edit_choice_buttons():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_edit_word = types.KeyboardButton(btn_edit_word_txt)
    btn_edit_translation = types.KeyboardButton(btn_edit_translation_txt)
    btn_edit_category = types.KeyboardButton(btn_edit_category_txt)
    btn_delete_full_word_translation_category = types.KeyboardButton(btn_delete_full_word_translation_category_txt)
    btn_cancel = types.KeyboardButton(btn_cancel_txt)
    markup.add(btn_edit_word, btn_edit_translation, btn_edit_category, btn_delete_full_word_translation_category, btn_cancel)

    return markup


@bot.message_handler(func=lambda message: message.text.lower() == btn_back_for_find_word_functions_txt.lower())
def btn_back_for_find_word_functions(message):
    user_id = message.chat.id
    
    if user_states:
        if user_states[user_id] is not None:
            user_states[user_id]["state"] = WAITING_FOR_EDIT_CHOICE

    bot.send_message(user_id, "Ок. Возвращаемся назад.", reply_markup=create_edit_choice_buttons())
    

# Создание кнопки для перехода назад
def create_back_button():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_back = types.KeyboardButton(btn_back_for_find_word_functions_txt)

    markup.add(btn_back)
    
    return markup


# Создание кнопкок для подтверждения удаления
def create_confirmation_for_detete_buttons():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_delete_word_yes = types.KeyboardButton(btn_delete_word_yes_txt)
    btn_delete_word_no = types.KeyboardButton(btn_delete_word_no_txt)
    markup.add(btn_delete_word_yes, btn_delete_word_no)

    return markup

# Создание кнопки /stop
def create_stop_button():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_stop = types.KeyboardButton(btn_stop_txt)

    markup.add(btn_stop)

    return markup

##########################################################################################
# Главная функция. Точка отсчета :)
@bot.message_handler(commands=['start'])
def start(message):
    try:
        user_id = message.chat.id
        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]

        sticker = open('res/kpopHi.webp', 'rb')
        bot.send_sticker(user_id, sticker)

        bot.send_message(user_id, "👋🏻 Привет, {0.first_name}!\n <b>Я - Ваш ассистент по корейскому языку</b>. Я буду помогать тебе в заучивании корейских слов 🤓.".format(message.from_user), parse_mode='html', reply_markup=create_main_menu())
        bot.send_message(user_id, "<b>{0.first_name}</b>, нажмите на кнопку <b>{1}</b>, и я расскажу Вам много интересного о себе и о том, что я умею.".format(message.from_user, btn_info_txt),parse_mode='html')

        # Получаем данные пользователя и сохраняем в БД через готовую функцию
        save_user_data(
            id                  = message.chat.id,
            first_name          = message.from_user.first_name,
            last_name           = message.from_user.last_name,
        )
    except requests.exceptions.Timeout:
        bot.send_message(user_id, "Время ввода истекло. Пожалуйста, повторите весь процесс заново 🙂.", reply_markup=create_main_menu())
        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]
    except:
        bot.send_message(user_id, "Возникла непредвиденная ошибка. Извините, но Вам нужно будет повторить весь процесс заново 🙂\nПожалуйста, нажмите на кнопку " + "<b>'" + btn_restart_russian_txt + "'</b>.", reply_markup=create_restart_button(), parse_mode='html')
        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]

##########################################################################################
# Здесь функция добавления нового слова
@bot.message_handler(func=lambda message: message.text.lower() == btn_add_word_txt.lower())
def add_word(message):
    try:
        user_id = message.chat.id
        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]

        user_states[user_id] = {"state": WAITING_FOR_ADD_WORD}

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn_cancel = types.KeyboardButton(btn_cancel_txt)
        markup.add(btn_cancel)

        bot.send_message(user_id, "Введите слово/выражение, которое хотите добавить:", reply_markup=markup)
    except requests.exceptions.Timeout:
        bot.send_message(user_id, "Время ввода истекло. Пожалуйста, повторите весь процесс заново 🙂.", reply_markup=create_main_menu())
        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]
    except:
        bot.send_message(user_id, "Возникла непредвиденная ошибка. Извините, но Вам нужно будет повторить весь процесс заново 🙂\nПожалуйста, нажмите на кнопку " + "<b>'" + btn_restart_russian_txt + "'</b>.", reply_markup=create_restart_button(), parse_mode='html')
        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get("state") == WAITING_FOR_ADD_WORD)
def handle_word_input(message):
    try:
        user_id = message.chat.id
        if user_states:
            if user_states[user_id] is not None:
                user_states[user_id]["word"] = message.text
                user_states[user_id]["state"] = WAITING_FOR_ADD_TRANSLATION

                # Для проверки, есть ли слово в БД
                word_check = ""

                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                btn_cancel = types.KeyboardButton(btn_cancel_txt)
                markup.add(btn_cancel)
                
                conn = sqlite3.connect('voc.db')
                cursor = conn.cursor()

                # Проверяем, есть ли слово в БД (ищем либо по русскому, либо по корейскому)
                if hasRussianLetters(user_states[user_id]["word"]):
                    if not (user_states[user_id]["word"].startswith('/')):
                        cursor.execute("SELECT russian FROM words WHERE russian = ?", (user_states[user_id]["word"],))
                    else:
                        bot.send_message(user_id, "Слово/Выражение не должно начинаться с символа '/'.")
                        user_states[user_id]["state"] = WAITING_FOR_ADD_WORD
                        return
                        
                elif hasKoreanLetters(user_states[user_id]["word"]):
                    if not (user_states[user_id]["word"].startswith('/')):
                        cursor.execute("SELECT korean FROM words WHERE korean = ?", (user_states[user_id]["word"],))
                    else:
                        bot.send_message(user_id, "Слово/Выражение не должно начинаться с символа '/'.")
                        user_states[user_id]["state"] = WAITING_FOR_ADD_WORD
                        return
                else:
                    bot.send_message(user_id, "Пишите слово/выражение либо на корейском языке, либо на русском. Других языков я не знаю 😁")
                    user_states[user_id]["state"] = WAITING_FOR_ADD_WORD

                result = cursor.fetchone()  # Получаем результат
                conn.close()

                # Проверяем, найдено ли слово в БД
                if result is None:  # Если не найдено
                    if hasKoreanLetters(user_states[user_id]["word"]):
                        bot.send_message(user_id, "Введите перевод на <b>русском языке</b>:", parse_mode='html', reply_markup=markup)
                    elif hasRussianLetters(user_states[user_id]["word"]):
                        bot.send_message(user_id, "Введите перевод на <b>корейском языке</b>:", parse_mode='html', reply_markup=markup)
                else:
                    user_states[user_id]["state"] = WAITING_FOR_ADD_WORD
                    bot.send_message(user_id, "Такое слово уже есть в словаре.")
        else:
            bot.send_message(user_id, "Возникла непредвиденная ошибка. Возможно потеря соединения. Извините, но Вам нужно будет повторить весь процесс заново 🙂\nПожалуйста, нажмите на кнопку " + "<b>'" + btn_restart_russian_txt + "'</b>.", reply_markup=create_restart_button(), parse_mode='html')
            if user_states:
                if user_states[user_id] is not None:
                    del user_states[user_id]

    except requests.exceptions.Timeout:
        bot.send_message(user_id, "Время ввода истекло. Пожалуйста, повторите весь процесс заново 🙂.", reply_markup=create_main_menu())
        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]
    except:
        bot.send_message(user_id, "Возникла непредвиденная ошибка. Извините, но Вам нужно будет повторить весь процесс заново 🙂\nПожалуйста, нажмите на кнопку " + "<b>'" + btn_restart_russian_txt + "'</b>.", reply_markup=create_restart_button(), parse_mode='html')
        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]
    finally:
        conn.close()

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get("state") == WAITING_FOR_ADD_TRANSLATION)
def handle_translation_input(message):
    try:
        user_id = message.chat.id
        if user_states:
            if user_states[user_id] is not None:
                user_states[user_id]["translation"] = message.text

                conn = sqlite3.connect('voc.db')
                cursor = conn.cursor()
                if (hasRussianLetters(user_states[user_id]["translation"])):
                    if not (user_states[user_id]["translation"].startswith('/')):
                        cursor.execute("SELECT russian FROM words WHERE russian = ?", (user_states[user_id]["translation"],))
                    else:
                        bot.send_message(user_id, "Перевод не должен начинаться с символа '/'.")
                        user_states[user_id]["state"] = WAITING_FOR_ADD_TRANSLATION
                        return      
                elif (hasKoreanLetters(user_states[user_id]["translation"])):
                    if not (user_states[user_id]["translation"].startswith('/')):
                        cursor.execute("SELECT korean FROM words WHERE korean = ?", (user_states[user_id]["translation"],))
                    else:
                        bot.send_message(user_id, "Перевод не должен начинаться с символа '/'.")
                        user_states[user_id]["state"] = WAITING_FOR_ADD_TRANSLATION
                        return 
                else:
                    bot.send_message(user_id, "Пишите слово/выражение либо на корейском языке, либо на русском. Других языков я не знаю 😁.")
                    user_states[user_id]["state"] = WAITING_FOR_ADD_TRANSLATION
                    return
                

                result = cursor.fetchone()  # Получаем результат
                conn.close()

                markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
                btn_society = types.KeyboardButton(btn_category_society_txt)
                btn_education = types.KeyboardButton(btn_category_education_txt)
                btn_culture = types.KeyboardButton(btn_category_culture_txt)
                btn_religion = types.KeyboardButton(btn_category_religion_txt)
                btn_animals = types.KeyboardButton(btn_category_animals_txt)
                btn_plants = types.KeyboardButton(btn_category_plants_txt)
                btn_objects = types.KeyboardButton(btn_category_objects_txt)
                btn_food = types.KeyboardButton(btn_category_food_txt)
                btn_cancel = types.KeyboardButton(btn_cancel_txt)

                markup.add(btn_society)
                markup.add(btn_education)
                markup.add(btn_culture)
                markup.add(btn_religion)
                markup.add(btn_animals)
                markup.add(btn_plants)
                markup.add(btn_objects)
                markup.add(btn_food)
                markup.add(btn_cancel)

                # Проверяем, найдено ли слово в БД
                if result is None:  # Если не найдено
                    bot.send_message(user_id, "Выберите категорию", reply_markup=markup)
                    user_states[user_id]["state"] = WAITING_FOR_ADD_CATEGORY
                else:
                    user_states[user_id]["state"] = WAITING_FOR_ADD_TRANSLATION
                    bot.send_message(user_id, "Такой перевод уже есть в словаре.")
        else:
            bot.send_message(user_id, "Возникла непредвиденная ошибка. Возможно потеря соединения. Извините, но Вам нужно будет повторить весь процесс заново 🙂\nПожалуйста, нажмите на кнопку " + "<b>'" + btn_restart_russian_txt + "'</b>.", reply_markup=create_restart_button(), parse_mode='html')
            if user_states:
                if user_states[user_id] is not None:
                    del user_states[user_id]
    except requests.exceptions.Timeout:
        bot.send_message(user_id, "Время ввода истекло. Пожалуйста, повторите весь процесс заново 🙂.", reply_markup=create_main_menu())
        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]
    except:
        bot.send_message(user_id, "Возникла непредвиденная ошибка. Извините, но Вам нужно будет повторить весь процесс заново 🙂\nПожалуйста, нажмите на кнопку " + "<b>'" + btn_restart_russian_txt + "'</b>.", reply_markup=create_restart_button(), parse_mode='html')
        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]
    finally:
        conn.close()

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get("state") == WAITING_FOR_ADD_CATEGORY)
def handle_category_input(message):
    try:
        user_id = message.chat.id
        if user_states:
            if user_states[user_id] is not None:
                category = message.text
                word = user_states[user_id]["word"]
                translation = user_states[user_id]["translation"]
                
                if not (category in list_categories):
                    bot.send_message(user_id, "Нужно выбрать вариант только из предложенных категорий.")
                else:
                    # Сохранение в базу данных
                    conn = sqlite3.connect('voc.db')
                    cursor = conn.cursor()
                    if (hasKoreanLetters(user_states[user_id]["word"])) and (hasRussianLetters(user_states[user_id]["translation"])):
                        cursor.execute("INSERT INTO words (korean, russian, category) VALUES (?, ?, ?)", (word, translation.lower(), category))
                    elif (hasRussianLetters(user_states[user_id]["word"])) and (hasKoreanLetters(user_states[user_id]["translation"])):
                        cursor.execute("INSERT INTO words (russian, korean, category) VALUES (?, ?, ?)", (word.lower(), translation, category))
                    else:
                        bot.send_message(user_id, "Возникла ошибка. Повторите, пожалуйста, весь процесс заново 🙂.")
                        if user_states:
                            if user_states[user_id] is not None:
                                del user_states[user_id]
                        return

                    conn.commit()

                    bot.send_message(user_id, f"Слово/выражение <b>'{word}'</b> с переводом <b>'{translation}'</b> в категории <b>'{category}'</b> успешно добавлено!", reply_markup=create_main_menu(), parse_mode='html')
                    if user_states:
                        if user_states[user_id] is not None:
                            del user_states[user_id]
                    conn.close()
                    lists_updates()
        else:
            bot.send_message(user_id, "Возникла непредвиденная ошибка. Возможно потеря соединения. Извините, но Вам нужно будет повторить весь процесс заново 🙂\nПожалуйста, нажмите на кнопку " + "<b>'" + btn_restart_russian_txt + "'</b>.", reply_markup=create_restart_button(), parse_mode='html')
            if user_states:
                if user_states[user_id] is not None:
                    del user_states[user_id]
    except requests.exceptions.Timeout:
        bot.send_message(user_id, "Время ввода истекло. Пожалуйста, повторите весь процесс заново 🙂.", reply_markup=create_main_menu())
        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]
    except:
        bot.send_message(user_id, "Возникла непредвиденная ошибка. Извините, но Вам нужно будет повторить весь процесс заново 🙂\nПожалуйста, нажмите на кнопку " + "<b>'" + btn_restart_russian_txt + "'</b>.", reply_markup=create_restart_button(), parse_mode='html')
        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]
    finally:
        conn.close()

##########################################################################################
# Функция для нахождения слова
@bot.message_handler(func=lambda message: message.text.lower() == btn_find_word_txt.lower())
def find_word(message):
    try:
        user_id = message.chat.id
        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]

        user_states[user_id] = {"state": WAITING_FOR_PARTIAL_WORD}

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn_cancel = types.KeyboardButton(btn_cancel_txt)
        markup.add(btn_cancel)
        bot.send_message(user_id, "Введите слово/выражение или часть слова/выражения, которые хотите найти:", reply_markup=markup)
    except requests.exceptions.Timeout:
        bot.send_message(user_id, "Время ввода истекло. Пожалуйста, повторите весь процесс заново 🙂.", reply_markup=create_main_menu())
        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]
    except:
        bot.send_message(user_id, "Возникла непредвиденная ошибка. Извините, но Вам нужно будет повторить весь процесс заново 🙂\nПожалуйста, нажмите на кнопку " + "<b>'" + btn_restart_russian_txt + "'</b>.", reply_markup=create_restart_button(), parse_mode='html')
        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get("state") == WAITING_FOR_PARTIAL_WORD)
def handle_partial_word_input(message):
    try:
        user_id = message.chat.id
        if user_states:
            if user_states[user_id] is not None:
                partial_word = message.text
            
                # Поиск слов, которые содержат введенную часть
                conn = sqlite3.connect('voc.db')
                cursor = conn.cursor()
                cursor.execute("SELECT russian FROM words WHERE russian LIKE ? or russian LIKE ? or russian LIKE ? or russian LIKE ?", ('%' + partial_word + '%', '%' + partial_word.capitalize() + '%', '%' + partial_word.upper() + '%', '%' + partial_word.lower() + '%', ))
                results = cursor.fetchall()
                conn.close()
                if results:
                    markup = types.InlineKeyboardMarkup()
                    for result in results:
                        word = result[0]
                        markup.add(types.InlineKeyboardButton(text=word, callback_data=f"edit_{word}"))

                    bot.send_message(user_id, "Выберите слово/выражение для редактирования:", reply_markup=markup)
                else:
                    conn = sqlite3.connect('voc.db')
                    cursor = conn.cursor()
                    cursor.execute("SELECT korean FROM words WHERE korean LIKE ?", ('%' + partial_word + '%',))
                    results = cursor.fetchall()
                    if results:
                        markup = types.InlineKeyboardMarkup()
                        for result in results:
                            word = result[0]
                            markup.add(types.InlineKeyboardButton(text=word, callback_data=f"edit_{word}"))

                        bot.send_message(user_id, "Выберите слово/выражение для редактирования:", reply_markup=markup)
                    else:
                        bot.send_message(user_id, "К сожалению, подходящих слов/выражений я не смог найти. Попробуйте ввести другую часть слова/выражения.")
                    conn.close()
        else:
            bot.send_message(user_id, "Возникла непредвиденная ошибка. Возможно потеря соединения. Извините, но Вам нужно будет повторить весь процесс заново 🙂\nПожалуйста, нажмите на кнопку " + "<b>'" + btn_restart_russian_txt + "'</b>.", reply_markup=create_restart_button(), parse_mode='html')
            if user_states:
                if user_states[user_id] is not None:
                    del user_states[user_id]
    except requests.exceptions.Timeout:
        bot.send_message(user_id, "Время ввода истекло. Пожалуйста, повторите весь процесс заново 🙂.", reply_markup=create_main_menu())
        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]
    except:
        bot.send_message(user_id, "Возникла непредвиденная ошибка. Извините, но Вам нужно будет повторить весь процесс заново 🙂\nПожалуйста, нажмите на кнопку " + "<b>'" + btn_restart_russian_txt + "'</b>.", reply_markup=create_restart_button(), parse_mode='html')
        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]
    finally:
        conn.close()

@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_"))
def handle_word_selection(call):
    try:
        user_id = call.message.chat.id
        if user_states:
            if user_states[user_id] is not None:
                selected_word = call.data[len("edit_"):]
            
                translation_for_selected_word = ""
                category_for_selected_word = ""

                user_states[user_id] = {
                    "state": WAITING_FOR_EDIT_CHOICE,
                    "current_word": selected_word
                }

                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                item1 = types.KeyboardButton(btn_edit_word_txt)
                item2 = types.KeyboardButton(btn_edit_translation_txt)
                item3 = types.KeyboardButton(btn_edit_category_txt)
                item4 = types.KeyboardButton(btn_delete_full_word_translation_category_txt)
                item5 = types.KeyboardButton(btn_cancel_txt)
                markup.add(item1, item2, item3, item4, item5)
            
                # Надо получить основную информацию о слове - перевод и категорию. Все это для удобство пользователей.
                # Здесь ошибка. Надо найти ее и устранить :(
                if hasRussianLetters(user_states[user_id]["current_word"]):
                    conn = sqlite3.connect('voc.db')
                    cursor = conn.cursor()
                    cursor.execute("SELECT korean, category FROM words WHERE russian=?", (user_states[user_id]["current_word"],))
                    result = cursor.fetchone()
                    translation_for_selected_word = result[0]
                    category_for_selected_word = result[1]
                    conn.close()

                elif hasKoreanLetters(user_states[user_id]["current_word"]):
                    conn = sqlite3.connect('voc.db')
                    cursor = conn.cursor()
                    cursor.execute("SELECT russian, category FROM words WHERE korean=?", (user_states[user_id]["current_word"],))
                    result = cursor.fetchone()
                    translation_for_selected_word = result[0]
                    category_for_selected_word = result[1]
                    conn.close()

                user_states[user_id]["translation"] = translation_for_selected_word
                user_states[user_id]["category"] = category_for_selected_word

                bot.send_message(user_id, "[Информация]" + "\n" + "Слово/Выражение: " + "<b>" + user_states[user_id]["current_word"] + "</b>" + "\n" + "Перевод: " + "<b>" + translation_for_selected_word + "</b>" + "\n" + "Категория: " + "<b>" + category_for_selected_word + "</b>", parse_mode='html')
                bot.send_message(user_id, f"Вы выбрали слово/выражение: {selected_word}. Что Вы хотите с ним сделать сделать?", reply_markup=markup)
        else:
            bot.send_message(user_id, "Возникла непредвиденная ошибка. Возможно потеря соединения. Извините, но Вам нужно будет повторить весь процесс заново 🙂\nПожалуйста, нажмите на кнопку " + "<b>'" + btn_restart_russian_txt + "'</b>.", reply_markup=create_restart_button(), parse_mode='html')
            if user_states:
                if user_states[user_id] is not None:
                    del user_states[user_id]
    except requests.exceptions.Timeout:
        bot.send_message(user_id, "Время ввода истекло. Пожалуйста, повторите весь процесс заново 🙂.", reply_markup=create_main_menu())
        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]
    except:
        bot.send_message(user_id, "Возникла непредвиденная ошибка. Извините, но Вам нужно будет повторить весь процесс заново 🙂\nПожалуйста, нажмите на кнопку " + "<b>'" + btn_restart_russian_txt + "'</b>.", reply_markup=create_restart_button(), parse_mode='html')
        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]
    finally:
        conn.close()


##########################################################################################
# Функций для изменений слов и категорий
# Функция для изменения слова

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get("state") == WAITING_FOR_EDIT_CHOICE)
def handle_edit_choice(message):
    try:
        user_id = message.chat.id
        if user_states:
            if user_states[user_id] is not None:
                choice = message.text.lower()

                if choice == btn_edit_word_txt.lower():
                    user_states[user_id]["state"] = WAITING_FOR_NEW_WORD
                    bot.send_message(user_id, "Введите новое <b>слово/выражение</b>:", reply_markup=create_back_button(), parse_mode='html')
                elif choice == btn_edit_translation_txt.lower():
                    user_states[user_id]["state"] = WAITING_FOR_NEW_TRANSLATION
                    bot.send_message(user_id, "Введите новый <b>перевод</b>:", reply_markup=create_back_button(), parse_mode='html')
                elif choice == btn_edit_category_txt.lower():
                    user_states[user_id]["state"] = WAITING_FOR_NEW_CATEGORY
                    bot.send_message(user_id, "Введите новую <b>категорию</b>:", reply_markup=create_back_button(), parse_mode='html')
                elif choice == btn_delete_full_word_translation_category_txt.lower():
                    user_states[user_id]["state"] = WAITING_FOR_DELETE_FULL_WORD_TRANSLATION_CATEGORY
                    bot.send_message(user_id, "Вы точно хотите удалить " + "<b>" + user_states[user_id]["current_word"] + "</b>" + " - " + "<b>" + user_states[user_id]["translation"] + "</b>" + "{📚Категория: " + "[" + "<b>" + user_states[user_id]["category"] + "</b>" + "]}" + "🤔?", reply_markup=create_confirmation_for_detete_buttons(), parse_mode='html')
                    # create_confirmation_for_detete_buttons
                elif choice == btn_cancel_txt.lower():
                    pass # Можно было это не делать так, как кнопка сама по себе сработает.
                else:
                    bot.send_message(user_id, "К сожалению, такого выбора здесь нет. Выберите, пожалуйста, один из предложенныйх вариантов 😁.")
                    if user_states:
                        if user_states[user_id] is not None:
                            del user_states[user_id]
        else:
            bot.send_message(user_id, "Возникла непредвиденная ошибка. Возможно потеря соединения. Извините, но Вам нужно будет повторить весь процесс заново 🙂\nПожалуйста, нажмите на кнопку " + "<b>'" + btn_restart_russian_txt + "'</b>.", reply_markup=create_restart_button(), parse_mode='html')
            if user_states:
                if user_states[user_id] is not None:
                    del user_states[user_id]
    except requests.exceptions.Timeout:
        bot.send_message(user_id, "Время ввода истекло. Пожалуйста, повторите весь процесс заново 🙂.", reply_markup=create_main_menu())
        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]
    except:
        bot.send_message(user_id, "Возникла непредвиденная ошибка. Извините, но Вам нужно будет повторить весь процесс заново 🙂\nПожалуйста, нажмите на кнопку " + "<b>'" + btn_restart_russian_txt + "'</b>.", reply_markup=create_restart_button(), parse_mode='html')
        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]
# Меняем на новое слово
@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get("state") == WAITING_FOR_NEW_WORD)
def handle_new_word_input(message):
    try:
        user_id = message.chat.id
        if user_states:
            if user_states[user_id] is not None:
                new_word = message.text
                current_word = user_states[user_id]["current_word"]

                conn = sqlite3.connect('voc.db')
                cursor = conn.cursor()
                if hasKoreanLetters(current_word):
                    if hasKoreanLetters(new_word):
                        if not (new_word.startswith('/')):
                            cursor.execute("SELECT korean FROM words WHERE korean = ? ", (new_word,))
                            result = cursor.fetchone()
                            if result is None:
                                cursor.execute("UPDATE words SET korean=? WHERE korean=?", (new_word, current_word))
                                bot.send_message(user_id, f"Слово/Выражение '{current_word}' успешно изменено на '{new_word}'!")
                                user_states[user_id]["state"] = WAITING_FOR_EDIT_CHOICE
                                conn.commit()
                                user_states[user_id]["current_word"] = new_word
                                conn.close()
                                
                                lists_updates()
                            else:
                                bot.send_message(user_id, "Такое слово/выражение уже есть в словаре 🙂.")
                                user_states[user_id]["state"] = WAITING_FOR_NEW_WORD
                                return
                        else:
                            bot.send_message(user_id, "<b>Слово/Выражение</b> не должно начинаться с символа '/'.", parse_mode='html')
                            user_states[user_id]["state"] = WAITING_FOR_NEW_WORD
                            return
                    else:
                        bot.send_message(user_id, "Так как слово/выражение '<b>" + current_word + "</b>' написанно на корейском языке, то слово/выражение на которое Вы хотите заменить тоже должно быть написано на корейском.", parse_mode='html')
                        bot.send_message(user_id, "Напишите, пожалуйста, еще раз на какое слово/выражение Вы хотите поменять 😉.")
                        conn.close()
                        return
                elif hasRussianLetters(current_word):
                    if hasRussianLetters(new_word):
                        if not (new_word.startswith('/')):
                            cursor.execute("SELECT russian FROM words WHERE russian = ? ", (new_word,))
                            result = cursor.fetchone()
                            if result is None:
                                cursor.execute("UPDATE words SET russian=? WHERE russian=?", (new_word.lower(), current_word.lower()))
                                bot.send_message(user_id, f"Слово '{current_word}' успешно изменено на '{new_word}'!")
                                user_states[user_id]["state"] = WAITING_FOR_EDIT_CHOICE
                                conn.commit()
                                user_states[user_id]["current_word"] = new_word
                                conn.close()

                                lists_updates()
                            else:
                                bot.send_message(user_id, "Такое слово/выражение уже есть в словаре.")
                                user_states[user_id]["state"] = WAITING_FOR_NEW_WORD
                                return
                        else:
                            bot.send_message(user_id, "<b>Слово/Выражение</b> не должно начинаться с символа '/'.", parse_mode='html')
                            user_states[user_id]["state"] = WAITING_FOR_NEW_WORD
                            return
                    else:
                        bot.send_message(user_id, "Так как слово/выражение '<b>" + current_word + "</b>' написанно на русском языке, то слово/выражение на которое Вы хотите заменить тоже должно быть написано на русском.", parse_mode='html')
                        bot.send_message(user_id, "Напишите, пожалуйста, еще раз на какое слово/выражение Вы хотите поменять 😉.")
                        conn.close()
                        return
                else:
                    bot.send_message(user_id, "Возникла непредвиденная ошибка. Извините, но Вам нужно будет повторить весь процесс заново 🙂\nПожалуйста, нажмите на кнопку " + "<b>'" + btn_restart_russian_txt + "'</b>.", reply_markup=create_restart_button(), parse_mode='html')
                    if user_states:
                        if user_states[user_id] is not None:
                            del user_states[user_id]
        else:
            bot.send_message(user_id, "Возникла непредвиденная ошибка. Возможно потеря соединения. Извините, но Вам нужно будет повторить весь процесс заново 🙂\nПожалуйста, нажмите на кнопку " + "<b>'" + btn_restart_russian_txt + "'</b>.", reply_markup=create_restart_button(), parse_mode='html')
            if user_states:
                if user_states[user_id] is not None:
                    del user_states[user_id]
    except requests.exceptions.Timeout:
        bot.send_message(user_id, "Время ввода истекло. Пожалуйста, повторите весь процесс заново 🙂.", reply_markup=create_main_menu())
        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]
    except:
        bot.send_message(user_id, "Возникла непредвиденная ошибка. Извините, но Вам нужно будет повторить весь процесс заново 🙂\nПожалуйста, нажмите на кнопку " + "<b>'" + btn_restart_russian_txt + "'</b>.", reply_markup=create_restart_button(), parse_mode='html')
        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]
    finally:
        conn.close()

# Меняем перевод слова
@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get("state") == WAITING_FOR_NEW_TRANSLATION)
def handle_new_translation_input(message):
    try:
        user_id = message.chat.id
        if user_states:
            if user_states[user_id] is not None:
                new_translation = message.text
                current_word = user_states[user_id]["current_word"]
            
                conn = sqlite3.connect('voc.db')
                cursor = conn.cursor()
                if hasKoreanLetters(current_word):
                    if hasRussianLetters(new_translation):
                        if not (new_translation.startswith('/')):
                            cursor.execute("SELECT russian FROM words WHERE russian = ?", (new_translation.lower(),))
                            result = cursor.fetchone()
                            if result is None:
                                cursor.execute("UPDATE words SET russian=? WHERE korean=?", (new_translation, current_word))
                                bot.send_message(user_id, f"Перевод для слова '{current_word}' успешно изменен на '{new_translation}'!")
                                user_states[user_id]["state"] = WAITING_FOR_EDIT_CHOICE
                                conn.commit()
                                conn.close()

                                lists_updates()
                                user_states[user_id]["translation"] = new_translation
                            else:
                                bot.send_message(user_id, "Такой перевод уже есть в словаре.")
                                user_states[user_id]["state"] = WAITING_FOR_NEW_TRANSLATION
                                return
                        else:
                            bot.send_message(user_id, "<b>Перевод</b> не должен начинаться с символа '/'.", parse_mode='html')
                            user_states[user_id]["state"] = WAITING_FOR_NEW_TRANSLATION
                            return
                    else:
                        bot.send_message(user_id, "Так как перевод '<b>" + user_states[user_id]["translation"] + "</b>' написан на русском языке, то новый перевод тоже должен быть написан на русском.", parse_mode='html')
                        bot.send_message(user_id, "Напишите, пожалуйста, еще раз новый перевод для слова/выражения '" + current_word + "' 😉.")
                        conn.close()
                        return
                elif hasRussianLetters(current_word):
                    if hasKoreanLetters(new_translation):
                        if not(new_translation.startswith('/')):
                            cursor.execute("SELECT korean FROM words WHERE korean = ?", (new_translation,))
                            result = cursor.fetchone()
                            if result is None:
                                cursor.execute("UPDATE words SET korean=? WHERE russian=?", (new_translation, current_word.lower()))
                                bot.send_message(user_id, f"Перевод для слова '{current_word}' успешно изменен на '{new_translation}'!")
                                user_states[user_id]["state"] = WAITING_FOR_EDIT_CHOICE
                                conn.commit()
                                conn.close()

                                lists_updates()
                                user_states[user_id]["translation"] = new_translation
                            else:
                                bot.send_message(user_id, "Такой перевод уже есть в словаре.")
                                user_states[user_id]["state"] = WAITING_FOR_NEW_TRANSLATION
                                return
                        else:
                            bot.send_message(user_id, "<b>Перевод</b> не должен начинаться с символа '/'.", parse_mode='html')
                            user_states[user_id]["state"] = WAITING_FOR_NEW_TRANSLATION
                            return
                    else:
                        bot.send_message(user_id, "Так как перевод '<b>" + user_states[user_id]["translation"] + "</b>' написан на корейском языке, то новый перевод тоже должен быть написан на корейском.", parse_mode='html')
                        bot.send_message(user_id, "Напишите, пожалуйста, еще раз новый перевод для слова/выражения '" + current_word + "' 😉.")
                        conn.close()
                        return
                else:
                    bot.send_message(user_id, "Возникла непредвиденная ошибка. Извините, но Вам нужно будет повторить весь процесс заново 🙂\nПожалуйста, нажмите на кнопку " + "<b>'" + btn_restart_russian_txt + "'</b>.", reply_markup=create_restart_button(), parse_mode='html')
                    if user_states:
                        if user_states[user_id] is not None:
                            del user_states[user_id]
        else:
            bot.send_message(user_id, "Возникла непредвиденная ошибка. Возможно потеря соединения. Извините, но Вам нужно будет повторить весь процесс заново 🙂\nПожалуйста, нажмите на кнопку " + "<b>'" + btn_restart_russian_txt + "'</b>.", reply_markup=create_restart_button(), parse_mode='html')
            if user_states:
                if user_states[user_id] is not None:
                    del user_states[user_id]
    except requests.exceptions.Timeout:
        bot.send_message(user_id, "Время ввода истекло. Пожалуйста, повторите весь процесс заново 🙂.", reply_markup=create_main_menu())
        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]
    except:
        bot.send_message(user_id, "Возникла непредвиденная ошибка. Извините, но Вам нужно будет повторить весь процесс заново 🙂\nПожалуйста, нажмите на кнопку " + "<b>'" + btn_restart_russian_txt + "'</b>.", reply_markup=create_restart_button(), parse_mode='html')
        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]
    finally:
        conn.close()
# Меняем категорию
@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get("state") == WAITING_FOR_NEW_CATEGORY)
def handle_new_category_input(message):
    try:
        user_id = message.chat.id
        if user_states:
            if user_states[user_id] is not None:
                new_category = message.text
                current_word = user_states[user_id]["current_word"]
            
                conn = sqlite3.connect('voc.db')
                cursor = conn.cursor()
                if new_category in categoryList:
                    if hasRussianLetters(current_word):
                        cursor.execute("SELECT category FROM words WHERE russian = ?", (current_word,))
                    elif hasKoreanLetters(current_word):
                        cursor.execute("SELECT category FROM words WHERE korean = ?", (current_word,))
                    else:
                        bot.send_message(user_id, "Хммм...Странно, обычно до этого момента, такая ошибка должна быть обработана уже заранее...Пожалуста, перезагрузите меня:).", reply_markup=create_restart_button())
                        if user_states:
                            if user_states[user_id] is not None:
                                del user_states[user_id]
                    result = cursor.fetchone()
                    if result is not None:
                        if new_category == result[0]:
                            bot.send_message(user_id, "Слово/Выражение " + current_word + " уже имеет категорию " + new_category + "." + "\nВыберите другую категорию.")
                            user_states[user_id]["state"] = WAITING_FOR_NEW_CATEGORY
                        else:
                            cursor.execute("UPDATE words SET category=? WHERE korean=?", (new_category, current_word))
                            bot.send_message(user_id, f"Категория для слова '{current_word}' успешно изменена на '{new_category}'!")
                            conn.commit()
                            conn.close()
                            user_states[user_id]["category"] = new_category
                    else:
                        bot.send_message(user_id, "Хммм...Странно, обычно до этого момента, такая ошибка должна быть обработана уже заранее...Пожалуйста, перезагрузите меня:).", reply_markup=create_restart_button())
                        if user_states:
                            if user_states[user_id] is not None:
                                del user_states[user_id]
                else:
                    bot.send_message(user_id, "Возникла непредвиденная ошибка. Извините, но Вам нужно будет повторить весь процесс заново 🙂\nПожалуйста, нажмите на кнопку " + "<b>'" + btn_restart_russian_txt + "'</b>.", reply_markup=create_restart_button(), parse_mode='html')
                    if user_states:
                        if user_states[user_id] is not None:
                            del user_states[user_id]
        else:
            bot.send_message(user_id, "Возникла непредвиденная ошибка. Возможно потеря соединения. Извините, но Вам нужно будет повторить весь процесс заново 🙂\nПожалуйста, нажмите на кнопку " + "<b>'" + btn_restart_russian_txt + "'</b>.", reply_markup=create_restart_button(), parse_mode='html')
            if user_states:
                if user_states[user_id] is not None:
                    del user_states[user_id]

    except requests.exceptions.Timeout:
        bot.send_message(user_id, "Время ввода истекло. Пожалуйста, повторите весь процесс заново 🙂.", reply_markup=create_main_menu())
        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]
    except:
        bot.send_message(user_id, "Возникла непредвиденная ошибка. Извините, но Вам нужно будет повторить весь процесс заново 🙂\nПожалуйста, нажмите на кнопку " + "<b>'" + btn_restart_russian_txt + "'</b>.", reply_markup=create_restart_button(), parse_mode='html')
        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]
    finally:
        conn.close()
##########################################################################################
# Функция, реализующая удаления слова, перевода и категории из БД
@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get("state") == WAITING_FOR_DELETE_FULL_WORD_TRANSLATION_CATEGORY)
def handle_full_delete_word_translation_category_input(message):
    try:
        user_id = message.chat.id
        if user_states:
            if user_states[user_id] is not None:
                current_word = user_states[user_id]["current_word"]

                choice = message.text.lower()

                conn = sqlite3.connect('voc.db')
                cursor = conn.cursor()

                if choice == btn_delete_word_yes_txt.lower():
                    if hasRussianLetters(current_word):
                        cursor.execute("DELETE FROM words WHERE russian = ?", (current_word,))
                        conn.commit()
                        bot.send_message(user_id, "<b>" + user_states[user_id]["current_word"] + "</b>" + " - " + "<b>" + user_states[user_id]["translation"] + "</b>" + "{📚Категория: " + "[" + "<b>" + user_states[user_id]["category"] + "</b>" + "]}" + " удалены.", reply_markup=create_main_menu(), parse_mode='html')
                        conn.close()
                        if user_states:
                            if user_states[user_id] is not None:
                                del user_states[user_id]
                    elif hasKoreanLetters(current_word):
                        cursor.execute("DELETE FROM words WHERE korean = ?", (current_word,))
                        conn.commit()
                        bot.send_message(user_id, "<b>" + user_states[user_id]["current_word"] + "</b>" + " - " + "<b>" + user_states[user_id]["translation"] + "</b>" + "{📚Категория: " + "[" + "<b>" + user_states[user_id]["category"] + "</b>" + "]}" + " удалены.", reply_markup=create_main_menu(), parse_mode='html')
                        conn.close()
                        if user_states:
                            if user_states[user_id] is not None:
                                del user_states[user_id]
                    else:
                        bot.send_message(user_id, "Хммм...Странно, обычно до этого момента, такая ошибка должна быть обработана уже заранее...Пожалуйста, перезагрузите меня:).", reply_markup=create_restart_button())
                        if user_states:
                            if user_states[user_id] is not None:
                                del user_states[user_id]
                elif choice == btn_delete_word_no_txt.lower():
                    user_states[user_id]["state"] = WAITING_FOR_EDIT_CHOICE
                    bot.send_message(user_id, "Ок. Возвращаемся назад.", reply_markup=create_edit_choice_buttons())
                else:
                    bot.send_message(user_id, "К сожалению, такого выбора здесь нет 😂. Пожалуйста, выберите из того что есть 😁.")   
        else:
            bot.send_message(user_id, "Возникла непредвиденная ошибка. Возможно потеря соединения. Извините, но Вам нужно будет повторить весь процесс заново 🙂\nПожалуйста, нажмите на кнопку " + "<b>'" + btn_restart_russian_txt + "'</b>.", reply_markup=create_restart_button(), parse_mode='html')
            if user_states:
                if user_states[user_id] is not None:
                    del user_states[user_id]
    except requests.exceptions.Timeout:
        bot.send_message(user_id, "Время ввода истекло. Пожалуйста, повторите весь процесс заново 🙂.", reply_markup=create_main_menu())
        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]
    except:
        bot.send_message(user_id, "Возникла непредвиденная ошибка. Извините, но Вам нужно будет повторить весь процесс заново 🙂\nПожалуйста, нажмите на кнопку " + "<b>'" + btn_restart_russian_txt + "'</b>.", reply_markup=create_restart_button(), parse_mode='html')
        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]
    finally:
        conn.close()

##########################################################################################
# Функция для вывода случаных 10 слов из БД
@bot.message_handler(func=lambda message: message.text.lower() == btn_random_ten_words_txt.lower())
def random_ten_words(message):
    try:
        user_id = message.chat.id

        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]

        bot.send_message(user_id, "Давайте начнем. 😎 Желаю Вам удачи! 🍀", reply_markup=create_stop_button())
        bot.send_message(user_id, "Здесь случайным образом выбраны 10 слов/выражений из словаря и также случайно выбран вариант тестирования 😉.", reply_markup=create_stop_button())
    
        random_ten_combined_list = []
        # Перемешиваем вопросы и ответы
        combined_list = list(zip(koreanList, russianList))

        random.shuffle(combined_list)
        

        for i in range(10):
            random_ten_combined_list.append(combined_list[i])

        shuffled_koreanList, shuffled_russianList = zip(*random_ten_combined_list)
        
    
        user_states[user_id] = {
            "state": WAITING_FOR_TRANSLATION,
            "current_word_index": 0,
            "score": 0,
            "shuffled_koreanList": shuffled_koreanList,
            "shuffled_russianList": shuffled_russianList,
            "translation": "none"
        }

        # Реализуем, так:
        # Сделаем реализацию случая. Пользователю наугад выпадет либо корейско-русский, либо русско-корейский
        random_choice = random.randint(0,1)
        if (random_choice == 0):
            user_states[user_id]["translation"] = "korean_russian"
            send_question_korean_russian(user_id)
        else:
            user_states[user_id]["translation"] = "russian_korean"
            send_question_russian_korean(user_id)
    
    except requests.exceptions.Timeout:
        bot.send_message(user_id, "Время ввода истекло. Пожалуйста, повторите весь процесс заново 🙂.", reply_markup=create_main_menu())
        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]
    except:
        bot.send_message(user_id, "Возникла непредвиденная ошибка. Извините, но Вам нужно будет повторить весь процесс заново 🙂\nПожалуйста, нажмите на кнопку " + "<b>'" + btn_restart_russian_txt + "'</b>.", reply_markup=create_restart_button(), parse_mode='html')
        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]

##########################################################################################
# Здесь функция STOP для всех тестов
@bot.message_handler(commands=['stop'])
def stop_quiz(message):
    try:
        user_id = message.chat.id
    
        if user_id in user_states:
            score = user_states[user_id]["score"]
            total_questions = len(user_states[user_id]["shuffled_koreanList"])
            bot.send_message(user_id, f"Тест завершён! Ваш результат: <b>{score}</b> из <b>{total_questions}</b>", reply_markup=create_main_menu(), parse_mode='html')

            percentage = (score / total_questions) * 100
            bot.send_message(user_id, "В процентном значении: " + str(percentage) + " %")
 
            # Отправка стикеров в зависимости от результата
            if percentage <= 20:  # 0% - 20% BAD
                sticker = open('res/kpopBad.webp', 'rb')
                bot.send_sticker(user_id, sticker)
                bot.send_message(user_id, "Честно говоря - плохо. Нужно больше стараться.")
            elif percentage <= 40:  # 21% - 40% BELOW AVERAGE
                sticker = open('res/kpopNotBad.webp', 'rb')
                bot.send_sticker(user_id, sticker)
                bot.send_message(user_id, "Неплохо. Но надо быть усерднее.") 
            elif percentage <= 60:  # 41% - 60% GOOD
                sticker = open('res/kpopGood.webp', 'rb')
                bot.send_sticker(user_id, sticker) 
                bot.send_message(user_id, "Хороший результат!")
            elif percentage <= 80:  # 61% - 80% VERY GOOD
                sticker = open('res/kpopVeryGood.webp', 'rb')
                bot.send_sticker(user_id, sticker)
                bot.send_message(user_id, "Очень хорошо. Так держать!")
            else:  # 81% - 100% EXCELLENT
                sticker = open('res/kpopExcellent.webp', 'rb')
                bot.send_sticker(user_id, sticker)
                bot.send_message(user_id, "Супер! Отлично, молодец!")

            if user_states:
                if user_states[user_id] is not None:
                    del user_states[user_id]
        else:
            bot.send_message(user_id, "Вы ещё не начали тест. Напишите 'Проверь меня!', чтобы начать.")
    except requests.exceptions.Timeout:
        bot.send_message(user_id, "Время ввода истекло. Пожалуйста, повторите весь процесс заново 🙂.", reply_markup=create_main_menu())
        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]
    except:
        bot.send_message(user_id, "Возникла непредвиденная ошибка. Извините, но Вам нужно будет повторить весь процесс заново 🙂\nПожалуйста, нажмите на кнопку " + "<b>'" + btn_restart_russian_txt + "'</b>.", reply_markup=create_restart_button(), parse_mode='html')
        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]
##########################################################################################
# Здесь функции для корейско-русского варианта
@bot.message_handler(func=lambda message: message.text.lower() == btn_kor_rus_test_txt.lower())
def start_quiz_korean_russian(message):
    try:
        user_id = message.chat.id

        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]

        bot.send_message(user_id, "Давайте начнем. 😎 Желаю Вам удачи! 🍀", reply_markup=create_stop_button())

        # Перемешиваем вопросы и ответы
        combined_list = list(zip(koreanList, russianList))
        random.shuffle(combined_list)
        shuffled_koreanList, shuffled_russianList = zip(*combined_list)

        user_states[user_id] = {
            "state": WAITING_FOR_TRANSLATION,
            "current_word_index": 0,
            "score": 0,
            "shuffled_koreanList": shuffled_koreanList,
            "shuffled_russianList": shuffled_russianList,
            "translation": "korean_russian"
        }
        send_question_korean_russian(user_id)
    except requests.exceptions.Timeout:
        bot.send_message(user_id, "Время ввода истекло. Пожалуйста, повторите весь процесс заново 🙂.", reply_markup=create_main_menu())
        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]
    except:
        bot.send_message(user_id, "Возникла непредвиденная ошибка. Извините, но Вам нужно будет повторить весь процесс заново 🙂\nПожалуйста, нажмите на кнопку " + "<b>'" + btn_restart_russian_txt + "'</b>.", reply_markup=create_restart_button(), parse_mode='html')
        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]

def send_question_korean_russian(user_id):
    try:
        current_index = user_states[user_id]["current_word_index"]
        word = user_states[user_id]["shuffled_koreanList"][current_index]
        
        markup = types.InlineKeyboardMarkup()
        
        correct_translation = user_states[user_id]["shuffled_russianList"][current_index]
        possible_answers = [correct_translation]
        while len(possible_answers) < 4:
            random_translation = user_states[user_id]["shuffled_russianList"][(current_index + len(possible_answers)) % len(user_states[user_id]["shuffled_russianList"])]
            if random_translation not in possible_answers:
                possible_answers.append(random_translation)
        
        random.shuffle(possible_answers)
        
        for answer in possible_answers:
            markup.add(types.InlineKeyboardButton(answer, callback_data=answer))
        
        # Выводим вопрос и прикрепляем к нему кнопки с ответами
        bot.send_message(user_id, f"Переведи слово: <b>{word}</b>" + " (" + str(user_states[user_id]["current_word_index"] + 1) + "/" + str(len(user_states[user_id]["shuffled_russianList"])) + ")", parse_mode='html', reply_markup=markup)
    except requests.exceptions.Timeout:
        bot.send_message(user_id, "Время ввода истекло. Пожалуйста, повторите весь процесс заново 🙂.", reply_markup=create_main_menu())
        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]
    except:
        bot.send_message(user_id, "Возникла непредвиденная ошибка. Извините, но Вам нужно будет повторить весь процесс заново 🙂\nПожалуйста, нажмите на кнопку " + "<b>'" + btn_restart_russian_txt + "'</b>.", reply_markup=create_restart_button(), parse_mode='html')
        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]

@bot.callback_query_handler(func=lambda call: user_states.get(call.message.chat.id, {}).get("translation") == "korean_russian")
def handle_answer_korean_russian(call):
    try:
        user_id = call.message.chat.id
        if user_states:
            if user_states[user_id] is not None:
                if (user_states[user_id]["translation"] == "korean_russian"):
                    if user_id in user_states and user_states[user_id]["state"] == WAITING_FOR_TRANSLATION:
                        user_translation = call.data
                        current_index = user_states[user_id]["current_word_index"]
                        correct_translation = user_states[user_id]["shuffled_russianList"][current_index]

                        if user_translation.strip().lower() == correct_translation.strip().lower():
                            bot.send_message(user_id, "Правильно! ✅")
                            user_states[user_id]["score"] += 1
                        else:
                            bot.send_message(user_id, f"Неправильно! ❌. Правильный перевод: <b>{correct_translation}</b>", parse_mode='html')

                        if current_index + 1 < len(user_states[user_id]["shuffled_koreanList"]):
                            user_states[user_id]["current_word_index"] += 1
                            send_question_korean_russian(user_id)
                        else:
                            total_questions = len(user_states[user_id]["shuffled_koreanList"])
                            score = user_states[user_id]["score"]
                            percentage = (score / total_questions) * 100

                            bot.send_message(user_id, f"Вы закончили тест! Ваш результат: <b>{score}</b> из <b>{len(user_states[user_id]['shuffled_koreanList'])}</b>", reply_markup=create_main_menu(), parse_mode='html')
                            bot.send_message(user_id, "В процентном значении: " + str(percentage) + " %")
                            # Отправка стикеров в зависимости от результата
                            if percentage <= 20:  # 0% - 20% BAD
                                sticker = open('res/kpopBad.webp', 'rb')
                                bot.send_sticker(user_id, sticker)
                                bot.send_message(user_id, "Честно говоря - плохо. Нужно больше стараться.")
                            elif percentage <= 40:  # 21% - 40% BELOW AVERAGE
                                sticker = open('res/kpopNotBad.webp', 'rb')
                                bot.send_sticker(user_id, sticker)
                                bot.send_message(user_id, "Неплохо. Но надо быть усерднее.") 
                            elif percentage <= 60:  # 41% - 60% GOOD
                                sticker = open('res/kpopGood.webp', 'rb')
                                bot.send_sticker(user_id, sticker) 
                                bot.send_message(user_id, "Хороший результат!")
                            elif percentage <= 80:  # 61% - 80% VERY GOOD
                                sticker = open('res/kpopVeryGood.webp', 'rb')
                                bot.send_sticker(user_id, sticker)
                                bot.send_message(user_id, "Очень хорошо. Так держать!")
                            else:  # 81% - 100% EXCELLENT
                                sticker = open('res/kpopExcellent.webp', 'rb')
                                bot.send_sticker(user_id, sticker)
                                bot.send_message(user_id, "Супер! Отлично, молодец!")

                            if user_states:
                                if user_states[user_id] is not None:
                                    del user_states[user_id]
                else:
                    bot.send_message(user_id, "Возникла непредвиденная ошибка. Извините, но Вам нужно будет повторить весь процесс заново 🙂\nПожалуйста, нажмите на кнопку " + "<b>'" + btn_restart_russian_txt + "'</b>.", reply_markup=create_restart_button(), parse_mode='html')
                    if user_states:
                        if user_states[user_id] is not None:
                            del user_states[user_id]
        else:
            bot.send_message(user_id, "Возникла непредвиденная ошибка. Возможно потеря соединения. Извините, но Вам нужно будет повторить весь процесс заново 🙂\nПожалуйста, нажмите на кнопку " + "<b>'" + btn_restart_russian_txt + "'</b>.", reply_markup=create_restart_button(), parse_mode='html')
            if user_states:
                if user_states[user_id] is not None:
                    del user_states[user_id]
    except requests.exceptions.Timeout:
        bot.send_message(user_id, "Время ввода истекло. Пожалуйста, повторите весь процесс заново 🙂.", reply_markup=create_main_menu())
        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]
    except:
        bot.send_message(user_id, "Возникла непредвиденная ошибка. Извините, но Вам нужно будет повторить весь процесс заново 🙂\nПожалуйста, нажмите на кнопку " + "<b>'" + btn_restart_russian_txt + "'</b>.", reply_markup=create_restart_button(), parse_mode='html')
        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]

# Русско-корейский вариант
@bot.message_handler(func=lambda message: message.text.lower() == btn_rus_kor_test_txt.lower())
def start_quiz_russian_korean(message):
    try:
        user_id = message.chat.id

        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]
        
        bot.send_message(user_id, "Давайте начнем. 😎 Желаю Вам удачи! 🍀", reply_markup=create_stop_button())

        # Перемешиваем вопросы и ответы
        combined_list = list(zip(russianList, koreanList))
        random.shuffle(combined_list)
        shuffled_russianList, shuffled_koreanList = zip(*combined_list)

        user_states[user_id] = {
            "state": WAITING_FOR_TRANSLATION,
            "current_word_index": 0,
            "score": 0,
            "shuffled_koreanList": shuffled_koreanList,
            "shuffled_russianList": shuffled_russianList,
            "translation": "russian_korean"
        }
        send_question_russian_korean(user_id)
    except requests.exceptions.Timeout:
        bot.send_message(user_id, "Время ввода истекло. Пожалуйста, повторите весь процесс заново 🙂.", reply_markup=create_main_menu())
        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]
    except:
        bot.send_message(user_id, "Возникла непредвиденная ошибка. Извините, но Вам нужно будет повторить весь процесс заново 🙂\nПожалуйста, нажмите на кнопку " + "<b>'" + btn_restart_russian_txt + "'</b>.", reply_markup=create_restart_button(), parse_mode='html')
        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]
def send_question_russian_korean(user_id):
    try:
        current_index = user_states[user_id]["current_word_index"]
        word = user_states[user_id]["shuffled_russianList"][current_index]
        
        markup = types.InlineKeyboardMarkup()
        
        correct_translation = user_states[user_id]["shuffled_koreanList"][current_index]
        possible_answers = [correct_translation]
        while len(possible_answers) < 4:
            random_translation = user_states[user_id]["shuffled_koreanList"][(current_index + len(possible_answers)) % len(user_states[user_id]["shuffled_koreanList"])]
            if random_translation not in possible_answers:
                possible_answers.append(random_translation)
        
        random.shuffle(possible_answers)
        
        for answer in possible_answers:
            markup.add(types.InlineKeyboardButton(answer, callback_data=answer))
        
        # Выводим вопрос и прикрепляем к нему кнопки с ответами
        bot.send_message(user_id, f"Переведи слово: <b>{word}</b>" + " (" + str(user_states[user_id]["current_word_index"] + 1) + "/" + str(len(user_states[user_id]["shuffled_koreanList"])) + ")", parse_mode='html', reply_markup=markup)
    except requests.exceptions.Timeout:
        bot.send_message(user_id, "Время ввода истекло. Пожалуйста, повторите весь процесс заново 🙂.", reply_markup=create_main_menu())
        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]
    except:
        bot.send_message(user_id, "Возникла непредвиденная ошибка. Извините, но Вам нужно будет повторить весь процесс заново 🙂\nПожалуйста, нажмите на кнопку " + "<b>'" + btn_restart_russian_txt + "'</b>.", reply_markup=create_restart_button(), parse_mode='html')
        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]

@bot.callback_query_handler(func=lambda call: user_states.get(call.message.chat.id, {}).get("translation") == "russian_korean")
def handle_answer_russian_korean(call):
    try:
        user_id = call.message.chat.id
        if user_states:
            if user_states[user_id] is not None:
                if (user_states[user_id]["translation"] == "russian_korean"):
                    if user_id in user_states and user_states[user_id]["state"] == WAITING_FOR_TRANSLATION:
                        user_translation = call.data
                        current_index = user_states[user_id]["current_word_index"]
                        correct_translation = user_states[user_id]["shuffled_koreanList"][current_index]

                        if user_translation.strip().lower() == correct_translation.strip().lower():
                            bot.send_message(user_id, "Правильно! ✅")
                            user_states[user_id]["score"] += 1
                        else:
                            bot.send_message(user_id, f"Неправильно! ❌. Правильный перевод: <b>{correct_translation}</b>", parse_mode='html')

                        if current_index + 1 < len(user_states[user_id]["shuffled_russianList"]):
                            user_states[user_id]["current_word_index"] += 1
                            send_question_russian_korean(user_id)
                        else:
                            total_questions = len(user_states[user_id]["shuffled_russianList"])
                            score = user_states[user_id]["score"]
                            percentage = (score / total_questions) * 100

                            bot.send_message(user_id, f"Вы закончили тест! Ваш результат: <b>{score}</b> из <b>{len(user_states[user_id]['shuffled_russianList'])}</b>", reply_markup=create_main_menu(), parse_mode='html')
                            bot.send_message(user_id, "В процентном значении: " + str(percentage) + " %")
                            # Отправка стикеров в зависимости от результата
                            if percentage <= 20:  # 0% - 20% BAD
                                sticker = open('res/kpopBad.webp', 'rb')
                                bot.send_sticker(user_id, sticker)
                                bot.send_message(user_id, "Честно говоря - плохо. Нужно больше стараться.")
                            elif percentage <= 40:  # 21% - 40% BELOW AVERAGE
                                sticker = open('res/kpopNotBad.webp', 'rb')
                                bot.send_sticker(user_id, sticker)
                                bot.send_message(user_id, "Неплохо. Но надо быть усерднее.") 
                            elif percentage <= 60:  # 41% - 60% GOOD
                                sticker = open('res/kpopGood.webp', 'rb')
                                bot.send_sticker(user_id, sticker) 
                                bot.send_message(user_id, "Хороший результат!")
                            elif percentage <= 80:  # 61% - 80% VERY GOOD
                                sticker = open('res/kpopVeryGood.webp', 'rb')
                                bot.send_sticker(user_id, sticker)
                                bot.send_message(user_id, "Очень хорошо. Так держать!")
                            else:  # 81% - 100% EXCELLENT
                                sticker = open('res/kpopExcellent.webp', 'rb')
                                bot.send_sticker(user_id, sticker)
                                bot.send_message(user_id, "Супер! Отлично, молодец!")

                            if user_states:
                                if user_states[user_id] is not None:
                                    del user_states[user_id]
                else:
                    bot.send_message(user_id, "Возникла непредвиденная ошибка. Извините, но Вам нужно будет повторить весь процесс заново 🙂\nПожалуйста, нажмите на кнопку " + "<b>'" + btn_restart_russian_txt + "'</b>.", reply_markup=create_restart_button(), parse_mode='html')
                    if user_states:
                        if user_states[user_id] is not None:
                            del user_states[user_id]
        else:
            bot.send_message(user_id, "Возникла непредвиденная ошибка. Возможно потеря соединения. Извините, но Вам нужно будет повторить весь процесс заново 🙂\nПожалуйста, нажмите на кнопку " + "<b>'" + btn_restart_russian_txt + "'</b>.", reply_markup=create_restart_button(), parse_mode='html')
            if user_states:
                if user_states[user_id] is not None:
                    del user_states[user_id]
    except requests.exceptions.Timeout:
        bot.send_message(user_id, "Время ввода истекло. Пожалуйста, повторите весь процесс заново 🙂.", reply_markup=create_main_menu())
        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]
    except:
        bot.send_message(user_id, "Возникла непредвиденная ошибка. Извините, но Вам нужно будет повторить весь процесс заново 🙂\nПожалуйста, нажмите на кнопку " + "<b>'" + btn_restart_russian_txt + "'</b>.", reply_markup=create_restart_button(), parse_mode='html')
        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]

##########################################################################################
# Информация о боте
@bot.message_handler(func=lambda message: message.text.lower() == btn_info_txt.lower())
def info(message):
    try:
        user_id = message.chat.id
        
        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]

        sticker = open('res/kpopCreator.webp', 'rb')
        bot.send_sticker(message.chat.id, sticker)

        bot.send_message(user_id, "🇰🇷 Я Ваш <b>Корейский Ассистент</b> ☺️.\n<b>{0.first_name}</b>, на данный момент я могу помочь Вам только заучивать корейские слова. Я буду задавать вопрос, а Вы просто на него отвечайте. Для удобства я уже буду давать варианты ответов. Есть несколько вариантов тестирования:\n<b>1. {1}</b> - означает, что вопрос будет на корейском языке, а ответы на русском языке.\n<b>2. {2}</b> - вопрос на русском языке, а ответы на корейском языке.\n3. <b>{3}</b> - здесь же будут выдаваться случайным образом <b>10</b> слов из моего словаря, а вариант тестирования тоже будет случаным.\n<b>У меня есть еще другие кнопки: 🔠\n<b>1</b>. {4}</b> - эта кнопка поможет Вам добавить новое слово.\n<b><b>2</b>. {5}</b> - эта кнопка, поможет Вам найти интересующее Вас слово или выражение, и сделать следующие дествия: <b>{6}</b>, <b>{7}</b>, <b>{8}</b> и <b>{9}</b>.\n<b><b>3</b>. {10}</b> - нажав на эту кнопку, я покажу Вам свой <b>словарь</b>, и отсортирую его так, как Вы захотите.\nЕсть <b>3</b> вида сортировки:\n<b>1</b>. <b>{11}</b>\n<b>2</b>. <b>{12}</b>\n<b>3</b>. <b>{13}</b>\nТакже для более <b><i>эффективного</i></b> использования моих возможностей Вам следует обратить внимание на <b><u>пару</u> <u>правил</u></b>, которые описаны ниже. ⬇️".format(message.from_user, btn_kor_rus_test_txt, btn_rus_kor_test_txt, btn_random_ten_words_txt, btn_add_word_txt, btn_find_word_txt, btn_edit_word_txt, btn_edit_translation_txt, btn_edit_category_txt, btn_delete_full_word_translation_category_txt, btn_all_words_txt, btn_all_words_korean_sort_txt, btn_all_words_russian_sort_txt, btn_all_words_category_sort_txt), parse_mode='html')
        
        bot.send_message(user_id, """<b><u>Правила эффективного использования</u></b>:\n<b>1</b>. Когда Вы добавляете или изменяете <b>слово/выражение</b>, <b>перевод</b> и <b>категорию</b>, то не добавляйте <b>'/'</b> в самом начале слова. Символ <b>'/'</b> используется для моих команд 🤖.\n<b>2</b>. Если вдруг кнопки перестанут работать должным образом, и если я не смогу обрабатывать Ваши слова или команды, то, пожалуйста, <b>перезагрузите</b> меня. 😮‍💨 Вы можете сделать это по нажатию кнопки <b>{3}</b> или написать мне <b>{4}</b>.\n<b>3</b>. Если Вы вдруг найдете какую-нибудь ошибку во мне или захотите поделиться идеями по улучшению меня, то, пожалуйста, сообщите об этом моему разработчику @SourceCode20000530.""".format(message.from_user.first_name, btn_all_words_txt, btn_find_word_txt, btn_restart_russian_txt, btn_restart_english_txt.lower()), parse_mode='html')
    except requests.exceptions.Timeout:
        bot.send_message(user_id, "Время ввода истекло. Пожалуйста, повторите весь процесс заново 🙂.", reply_markup=create_main_menu())
        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]
    except:
        bot.send_message(user_id, "Возникла непредвиденная ошибка. Извините, но Вам нужно будет повторить весь процесс заново 🙂\nПожалуйста, нажмите на кнопку " + "<b>'" + btn_restart_russian_txt + "'</b>.", reply_markup=create_restart_button(), parse_mode='html')
        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]

##########################################################################################
# Здесь будут реализованы все функции, которые будут учавствовать в выводе все слов с переводом и категориями
# Главная функция будет предлагать вывести все слова сортировав их в алфавитном порядке:
# 1. По корейскому языку
# 2. По русскому языку
# 3. По категориям
@bot.message_handler(func=lambda message: message.text.lower() == btn_all_words_txt.lower())
def print_all_words(message):
    try:
        user_id = message.chat.id

        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]

        user_states[user_id] = {"state" : "PRINT_ALL_WORDS"}

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        btn_all_words_korean_sort = types.KeyboardButton(btn_all_words_korean_sort_txt)
        btn_all_words_russian_sort = types.KeyboardButton(btn_all_words_russian_sort_txt)
        btn_all_words_category_sort = types.KeyboardButton(btn_all_words_category_sort_txt)
        btn_cancel = types.KeyboardButton(btn_cancel_txt)

        markup.add(btn_all_words_korean_sort, btn_all_words_russian_sort, btn_all_words_category_sort, btn_cancel)
        
        bot.send_message(user_id, "Как Вы хотите, чтобы я отсортировал словарь?", reply_markup=markup)
    
    except requests.exceptions.Timeout:
        bot.send_message(user_id, "Время ввода истекло. Пожалуйста, повторите весь процесс заново 🙂.", reply_markup=create_main_menu())
        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]
    except:
        bot.send_message(user_id, "Возникла непредвиденная ошибка. Извините, но Вам нужно будет повторить весь процесс заново 🙂\nПожалуйста, нажмите на кнопку " + "<b>'" + btn_restart_russian_txt + "'</b>.", reply_markup=create_restart_button(), parse_mode='html')
        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]
    

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get("state") == PRINT_ALL_WORDS)
def print_all_words_choice(message):
    try:
        user_id = message.chat.id
        if user_states:
            if user_states[user_id] is not None:
                user_states[user_id]["choice"] = message.text
            
                if user_states[user_id]["choice"] == btn_all_words_korean_sort_txt:
                    bot.send_message(user_id, "Хорошо. Я выдаю словарь, отсортированный по корейскому алфавиту:")
                    sorted_korean_words = sorted(koreanList, key=lambda x: (x.lower() if isinstance(x, str) else x))
                    sorted_russian_words = []
                    sorted_category_words = []

                    conn = sqlite3.connect('voc.db')
                    # Теперь заранее перевод для только что заполненного списка
                    for i in range(len(sorted_korean_words)):
                        cursor = conn.cursor()
                        cursor.execute("SELECT russian FROM words WHERE korean = ?", (sorted_korean_words[i],))
                        result = cursor.fetchone()
                        sorted_russian_words.append(result[0])
                    conn.close()

                    # Получаем категории
                    conn = sqlite3.connect('voc.db')
                    cursor = conn.cursor()
                    for i in range(len(sorted_korean_words)):
                        cursor.execute("SELECT category FROM words WHERE korean = ?", (sorted_korean_words[i],))
                        result = cursor.fetchone()
                        sorted_category_words.append(result[0])
                    conn.close()

                    sorted_words_text = "" 
                    for i in range(len(sorted_korean_words)):
                        sorted_words_text = sorted_words_text + str(i+1) + ". " + "<b>" + sorted_korean_words[i] + "</b>" + " - " + "<b>" + sorted_russian_words[i] + "</b>" + "   {📚Категория[" + "<b>" + sorted_category_words[i] + "</b>" + "]}" + "\n"

                elif user_states[user_id]["choice"] == btn_all_words_russian_sort_txt:
                    bot.send_message(user_id, "Хорошо. Я выдаю словарь, отсортированный по русскому алфавиту:")

                    sorted_russian_words = sorted(russianList)
                    sorted_korean_words = [] 
                    sorted_category_words = []

                    conn = sqlite3.connect('voc.db')
                    cursor = conn.cursor()
                
                    # Получаем корейские слова
                    for i in range(len(sorted_russian_words)):
                        cursor.execute("SELECT korean FROM words WHERE russian = ?", (sorted_russian_words[i],))
                        result = cursor.fetchone()
                        sorted_korean_words.append(result[0])
                    conn.close()
                    
                    # Получаем категории
                    conn = sqlite3.connect('voc.db')
                    cursor = conn.cursor()
                    for i in range(len(sorted_korean_words)):
                        cursor.execute("SELECT category FROM words WHERE russian = ?", (sorted_russian_words[i],))
                        result = cursor.fetchone()
                        sorted_category_words.append(result[0])
                    conn.close()

                    sorted_words_text = ""
                    for i in range(len(sorted_russian_words)):
                        sorted_words_text = sorted_words_text + str(i+1) + ". " + "<b>" + sorted_russian_words[i] + "</b>" + " - " + "<b>" + sorted_korean_words[i] + "</b>" + "   {📚Категория[" + "<b>" + sorted_category_words[i] + "</b>" + "]}" + "\n"

                elif user_states[user_id]["choice"] == btn_all_words_category_sort_txt:
                    bot.send_message(user_id, "Хорошо. Я выдаю словарь, отсортированный по категориям:")

                    sorted_russian_words = []
                    sorted_korean_words = []
                    sorted_category_words = sorted(set(categoryList))  # Убираем дубли категорий
                    sorted_words_text = ""

                    conn = sqlite3.connect('voc.db')
                    cursor = conn.cursor()

                    # Проходим по каждой уникальной категории
                    for category in sorted_category_words:
                        # Получаем все корейские и русские слова для текущей категории
                        cursor.execute("SELECT korean, russian FROM words WHERE category = ?", (category,))
                        results = cursor.fetchall()
                
                        # Если есть результаты, добавляем их в списки и текст
                        if results:
                            sorted_words_text += f"📚Категория [{category}]:\n"
                            for i, (korean_word, russian_word) in enumerate(results, 1):
                                sorted_korean_words.append(korean_word)
                                sorted_russian_words.append(russian_word)
                                sorted_words_text += f"{i}. {korean_word} - {russian_word}\n"
                            sorted_words_text += "\n"  # Отступ после категории
                    conn.close()

                    sorted_words_text += "Общее количество слов: " + "<b>" + str(len(sorted_korean_words)) + "</b>"
                else:
                    pass

                bot.send_message(user_id, sorted_words_text, reply_markup=create_main_menu(), parse_mode='html')
                if user_states:
                    if user_states[user_id] is not None:
                        del user_states[user_id]
        else:
            bot.send_message(user_id, "Возникла непредвиденная ошибка. Возможно потеря соединения. Извините, но Вам нужно будет повторить весь процесс заново 🙂\nПожалуйста, нажмите на кнопку " + "<b>'" + btn_restart_russian_txt + "'</b>.", reply_markup=create_restart_button(), parse_mode='html')
            if user_states:
                if user_states[user_id] is not None:
                    del user_states[user_id]
    except requests.exceptions.Timeout:
        bot.send_message(user_id, "Время ввода истекло. Пожалуйста, повторите весь процесс заново 🙂.", reply_markup=create_main_menu())
        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]
    except:
        bot.send_message(user_id, "Возникла непредвиденная ошибка. Извините, но Вам нужно будет повторить весь процесс заново 🙂\nПожалуйста, нажмите на кнопку " + "<b>'" + btn_restart_russian_txt + "'</b>.", reply_markup=create_restart_button(), parse_mode='html')
        if user_states:
            if user_states[user_id] is not None:
                del user_states[user_id]
    finally:
        conn.close()

##########################################################################################
# Реализация функций для отправки уведомлений в определенное время
# [----------------------------------------------]
# Уведомления
notify_sun = '⛅️'
notify_moon = '🌗'
notification_point = ''
morning_notification = ""
evening_notification = ""

notification_part_greeting = ""
notification_part_message = ""

def generate_morning_notification():
    conn = sqlite3.connect('voc.db')
    cursor = conn.cursor()
   
    for chat_id in data_users_id:
        cursor.execute("SELECT first_name FROM users WHERE id = ?", (chat_id,))
        result = cursor.fetchone()
        name = result[0]
        notification_part_greeting = random.choice(morning_greetings)
        notification_part_message = random.choice(morning_message)

        morning_notification = notify_sun + " " + "Доброе утро! Самое время проверить свои знания!"

        bot.send_message(chat_id, morning_notification, parse_mode='html')
    conn.close()

def generate_evening_notification():
    conn = sqlite3.connect('voc.db')
    cursor = conn.cursor()
   
    for chat_id in data_users_id:
        cursor.execute("SELECT first_name FROM users WHERE id = ?", (chat_id,))
        result = cursor.fetchone()
        name = result[0]
        notification_part_greeting = random.choice(evening_greetings)
        notification_part_message = random.choice(evening_message)

        evening_notification = notify_moon + " " + "Добрый вечер! Самое время проверить свои знания!"

        bot.send_message(chat_id, evening_notification, parse_mode='html')
    conn.close()

def schedule_daily_morning_messages(hour, minute):
    while True:
        now = datetime.now()
        target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        if now > target_time:
            target_time += timedelta(days=1)
        
        time_to_wait = (target_time - now).total_seconds()
        time.sleep(time_to_wait)

        generate_morning_notification()

def schedule_daily_evening_messages(hour, minute):
    while True:
        now = datetime.now()
        target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        if now > target_time:
            target_time += timedelta(days=1)
        
        time_to_wait = (target_time - now).total_seconds()
        time.sleep(time_to_wait)
        
        generate_evening_notification()

# Запускаем планировщик в фоновом режиме
threading.Thread(target=schedule_daily_morning_messages, args=(7, 00), daemon=True).start()
threading.Thread(target=schedule_daily_evening_messages, args=(21, 30), daemon=True).start()

# RUN
if __name__ == '__main__':
    bot.polling(none_stop=True)