import datetime
import requests
import telebot
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from db_connector import DatabaseOperations
from openAI_connector import generate_image_openAI
from zarinpaal import get_transaction_url
from telebot import apihelper

# Bot setup
api_key = ...
bot = telebot.TeleBot(api_key)
users_data = {}
apihelper.proxy = {
    'http': f'socks5://192.168.1.10:10808',
    'https': f'socks5://192.168.1.10:10808'
}


@bot.message_handler(commands=['start', 'restart'])
def start(message):
    user_id = message.from_user.id
    user_exists = DatabaseOperations.is_user_exists(user_id)
    if not user_exists:
        DatabaseOperations.add_user(user_id)
        if message.text.startswith('/start'):
            parts = message.text.split(' ')
            if len(parts) > 1:
                invite_link = parts[1]
                inviter_user_id = DatabaseOperations.get_user_by_invite_link(invite_link)
                if inviter_user_id:
                    DatabaseOperations.increase_user_credit(inviter_user_id, 3)
                    # todo: send message to inviter user "your credit increased to 3 points !"
                    # Send a message to the inviter user
                    inviter_user = bot.get_chat(inviter_user_id)
                    inviter_username = inviter_user.username if inviter_user.username else f"User {inviter_user_id}"
                    message_text = f"تبریک میگم ، یه نفر با لینک دعوت تو وارد پیکسالی شد. 3 امتیاز دیگه بهت تعلق گرفت :)"
                    bot.send_message(inviter_user_id, message_text)

    show_main_menu(message)


@bot.message_handler(commands=['pay'])
def go_to_increase_credit(message):
    increase_credit(message, user_id=message.from_user.id)


# Message handler
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    if message.text.lower() == 'برگرد منوی اصلی 🏠':
        show_main_menu(message)

    elif message.text == 'برام عکس جدید بساز 📸':
        handle_generate_image(user_id, message)

    elif message.text == 'عکس های من 🖼️':
        user_gallery(message, user_id)

    elif message.text == 'افزایش اعتبار 💰':
        increase_credit(message, user_id)

    elif message.text == 'راهنمایی ❓':
        pass
    elif message.text == 'تماس با مدیریت 📫':
        handle_contact_us(message, user_id)
    elif message.text == 'pay':
        zarinpaal(message, user_id)
    else:

        show_main_menu(message, didnt_understand=True)


def zarinpaal(message, user_id):
    pass


def user_gallery(message, user_id):
    user_rows = DatabaseOperations.get_user_images(user_id)
    if not user_rows:
        bot.send_message(message.chat.id, "هنوز عکسی ایجاد نکردی \nاز منوی زیر می تونی یه عکس جدید بسازی 👇")
    else:

        for row in user_rows:
            response_message = f"✍️ توصیف عکس:\n {row.image_description}\n\n📐 ابعاد: {row.resolution}\n\n💎 کیفیت: {row.quality}\n\n📅 تاریخ ایجاد: {row.generation_date.year}/{row.generation_date.month}/{row.generation_date.day}\n\n"

            markup = InlineKeyboardMarkup(row_width=3)
            button0 = InlineKeyboardButton("عکس رو با کیفیت اصلی بفرست", callback_data=f"image_url_{row.image_id}")
            button1 = InlineKeyboardButton("لینک اصلی عکس", url=row.image_url)
            # if row.generation_date was in an hour ago , add buttn 0 and button1 into markap

            if (datetime.datetime.now() - row.generation_date).total_seconds() < 3600:
                markup.row(button0)
                markup.row(button1)
            bot.send_photo(message.chat.id, photo=row.image_url, caption=response_message, reply_markup=markup)
        show_main_menu(message)


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "free":
        message = get_banner_message(call, call.from_user.id)
        bot.send_message(call.from_user.id, message)
    elif call.data.startswith("image_url_"):
        bot.send_message(call.message.chat.id,  # Use call.message.chat.id
                         "تا چند لحظه دیگه عکس برات ارسال میشه :)")

        image_id = int(call.data[len("image_url_"):])
        image_url = DatabaseOperations.get_image_url(image_id)
        send_image_file_with_url(chat_id=call.message.chat.id, image_url=image_url)
    elif call.data.startswith("pay_"):
        amount = int(call.data[len("pay_"):])
        url = get_transaction_url(amount)
        bot.send_message(call.message.chat.id,
                         f"لینک پرداخت بسته {amount} تومانی ساخته شد . \n میتونی از طریق لینک زیر برای پرداخت اقدام کنی 👇\n {url}")


    else:
        message = create_check_pay_message(call.data)
        bot.answer_callback_query(call.id, message)


