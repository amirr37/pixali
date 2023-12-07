# --------------------------------------------------------------------config
import requests
import telebot
from telebot import types
import datetime
import gspread
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButtonPollType
import uuid

# http=192.168.1.10:10810;socks=192.168.1.10:10808

# Bot setup
api_key = '6861008650:AAHVadlu-rvR_K1Khn7siWNfsjgrX3fpHrc'
bot = telebot.TeleBot(api_key)

# Google Sheets setup
service_account = gspread.service_account()
sheet = service_account.open('my_bot')
contact_us_worksheet = sheet.worksheet('contact_us')
credit_worksheet = sheet.worksheet('credits')
images_worksheet = sheet.worksheet('images')
banner_worksheet = sheet.worksheet('banners')
# --------------------------------------------------------------------variables

# User states
user_states = {}
descriptions = {}  # A dictionary to store the descriptions temporarily
packages = {}
users_credit = {}
user_invite_links = {}
user_qualities = {}
user_resolutions = {}


# -------------------------------------------------------------------- /start /restart
# Start command handler
@bot.message_handler(commands=['start', 'restart'])
def start(message):
    user_id = message.from_user.id
    user_exists = is_user_in_sheet(user_id)
    if not user_exists:
        add_user_to_sheet(user_id, initial_credit=10000)

    if message.text.startswith('/start') and not user_exists:
        parts = message.text.split(' ')
        if len(parts) > 1:
            invite_token = parts[1]
            inviter_user_id = get_invite_token_user(invite_token)
            if inviter_user_id:
                # increase user_id credit as 5000
                current_credit = get_user_credit(inviter_user_id)
                update_user_credit(inviter_user_id, current_credit + 5000)

    show_main_menu(message)


def is_user_in_sheet(user_id):
    user_ids = credit_worksheet.col_values(1)[1:]  # Skip the header
    return str(user_id) in user_ids


def add_user_to_sheet(user_id, initial_credit):
    # Add the user_id and initial_credit to the credits sheet
    credit_worksheet.append_row([str(user_id), initial_credit])


# -------------------------------------------------------------------- /message handler


# Message handler
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    if message.text.lower() == 'برگرد به منوی اصلی':
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

    else:
        print("dffdfd")
        print(message.text)
        print(message.text == 'عکس های من 🖼️')
        bot.reply_to(message, "متوجه نشدم ، چه کاری برات انجام بدم ؟")


# region gallery

def user_gallery(message, user_id):
    # Assuming 'sheet' is the variable representing 'images_worksheet'
    data = images_worksheet.get_all_values()

    # Extract column headers
    headers = data[0]

    # Find the index of the 'user_id' column
    user_id_index = headers.index('user_id')

    # Find rows where user_id matches
    user_rows = [row for row in data[1:] if row[user_id_index] == str(user_id)]

    if not user_rows:
        bot.send_message(message.chat.id, "شما تا کنون عکسی ایجاد نکردی :)")
    else:
        for row in user_rows:
            image_description = row[headers.index('image description')]
            resolution = row[headers.index('resolution')]
            quality = row[headers.index('quality')]
            image_url = row[headers.index('image_url')]
            generation_date = row[headers.index('generation_date')]
            response_message = f"توصیف عکس: {image_description}\n\nابعاد: {resolution}\n\nکیفیت: {quality}\n\nتاریخ ایجاد: {generation_date}\n\n"

            markup = InlineKeyboardMarkup(row_width=3)
            button0 = InlineKeyboardButton("عکس رو با کیفیت اصلی بفرست", callback_data=f"image_url_{image_url}")
            button1 = InlineKeyboardButton("لینک اصلی عکس", url=image_url)

            markup.row(button0)
            markup.row(button1)

            bot.send_photo(message.chat.id, photo=image_url, caption=response_message, reply_markup=markup, )


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "free":
        message = get_banner_message(call, call.from_user.id)
        bot.send_message(call.from_user.id, message)
    elif call.data.startswith("image_url_"):
        image_url = call.data[len("image_url_"):]
        send_image_file_with_url(chat_id=call.message.chat.id, image_url=image_url)
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


# endregion


# region main-menu


def show_main_menu(message):
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
    bot.send_message(message.chat.id, "خب ، چه کاری برات انجام بدم؟", reply_markup=markup)


# endregion

# region contact-us


