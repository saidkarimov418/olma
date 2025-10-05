import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, InputMediaPhoto
import random
import sqlite3
from collections import defaultdict

# ==== BOT MA'LUMOTLARI ====
BOT_TOKEN = "8197561600:AAEKFiF2zSUcJiv2ygMBV_-zDGgXly4EtJY"
ADMIN_ID = 7584639843
CHANNEL_USERNAME = "@SOFT_BET1"

bot = telebot.TeleBot(BOT_TOKEN)

# ==== DB tayyorlash ====
conn = sqlite3.connect("soft.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    first_name TEXT,
    username TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS blocked_users (
    user_id INTEGER PRIMARY KEY
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS user_temp (
    user_id INTEGER PRIMARY KEY,
    kantora TEXT,
    photo1 TEXT,
    photo2 TEXT
)
""")
conn.commit()

# ==== KANTORA RASMLARI ====
kantora_images = {
    "1xbet": ["xbet1.jpg", "xbet2.jpg"],
    "Linebet": ["linebet1.jpg", "linebet2.jpg"],
    "Winwin": ["winwin1.jpg", "winwin2.jpg"],
    "Dbbet": ["dbbet1.jpg", "dbbet2.jpg"]
}

# ==== SIGNAL RASMLARI ====
signal_images = ["rasm1.jpg", "rasm2.jpg", "rasm3.jpg", "rasm4.jpg", "rasm5.jpg"]

# ==== FOYDALANUVCHI HOLATLARI ====
user_choices = {}
waiting_for_photos = set()
user_photos = defaultdict(list)
broadcast_mode = {}

# ==== LINKLAR ====
kantora_links = {
    "1xbet": "https://t.me/SOFT_BONUS/19",
    "Linebet": "https://t.me/SOFT_BONUS/7",
    "Winwin": "https://t.me/SOFT_BONUS/15",
    "Dbbet": "https://t.me/SOFT_BONUS/13"
}

# ==== BLOCK TEKSHIRISH ====
def is_blocked(user_id):
    cursor.execute("SELECT 1 FROM blocked_users WHERE user_id=?", (user_id,))
    return cursor.fetchone() is not None

# ==== KANTORA MENYUSI ====
def show_kantora_menu(chat_id):
    cursor.execute("SELECT 1 FROM blocked_users WHERE user_id = ?", (chat_id,))
    if cursor.fetchone():
        bot.send_message(chat_id, "🚫 Siz botdan bloklangansiz!\n❌ Kantora tanlash mumkin emas.")
        return

    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🔵 1xbet", callback_data="kantora_1xbet"),
        InlineKeyboardButton("🟢 Linebet", callback_data="kantora_Linebet")
    )
    markup.row(
        InlineKeyboardButton("🟢 Winwin", callback_data="kantora_Winwin"),
        InlineKeyboardButton("🔴 Dbbet", callback_data="kantora_Dbbet")
    )
    bot.send_message(chat_id, "✅ Obuna tasdiqlandi!\nQuyidagi kantoradan birini tanlang:", reply_markup=markup)

# ==== START ====
@bot.message_handler(commands=['start'])
def start_message(message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    username = message.from_user.username

    if is_blocked(user_id):
        bot.send_message(message.chat.id, "🚫 Siz botdan bloklangansiz.")
        return

    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id, first_name, username) VALUES (?, ?, ?)",
        (user_id, first_name, username)
    )
    conn.commit()

    try:
        status = bot.get_chat_member(CHANNEL_USERNAME, user_id).status
        if status in ["member", "administrator", "creator"]:
            show_kantora_menu(message.chat.id)
        else:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📢 Kanal", url=f"https://t.me/{CHANNEL_USERNAME.strip('@')}"))
            markup.add(InlineKeyboardButton("✅ Obunani tasdiqlash", callback_data="check_sub"))
            bot.send_message(
                message.chat.id,
                "🚫 Quyidagi kanalga obuna bo‘ling va tasdiqlang:",
                reply_markup=markup
            )
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Kanalni tekshirib bo‘lmadi:\n{e}")

# ==== OBUNA TEKSHIRISH ====
@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_subscription(call):
    try:
        status = bot.get_chat_member(CHANNEL_USERNAME, call.from_user.id).status
        if status in ["member", "administrator", "creator"]:
            bot.delete_message(call.message.chat.id, call.message.message_id)
            show_kantora_menu(call.message.chat.id)
        else:
            bot.answer_callback_query(call.id, "❌ Avval kanalga obuna bo‘ling!", show_alert=True)
    except:
        bot.answer_callback_query(call.id, "⚠️ Kanal topilmadi!", show_alert=True)

# ==== KANTORA TANLASH ====
@bot.callback_query_handler(func=lambda call: call.data.startswith("kantora_"))
def send_kantora(call):
    user_id = call.from_user.id
    if is_blocked(user_id):
        bot.answer_callback_query(call.id, "🚫 Siz botdan bloklangansiz!", show_alert=True)
        return

    kantora = call.data.split("_")[1]
    user_choices[user_id] = kantora

    cursor.execute("INSERT OR REPLACE INTO user_temp (user_id, kantora) VALUES (?, ?)", (user_id, kantora))
    conn.commit()

    imgs = kantora_images[kantora]
    caption = (
        f"📌 {kantora} 'Apple Of Fortune' uchun signal olish uchun:\n\n"
        "1️⃣ Maxsus APK orqali ro‘yxatdan o‘ting.\n"
        "2️⃣ Promokodni kiriting.\n"
        "3️⃣ 2 ta rasm yuboring (promokod bilan ekran)."
    )
    bot.send_photo(call.message.chat.id, open(imgs[0], "rb"), caption=caption)
    bot.send_photo(call.message.chat.id, open(imgs[1], "rb"))

    link = kantora_links.get(kantora, "https://t.me/SOFT_BONUS")
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📲 Ro‘yxatdan o‘tish", url=link))
    bot.send_message(call.message.chat.id, "👇 Quyidagi havolani bosing:", reply_markup=markup)

    waiting_for_photos.add(user_id)

# ==== FOYDALANUVCHI RASM YUBORSA ====
@bot.message_handler(content_types=['photo'])
def handle_photos(message):
    user_id = message.from_user.id
    username = message.from_user.username or ""

    if is_blocked(user_id):
        bot.send_message(message.chat.id, "🚫 Siz botdan bloklangansiz!")
        return

    if username.lower() == "none":
        bot.send_message(message.chat.id, "❌ Profilingizda username yo‘q! @username qo‘shing.")
        return

    if user_id in waiting_for_photos:
        file_id = message.photo[-1].file_id
        user_photos[user_id].append(file_id)

        # DB ga yozamiz
        cursor.execute("SELECT photo1, photo2 FROM user_temp WHERE user_id=?", (user_id,))
        row = cursor.fetchone()

        if not row:
            cursor.execute("INSERT INTO user_temp (user_id, photo1) VALUES (?, ?)", (user_id, file_id))
        elif row[0] is None:
            cursor.execute("UPDATE user_temp SET photo1=? WHERE user_id=?", (file_id, user_id))
        elif row[1] is None:
            cursor.execute("UPDATE user_temp SET photo2=? WHERE user_id=?", (file_id, user_id))
        conn.commit()

        # Agar 2 ta rasm bo‘lsa
        cursor.execute("SELECT kantora, photo1, photo2 FROM user_temp WHERE user_id=?", (user_id,))
        kantora, p1, p2 = cursor.fetchone()

        if p1 and p2:
            bot.send_message(message.chat.id, "✅ Tekshiruv boshlandi. Javob 5 daqiqa – 24 soat ichida keladi.")
            caption = (
                f"📩 Yangi foydalanuvchi!\n\n"
                f"👤 @{username}\n🆔 {user_id}\n🏢 Kantora: {kantora}\n\n👇 Tanlang:"
            )
            bot.send_photo(ADMIN_ID, p1)
            bot.send_photo(ADMIN_ID, p2, caption=caption)

            markup = InlineKeyboardMarkup()
            markup.row(
                InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve_{user_id}"),
                InlineKeyboardButton("❌ Bekor qilish", callback_data=f"cancel_{user_id}")
            )
            markup.add(InlineKeyboardButton("🚫 Block qilish", callback_data=f"block_{user_id}"))
            bot.send_message(ADMIN_ID, "👇 Harakatni tanlang:", reply_markup=markup)

            cursor.execute("DELETE FROM user_temp WHERE user_id=?", (user_id,))
            conn.commit()
            user_photos[user_id].clear()
    else:
        bot.send_message(message.chat.id, "❌ Hozir rasm yubora olmaysiz.")

# ==== ADMIN CALLBACKLAR ====
@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_"))
def approve_user(call):
    user_id = int(call.data.split("_")[1])
    if user_id in waiting_for_photos:
        waiting_for_photos.remove(user_id)
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("📡 Signal olish"))
    bot.send_message(user_id, "✅ Tasdiqlandi! Endi signal olishingiz mumkin.", reply_markup=markup)
    bot.answer_callback_query(call.id, "✅ Foydalanuvchi tasdiqlandi!")

@bot.callback_query_handler(func=lambda call: call.data.startswith("cancel_"))
def cancel_user(call):
    user_id = int(call.data.split("_")[1])
    waiting_for_photos.discard(user_id)
    bot.send_message(user_id, "❌ So‘rovingiz bekor qilindi.")
    bot.answer_callback_query(call.id, "❌ Bekor qilindi!")

@bot.callback_query_handler(func=lambda call: call.data.startswith("block_"))
def block_user(call):
    user_id = int(call.data.split("_")[1])
    waiting_for_photos.discard(user_id)
    cursor.execute("INSERT OR IGNORE INTO blocked_users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    try:
        bot.send_message(user_id, "🚫 Siz bloklandingiz!")
    except:
        pass
    bot.answer_callback_query(call.id, "🚫 Foydalanuvchi bloklandi!")

# ==== SIGNAL OLIB BERISH ====
@bot.message_handler(func=lambda msg: msg.text == "📡 Signal olish")
def send_signal(message):
    img = random.choice(signal_images)
    bot.send_photo(message.chat.id, open(img, "rb"), caption="📊 Mag‘lubiyatda stavkani 2x qiling!")

# ==== ADMIN PANEL ====
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id == ADMIN_ID:
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row("📊 Statistika", "✉️ Habar yuborish")
        markup.add("❌ Chiqish")
        bot.send_message(message.chat.id, "🔐 Admin panelga xush kelibsiz!", reply_markup=markup)

# ==== STATISTIKA ====
@bot.message_handler(func=lambda msg: msg.text == "📊 Statistika" and msg.from_user.id == ADMIN_ID)
def show_stats(message):
    cursor.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM blocked_users")
    blocked = cursor.fetchone()[0]
    active = total - blocked
    bot.send_message(message.chat.id, f"📊 Umumiy: {total}\n✅ Aktiv: {active}\n🚫 Bloklangan: {blocked}")

# ==== BARCHAGA XABAR ====
@bot.message_handler(func=lambda msg: msg.text == "✉️ Habar yuborish" and msg.from_user.id == ADMIN_ID)
def enable_broadcast(message):
    broadcast_mode[message.from_user.id] = True
    bot.send_message(message.chat.id, "✉️ Yuboriladigan xabarni kiriting (matn, rasm, video va h.k.)")

@bot.message_handler(content_types=['text', 'photo', 'video', 'voice', 'video_note', 'sticker', 'animation', 'document'])
def broadcast_message(message):
    if message.from_user.id == ADMIN_ID and broadcast_mode.get(message.from_user.id):
        cursor.execute("SELECT user_id FROM users")
        users = cursor.fetchall()
        sent, failed = 0, 0

        for (uid,) in users:
            try:
                if message.content_type == "text":
                    bot.send_message(uid, message.text)
                elif message.content_type == "photo":
                    bot.send_photo(uid, message.photo[-1].file_id, caption=message.caption or "")
                elif message.content_type == "video":
                    bot.send_video(uid, message.video.file_id, caption=message.caption or "")
                elif message.content_type == "voice":
                    bot.send_voice(uid, message.voice.file_id)
                elif message.content_type == "video_note":
                    bot.send_video_note(uid, message.video_note.file_id)
                elif message.content_type == "animation":
                    bot.send_animation(uid, message.animation.file_id)
                elif message.content_type == "document":
                    bot.send_document(uid, message.document.file_id)
                sent += 1
            except:
                failed += 1

        broadcast_mode[message.from_user.id] = False
        bot.send_message(message.chat.id, f"✅ Yuborildi: {sent}\n❌ Yetmadi: {failed}")

# ==== ISHGA TUSHIRISH ====
print("🤖 Bot ishga tushdi...")
bot.infinity_polling()