def send_image_file_with_url(chat_id, image_url, caption_text=None):
    image_file = requests.get(image_url)
    # Save the image file locally
    with open('image.jpg', 'wb') as f:
        f.write(image_file.content)

    # Send the image file as a document with an inline keyboard
    if caption_text:
        bot.send_document(chat_id=chat_id, document=open('image.jpg', 'rb'), caption=caption_text)
    else:
        bot.send_document(chat_id=chat_id, document=open('image.jpg', 'rb'))

    bot.send_message(chat_id, "لینک اصلی عکس تا یک ساعت اعتبار داره. پس حتما فایل عکس رو یجا ذخیره کن :)")


# endregion


# region main-menu
# region main-menu


def show_main_menu(message, didnt_understand=False):
    markup = get_main_menu_markup()
    if not didnt_understand:
        bot.send_message(message.chat.id, "خب ، چه کاری برات انجام بدم؟", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "متوجه نشدم ، چه کاری برات انجام بدم؟", reply_markup=markup)


# endregion
def get_main_menu_markup():
    # Define buttons
    button1 = types.KeyboardButton('برام عکس جدید بساز 📸')
    button2 = types.KeyboardButton('عکس های من 🖼️')
    button3 = types.KeyboardButton('افزایش اعتبار 💰')
    button4 = types.KeyboardButton('راهنمایی ❓')
    button5 = types.KeyboardButton('تماس با مدیریت 📫')

    # Add the buttons to the markup with the desired layout
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.row(button1, button2)
    markup.row(button3, button4)
    markup.add(button5)
    return markup


# region contact-us


def handle_contact_us(message, user_id):
    markup = types.ReplyKeyboardMarkup(row_width=1, one_time_keyboard=True, resize_keyboard=True)
    button_text = 'برگرد منوی اصلی 🏠'
    markup.add(types.KeyboardButton(button_text))
    bot.send_message(message.chat.id, "خب حالا پیامت رو بنویس 🙂", reply_markup=markup)
    bot.register_next_step_handler(message, process_user_message, user_id)


def process_user_message(message, user_id):
    user_message = message.text
    if user_message == 'برگرد منوی اصلی 🏠':
        pass
    else:
        DatabaseOperations.create_message(user_id, content=user_message)
        bot.reply_to(message, "پیامت با موفقیت ارسال شد 🙌")
    show_main_menu(message)


# endregion

# region increase credit


def increase_credit(message, user_id):
    # Get the user's current credit from the sheet
    user_credit = DatabaseOperations.get_user_credit(user_id)

    info_message = f"""
💰 اعتباری که الان داری : {user_credit} 

❓ چطوری اعتبار خودمو افزایش بدم ؟

ــــــــــــــــــــــــــــــــــــــــ

1️⃣ روش رایگان     
برای افزایش اعتبار رایگان ، میتون بنر مخحصوصت رو برای دوستات فوروارد کنی. به ازای هر نفر که به ربات اضافه بشه و عکس بسازه ، 3 امتیاز رایگان دریافت میکنی😃

ــــــــــــــــــــــــــــــــــــــــ

2️⃣ روش خرید اعتبار         
می تونی یکی از گزینه های زیر رو انتخاب و خرید کنی  👇 


    """

    bot.send_message(message.chat.id, info_message, reply_markup=get_pricing_markup())
    show_main_menu(message)