def handle_contact_us(message, user_id):
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    markup = types.ReplyKeyboardMarkup(row_width=1, one_time_keyboard=True, resize_keyboard=True)
    button_text = 'برگرد منوی اصلی 🏠'
    markup.add(types.KeyboardButton(button_text))
    bot.send_message(message.chat.id, "خب حالا پیامت رو بنویس 🙂", reply_markup=markup)
    bot.register_next_step_handler(message, process_user_message, current_time, user_id)


def process_user_message(message, current_time, user_id):
    user_message = message.text
    if user_message == 'برگرد منوی اصلی 🏠':
        pass
    else:
        contact_us_worksheet.append_row([user_message, current_time, user_id])
        bot.reply_to(message, "پیامت با موفقیت ارسال شد 🙌")
    show_main_menu(message)


# endregion

# region increase credit
# todo


def increase_credit(message, user_id):
    # Get the user's current credit from the sheet
    user_credit = get_user_credit(user_id)

    info_message = f"""
اعتباری که الان داری : {user_credit} تومان

❓ چطوری اعتبار خودمو افزایش بدم ؟

ــــــــــــــــــــــــــــــــــــــــ

1️⃣ روش رایگان     

ــــــــــــــــــــــــــــــــــــــــ

2️⃣ روش خرید اعتبار         
می تونی یکی از گزینه های زیر رو انتخاب و خرید کنی  👇 

ــــــــــــــــــــــــــــــــــــــــ
    

    """

    bot.send_message(message.chat.id, info_message, reply_markup=get_pricing_markup())


def get_pricing_markup():
    markup = InlineKeyboardMarkup(row_width=3)
    # markup.row_width = 2
    button0 = InlineKeyboardButton("دریافت اعتبار رایگان", callback_data="free")
    button1 = InlineKeyboardButton("100 امتیاز 10,000 تومان", callback_data="100-point-10000-toman")
    button2 = InlineKeyboardButton("200 امتیاز 16,000 تومان", callback_data="200-point-16000-toman")
    button3 = InlineKeyboardButton("400 امتیاز 30,000 تومان", callback_data="400-point-30000-toman")
    button4 = InlineKeyboardButton("800 امتیاز 50,000 تومان", callback_data="800-point-50000-toman")
    markup.row(button0)
    markup.row(button1)
    markup.row(button2)
    markup.row(button3)
    markup.row(button4)
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
    invite_token = get_user_invite_token(user_id)
    if not invite_token:
        invite_token = str(uuid.uuid4())
        banner_worksheet.append_row([str(user_id), invite_token])

    invite_link = f"https://t.me/{bot_username}?start={invite_token}"
    message = f"""
این لینک دعوت توعه 
{invite_link}
               """
    return message


def get_invite_token_user(token):
    user_ids_and_tokens = banner_worksheet.get_all_values()[1:]  # Skip the header

    for row in user_ids_and_tokens:
        if token == row[1]:
            return row[0]  # Return the user_id associated with the token

    return None


def get_user_invite_token(user_id):
    # Fetch all user_ids and credit values from the credit sheet
    user_ids_and_tokens = banner_worksheet.get_all_values()[1:]  # Skip the header
    print(user_ids_and_tokens)
    # Iterate through the rows to find the user_id
    for row in user_ids_and_tokens:
        if str(user_id) in row:
            return row[1]

    # Return 0 if user_id is not found in the sheet
    return 0


def get_user_credit(user_id):
    # Fetch all user_ids and credit values from the credit sheet
    user_ids_and_credits = credit_worksheet.get_all_values()[1:]  # Skip the header

    # Iterate through the rows to find the user_id
    for row in user_ids_and_credits:
        if str(user_id) in row:
            # Extract the credit value if the user_id is found
            return int(row[1])

    # Return 0 if user_id is not found in the sheet
    return 0


def update_user_credit(user_id, new_credit):
    # Fetch all user_ids and credit values from the credit sheet
    user_ids_and_credits = credit_worksheet.get_all_values()[1:]  # Skip the header

    # Iterate through the rows to find the user_id
    for row in user_ids_and_credits:
        if str(user_id) in row:
            # Update the credit value if the user_id is found
            row_index = user_ids_and_credits.index(row) + 2  # Adjust for 0-based index and header row
            credit_worksheet.update(f'B{row_index}', new_credit)
            return

    # If the user_id is not found, create a new row
    credit_worksheet.append_row([str(user_id), new_credit])


# endregion

