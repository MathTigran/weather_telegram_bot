import time
from aiogram import Bot, Dispatcher, executor, types
from pytube import YouTube
from googleapiclient.discovery import build
import json
from time import sleep
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import datetime
import requests

download_folder = ''
token = ''
api = ''
weather_key = ''

bot = Bot(token=token)
dp = Dispatcher(bot)

def get_service():
    service = build('youtube', 'v3', developerKey=api)
    return service

def get_video_info(video_id):
    r = get_service().videos().list(id=video_id, part='snippet, statistics').execute()
    return r

@dp.message_handler(commands='start')
async def first_of_all(message):
    await bot.send_message(message.chat.id, f'Привет {message["from"]["first_name"]}, я YouTube-бот,\nпомогу тебе скачать видео из ютуба и вывести статистику ')
    await bot.send_sticker(message.chat.id, sticker='CAACAgIAAxkBAAEGwTVjk7ZWMCxnbgZGH5Mff-Fiu1Vz3QACeQUAAjbsGwWk_F_hIHgbZisE')
    await bot.send_message(message.chat.id, 'отправь ссылку на видео: \n'
                                            'или напиши город прогноз погоды которого ты хочешь увидеть (Москва, Лондон, Ереван) ')


@dp.message_handler(content_types='text')
async def get_message_and_send_info(message: types.Message):
    if 'https://www.youtube.com/' in message.text or 'https://youtu.be/' in message.text:
        link = message.text
        yt = YouTube(link)
        await bot.send_message(message.chat.id, f'Скачиваю видео: *{yt.title}* \n'
                                            f'Автор : [{yt.author}]({yt.channel_id}', parse_mode='Markdown')
        await download_youtube_video(link, message, bot)
    else:
        await bot.send_message(message.chat.id, f'Кажется ты просишь погоду, тогда получай погоду')
        code_to_smile = {
            "Clear": "Ясно \U00002600",
            "Clouds": "Облачно \U00002601",
            "Rain": "Дождь \U00002614",
            "Drizzle": "Дождь \U00002614",
            "Thunderstorm": "Гроза \U000026A1",
            "Snow": "Снег \U0001F328",
            "Mist": "Туман \U0001F32B"
        }

        try:
            r = requests.get(
                f"http://api.openweathermap.org/data/2.5/weather?q={message.text}&appid={weather_key}&units=metric"
            )
            data = r.json()

            city = data["name"]
            cur_weather = data["main"]["temp"]

            weather_description = data["weather"][0]["main"]
            if weather_description in code_to_smile:
                wd = code_to_smile[weather_description]
            else:
                wd = "Посмотри в окно, не пойму что там за погода!"

            humidity = data["main"]["humidity"]
            pressure = data["main"]["pressure"]
            wind = data["wind"]["speed"]
            sunrise_timestamp = datetime.datetime.fromtimestamp(data["sys"]["sunrise"])
            sunset_timestamp = datetime.datetime.fromtimestamp(data["sys"]["sunset"])
            length_of_the_day = datetime.datetime.fromtimestamp(
                data["sys"]["sunset"]) - datetime.datetime.fromtimestamp(
                data["sys"]["sunrise"])

            await message.reply(f"***{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}***\n"
                                f"Погода в городе: {city}\nТемпература: {cur_weather}C° {wd}\n"
                                f"Влажность: {humidity}%\nДавление: {pressure} мм.рт.ст\nВетер: {wind} м/с\n"
                                f"Восход солнца: {sunrise_timestamp}\nЗакат солнца: {sunset_timestamp}\nПродолжительность дня: {length_of_the_day}\n"
                                f"***Хорошего дня!***"
                                )
        except Exception as e:
            print(e)
        await bot.send_sticker(message.chat.id, sticker='CAACAgIAAxkBAAEGzl1jl7qCjejyxkchtpbxsyGrhm6nmAACjQMAAjbsGwU4uEquYGopGywE')