def get_pricing_markup():
    markup = InlineKeyboardMarkup(row_width=3)
    # markup.row_width = 2
    button0 = InlineKeyboardButton("دریافت اعتبار رایگان", callback_data="free")
    button1 = InlineKeyboardButton("5 امتیاز 10 تومان", callback_data="pay_10000")
    button2 = InlineKeyboardButton("10 امتیاز 20 تومان", callback_data="pay_20000")
    button3 = InlineKeyboardButton("20 امتیاز 35 تومان", callback_data="pay_35000")
    button4 = InlineKeyboardButton("40 امتیاز 65 تومان", callback_data="pay_65000")
    button5 = InlineKeyboardButton("80 امتیاز 120 تومان", callback_data="pay_120000")

    markup.row(button0)
    markup.row(button1)
    markup.row(button2)
    markup.row(button3)
    markup.row(button4)
    markup.row(button5)
    return markup


def create_check_pay_message(callback_data: str):
    callback__list = callback_data.split("-")
    point, price = int(callback__list[0]), int(callback__list[2])

    message = f"""
    بسته ای که انتخاب کردی 
     امتیازی هستش و {price} تومان هزینشه {point}
    
    درگاه برای پرداخت شما آماده است 
    """
    return message


def get_banner_message(call, user_id):
    bot_username = "amirr_37bot"  # Replace with your bot's username
    invite_link = DatabaseOperations.get_user_invite_link(user_id)
    full_invite_link = f"https://t.me/{bot_username}?start={invite_link}"
    message = f"""
    عکسی که میخوای رو پیدا نمیکنی؟ 😕
بیا تو پیکسالی و هر عکسی که میخوای رو توصیف کن تا برات بسازه 

عکسی که میخوای رو بساز 👇
{full_invite_link}
               """
    return message


# endregion

# region generate image
def handle_generate_image(user_id, message):
    user_credit = DatabaseOperations.get_user_credit(user_id)
    if user_credit < 2:

        bot.send_message(message.chat.id,
                         f"متاسفانه اعتبارت برای ایجاد عکس جدید به اتمام رسیده . میتونی با افزایش اعتبار دوباره عکسای جدید درست کنی . برای افزایش اعتبار /pay رو بزن", )

    else:
        # if 1 < user_credit < 6:
        #     bot.send_message(message.chat.id,
        #                      f"مقدار امتیازی که داری {user_credit} هستش. میتونی برای افزایش اعتبار /pay رو بزنی", )
        markup = types.ReplyKeyboardMarkup(row_width=1, one_time_keyboard=True, resize_keyboard=True)
        button_text = 'برگرد منوی اصلی 🏠'
        markup.add(types.KeyboardButton(button_text))
        bot.send_message(message.chat.id,
                         "حله! متنی عکسی که میخوای بسازی رو توصیف کن. بهتره که به تمام جزئیات بپردازی 🔍",
                         reply_markup=markup)
        bot.register_next_step_handler(message, process_image_description, user_id)


def process_image_description(message, user_id):
    user_message = message.text
    if user_message == 'برگرد منوی اصلی 🏠':
        show_main_menu(message)
    # elif user_message==
    else:

        users_data[user_id] = {}
        users_data[user_id]['prompt'] = user_message

        # User must now choose the quality

        # Create buttons for quality
        user_credit = DatabaseOperations.get_user_credit(user_id)
        markup = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True, resize_keyboard=True)
        button_hd = types.KeyboardButton('HD 🚀')
        button_standard = types.KeyboardButton('Standard')
        button_correction = types.KeyboardButton('میخواهم متنم رو اصلاح کنم ↩️')

        markup.add(button_hd, button_standard)
        markup.row(button_correction)
        quality_msg = f"""
💎  حالا کیفیت عکس رو انتخاب کن:
ــــــــــــــــــــــــــــــــــــــــ

عکسای استاندرارد 2️⃣ تا 4️⃣ امتیاز میخوان

🚀 عکسای اچ دی 4️⃣ تا 6️⃣ امتیاز میخوان 

💰 امتیازی که داری  : {user_credit} 
ــــــــــــــــــــــــــــــــــــــــ

"""

        bot.send_message(message.chat.id, quality_msg, reply_markup=markup)
        bot.register_next_step_handler(message, process_image_quality, user_id, user_credit)