# region generate image
def handle_generate_image(user_id, message):
    user_states[user_id] = 'awaiting_image_description'

    markup = types.ReplyKeyboardMarkup(row_width=1, one_time_keyboard=True, resize_keyboard=True)
    button_text = 'برگرد منوی اصلی 🏠'
    markup.add(types.KeyboardButton(button_text))
    bot.send_message(message.chat.id, "حله! متنی عکسی که میخوای بسازی رو توصیف کن. بهتره که به تمام جزئیات بپردازی 🔍",
                     reply_markup=markup)
    bot.register_next_step_handler(message, process_image_description, user_id)


def process_image_description(message, user_id):
    user_message = message.text
    if user_message == 'برگرد منوی اصلی 🏠':
        show_main_menu(message)
    else:
        # User must now choose the quality
        descriptions[user_id] = user_message

        # Create buttons for quality
        markup = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True, resize_keyboard=True)
        button_hd = types.KeyboardButton('HD 🚀')
        button_standard = types.KeyboardButton('Standard')
        button_correction = types.KeyboardButton('میخواهم متنم رو اصلاح کنم ↩️')

        markup.add(button_hd, button_standard)
        markup.row(button_correction)
        quality_msg = """
حالا کیفیت عکس رو انتخاب کن:

ــــــــــــــــــــــــــــــــــــــــ

عکسای استاندرارد 2️⃣ تا 4️⃣ امتیاز میخوان


🚀 عکسای اچ دی 4️⃣ تا 6️⃣ امتیاز میخوان 

ــــــــــــــــــــــــــــــــــــــــ

"""

        bot.send_message(message.chat.id, quality_msg, reply_markup=markup)
        bot.register_next_step_handler(message, process_image_quality, user_id)


def process_image_quality(message, user_id):
    user_quality = message.text
    if user_quality == 'میخواهم متنم رو اصلاح کنم ↩️':
        handle_generate_image(user_id, message)  # Go back to the image description step
    else:

        print(f"User {user_id} selected quality: {user_quality}")
        bot.send_message(message.chat.id, "حالا ابعاد عکس رو انتخاب کن:",
                         reply_markup=get_resolutions_for_hd_markup() if user_quality == 'HD 🚀' else get_resolutions_for_standard_markup())
        bot.register_next_step_handler(message, process_image_resolution, user_id)


def process_image_resolution(message, user_id):
    user_resolution: str = message.text
    if user_resolution == 'میخوام کیفیت عکس رو دوباره انتخاب کنم ↩️':
        # bot.send_message(message.chat.id, "حالا ابعاد عکس رو انتخاب کن:", reply_markup=get_resolutions_markup())
        process_image_description(message, user_id)  # Go back to the image quality step
    else:
        res = user_resolution.split('')[0]
        user_resolutions[user_id] = user_resolution.split('')[0]

        data = {'user_id': user_id,
                'prompt': descriptions[user_id],
                'quality': "HD" if user_qualities[user_id] == 'HD 🚀' else 'standard',
                'resolution': user_resolutions[user_id]}

        print(f"User {user_id} selected resolution: {user_resolution}")
        # You can now proceed with further actions based on the selected resolution and quality
        show_main_menu(message)


def get_resolutions_for_hd_markup():
    markup = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True, resize_keyboard=True)
    button_resolution1 = types.KeyboardButton('1024x1792 - 6 امتیاز')
    button_resolution2 = types.KeyboardButton('1792x1024 - 6 امتیاز')
    button_resolution3 = types.KeyboardButton('1024x1024 - 4 امتیاز')
    button_correction = types.KeyboardButton('میخوام کیفیت عکس رو دوباره انتخاب کنم ↩️')

    # markup.row(button_resolution1)
    # markup.row(button_resolution2)
    markup.row(button_resolution1, button_resolution2)

    markup.row(button_resolution3)
    markup.row(button_correction)

    return markup


def get_resolutions_for_standard_markup():
    markup = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True, resize_keyboard=True)
    button_resolution1 = types.KeyboardButton('1024x1792 - 4 امتیاز')
    button_resolution2 = types.KeyboardButton('1792x1024 - 4 امتیاز')
    button_resolution3 = types.KeyboardButton('1024x1024 - 2 امتیاز')

    button_correction = types.KeyboardButton('میخوام کیفیت عکس رو دوباره انتخاب کنم ↩️')

    # markup.row(button_resolution1)
    # markup.row(button_resolution2)
    markup.row(button_resolution1, button_resolution2)
    markup.row(button_resolution3)
    markup.row(button_correction)

    return markup


# endregion


bot.polling()
