import os
import telebot
import subprocess
import threading
import time

# --- الإعدادات ---
TOKEN = 'ضع_هنا_توكن_البوت_الخاص_بك' 
bot = telebot.TeleBot(TOKEN)

# تحديد مسار اللوجو الثابت (سيتم تحميله مرة واحدة ويبقى دائماً)
LOGO_PATH = os.path.join(os.getcwd(), 'logo.png')

# دالة معالجة الفيديو وإضافة اللوجو
def process_video_complete(message, input_path):
    # اسم ملف المخرج
    output_path = f"out_{message.video.file_id}.mp4"
    
    # التأكد من وجود اللوجو في المسار المحدد
    if not os.path.exists(LOGO_PATH):
        bot.reply_to(message, "❌ خطأ تقني: ملف logo.png غير موجود في السيرفر. أرجوك ارفعه أولاً.")
        return

    # أمر FFmpeg الاحترافي:
    # -threads 1: لضمان عدم استهلاك الرام بالكامل (مناسب لـ 512MB)
    # overlay=60:H-h-60: لوضع اللوجو في اليسار تحت مع مسافة أمان (مثل صورتك)
    # -preset ultrafast: لأسرع معالجة ممكنة لتقليل الضغط على السيرفر
    # -crf 26: للحفاظ على جودة 1080p بوزن ملف مناسب
    ffmpeg_cmd = [
        'ffmpeg',
        '-threads', '1',
        '-i', input_path,
        '-i', LOGO_PATH,
        '-filter_complex', '[0:v][1:v]overlay=60:H-h-60',
        '-c:v', 'libx264',
        '-preset', 'ultrafast',
        '-crf', '26',
        '-c:a', 'copy', # نسخ الصوت الأصلي بدون إعادة معالجة لتوفير الوقت
        '-y', output_path
    ]

    try:
        # إرسال رسالة انتظار للمستخدم
        msg = bot.send_message(message.chat.id, "🎬 جاري معالجة الفيديو بدقة 1080p...\nيرجى الانتظار، هذه العملية تعتمد على حجم المقطع.")
        
        # تشغيل عملية المعالجة
        subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # إرسال الفيديو الناتج مع حقوق قناتك
        with open(output_path, 'rb') as v:
            bot.send_video(
                message.chat.id, 
                v, 
                caption="✅ تم إضافة اللوجو بنجاح\n\n🆔 @RealMadridNews18",
                supports_streaming=True
            )
        
        # حذف رسالة الانتظار
        bot.delete_message(message.chat.id, msg.message_id)
        
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ أثناء المعالجة: {e}\nنصيحة: جرب مقطعاً أقصر إذا كان السيرفر ينهار.")
    
    finally:
        # تنظيف الملفات المؤقتة فوراً للحفاظ على مساحة السيرفر
        if os.path.exists(input_path): os.remove(input_path)
        if os.path.exists(output_path): os.remove(output_path)

# استقبال الفيديوهات من المستخدم
@bot.message_handler(content_types=['video'])
def handle_video(message):
    bot.reply_to(message, "📥 استلمت الفيديو، جاري التحميل لبدء دمج الشعار...")
    
    try:
        # تحميل الملف من سحابة تلجرام إلى السيرفر
        file_info = bot.get_file(message.video.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        input_path = f"in_{message.video.file_id}.mp4"
        with open(input_path, 'wb') as f:
            f.write(downloaded_file)
        
        # تشغيل المعالجة في خيط منفصل لكي لا يتوقف البوت عن الاستجابة
        t = threading.Thread(target=process_video_complete, args=(message, input_path))
        t.start()
        
    except Exception as e:
        bot.reply_to(message, f"❌ فشل تحميل الملف: {e}")

# رسالة الترحيب
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "مرحباً بك في بوت إضافة الحقوق! 🎥\n\nأرسل لي أي فيديو وسأقوم بوضع شعار قناتك في الزاوية اليسرى السفلية بدقة 1080p.")

print("🚀 Bot is Online and Ready!")
bot.polling(non_stop=True)
