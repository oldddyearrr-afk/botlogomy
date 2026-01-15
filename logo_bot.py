import os, telebot, subprocess, threading

TOKEN = 'ضع_هنا_توكن_البوت'
bot = telebot.TeleBot(TOKEN)

# --- إعداد اللوجو الدائم ---
# بمجرد وضع صورة باسم logo.png في مجلد البوت، سيتعامل معها كملف محلي دائم
LOGO_PATH = os.path.join(os.getcwd(), 'logo.png')

def process_video_fixed_logo(message, input_path):
    output_path = f"out_{message.video.file_id}.mp4"
    
    # التأكد من أن اللوجو موجود قبل البدء
    if not os.path.exists(LOGO_PATH):
        bot.reply_to(message, "⚠️ اللوجو غير موجود! تأكد من رفع ملف logo.png بجانب الكود.")
        return

    # الحيلة التقنية لتقليل الرام مع 1080p
    ffmpeg_cmd = [
        'ffmpeg',
        '-threads', '1',
        '-i', input_path,
        '-i', LOGO_PATH, # استخدام المسار الثابت المخزن
        '-filter_complex', 'overlay=30:main_h-overlay_h-30', 
        '-c:v', 'libx264',
        '-preset', 'ultrafast',
        '-crf', '26',
        '-c:a', 'copy',
        '-y', output_path
    ]

    try:
        msg = bot.send_message(message.chat.id, "⚙️ جاري المعالجة باستخدام اللوجو الثابت...")
        subprocess.run(ffmpeg_cmd, check=True)
        
        with open(output_path, 'rb') as v:
            bot.send_video(message.chat.id, v, caption="✅ تم بنجاح بدقة 1080p")
        
        bot.delete_message(message.chat.id, msg.message_id)
    except Exception as e:
        bot.reply_to(message, "❌ حدث خطأ في المعالجة.")
    finally:
        # نحذف الفيديوهات فقط ونبقي على logo.png دائماً
        if os.path.exists(input_path): os.remove(input_path)
        if os.path.exists(output_path): os.remove(output_path)

@bot.message_handler(content_types=['video'])
def handle(message):
    bot.reply_to(message, "📥 جاري استلام الفيديو...")
    file_info = bot.get_file(message.video.file_id)
    downloaded = bot.download_file(file_info.file_path)
    
    input_path = f"in_{message.video.file_id}.mp4"
    with open(input_path, 'wb') as f:
        f.write(downloaded)
    
    threading.Thread(target=process_video_fixed_logo, args=(message, input_path)).start()

print("🚀 Bot with Permanent Logo is running...")
bot.polling(non_stop=True)