async def download_youtube_video(link, message, bot):
    yt = YouTube(link)
    stream = yt.streams.filter(progressive=True, file_extension='mp4')
    stream.get_highest_resolution().download(f'{download_folder}', f'{message.chat.id}_{yt.title}')
    with open(f'{download_folder}{message.chat.id}_{yt.title}', 'rb') as video:
        if 'youtu.be' in link:
            print(link.split('.be/'))
            publication_date = get_video_info(link.split('.be/')[1])['items'][0]['snippet']['publishedAt']
            print(publication_date)
            view_count = get_video_info(link.split('.be/')[1])['items'][0]['statistics']['viewCount']
            like_count = get_video_info(link.split('.be/')[1])['items'][0]['statistics']['likeCount']
            comment_count = get_video_info(link.split('.be/')[1])['items'][0]['statistics']['commentCount']
        elif 'www.youtube.com' in link:
            print(link.split('='))
            if '&' in link.split('=')[1]:
                link2 = link.split('=')[1].split('&')[0]
                publication_date = get_video_info(link2)['items'][0]['snippet']['publishedAt']
                print(get_video_info(link2)['items'][0]['statistics'])
                view_count = get_video_info(link2)['items'][0]['statistics']['viewCount']
                like_count = get_video_info(link2)['items'][0]['statistics']['likeCount']
                comment_count = get_video_info(link2)['items'][0]['statistics']['commentCount']
            else:
                publication_date = get_video_info(link.split('=')[1])['items'][0]['snippet']['publishedAt']
                print(get_video_info(link.split('=')[1])['items'][0]['statistics'])
                view_count = get_video_info(link.split('=')[1])['items'][0]['statistics']['viewCount']
                like_count = get_video_info(link.split('=')[1])['items'][0]['statistics']['likeCount']
                comment_count = get_video_info(link.split('=')[1])['items'][0]['statistics']['commentCount']
        menu = InlineKeyboardMarkup(row_width=2)
        viewers = InlineKeyboardButton(text=f'Просмотры: {view_count}', callback_data='viewers')
        comments = InlineKeyboardButton(text=f'Комментарии: {comment_count}', callback_data='comments')
        likes = InlineKeyboardButton(text=f'Лайки: {like_count}', callback_data='likes')
        menu.insert(likes)
        menu.insert(comments)
        menu.insert(viewers)
        try:
            await bot.send_video(message.chat.id, video, caption=f'Дата Выхода:*{publication_date}*', parse_mode='Markdown', reply_markup=menu)
        except Exception as e:
            upload_file = open(f'{download_folder}{message.chat.id}_{yt.title}', 'rb')
            await bot.send_message(message.chat.id, 'К сожалению Видео слишком тяжелое, телеграм такой вес не поддерживает :)), '
                                                    f'\n но я любезно возвращаю ссылку: {link}')
            await bot.send_message(message.chat.id, f'Вот статистика: \n'
                                                    f'Просмотры: {view_count} \n'
                                                    f'Комментарии: {comment_count} \n'
                                                    f'Лайки: {like_count}')


@dp.message_handler(content_types=['location'])
async def send_weather_to_location(message: types.Message):
    latitude = message["location"]["latitude"]
    longitude = message["location"]["longitude"]
    lang = 'ru'
    code_to_smile = {
        "Clear": "Ясно \U00002600",
        "Clouds": "Облачно \U00002601",
        "Rain": "Дождь \U00002614",
        "Drizzle": "Дождь \U00002614",
        "Thunderstorm": "Гроза \U000026A1",
        "Snow": "Снег \U0001F328",
        "Mist": "Туман \U0001F32B"
    }

    try:
        r = requests.get(
            f"https://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={weather_key}&units=metric"
        )
        data = r.json()
        print(data)

        city = data["name"]
        cur_weather = data["main"]["temp"]

        weather_description = data["weather"][0]["main"]
        if weather_description in code_to_smile:
            wd = code_to_smile[weather_description]
        else:
            wd = "Посмотри в окно, не пойму что там за погода!"

        humidity = data["main"]["humidity"]
        pressure = data["main"]["pressure"]
        wind = data["wind"]["speed"]
        sunrise_timestamp = datetime.datetime.fromtimestamp(data["sys"]["sunrise"])
        sunset_timestamp = datetime.datetime.fromtimestamp(data["sys"]["sunset"])
        length_of_the_day = datetime.datetime.fromtimestamp(
            data["sys"]["sunset"]) - datetime.datetime.fromtimestamp(
            data["sys"]["sunrise"])

        await message.reply(f"***{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}***\n"
                            f"Погода в районе: {city}\nТемпература: {cur_weather}C° {wd}\n"
                            f"Влажность: {humidity}%\nДавление: {pressure} мм.рт.ст\nВетер: {wind} м/с\n"
                            f"Восход солнца: {sunrise_timestamp}\nЗакат солнца: {sunset_timestamp}\nПродолжительность дня: {length_of_the_day}\n"
                            f"***Хорошего дня!***"
                            )
    except Exception as e:
        print(e)



if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
