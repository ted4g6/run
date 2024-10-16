import os
import asyncio
from telethon import TelegramClient, events, Button
import re

# الحصول على بيانات API و معرف الإدمن من المتغيرات البيئية
api_id = os.environ.get('API_ID')
api_hash = os.environ.get('API_HASH')
bot_token = os.environ.get('BOT_TOKEN')
admin_id = int(os.environ.get('ADMIN_ID'))  # التأكد من تحويل معرف الإدمن إلى رقم

# قائمة لحفظ معرفات المستخدمين الذين يتفاعلون مع البوت
user_ids = set()

# تهيئة العميل (Client)
client = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

# نمط (Regex) لاستخراج معلومات القناة ومعرف الرسالة من الروابط
link_pattern = re.compile(r'https://t\.me/(?P<channel>\w+)/(?P<message_id>\d+)?')

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

    # إضافة المستخدم إلى قائمة المستخدمين
    user_ids.add(sender.id)

    # التحقق من اشتراك المستخدم
    if await is_subscribed(sender.id):
        await event.reply(f"مرحبًا {sender.first_name}!\nأرسل لي رابط المنشور الذي تريد سحبه من القناة، أو أرسل رابط القناة لسحب جميع الرسائل.")
    else:
        # إرسال رسالة مع زر "تحقق من الاشتراك"
        await event.reply(
            f"مرحبًا {sender.first_name}!\nيرجى الاشتراك في القناة التالية لاستخدام البوت: https://t.me/{required_channel}",
            buttons=[Button.inline("تحقق من الاشتراك", b'check_subscription')]
        )

# دالة للتعامل مع زر "تحقق من الاشتراك"
@client.on(events.CallbackQuery(data=b'check_subscription'))
async def check_subscription(event):
    sender = await event.get_sender()

    # التحقق من اشتراك المستخدم
    if await is_subscribed(sender.id):
        await event.edit(f"شكرًا لاشتراكك! الآن يمكنك استخدام البوت.")
    else:
        await event.edit(f"لم تقم بالاشتراك بعد. يرجى الاشتراك في القناة: https://t.me/{required_channel}")

# دالة لمعالجة الرسائل التي تحتوي على روابط فقط
@client.on(events.NewMessage)
async def handle_message(event):
    sender = await event.get_sender()

    # إضافة المستخدم إلى قائمة المستخدمين
    user_ids.add(sender.id)

    if event.out or event.message.message.startswith('/start'):
        return

    if not await is_subscribed(sender.id):
        await event.reply(f"يرجى الاشتراك في القناة التالية لاستخدام البوت: https://t.me/{required_channel}",
                          buttons=[Button.inline("تحقق من الاشتراك", b'check_subscription')])
        return

    message = event.message.message

    # التحقق من وجود رابط تليجرام في الرسالة
    match = link_pattern.search(message)
    if match:
        channel = match.group('channel')
        message_id = match.group('message_id')

        if message_id:
            # إذا كان هناك معرف رسالة، سحب الرسالة المحددة
            await event.reply(f"تم استلام الرابط من القناة: {channel}، معرف الرسالة: {message_id}. جاري معالجة المحتوى...")
            await fetch_content(event.sender_id, channel, int(message_id))
        else:
            # إذا لم يكن هناك معرف رسالة، سحب جميع الرسائل
            await event.reply(f"تم استلام رابط القناة: {channel}. جاري سحب جميع الرسائل...")
            await fetch_all_messages(event.sender_id, channel)
    else:
        return

# دالة لسحب رسالة محددة من القناة
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

# دالة لسحب جميع الرسائل من القناة مع تأخير
async def fetch_all_messages(user_id, channel):
    try:
        # الحصول على جميع الرسائل من القناة
        async for message in client.iter_messages(channel):
            response_text = ""
            if message.text:
                response_text += f"نص الرسالة: {message.text}\n"

            if message.media:
                response_text += "\n @ir6qe تم السحب بواسطة \n"
                await client.send_file(user_id, message.media)

            if response_text:
                await client.send_message(user_id, response_text)

            # تأخير لتجنب الحظر
            await asyncio.sleep(2)  # يمكنك تعديل الوقت حسب الحاجة
    except Exception as e:
        await client.send_message(user_id, f"حدث خطأ أثناء سحب جميع الرسائل: {str(e)}")

# دالة لمعالجة أوامر الإدمن
@client.on(events.NewMessage(pattern='/broadcast'))
async def broadcast(event):
    sender = await event.get_sender()

    # التحقق مما إذا كان المستخدم هو الإدمن
    if sender.id == admin_id:
        # تقسيم الرسالة للحصول على النص المراد إرساله
        command, *message_text = event.message.message.split(' ', 1)

        if message_text:
            message_text = message_text[0]

            # إرسال التبليغ لجميع المستخدمين
            for user_id in user_ids:
                try:
                    await client.send_message(user_id, message_text)
                except Exception as e:
                    print(f"Error sending message to {user_id}: {e}")
            await event.reply("تم إرسال التبليغ لجميع المستخدمين.")
        else:
            await event.reply("يرجى كتابة رسالة التبليغ بعد الأمر /broadcast.")
    else:
        await event.reply("هذا الأمر مخصص للإدمن فقط.")

# تشغيل البوت
client.start()
print("Bot is running...")
client.run_until_disconnected()
