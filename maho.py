import telebot
import subprocess
import os
import time
from flask import Flask, request
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Update

# التوكن الخاص ببوت التحميل
BOT_TOKEN = '8047447672:AAE6xtDMxrFfmD6Cl7jkEAYIfLsyLiKC1xE'
bot = telebot.TeleBot(BOT_TOKEN)

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ البوت يعمل عبر Webhook!"

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True))
    bot.process_new_updates([update])
    return "!", 200

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🎯 أرسل رابط حساب تيك توك وسأبدأ بإرسال المقاطع على دفعات...")

@bot.message_handler(func=lambda m: 'tiktok.com/' in m.text)
def handle_tiktok_account(message):
    url = message.text.strip()
    bot.send_message(message.chat.id, "⏳ جاري التحميل، سيتم الإرسال على دفعات...")
    download_tiktok_videos(message.chat.id, url)

def download_tiktok_videos(chat_id, url):
    folder = "tiktok_temp"
    os.makedirs(folder, exist_ok=True)

    command = [
        'yt-dlp',
        '--no-playlist',
        '--yes-playlist',
        '--download-archive', f'{folder}/archive.txt',
        '-o', f'{folder}/video_%(id)s.%(ext)s',
        '--retries', '5',
        '--fragment-retries', '5',
        '--no-check-certificate',
        '--no-warnings',
        url
    ]

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        bot.send_message(chat_id, f"❌ خطأ في التحميل:\n{e}")
        return

    files = sorted(os.listdir(folder))
    if not files:
        bot.send_message(chat_id, "❌ لم يتم العثور على أي فيديوهات.")
        return

    batch_size = 10
    total = len(files)
    sent_count = 0

    for i in range(0, total, batch_size):
        batch = files[i:i + batch_size]
        bot.send_message(chat_id, f"📦 إرسال الدفعة {i//batch_size + 1} من {((total-1)//batch_size)+1}...")

        for f in batch:
            path = os.path.join(folder, f)
            try:
                with open(path, 'rb') as file:
                    if f.endswith(('.mp4', '.mkv', '.webm')):
                        bot.send_video(chat_id, file, timeout=60)
                    elif f.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                        bot.send_photo(chat_id, file, timeout=60)
                    elif f.endswith(('.mp3', '.ogg', '.wav')):
                        bot.send_audio(chat_id, file, timeout=60)
                    else:
                        bot.send_document(chat_id, file, timeout=60)
                sent_count += 1
                os.remove(path)
                time.sleep(1.2)
            except Exception as e:
                bot.send_message(chat_id, f"⚠️ خطأ في الملف {f}: {e}")
        time.sleep(5)

    bot.send_message(chat_id, f"✅ تم إرسال {sent_count} ملف بنجاح.")

# إعداد Webhook
WEBHOOK_URL = f'https://اسم-مشروعك.onrender.com/{BOT_TOKEN}'

if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
