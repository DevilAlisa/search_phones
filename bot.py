import aiohttp
import requests
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import sqlite3
from datetime import datetime

API_TOKEN = '6132505078:AAGqpyUUxTUmA5K3O3HprrxyvUXH3uElYRg'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Создание базы данных и таблиц
conn = sqlite3.connect('users.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users
                (id INTEGER PRIMARY KEY, username TEXT, full_name TEXT, reg_date TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS searches
                (user_id INTEGER, search_date TEXT, phone_number TEXT)''')
conn.commit()

# Функция для добавления пользователя в базу данных
def add_user_to_db(user_id, username, full_name):
    reg_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("INSERT INTO users (id, username, full_name, reg_date) VALUES (?, ?, ?, ?)", (user_id, username, full_name, reg_date))
    conn.commit()

# Функция для добавления поиска в базу данных
def add_search_to_db(user_id, phone_number):
    search_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("INSERT INTO searches (user_id, search_date, phone_number) VALUES (?, ?, ?)", (user_id, search_date, phone_number))
    conn.commit()

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.full_name
    add_user_to_db(user_id, username, full_name)
    await message.reply("Привет! Я бот, который поможет тебе узнать информацию о телефонном номере. Просто отправь мне номер телефона в формате +79123456789")

@dp.message_handler(regexp=r'\+\d{11}')
async def handle_phone_number(message: types.Message):
    phone_number = message.text
    user_id = message.from_user.id
    add_search_to_db(user_id, phone_number)
    fstep_msg = await message.answer('📍 *Определяем страну, регион и оператора...*', parse_mode="Markdown")

    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://fincalculator.ru/api/tel/{phone_number}') as SBnum:
            datae = await SBnum.json()

    mnp = 'Неизвестно'
    whatsapp = InlineKeyboardButton('✅ Whatsapp', url=f'https://wa.me/{phone_number}')
    viber = InlineKeyboardButton('⚛️ Viber', url=f'https://viber.click/{phone_number}')
    telegram = InlineKeyboardButton('💎 Телеграм', url=f'https://t.me/{phone_number}')
    yandex = InlineKeyboardButton('㊗️ Яндекс', url=f'https://yandex.ru/search/?text={phone_number}')
    google = InlineKeyboardButton('🌐 Google', url=f'https://www.google.com/search?q={phone_number}')

    variations = InlineKeyboardMarkup().add(whatsapp, viber, telegram, yandex, google)

    await fstep_msg.delete()
    mnp_msg = await message.answer('📶 *Определяем перенос номера...*', parse_mode="Markdown")

    try:
        urlMNP = f"https://xn----dtbofgvdd5ah.xn--p1ai/php/mnp.php?nomer={phone_number}"
        mnpSiteSourc = requests.get(urlMNP).text.strip()
        mnp = mnpSiteSourc.replace('no', 'Не переносился')
    except Exception as e:
        print(e)

    try:
        country = datae["country"]
        region = datae["region"]
        operator = datae["operator"]
        if country != 'Россия':
            fstep = f'📲 *Номер телефона:* {phone_number}\n │ *Страна:* {country}\n │ *Перенос номера:* {mnp}\n └ *Оператор:* {region}'
            fstep_html = f'Страна {country}<br>Перенос номера: {mnp}<br>Оператор: {region}'
        else:
            fstep = f'📲 *Номер телефона:* {phone_number}\n │ *Страна:* {country}\n │ *Регион:* {region}\n │ *Перенос номера:* {mnp}\n └ *Оператор:* {operator}'
            fstep_html = f'Страна {country}<br>Регион: {region}<br>Перенос номера: {mnp}<br>Оператор: {operator}'
    except:
        country = 'Не опознано'
        region = 'Не опознано'
        operator = 'Не опознано'

    await mnp_msg.delete()
    await message.answer(fstep, reply_markup=variations,parse_mode="Markdown")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