def process_image_quality(message, user_id, user_credit):
    user_quality = message.text
    qualities = {
        'HD 🚀': 'hd',
        'Standard': 'standard'

    }
    if user_quality == 'میخواهم متنم رو اصلاح کنم ↩️':
        handle_generate_image(user_id, message)  # Go back to the image description step
    elif user_quality not in qualities.keys():
        commands = {
            '/pay': go_to_increase_credit,
            '/start': start,
            'restart': start,
        }

        # Check if the given text is a command
        if user_quality in commands:
            # If it is, call the associated function
            return commands[user_quality](message)
        else:
            bot.send_message(message.chat.id, " متوجه نشدم . لطفا یکی از گزینه های منو رو انتخاب کن 👇")
        # process_image_quality(message, user_id)
        bot.register_next_step_handler(message, lambda msg: process_image_quality(msg, user_id, user_credit))

    else:
        if user_credit < 4 and user_quality == 'HD 🚀':
            bot.send_message(message.chat.id, " متاسفانه اعتبارت برای ایجاد عکس HD کافی نیست \n"
                                              " میتونی با کلیک روی /pay  اعتبارت رو افزایش بدی \n"
                                              " یا میتونی کیفیت استاندارد رو انتخاب کنی")
            bot.register_next_step_handler(message, process_image_quality, user_id, user_credit)
        else:
            # elif user_credit

            users_data[user_id]['quality'] = qualities[user_quality]

            bot.send_message(message.chat.id, "👇  حالا ابعاد عکس رو از منوی زیر انتخاب کن:",
                             reply_markup=get_resolutions_for_hd_markup() if user_quality == 'HD 🚀' else get_resolutions_for_standard_markup())
            bot.register_next_step_handler(message, process_image_size, user_id)


def process_image_size(message, user_id):
    user_size: str = message.text
    resolutions = {
        'افقی - 6 امتیاز': '1792x1024 6',
        'افقی - 4 امتیاز': '1792x1024 4',
        'عمودی - 6 امتیاز': '1024x1792 6',
        'عمودی - 4 امتیاز': '1024x1792 4',
        'یک در یک - 4 امتیاز': '1024x1024 4',
        'یک در یک - 2 امتیاز': '1024x1024 2'

    }
    if user_size == 'میخوام کیفیت عکس رو دوباره انتخاب کنم ↩️':
        process_image_description(message, user_id)  # Go back to the image quality step
    elif user_size not in resolutions.keys():
        commands = {
            '/pay': go_to_increase_credit,
            '/start': start,
            'restart': start,
        }

        # Check if the given text is a command
        if user_size in commands:
            # If it is, call the associated function
            return commands[user_size](message)
        else:
            bot.send_message(message.chat.id, " متوجه نشدم . لطفا یکی از گزینه های منو رو انتخاب کن 👇")

        bot.register_next_step_handler(message, lambda msg: process_image_size(msg, user_id))
    elif DatabaseOperations.get_user_credit(user_id) < int(resolutions[user_size].split()[-1]):
        bot.send_message(message.chat.id, " متاسفانه اعتبارت برای ایجاد عکس با این ابعاد کافی نیست \n"
                                          " میتونی با کلیک روی /pay  اعتبارت رو افزایش بدی \n"
                                          " یا ابعاد یک در یک رو رو انتخاب کنی")
        bot.register_next_step_handler(message, lambda msg: process_image_size(msg, user_id))

    else:

        users_data[user_id]['size'] = resolutions[user_size].split()[0]
        send_request_to_dall_e(message, user_id, cost=int(resolutions[user_size].split()[-1]))
        # show_main_menu(message)


