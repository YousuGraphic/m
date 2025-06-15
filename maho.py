import os
import time
import subprocess
from flask import Flask, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telebot import apihelper

TOKEN ='8047447672:AAE6xtDMxrFfmD6Cl7jkEAYIfLsyLiKC1xE'
bot = telebot.TeleBot(TOKEN)
WEBHOOK_URL = 'https://اسم-تطبيقك.onrender.com/'  # ← غيّره إلى رابط موقعك

app = Flask(__name__)

@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    else:
        return '403 Forbidden', 403

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

# === إعادة محاولة تفعيل الويبهوك مهما حصل ===
def set_webhook_forever():
    while True:
        try:
            bot.remove_webhook()
            time.sleep(1)
            bot.set_webhook(url=WEBHOOK_URL)
            print("✅ تم تفعيل Webhook بنجاح")
            break
        except apihelper.ApiTelegramException as e:
            if e.result.status_code == 429:
                wait_time = int(e.result.json()['parameters']['retry_after'])
                print(f"⏳ تم رفض الطلب مؤقتًا، إعادة المحاولة بعد {wait_time} ثانية...")
                time.sleep(wait_time + 1)
            else:
                print(f"❌ خطأ عند محاولة تفعيل Webhook: {e}")
                time.sleep(10)
        except Exception as e:
            print(f"❌ خطأ غير متوقع عند تفعيل Webhook: {e}")
            time.sleep(10)

if __name__ == "__main__":
    print("🚀 بدء تشغيل البوت باستخدام Webhook...")
    while True:
        try:
            set_webhook_forever()
            app.run(host="0.0.0.0", port=10000)
        except Exception as e:
            print(f"❌ خطأ في الخادم: {e}\n🔁 إعادة التشغيل خلال 10 ثواني...")
            time.sleep(10)
