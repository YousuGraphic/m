import asyncio
from telethon.sync import TelegramClient
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
from datetime import datetime
import os
import shutil

# بياناتك
api_id = 12345678
api_hash = 'your_api_hash'
session = 'mysession'

source_bot = 'designXbot'
target_group = 'https://t.me/maktabat_m'
batch_size = 10
wait_seconds = 5
log_channel = 'https://t.me/apk_reports_channel'  # قناة التتبع

media_dir = 'media_temp'

if not os.path.exists(media_dir):
    os.makedirs(media_dir)

def log(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")

async def main():
    async with TelegramClient(session, api_id, api_hash) as client:
        await client.start()
        log("✅ بدأ السكربت")

        messages = []
        async for message in client.iter_messages(source_bot, reverse=True):
            if message.media:
                messages.append(message)

        total = len(messages)
        log(f"📦 تم العثور على {total} منشور يحتوي وسائط")

        batch_counter = 0
        for i in range(0, total, batch_size):
            batch = messages[i:i + batch_size]
            batch_counter += 1
            log(f"\n🚚 رفع الدفعة {batch_counter} ({len(batch)} منشور)...")

            for msg_index, message in enumerate(batch, 1):
                try:
                    file_name = f"{media_dir}/{message.id}"
                    if isinstance(message.media, MessageMediaPhoto):
                        path = await client.download_media(message, file=file_name + ".jpg")
                    elif isinstance(message.media, MessageMediaDocument):
                        path = await client.download_media(message, file=file_name)
                    else:
                        log(f"⚠️ نوع غير مدعوم في الرسالة {message.id}")
                        continue

                    caption = message.text or "🔄 تم النقل من البوت"
                    await client.send_file(target_group, path, caption=caption)
                    log(f"✅ [{msg_index}/{len(batch)}] تم رفع الرسالة {message.id}")

                    if os.path.exists(path):
                        os.remove(path)

                except Exception as e:
                    log(f"❌ خطأ في الرسالة {message.id}: {e}")
                    await client.send_message(log_channel, f"❌ خطأ أثناء رفع الرسالة {message.id}: {e}")

            log(f"✅ انتهاء الدفعة {batch_counter}")
            await client.send_message(log_channel, f"📤 تم رفع الدفعة {batch_counter} ({len(batch)} منشور) بنجاح.")
            await asyncio.sleep(wait_seconds)

        log("🎉 تم الانتهاء من جميع الدفعات")
        await client.send_message(log_channel, "✅ انتهى السكربت من نقل جميع المنشورات بنجاح.")

        if os.path.exists(media_dir):
            shutil.rmtree(media_dir)

if __name__ == '__main__':
    asyncio.run(main())
