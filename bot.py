import os
import re
import asyncio
from telethon import TelegramClient, events, Button

# الحصول على بيانات API من المتغيرات البيئية
api_id = os.environ.get('API_ID')
api_hash = os.environ.get('API_HASH')
bot_token = os.environ.get('BOT_TOKEN')
admin_id_str = 1900509620

# التحقق من تعيين معرف الإدمن كرقم صحيح
if not admin_id_str:
    raise ValueError("ADMIN_ID is not set in environment variables.")
try:
    admin_id = int(admin_id_str)
except ValueError:
    raise ValueError(f"ADMIN_ID must be a valid integer, but got: {admin_id_str}")

# تهيئة العميل (Client)
client = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

# نمط (Regex) لاستخراج معلومات القناة ومعرف الرسالة من الروابط
link_pattern = re.compile(r'https://t\.me/(?P<channel>\w+)/(?P<message_id>\d+)')
link_pattern_channel_only = re.compile(r'https://t\.me/(?P<channel>\w+)')

# اسم القناة المطلوبة للاشتراك الإجباري
required_channel = 'ir6qe'  # بدون @ أو https://t.me/

# دالة للتحقق من اشتراك المستخدم في القناة باستخدام get_participants
async def is_subscribed(user_id):
    try:
        participants = await client.get_participants(required_channel)
        for participant in participants:
            if participant.id == user_id:
                return True
        return False
    except Exception as e:
        print(f"Error checking subscription: {e}")
        return False

# دالة لمعالجة الأمر /start
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    sender = await event.get_sender()

    # التحقق من اشتراك المستخدم
    if await is_subscribed(sender.id):
        message = f"مرحبًا {sender.first_name}!\nأرسل لي رابط المنشور الذي تريد سحبه من القناة، وسأقوم بمعالجته لك."

        # عرض زر التبليغ إذا كان المستخدم هو الإدمن
        if sender.id == admin_id:
            await event.reply(message, buttons=[Button.inline("إرسال تبليغ", b'send_broadcast')])
        else:
            await event.reply(message)
    else:
        await event.reply(
            f"مرحبًا {sender.first_name}!\nيرجى الاشتراك في القناة التالية لاستخدام البوت: https://t.me/{required_channel}",
            buttons=[Button.inline("تحقق من الاشتراك", b'check_subscription')]
        )

# دالة للتعامل مع زر "تحقق من الاشتراك"
@client.on(events.CallbackQuery(data=b'check_subscription'))
async def check_subscription(event):
    sender = await event.get_sender()

    if await is_subscribed(sender.id):
        await event.edit(f"شكرًا لاشتراكك! الآن يمكنك استخدام البوت.")
    else:
        await event.edit(f"لم تقم بالاشتراك بعد. يرجى الاشتراك في القناة: https://t.me/{required_channel}")

# دالة لمعالجة الرسائل التي تحتوي على روابط
@client.on(events.NewMessage)
async def handle_message(event):
    sender = await event.get_sender()

    # تجاهل الرد على الرسائل التي أرسلها البوت نفسه
    if event.out:
        return

    # تجاهل الأمر '/start' لتجنب تكرار معالجته
    if event.message.message.startswith('/start'):
        return

    # التحقق من اشتراك المستخدم
    if not await is_subscribed(sender.id):
        await event.reply(f"يرجى الاشتراك في القناة التالية لاستخدام البوت: https://t.me/{required_channel}",
                          buttons=[Button.inline("تحقق من الاشتراك", b'check_subscription')])
        return

    message = event.message.message

    # التحقق من وجود رابط قناة فقط (بدون معرف الرسالة)
    match_channel_only = link_pattern_channel_only.search(message)
    if match_channel_only:
        channel = match_channel_only.group('channel')
        await event.reply(f"تم استلام رابط القناة: {channel}. جاري سحب جميع الرسائل...")

        # سحب جميع الرسائل من القناة
        await fetch_all_messages(event.sender_id, channel)
        return

    # التحقق من وجود رابط تليجرام مع معرف الرسالة
    match = link_pattern.search(message)
    if match:
        channel = match.group('channel')
        message_id = int(match.group('message_id'))

        await event.reply(f"تم استلام الرابط من القناة: {channel}، معرف الرسالة: {message_id}. جاري معالجة المحتوى...")
        
        # سحب المحتوى من القناة
        await fetch_content(event.sender_id, channel, message_id)
    else:
        return

# دالة لسحب المحتوى من القناة بناءً على معرف الرسالة
async def fetch_content(user_id, channel, message_id):
    try:
        message = await client.get_messages(channel, ids=message_id)

        if message:
            response_text = ""
            if message.text:
                response_text += f"نص الرسالة: {message.text}\n"

            if message.media:
                response_text += "\n @ir6qe تم السحب بواسطة \n"
                await client.send_file(user_id, message.media)

            if response_text:
                await client.send_message(user_id, response_text)
        else:
            await client.send_message(user_id, "لم يتم العثور على المحتوى المطلوب.")
    except Exception as e:
        await client.send_message(user_id, f"حدث خطأ أثناء سحب المحتوى: {str(e)}")

# دالة لسحب جميع الرسائل من القناة
async def fetch_all_messages(user_id, channel):
    try:
        # سحب جميع الرسائل من القناة
        messages = await client.get_messages(channel, limit=None)  # سحب كل الرسائل

        if messages:
            for message in messages:
                await asyncio.sleep(1)  # تأخير لتجنب الحظر

                response_text = ""
                if message.text:
                    response_text += f"نص الرسالة: {message.text}\n"

                if message.media:
                    response_text += "\n @ir6qe تم السحب بواسطة \n"
                    await client.send_file(user_id, message.media)

                if response_text:
                    await client.send_message(user_id, response_text)
        else:
            await client.send_message(user_id, "لم يتم العثور على محتوى في القناة.")
    except Exception as e:
        await client.send_message(user_id, f"حدث خطأ أثناء سحب المحتوى: {str(e)}")

# دالة لمعالجة زر "إرسال تبليغ" (للإدمن فقط)
@client.on(events.CallbackQuery(data=b'send_broadcast'))
async def send_broadcast(event):
    sender = await event.get_sender()

    # التحقق من إذا كان المستخدم هو الإدمن
    if sender.id == admin_id:
        await event.reply("يرجى إرسال الرسالة التي ترغب في تبليغها لجميع المستخدمين.")
        @client.on(events.NewMessage(from_user=admin_id))
        async def broadcast_message(event):
            message = event.message.message
            async for user in client.iter_participants(required_channel):
                try:
                    await client.send_message(user.id, message)
                except Exception as e:
                    print(f"Error sending message to {user.id}: {e}")
            await event.reply("تم إرسال التبليغ لجميع المستخدمين.")
    else:
        await event.reply("ليس لديك صلاحية استخدام هذا الأمر.")

# تشغيل البوت
client.start()
print("Bot is running...")
client.run_until_disconnected()