def send_request_to_dall_e(message, user_id, cost, ):
    bot.send_message(message.chat.id, "در حال درست کردن عکسی که خواستی هستیم...کمتر از یک دقیقه دیگه عکست آمادست :)")

    data = users_data[user_id]
    try:
        # image_url = 'https://oaidalleapiprodscus.blob.core.windows.net/private/org-P9SRjWipesJg9qNb9T6KsqDP/user-oJi7vrLs8pG9KLtyX6XGuVOs/img-0zxbexikXHHsnBUqm858QWMm.png?st=2023-12-12T15%3A47%3A23Z&se=2023-12-12T17%3A47%3A23Z&sp=r&sv=2021-08-06&sr=b&rscd=inline&rsct=image/png&skoid=6aaadede-4fb3-4698-a8f6-684d7786b067&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2023-12-11T23%3A19%3A08Z&ske=2023-12-12T23%3A19%3A08Z&sks=b&skv=2021-08-06&sig=a5VFqmRYyyF/AQd8KmNAYTChsmzsFMrfIuAyDzPctno%3D'

        image_url = generate_image_openAI(users_data[user_id])
    except Exception as e:
        bot.send_message(message.chat.id, str(e))
        return show_main_menu(message)

    prompt = data['prompt']
    size = data['size']
    quality = data['quality']
    new_image = DatabaseOperations.create_image(user_id, prompt, size, quality, image_url)
    DatabaseOperations.decrease_user_credit(user_id, cost)
    DatabaseOperations.decrease_user_credit(1754664857, amount=cost)
    response_message = f"✍️ توصیف عکس:\n {prompt}\n\n📐 ابعاد: {size}\n\n💎 کیفیت: {quality}\n\n📅 تاریخ ایجاد: {datetime.datetime.now()}\n\n"

    markup = InlineKeyboardMarkup(row_width=3)
    button0 = InlineKeyboardButton("عکس رو با کیفیت اصلی بفرست", callback_data=f"image_url_{new_image.image_id}")
    button1 = InlineKeyboardButton("لینک اصلی عکس", url=image_url)

    markup.row(button0)
    markup.row(button1)

    bot.send_photo(message.chat.id, photo=image_url, caption=response_message, reply_markup=markup)
    # send_image_file_with_url(chat_id=message.chat.id, image_url=image_url)

    return show_main_menu(message)


def get_resolutions_for_hd_markup():
    markup = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True, resize_keyboard=True)
    button_resolution1 = types.KeyboardButton('افقی - 6 امتیاز')
    button_resolution2 = types.KeyboardButton('عمودی - 6 امتیاز')
    button_resolution3 = types.KeyboardButton('یک در یک - 4 امتیاز')
    button_correction = types.KeyboardButton('میخوام کیفیت عکس رو دوباره انتخاب کنم ↩️')

    # markup.row(button_resolution1)
    # markup.row(button_resolution2)
    markup.row(button_resolution1, button_resolution2)

    markup.row(button_resolution3)
    markup.row(button_correction)

    return markup


def get_resolutions_for_standard_markup():
    markup = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True, resize_keyboard=True)
    button_resolution1 = types.KeyboardButton('افقی - 4 امتیاز')
    button_resolution2 = types.KeyboardButton('عمودی - 4 امتیاز')
    button_resolution3 = types.KeyboardButton('یک در یک - 2 امتیاز')

    button_correction = types.KeyboardButton('میخوام کیفیت عکس رو دوباره انتخاب کنم ↩️')

    # markup.row(button_resolution1)
    # markup.row(button_resolution2)
    markup.row(button_resolution1, button_resolution2)
    markup.row(button_resolution3)
    markup.row(button_correction)

    return markup


bot.polling()

# bot.message_loop()
