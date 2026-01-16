import os
import telebot
import subprocess
import threading
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- الإعدادات الأساسية ---
TOKEN = '8412705275:AAF3YfkURUCObv6iFavAe3fQI1Id81JihPs'
bot = telebot.TeleBot(TOKEN)
LOGO_PATH = "logo.png"
CONFIG_FILE = "settings.json"

# --- تحميل الإعدادات أو إنشاؤها (التحميل لمرة واحدة) ---
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'r') as f:
        settings = json.load(f)
else:
    # إعدادات افتراضية بناءً على طلبك (أسفل يسار مع إزاحة 50 بكسل)
    settings = {
        "size": "200", 
        "opacity": "1.0",
        "x_offset": "50",
        "y_offset": "50"
    }

def save_settings():
    with open(CONFIG_FILE, 'w') as f:
        json.dump(settings, f)

# --- 1. خادم وهمي بسيط لإرضاء Render ومنع التوقف ---
class SimpleServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is Running - High Performance Mode")

def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleServer)
    print(f"🌐 Dummy Server running on port {port}")
    server.serve_forever()

# --- 2. أوامر التحكم الديناميكي ---
@bot.message_handler(commands=['start', 'settings'])
def show_settings(message):
    text = (f"⚙️ **إعدادات اللوجو الحالية:**\n\n"
            f"📏 الحجم: `{settings['size']}px`\n"
            f"✨ الشفافية: `{settings['opacity']}`\n"
            f"📍 الإزاحة من اليسار: `{settings['x_offset']}px`\n"
            f"📍 الرفع من الأسفل: `{settings['y_offset']}px`\n\n"
            f"🛠 **أوامر التحكم:**\n"
            f"• لتغيير الحجم: `/size 150`\n"
            f"• لتغيير الشفافية: `/opacity 0.7`\n"
            f"• للتحريك (يمين ثم أعلى): `/move 60 60`\n"
            f"• فقط أرسل الفيديو ليتم المعالجة فوراً.")
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['size'])
def set_size(message):
    try:
        val = message.text.split()[1]
        settings['size'] = val
        save_settings()
        bot.reply_to(message, f"✅ تم ضبط الحجم إلى {val} بكسل.")
    except: bot.reply_to(message, "⚠️ مثال: `/size 200`")

@bot.message_handler(commands=['opacity'])
def set_opacity(message):
    try:
        val = message.text.split()[1]
        settings['opacity'] = val
        save_settings()
        bot.reply_to(message, f"✅ تم ضبط الشفافية إلى {val}.")
    except: bot.reply_to(message, "⚠️ مثال: `/opacity 0.8` (من 0.1 إلى 1.0)")

@bot.message_handler(commands=['move'])
def set_move(message):
    try:
        parts = message.text.split()
        settings['x_offset'] = parts[1]
        settings['y_offset'] = parts[2]
        save_settings()
        bot.reply_to(message, f"✅ تم تحريك اللوجو: {parts[1]} لليمين و {parts[2]} للأعلى.")
    except: bot.reply_to(message, "⚠️ مثال: `/move 50 50`")

# --- 3. محرك المعالجة السريع ---
def get_overlay_filter():
    # الإحداثيات بناءً على طلبك: من اليسار x ومن الأسفل y
    x = settings['x_offset']
    y = settings['y_offset']
    coords = f"{x}:main_h-overlay_h-{y}"
    return f"[1:v]scale={settings['size']}:-1,format=argb,colorchannelmixer=aa={settings['opacity']}[logo];[0:v][logo]overlay={coords}"

@bot.message_handler(content_types=['video'])
def handle_video(message):
    input_file = f"in_{message.message_id}.mp4"
    output_file = f"out_{message.message_id}.mp4"
    
    try:
        msg = bot.reply_to(message, "📥 استلمت الفيديو، جاري التحميل...")
        
        file_info = bot.get_file(message.video.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open(input_file, 'wb') as f:
            f.write(downloaded_file)
            
        bot.edit_message_text("🎬 جاري معالجة الفيديو بدقة أصلية...\nيرجى الانتظار، جاري دمج الشعار.", 
                              chat_id=message.chat.id, message_id=msg.message_id)

        # دمج اللوجو مع نسخ الصوت (سرعة قصوى)
        cmd = [
            'ffmpeg', '-y', '-i', input_file, '-i', LOGO_PATH,
            '-filter_complex', get_overlay_filter(),
            '-c:a', 'copy', '-preset', 'ultrafast', output_file
        ]
        
        subprocess.run(cmd, check=True)

        with open(output_file, 'rb') as video:
            bot.send_video(message.chat.id, video, caption="✅ تم دمج الشعار بنجاح!")
            
        # تنظيف
        if os.path.exists(input_file): os.remove(input_file)
        if os.path.exists(output_file): os.remove(output_file)
        bot.delete_message(message.chat.id, msg.message_id)

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ حدث خطأ: {str(e)}")
        if os.path.exists(input_file): os.remove(input_file)
        if os.path.exists(output_file): os.remove(output_file)

# --- التشغيل النهائي ---
if __name__ == "__main__":
    # تشغيل الخادم الوهمي في خلفية الكود
    threading.Thread(target=run_dummy_server, daemon=True).start()
    
    # تحميل اللوجو المسبق: البوت يحتفظ باللوجو والإعدادات في الذاكرة
    print("🚀 Bot is Online with Dynamic Settings!")
    bot.polling(non_stop=True)
