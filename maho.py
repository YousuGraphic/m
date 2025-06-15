import telebot
import subprocess
import os
import time
from flask import Flask, request

TOKEN = '8047447672:AAE6xtDMxrFfmD6Cl7jkEAYIfLsyLiKC1xE'
WEBHOOK_URL = 'https://m-11.onrender.com/'  # رابط تطبيقك
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/', methods=['POST'])
def webhook():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return 'ok', 200

@app.route('/', methods=['GET'])
def index():
    return 'Bot is alive!', 200

# بدء عند /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🎯 أرسل رابط حساب تيك توك وسأبدأ بإرسال المقاطع على دفعات...")

# عند استقبال رابط تيك توك
@bot.message_handler(func=lambda m: 'tiktok.com/' in m.text)
def handle_tiktok_account(message):
    url = message.text.strip()
    bot.send_message(message.chat.id, "⏳ جاري التحميل، سيتم الإرسال على دفعات...")
    download_tiktok_videos(message.chat.id, url)

# وظيفة التحميل
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
    sent_count = 0
    total = len(files)

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

# تفعيل Webhook مع إعادة المحاولة اللانهائية
def start_webhook():
    print("🚀 بدء تشغيل البوت باستخدام Webhook...")
    success = False
    while not success:
        try:
            bot.remove_webhook()
            time.sleep(1)
            bot.set_webhook(url=WEBHOOK_URL)
            success = True
            print("✅ تم تفعيل Webhook بنجاح")
        except Exception as e:
            print(f"❌ فشل التفعيل، إعادة المحاولة خلال 5 ثواني... {e}")
            time.sleep(5)

if __name__ == '__main__':
    start_webhook()
    app.run(host="0.0.0.0", port=10000)
