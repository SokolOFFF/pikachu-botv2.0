import random
import csv
import os
import config
import requests
import datetime
from django.core.management.base import BaseCommand
from bot.models import User, Theme, LinkToPicture, Schedule, CSV, FavLocation
import telebot
import SECRETS
from telebot import types
from tzlocal import get_localzone


class Command(BaseCommand):
    help = ''

    def handle(self, *args, **kwargs):
        bot = telebot.TeleBot(SECRETS.BOT_TOKEN)

        @bot.message_handler(content_types=['text'], commands=['start', 'help'])
        def handle_start_help(message):
            if message.text == "/start":
                bot.send_sticker(message.chat.id, sticker=SECRETS.start_sticker)
                bot.send_message(message.chat.id,
                                 text="hi, {0.first_name}!\ni'm <b>{1.first_name}</b>, and i'm <b>Picture Bot</b> (but i have some other features). \ni hope i can help you somehow. ❤️".format(
                                     message.from_user, bot.get_me()), parse_mode='HTML')
                user = User.objects.get_or_create(telegram_id=message.chat.id)

            if message.text == "/help":
                bot.send_sticker(message.chat.id, sticker=SECRETS.help_sticker)
                bot.send_message(message.chat.id, text="i can help you with a lot of things! type '/commands' to see all commands or use telegram interface to get it!\n\na little bit about some commands:\n/get_random_photo - choose the theme and i will send you a random picture on this theme!\n/game - choose the game and get luck!\n/weather - choose the type of using and send data (city name should be real and can be on any language)\n/schedule - use butons to navigate (for adding new schedule save schedule in CSV format)\n/manage_locations - manage your fav locations: send location and name to save it, edit or delete!\n/favourite_locations - choose one of your fav locations and i will remind you where is it!\n\nsome of commands can be aborted by typing /exit")

        @bot.message_handler(content_types=['text'], commands=['commands'])
        def handle_commands(message):
            commands = ['🥺 /help', '🔧 /login', '🖼 /add_photo', '🪩 /get_random_photo', '📂 /manage_themes', '🎮 /game', '⛅ /weather', '🗓 /schedule', '🗺 /manage_locations', '🏖 /favourite_locations' ]
            text = 'here are all commands: \n'
            for command in commands:
                text = text + f'{command}\n'
            bot.send_message(message.chat.id, text=text)

        @bot.message_handler(content_types=['text'], commands=['login'])
        def handle_login(message):
            user = User.objects.get(telegram_id=message.chat.id)
            if user.is_logged == 1:
                bot.send_message(message.chat.id, text="you don't need it! you already logged in!")

            else:
                msg = bot.send_message(message.chat.id, text="type the password!")
                bot.register_next_step_handler(msg, check_password)

        def check_password(message):
            try:
                if message.text == SECRETS.password:
                    bot.reply_to(message, text="you are ok! 👌")
                    user = User.objects.get(telegram_id=message.chat.id)
                    user.is_logged = True
                    user.save()
                elif message.text == '/exit':
                    bot.send_message(message.chat.id, text='aight, mate')
                    return
                else:
                    msg = bot.reply_to(message, text="one more time.. (or type /exit)")
                    bot.register_next_step_handler(msg, check_password)

            except Exception as e:
                bot.reply_to(message, text="sorry, gotcha problems :(")

        @bot.message_handler(content_types=['text'], commands=['add_photo'])
        def handle_add_photo(message):
            user = User.objects.get(telegram_id=message.chat.id)
            if user.is_logged == 0:
                bot.send_message(message.chat.id, text="sorry, you can't do this :(")

            else:
                markup = types.InlineKeyboardMarkup()
                themes = Theme.objects.all()
                for theme in themes:
                    markup.add(types.InlineKeyboardButton(text=theme.name, callback_data=theme.short_name + "_add_photo"))
                msg = bot.send_message(message.chat.id, text='aight! choose theme!', reply_markup=markup)

        def receive_photo(message, short_theme):
            try:
                if message.text:
                    if message.text == '/exit':
                        bot.send_message(message.chat.id, text="okay, mate!")
                        return
                file_info = bot.get_file(message.photo[len(message.photo) - 1].file_id)
                downloaded_file = bot.download_file(file_info.file_path)
                theme = Theme.objects.get(short_name=short_theme)
                src = 'images/' + short_theme + f"{theme.number_of_pictures}.png"
                theme.number_of_pictures = theme.number_of_pictures + 1
                theme.save()
                with open(src, 'wb') as new_file:
                    new_file.write(downloaded_file)
                new_link = LinkToPicture(theme=theme, link=src)
                new_link.save()
                bot.reply_to(message, text='okay, i added!')

            except Exception as e:
                bot.reply_to(message, "sorry, gotcha problems :(")
                print(e)

        @bot.message_handler(content_types=['text'], commands=['get_random_photo'])
        def handle_get_random_photo(message):
            try:
                markup = types.InlineKeyboardMarkup()
                themes = Theme.objects.all()
                for theme in themes:
                    markup.add(types.InlineKeyboardButton(text=theme.name, callback_data=theme.short_name + "_get_photo"))
                bot.send_message(message.chat.id, "okay, choose theme!", reply_markup=markup)

            except Exception as e:
                bot.reply_to(message, "sorry, gotcha problems :(")
                print(e)

        def send_random_photo(message, theme_short_name):
            try:
                theme = Theme.objects.get(short_name=theme_short_name)
                theme_id = theme.id
                links = LinkToPicture.objects.filter(theme_id=theme_id)
                rand_number = random.randint(0, theme.number_of_pictures-1)
                path = links[rand_number].link
                bot.send_photo(message.chat.id,  photo=open(path, 'rb'))

            except Exception as e:
                bot.reply_to(message, "sorry, gotcha problems :(")
                print(e)

        @bot.message_handler(content_types=['text'], commands=['game'])
        def handle_game(message):
            try:
                games = ['dice', 'bowling', 'dart', 'basketball', 'football', 'slot machine']
                callback = ['dice', 'bowling', 'dart', 'basketball', 'football', 'slot_machine']
                markup = types.InlineKeyboardMarkup()
                for i in range(len(games)):
                    markup.add(
                        types.InlineKeyboardButton(text=games[i], callback_data=callback[i]))
                bot.send_message(message.chat.id, 'chooooose game! 🎮', reply_markup=markup)

            except Exception as e:
                bot.reply_to(message, "sorry, gotcha problems :(")
                print(e)

        @bot.message_handler(content_types=['photo'])
        def handle_photo(message):
            try:
                bot.reply_to(message, "sorry, dont support photos :(")

            except Exception as e:
                bot.reply_to(message, "sorry, gotcha problems :(")
                print(e)

        @bot.message_handler(content_types=['text'], commands=['weather'])
        def handle_weather(message):
            try:
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton(text='by city name 🏙', callback_data='get_weather_city'))
                markup.add(types.InlineKeyboardButton(text='with map 🗺', callback_data='get_weather_map'))
                bot.send_message(message.chat.id, text='okay! but firstly choose type of info you send me!', reply_markup=markup)
            except Exception as e:
                bot.reply_to(message, "sorry, gotcha problems :(")
                print(e)

        def get_weather(message, type):
            try:
                msg_template = '{weather_emoji} today in {city}: {weather_type},\n\n🌡  temperature: {temp} ℃ (feels like {feels_like} ℃),\n🌡  max. temperature: {max_temp} ℃,\n🌡  min. temperature: {min_temp} ℃,\n\n🗜  pressure: {pres} hPa,\n🛁  humidity: {hum}%,\n🌬  wind: {wind} m/s,\n\n🌝  sunrise at: {sunrise},\n🌚  sunset at: {sunset}'
                data = ''
                if type == 'city':
                    city = message.text
                    req = requests.get(f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={SECRETS.OPEN_WEATHER_TOKEN}&units=metric')
                    data = req.json()

                if type == 'map':
                    if message.text:
                        if message.text == '/exit':
                            bot.send_message(message.chat.id, text='ok, man!')
                            return
                    longitude = message.location.longitude
                    latitude = message.location.latitude
                    req = requests.get(f'https://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={SECRETS.OPEN_WEATHER_TOKEN}&units=metric')
                    data = req.json()

                weather_type = data['weather'][0]['main'].lower()
                temperature = data['main']['temp']
                feels_like = data['main']['feels_like']
                pressure = data['main']['pressure']
                humidity = data['main']['humidity']
                temp_min = data['main']['temp_min']
                temp_max = data['main']['temp_max']
                wind_speed = data['wind']['speed']
                city = data['name'].lower()

                tz = get_localzone()
                delta = datetime.datetime.now(tz).utcoffset()
                hours = (datetime.datetime.fromtimestamp(data['sys']['sunrise'] + data['timezone']) - delta).hour
                if hours < 10:
                    hours = f'0{hours}'
                minutes = datetime.datetime.fromtimestamp(data['sys']['sunrise']).minute
                if minutes < 10:
                    minutes = f'0{minutes}'
                sunrise = f"{hours}:{minutes}"

                hours = (datetime.datetime.fromtimestamp(data['sys']['sunset'] + data['timezone']) - delta).hour
                if hours < 10:
                    hours = f'0{hours}'
                minutes = datetime.datetime.fromtimestamp(data['sys']['sunset']).minute
                if minutes < 10:
                    minutes = f'0{minutes}'
                sunset = f"{hours}:{minutes}"
                weather_emoji = ''

                if weather_type == 'thunderstorm':
                    weather_emoji = '🌩'
                if weather_type == 'rain':
                    weather_emoji = '🌧'
                if weather_type == 'drizzle':
                    weather_emoji = '🌨'
                if weather_type == 'snow':
                    weather_emoji = '❄'
                if weather_type == 'mist' or weather_type == 'smoke' or weather_type == 'haze' or weather_type == 'dust' or weather_type == 'fog' or weather_type == 'sand' or weather_type == 'ash' or weather_type == 'squall' or weather_type == 'tornado':
                    weather_emoji = '🌫'
                if weather_type == 'clear':
                    weather_emoji = '☀'
                if weather_type == 'clouds':
                    weather_emoji = '⛅'
                bot.send_message(message.chat.id, text=msg_template.format(city=city, weather_emoji=weather_emoji,
                                                                           weather_type=weather_type, temp=temperature,
                                                                           feels_like=feels_like, pres=pressure,
                                                                           hum=humidity, min_temp=temp_min,
                                                                           max_temp=temp_max, wind=wind_speed,
                                                                           sunrise=sunrise, sunset=sunset), reply_markup=types.ReplyKeyboardRemove())
            except Exception as e:
                bot.reply_to(message, "sorry, gotcha problems :(")
                print(e)

        @bot.message_handler(content_types=['text'], commands=['manage_themes'])
        def handle_manage_themes(message):
            user = User.objects.get(telegram_id=message.chat.id)
            if user.is_logged == 1:
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton(text='✅ add theme', callback_data='add_theme'))
                markup.add(types.InlineKeyboardButton(text='🚫 delete theme', callback_data='delete_theme'))
                msg = bot.send_message(message.chat.id, text="aight! what you want?", reply_markup=markup)

            else:
                bot.send_message(message.chat.id, text="sorry, you dont have access to it :<")

        def get_new_theme(message):
            try:
                if message.text == '/exit':
                    bot.send_message(message.chat.id, text='got you!')
                    return
                new_theme = message.text
                theme = Theme.objects.filter(name=new_theme)
                if len(theme) > 0:
                    msg = bot.reply_to(message, text='sorry, this theme is already occupied :(\ntype new one!')
                    bot.register_next_step_handler(msg, get_new_theme)
                else:
                    msg = bot.reply_to(message, text='got you! what is the short name?')
                    bot.register_next_step_handler(msg, get_new_short_theme, new_theme)
            except Exception as e:
                bot.reply_to(message, "sorry, gotcha problems :(")

        def get_new_short_theme(message, new_theme):
            try:
                if message.text == '/exit':
                    bot.send_message(message.chat.id, text='got you!')
                    return
                new_short_theme = message.text
                short_theme = Theme.objects.filter(short_name=new_short_theme)
                if len(short_theme) > 0:
                    msg = bot.reply_to(message, text='sorry, this short theme is already occupied :(\ntype new one!')
                    bot.register_next_step_handler(msg, get_new_short_theme, new_theme)
                else:
                    theme = Theme(name=new_theme, short_name=new_short_theme)
                    theme.save()
                    bot.reply_to(message, text='good news! new theme!')

            except Exception as e:
                bot.reply_to(message, "sorry, gotcha problems :(")

        @bot.message_handler(content_types=['text'], commands=['schedule'])
        def handle_schedule(message):
            try:
                markup = schedule_markup
                bot.send_message(message.chat.id, text='well, what you looking for?', reply_markup=markup)
            except Exception as e:
                bot.reply_to(message, "sorry, gotcha problems :(")
                print(e)

        def get_date_emojis(type):
            day = ''
            if type == 'today':
                day = datetime.datetime.now().day
            if type == 'tomorrow':
                day = (datetime.datetime.now() + datetime.timedelta(1)).day
            if day < 10:
                day = f'0{day}'
            day = f'{day}'
            return_emojis = ''
            for number in day:
                return_emojis = return_emojis + config.emojis[number]
            return return_emojis

        schedule_markup = types.InlineKeyboardMarkup(row_width=1)
        schedule_markup.row(types.InlineKeyboardButton(text=f'today {get_date_emojis("today")}',
                                                       callback_data='schedule_today'),
                            types.InlineKeyboardButton(text=f'tomorrow {get_date_emojis("tomorrow")}',
                                                       callback_data='schedule_tomorrow'))
        schedule_markup.row(types.InlineKeyboardButton(text='add new schedule 📝', callback_data='add_new_schedule'),
                            types.InlineKeyboardButton(text='week 📆', callback_data='schedule_week'))

        week_markup = types.InlineKeyboardMarkup(row_width=1)
        week_markup.row(types.InlineKeyboardButton(text='monday', callback_data='week_schedule_monday'),
                   types.InlineKeyboardButton(text='tuesday', callback_data='week_schedule_tuesday'),
                   types.InlineKeyboardButton(text='wednesday', callback_data='week_schedule_wednesday'))
        week_markup.row(types.InlineKeyboardButton(text='thursday', callback_data='week_schedule_thursday'),
                   types.InlineKeyboardButton(text='friday', callback_data='week_schedule_friday'),
                   types.InlineKeyboardButton(text='saturday', callback_data='week_schedule_saturday'))
        week_markup.row(types.InlineKeyboardButton(text=' ', callback_data='aboba'),
                   types.InlineKeyboardButton(text='sunday', callback_data='week_schedule_sunday'),
                   types.InlineKeyboardButton(text=' ', callback_data='aboba'))

        def day_schedule(message, day, markup=types.ReplyKeyboardRemove(), is_week=False):
            try:
                msg_template = 'schedule for {day}:\n'
                user = User.objects.get(telegram_id=message.chat.id)
                schedule = Schedule.objects.filter(user_id=user.id).filter(day_of_week=config.num_to_day_of_week[f'{day}'])
                if len(schedule) == 0:
                    msg_template = msg_template + 'chiiiiiiiil 🦦'
                for slot in schedule:
                    name = slot.name
                    start_time = slot.start_time
                    end_time = slot.end_time
                    place = slot.place
                    professor = slot.professor
                    if professor == '-':
                        slot_message = f'🎨 <b>{name}</b>\n🏠 {place}\n⏱ {start_time} - {end_time}\n\n'
                    else:
                        slot_message = f'🎨 <b>{name}</b>\n🏠 {place}\n👩🏻‍🚀 {professor}\n⏱ {start_time} - {end_time}\n\n'
                    msg_template = msg_template + slot_message
                if is_week:
                    bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=msg_template.format(day=config.num_to_day_of_week[f'{day}']), parse_mode='html', reply_markup=markup)
                else:
                    bot.send_message(message.chat.id, text=msg_template.format(day=config.num_to_day_of_week[f'{day}']), parse_mode='html', reply_markup=markup)
            except Exception as e:
                bot.reply_to(message, "sorry, gotcha problems :(")
                print(e)

        def get_csv_schedule(message):
            try:
                if message.text:
                    if message.text == '/exit':
                        bot.send_message(message.chat.id, text="okay, mate!")
                        return
                file_info = bot.get_file(message.document.file_id)
                downloaded_file = bot.download_file(file_info.file_path)
                src = 'csv/' + f"{CSV.objects.get(id=1).number}.csv"

                with open(src, 'wb') as new_file:
                    new_file.write(downloaded_file)
                csv_db = CSV.objects.get(id=1)
                csv_db.number = csv_db.number + 1
                csv_db.save()

                user = User.objects.get(telegram_id=message.chat.id)
                outdated_schedule = Schedule.objects.filter(user_id=user.id)
                outdated_schedule.delete()

                with open(src, 'r') as csv_file:
                    reader = csv.reader(csv_file)
                    count = 0
                    for row in reader:
                        if count == 0:
                            count = count + 1
                            continue
                        day = row[0].split(';')[0].lower()
                        name = row[0].split(';')[1].lower()
                        place = row[0].split(';')[2].lower()
                        professor = row[0].split(';')[3].lower()
                        start_time = row[0].split(';')[4].lower()
                        end_time = row[0].split(';')[5].lower()
                        new_slot = Schedule(day_of_week=day, name=name, place=place, professor=professor, start_time=start_time, end_time=end_time, user_id=user.id)
                        new_slot.save()
                        count = count + 1

                os.remove(src)
                csv_db.number = csv_db.number - 1
                csv_db.save()

                bot.send_message(message.chat.id, text='niccce, created new one!')

            except Exception as e:
                bot.reply_to(message, "sorry, gotcha problems :(")
                print(e)

        @bot.message_handler(content_types=['text'], commands=['manage_locations'])
        def handle_manage_locations(message):
            try:
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton(text='✅ add location', callback_data='add_location'))
                markup.add(types.InlineKeyboardButton(text='🚫 delete location', callback_data='delete_location'))
                markup.add(types.InlineKeyboardButton(text='✍ edit location name', callback_data='edit_location'))
                bot.send_message(message.chat.id, text='okay! choose the option!', reply_markup=markup)

            except Exception as e:
                bot.reply_to(message, "sorry, gotcha problems :(")
                print(e)

        def save_location(message):
            try:
                keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
                button_geo = types.KeyboardButton(text="send location!", request_location=True)
                keyboard.add(button_geo)
                msg = bot.send_message(message.chat.id, text='okay! send me your location!', reply_markup=keyboard)
                bot.register_next_step_handler(msg, receive_location)
            except Exception as e:
                bot.reply_to(message, "sorry, gotcha problems :(")
                print(e)

        def receive_location(message):
            try:
                if message.text:
                    if message.text == '/exit':
                        bot.send_message(message.chat.id, text='ok, man!')
                        return
                longitude = message.location.longitude
                latitude = message.location.latitude
                msg = bot.send_message(message.chat.id, text='got it! now, name this place!', reply_markup=types.ReplyKeyboardRemove())
                bot.register_next_step_handler(msg, receive_location_name, longitude, latitude)
            except Exception as e:
                bot.reply_to(message, "sorry, gotcha problems :(")
                print(e)

        def receive_location_name(message, longitude, latitude):
            try:
                if message.text == '/exit':
                    bot.send_message(message.chat.id, text='okay :<')

                name = message.text
                if name.count('_') > 0:
                    msg = bot.send_message(message.chat.id, text='sorry.. name cant have "_".. try again!')
                    bot.register_next_step_handler(msg, receive_location_name, longitude, latitude)
                    return
                if len(name) > 15:
                    msg = bot.send_message(message.chat.id, text='sorry.. name is too big.. try again!')
                    bot.register_next_step_handler(msg, receive_location_name, longitude, latitude)
                    return
                name = name.replace(' ', '+')
                user = User.objects.get(telegram_id=message.chat.id)
                new_fav_location = FavLocation(name=name, user_id=user.id, longitude=longitude, latitude=latitude)
                new_fav_location.save()
                bot.send_message(message.chat.id, text='new favourite place added!')
            except Exception as e:
                bot.reply_to(message, "sorry, gotcha problems :(")
                print(e)

        def delete_location(message):
            try:
                markup = types.InlineKeyboardMarkup(row_width=1)
                user = User.objects.get(telegram_id=message.chat.id)
                fav_locations = FavLocation.objects.filter(user_id=user.id)
                if len(fav_locations) == 0:
                    bot.send_message(message.chat.id, text='you didnt add any location yet :<')
                    return
                for location in fav_locations:
                    markup.add(types.InlineKeyboardButton(text=f'{location.name.replace("+", " ")}', callback_data=f'delete_fav_location_{location.id}_by_{user.id}'))
                bot.send_message(message.chat.id, text='here are all your locations! choose one to delete', reply_markup=markup)
            except Exception as e:
                bot.reply_to(message, "sorry, gotcha problems :(")
                print(e)

        def edit_location(message):
            try:
                markup = types.InlineKeyboardMarkup(row_width=1)
                user = User.objects.get(telegram_id=message.chat.id)
                fav_locations = FavLocation.objects.filter(user_id=user.id)
                if len(fav_locations) == 0:
                    bot.send_message(message.chat.id, text='you didnt add any location yet :<')
                    return
                for location in fav_locations:
                    markup.add(types.InlineKeyboardButton(text=f'{location.name.replace("+", " ")}', callback_data=f'rename_location_{location.id}_by_{user.id}'))
                bot.send_message(message.chat.id, text='here are all your locations! choose one to edit', reply_markup=markup)
            except Exception as e:
                bot.reply_to(message, "sorry, gotcha problems :(")
                print(e)

        def get_new_location_name(message, location):
            try:
                if message.text == '/exit':
                    bot.send_message(message.chat.id, text='aight!')
                    return
                new_name = message.text
                last_name = location.name
                location.name = new_name
                location.save()
                bot.send_message(message.chat.id, text=f"success! your location <b>{last_name}</b> was renamed to <b>{new_name}</b>!", parse_mode='html')
            except Exception as e:
                bot.reply_to(message, "sorry, gotcha problems :(")
                print(e)
        @bot.message_handler(content_types=['text'], commands=['favourite_locations'])
        def handle_favourite_locations(message):
            try:
                markup = types.InlineKeyboardMarkup(row_width=1)
                user = User.objects.get(telegram_id=message.chat.id)
                fav_locations = FavLocation.objects.filter(user_id=user.id)
                if len(fav_locations) == 0:
                    bot.send_message(message.chat.id, text='you didnt add any location yet :<')
                    return
                for location in fav_locations:
                    markup.add(types.InlineKeyboardButton(text=f'{location.name.replace("+", " ")}', callback_data=f'get_fav_location_{location.id}_by_{user.id}'))
                bot.send_message(message.chat.id, text='here are all your locations!', reply_markup=markup)
            except Exception as e:
                bot.reply_to(message, "sorry, gotcha problems :(")
                print(e)

        @bot.callback_query_handler(func=lambda call: True)
        def callback_query(call):
            req = call.data

            if req == 'edit_location':
                bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                edit_location(call.message)

            if req == 'add_location':
                bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                save_location(call.message)

            if req == 'delete_location':
                bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                delete_location(call.message)

            if req.count('rename_location_') == 1:
                try:
                    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                    location_id = req.split('_')[2]
                    user_id = req.split('_')[4]
                    location = FavLocation.objects.filter(user_id=user_id).get(id=location_id)
                    msg = bot.send_message(call.message.chat.id, text=f'okay! now type new name!', parse_mode='html')
                    bot.register_next_step_handler(msg, get_new_location_name, location)

                except Exception as e:
                    bot.reply_to(call.message, "sorry, gotcha problems :(")
                    print(e)

            if req.count('delete_fav_location_') == 1:
                try:
                    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                    location_id = req.split('_')[3]
                    user_id = req.split('_')[5]
                    location = FavLocation.objects.filter(user_id=user_id).get(id=location_id)
                    location.delete()
                    bot.send_message(call.message.chat.id, text=f'your fav location <b>{location.name.replace("+", " ")}</b> deleted :(', parse_mode='html')
                except Exception as e:
                    bot.reply_to(call.message, "sorry, gotcha problems :(")
                    print(e)

            if req.count('get_fav_location_') == 1:
                try:
                    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                    location_id = req.split('_')[3]
                    user_id = req.split('_')[5]
                    location = FavLocation.objects.filter(user_id=user_id).get(id=location_id)
                    bot.send_message(call.message.chat.id, text=f'your fav location <b>{location.name.replace("+", " ")}</b>!', parse_mode='html')
                    bot.send_location(call.message.chat.id, latitude=location.latitude, longitude=location.longitude)
                except Exception as e:
                    bot.reply_to(call.message, "sorry, gotcha problems :(")
                    print(e)

            if req.count('week_schedule_') == 1:
                day = config.day_of_week_to_num[req.split('_')[2]]
                markup = week_markup
                day_schedule(call.message, day=day, markup=markup, is_week=True)

            if req == 'add_new_schedule':
                bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                bot.send_message(call.message.chat.id, text="alright, send me CSV as shown below (or type '/exit'):")
                bot.send_photo(call.message.chat.id, photo=open('images/schedule_example.png', 'rb'))
                msg = bot.send_message(call.message.chat.id,
                                       text="<b> notice: </b>\n  - first row <b>WON'T</b> be read\n  - if you don't have professor field for business, write '-'",
                                       parse_mode='html')
                bot.register_next_step_handler(msg, get_csv_schedule)

            if req == 'schedule_today':
                bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                msg = bot.send_message(call.message.chat.id, text="here is your schedule for today!")
                markup = schedule_markup
                day_schedule(msg, day = datetime.datetime.now().weekday(), markup=markup)

            if req == 'schedule_tomorrow':
                bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                msg = bot.send_message(call.message.chat.id, text="here is your schedule for tomorrow!")
                markup = schedule_markup
                day_schedule(msg, day=(datetime.datetime.now() + datetime.timedelta(1)).weekday(), markup=markup)

            if req == 'schedule_week':
                bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                markup = week_markup
                day_schedule(call.message, day = datetime.datetime.now().weekday(), markup=markup)

            if req == 'add_theme':
                bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                msg = bot.send_message(call.message.chat.id, text='aight! type the name of new theme!')
                bot.register_next_step_handler(msg, get_new_theme)

            if req == 'delete_theme':
                bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                markup = types.InlineKeyboardMarkup()
                themes = Theme.objects.all()
                for theme in themes:
                    markup.add(
                        types.InlineKeyboardButton(text=theme.name, callback_data=theme.short_name + "_delete_theme"))
                markup.add(types.InlineKeyboardButton(text='🚫 cancel', callback_data="cancel_deleting"))
                bot.send_message(call.message.chat.id, text='okay :< choose theme then....', reply_markup=markup)

            if req == 'cancel_deleting':
                bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                bot.send_message(call.message.chat.id, text='hoooray! a theme survived!!')

            if req == 'get_weather_city':
                bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                msg = bot.send_message(call.message.chat.id, text='okay! text the city you would like to check!')
                bot.register_next_step_handler(msg, get_weather, 'city')

            if req == 'get_weather_map':
                bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
                button_geo = types.KeyboardButton(text="send location!", request_location=True)
                keyboard.add(button_geo)
                msg = bot.send_message(call.message.chat.id, text='okay! send me your location!', reply_markup=keyboard)
                bot.register_next_step_handler(msg, get_weather, 'map')

            if req == 'dice':
                bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                bot.send_dice(call.message.chat.id)

            if req == 'football':
                bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                bot.send_dice(call.message.chat.id, emoji='⚽')

            if req == 'basketball':
                bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                bot.send_dice(call.message.chat.id, emoji='🏀')

            if req == 'bowling':
                bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                bot.send_dice(call.message.chat.id, emoji='🎳')

            if req == 'dart':
                bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                bot.send_dice(call.message.chat.id, emoji='🎯')

            if req == 'slot_machine':
                bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                bot.send_dice(call.message.chat.id, emoji='🎰')

            themes = Theme.objects.all()
            for theme in themes:
                if req == theme.short_name + "_add_photo":
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                          text=f'you chose "{theme.name}" theme!')
                    msg = bot.send_message(call.message.chat.id, text='okay, now send photo!')
                    bot.register_next_step_handler(msg, receive_photo, theme.short_name)

                if req == theme.short_name + "_get_photo":
                    if theme.number_of_pictures == 0:
                        bot.send_message(call.message.chat.id, text="sorry, i dont have photos on this theme yet :(")
                        return
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                          text=f'you chose "{theme.name}" theme!')
                    msg = bot.send_message(call.message.chat.id, text='here you are!')
                    send_random_photo(msg, theme.short_name)

                if req == theme.short_name + "_delete_theme":
                    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                    theme.delete()
                    bot.send_message(call.message.chat.id, text='well.. \nbye, theme......😢')

        bot.polling(none_stop=True)