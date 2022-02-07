import time
import schedule
import datetime
from datetime import date
import requests
import telebot
from telebot import types
import threading
import sqlite3
from sqlite3 import Error
from my_token import token, ow_key
from pyopenweather.weather import Weather
from pyowm.owm import OWM
from pyowm.utils.config import get_default_config
from func import wind_deg_to_str    # импортирую функцию, которая преобразовывает направление ветра из градусов
                                    # в буквенное значение

config_dict = get_default_config()
config_dict['language'] = 'ru'
owm = OWM(ow_key, config_dict)
mgr = owm.weather_manager()

connection = None
try:
    connection = sqlite3.connect('base.db', check_same_thread=False)
    print("Connection to SQLite DB successful")
except Error as e:
    print(f"The error '{e}' occurred")

cur = connection.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS default_city(
            userid INTEGER, city TEXT, id INTEGER);
            """)
cur.execute("""CREATE TABLE IF NOT EXISTS reminder
            (userid INTEGER, city TEXT, time TEXT);""")
connection.commit()

bot = telebot.TeleBot(token)


@bot.message_handler(commands=["help", "info"])
def help_command(message):
    bot.send_message(message.chat.id,
                     f' Привет!\n/start для начала '
                     f'\n/default для установки города по умолчанию '
                     f'\n/tomorrow для прогноза на завтра'
                     f'\n/weekend  для прогноза погоды на выходные'
                     f'\n/everyday для установки ежедневных прогнозов'
                     f'\n если хотите, просто узнать погоду в месте нахождения, пришлите локацию')

# Установка города по умолчанию


@bot.message_handler(commands=["default"])
def default(message):
    # sql_update_query = """DELETE from default_city where userid = ?"""
    # cur.execute(sql_update_query, (message.from_user.id,))
    # connection.commit()

    bot.send_message(message.from_user.id,
                     text="Введи город")
    bot.register_next_step_handler(message, set_default)


def set_default(message):

    try:
        observation = mgr.weather_at_place(message.text)
        def_city_name = observation.location.name
        def_city_id = observation.location.id
        #print(def_city_name, def_city_id)

        bot.send_message(message.from_user.id,
                         text=f'{def_city_name} установлен как город по умолчанию')
        #print(message.from_user.id)
    except Exception:
        print('неправильно указан город')
        bot.send_message(message.from_user.id,
                         text="Нет такого города. Пиши правильно!")
        pass

    tupl_from_base = (message.from_user.id, def_city_name, def_city_id)

    # Удаляю из базы города по умолчанию для этого юзера , если они были.
    sql_update_query = """DELETE from default_city where userid = ?"""
    cur.execute(sql_update_query, (message.from_user.id,))
    connection.commit()
    print("Запись успешно удалена")

    # Добавляю в базу город по умолчанию для юзера
    cur.execute("INSERT INTO default_city VALUES(?, ?, ?)", tupl_from_base)
    connection.commit()

    # Просто проверка
    cur.execute("SELECT * FROM default_city;")
    all_results = cur.fetchall()
    print(all_results)

# просто, чтобы вставить кнопки


@bot.message_handler(commands=["start"])
def start(message):
    start_menu_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True,
                                                    one_time_keyboard=True)
    start_menu_keyboard.row('Здесь и сейчас!', 'На весь день')

    bot.send_message(message.from_user.id,
                     text="Какую погоду ты хочешь узнать}",
                     reply_markup=start_menu_keyboard)

    bot.register_next_step_handler(message, start_question_handler)


def start_question_handler(message):
    if message.text == 'Здесь и сейчас!':

        bot.send_message(message.from_user.id,
                         'Пожалуйста пришли свою геопозицию')

    elif message.text == 'На весь день':
        # Делаю проверку на наличие у пользователя города по умолчанию
        sql_find_query = """SELECT id from default_city where userid = ?"""
        result = cur.execute(sql_find_query, (message.from_user.id,))
        row = result.fetchone()

        if row is not None:
            try:
                res = requests.get("http://api.openweathermap.org/data/2.5/forecast",
                                   params={'id': row[0], 'units': 'metric', 'lang': 'ru', 'APPID': ow_key})
                data = res.json()
                print(data)

                for i in data['list']:
                    if str(i['dt_txt'][0:10]) == str(date.today()):
                        print(i['dt_txt'], '{0:+3.0f}'.format(i['main']['temp']), i['weather'][0]['description'])
                        bot.send_message(message.chat.id,
                                         f" В {(i['dt_txt'][11] + i['dt_txt'][12])} температура будет -" \
                                         f" {(i['main']['temp'])},{i['weather'][0]['description']}"
                                         )
                    else:
                        pass

            except Exception as e:
                print("Exception (forecast):", e)
                pass

        else:
            bot.send_message(message.from_user.id,
                             'Введите название города')
            bot.register_next_step_handler(message, city_name)


def city_name(message):
    try:
        observation = mgr.weather_at_place(message.text)
        row = observation.location.id
        res = requests.get("http://api.openweathermap.org/data/2.5/forecast",
                       params={'id': row, 'units': 'metric', 'lang': 'ru', 'APPID': ow_key})
        data = res.json()

        for i in data['list']:
            if str(i['dt_txt'][0:10]) == str(date.today()):
                print(f" В {(i['dt_txt'][11] + i['dt_txt'][12])} температура будет -" \
                      f" {(i['main']['temp'])},{i['weather'][0]['description']}")

                bot.send_message(message.chat.id,
                                 f" В {(i['dt_txt'][11] + i['dt_txt'][12])} температура  -" \
                                 f" {(i['main']['temp'])},{i['weather'][0]['description']}"
                                         )
            else:
                pass
    except Exception as e:
        print("Exception (forecast):", e)
        bot.send_message(message.chat.id, 'Не могу найти этот город')
        pass


@bot.message_handler(commands=["tomorrow"])
def tomorrow(message):
    sql_find_query = """SELECT id from default_city where userid = ?"""
    result = cur.execute(sql_find_query, (message.from_user.id,))
    row = result.fetchone()
    print(date.today())
    print(date.today() + datetime.timedelta(1))
    zavtra = date.today() + datetime.timedelta(1)
    if row is not None:
        try:
            res = requests.get("http://api.openweathermap.org/data/2.5/forecast",
                               params={'id': row[0], 'units': 'metric', 'lang': 'ru', 'APPID': ow_key})
            data = res.json()
            print(data)
            for i in data['list']:

                if str(i['dt_txt'][0:10]) == str(zavtra):
                    print(i['dt_txt'], '{0:+3.0f}'.format(i['main']['temp']), i['weather'][0]['description'])

                    bot.send_message(message.chat.id,
                                     f" Завтра в {i['dt_txt'][11:13]}  температура будет -" \
                                     f" {(i['main']['temp'])},{i['weather'][0]['description']}"
                                     )
                else:
                    pass
        except Exception as e:
            print("Exception (forecast):", e)
            pass

    else:
        bot.send_message(message.from_user.id,
                         'Введите название города')
        bot.register_next_step_handler(message, city_name_tomorrow)


def city_name_tomorrow(message):
    try:
        zavtra = date.today() + datetime.timedelta(1)
        observation = mgr.weather_at_place(message.text)
        row = observation.location.id
        res = requests.get("http://api.openweathermap.org/data/2.5/forecast",
                           params={'id': row, 'units': 'metric', 'lang': 'ru', 'APPID': ow_key})
        data = res.json()
        print(data)
        for i in data['list']:
            if str(i['dt_txt'][0:10]) == str(zavtra):
                print(f" Завтра в {i['dt_txt'][11:13]} температура будет -" \
                      f" {(i['main']['temp'])},{i['weather'][0]['description']}")

                bot.send_message(message.chat.id,
                                 f" В {(i['dt_txt'][11] + i['dt_txt'][12])} температура  -" \
                                 f" {(i['main']['temp'])},{i['weather'][0]['description']}"
                                 )
            else:
                pass
    except Exception as e:
        print("Exception (forecast):", e)
        bot.send_message(message.chat.id, 'Не могу найти этот город')
        pass


@bot.message_handler(commands=["weekend"])
def weekend(message):
    sql_find_query = """SELECT id from default_city where userid = ?"""
    result = cur.execute(sql_find_query, (message.from_user.id,))
    row = result.fetchone()

    if row is not None:
        try:
            res = requests.get("http://api.openweathermap.org/data/2.5/forecast",
                               params={'id': row[0], 'units': 'metric', 'lang': 'ru', 'APPID': ow_key})
            data = res.json()
            print(data)
            for i in data['list']:
                if datetime.datetime.strptime(str(i['dt_txt'][0:10]), '%Y-%m-%d').date().weekday() >= 5:
                    print(i['dt_txt'], '{0:+3.0f}'.format(i['main']['temp']), i['weather'][0]['description'])

                    bot.send_message(message.chat.id,
                                     f" {i['dt_txt'][8:10]} числа в {i['dt_txt'][11:13]} часов, температура будет -" \
                                     f" {(i['main']['temp'])},{i['weather'][0]['description']}"
                                     )
                else:
                    pass

        except Exception as e:
            print("Exception (forecast):", e)
            pass

    else:
        bot.send_message(message.from_user.id,
                         'Введите название города')
        bot.register_next_step_handler(message, city_name_for_week)


def city_name_for_week(message):
    try:
        observation = mgr.weather_at_place(message.text)
        row = observation.location.id
        res = requests.get("http://api.openweathermap.org/data/2.5/forecast",
                           params={'id': row, 'units': 'metric', 'lang': 'ru', 'APPID': ow_key})
        data = res.json()
        print(data)
        for i in data['list']:
            if datetime.datetime.strptime(str(i['dt_txt'][0:10]), '%Y-%m-%d').date().weekday() >= 5:
                print(f" В {(i['dt_txt'][11] + i['dt_txt'][12])} температура будет -" \
                      f" {(i['main']['temp'])},{i['weather'][0]['description']}")

                bot.send_message(message.chat.id,
                                 f" {i['dt_txt'][8:10]} числа в {i['dt_txt'][11:13]} часов температура  -" \
                                 f" {(i['main']['temp'])},{i['weather'][0]['description']}"
                                 )
            else:
                pass
    except Exception as e:
        print("Exception (forecast):", e)
        bot.send_message(message.chat.id, 'Не могу найти этот город')
        pass


# Приниаем локацию отвечаем погодой
@bot.message_handler(content_types=['location'])
def location (message):
    if message.location is not None:
        weather = Weather(lat=message.location.latitude, long=message.location.longitude, api_key=ow_key)
        local_temp = weather.temperature
        local_humidity = weather.humidity
        local_pressure = weather.pressure
        local_wind_speed = weather.wind_speed
        # icon_url гиперссылка на иконку погоды
        # icon_url = f'http://openweathermap.org/img/wn/{weather.raw_weather_dict["weather"][0]["icon"]}@2x.png'

        bot.send_message(message.chat.id,
                         f'Твоя широта - {message.location.latitude} , долгота - {message.location.longitude} '
                         f'Температура воздуха  {int(local_temp)} градусов, влажность {local_humidity} ,'
                         f'давление {local_pressure} мм ртутного столба, скорость ветра {local_wind_speed} м.с.,'
                         f'направление {wind_deg_to_str(weather.wind_direction)}')
        # print(weather.humidity)
        # print(weather.raw_weather_dict['weather'][0]['icon'])
        # print(message.location.longitude)
        # print(message.location)
        # print(message)

@bot.message_handler(commands=["everyday"])
def everyday(message):

    bot.send_message(message.from_user.id,
                     'Введите время напоминания,в формате hh:mm')

    bot.register_next_step_handler(message, send_city)
user_time = str

def send_city(message):
    global user_time
    user_time = message.text[0:2] + ':' + message.text[3:5]

    try:
        if int(user_time[0:2]) <= 23 and int(user_time[3:5]) <= 59 :
            bot.send_message(message.from_user.id,
                             'Введите название города')
            bot.register_next_step_handler(message, set_city_reminder)
        else:
            bot.send_message(message.from_user.id,
                             "Не правильно указано время. Пример 12:35")
            bot.register_next_step_handler(message, everyday)

    except Exception:
        print(Exception)
        bot.send_message(message.from_user.id,
                         "Не правильно указано время. Пример 12:35")
        bot.register_next_step_handler(message, help_command)
        pass


def set_city_reminder(message):

    try:
        observation = mgr.weather_at_place(message.text)
        def_city_name = observation.location.name
        def_city_id = observation.location.id
        print(def_city_name, def_city_id)

        bot.send_message(message.from_user.id,
                         text=f'Прогноз погоды в {def_city_name} будет приходить вам в {user_time} ')
        print(message.from_user.id)
        tupl_for_base = (message.from_user.id, def_city_name, user_time)

        # Удаляю из базы города по умолчанию для этого юзера , если они были.
        sql_update_query = """DELETE from reminder where userid = ?"""
        cur.execute(sql_update_query, (message.from_user.id,))
        connection.commit()
        print("Запись успешно удалена")

        # Добавляю в базу город и время рассылки погоды для юзера
        cur.execute("INSERT INTO reminder VALUES(?, ?, ?)", tupl_for_base)
        connection.commit()

        # Просто проверка
        cur.execute("SELECT * FROM reminder;")
        all_results = cur.fetchall()
        print(all_results)

    except Exception:
        print('Неправильно указан город')
        bot.send_message(message.from_user.id,
                         text="Нет такого города. Пиши правильно!")
        pass


def check_reminders():
    current_time = str(datetime.datetime.now().time())
    x = (current_time[0:5])  # дает время в формате чч:мм
    print(x)
    cur.execute("SELECT userid, city FROM reminder WHERE time = ?", (x,))
    result = cur.fetchone() #выгружает того чье время подошло

    if result != None:
        print(result)
        try:
            observation = mgr.weather_at_place(result[1])
            row = observation.location.id
            res = requests.get("http://api.openweathermap.org/data/2.5/forecast",
                               params={'id': row, 'units': 'metric', 'lang': 'ru', 'APPID': ow_key})
            data = res.json()
            print(data)
            for i in data['list']:

                if str(i['dt_txt'][0:10]) == str(date.today() + datetime.timedelta(1)):
                    print(i['dt_txt'], '{0:+3.0f}'.format(i['main']['temp']), i['weather'][0]['description'])

                    bot.send_message(result[0],
                                     f" Завтра в {i['dt_txt'][11:13]}  температура будет -" \
                                     f" {(i['main']['temp'])},{i['weather'][0]['description']}"
                                     )
                else:
                    pass
        except Exception as e:
            print("Exception (forecast):", e)
            pass


schedule.every(1).minutes.do(check_reminders)


def go():
    while 1:
        schedule.run_pending()
        time.sleep(1)

# Без запуска процесса перестает работать botpooling
t = threading.Thread(target=go, name="тест")
t.start()




if __name__ == '__main__':
    bot.polling(none_stop=False, interval=0)


