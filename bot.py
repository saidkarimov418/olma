import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, InputMediaPhoto
import random
import sqlite3
from collections import defaultdict

# ==== BOT MA'LUMOTLARI ====
BOT_TOKEN = "8197561600:AAG4YP-FUfRr0D6wry3qpf68jZa4Ml8-DOU"
ADMIN_ID = 7584639843
CHANNEL_USERNAME = "@SOFT_BET1"

bot = telebot.TeleBot(BOT_TOKEN)

# ==== DATABASE ====
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

# ==== RASMLAR ====
kantora_images = {
    "1xbet": ["xbet1.jpg", "xbet2.jpg"],
    "Linebet": ["linebet1.jpg", "linebet2.jpg"],
    "Winwin": ["winwin1.jpg", "winwin2.jpg"],
    "Dbbet": ["dbbet1.jpg", "dbbet2.jpg"]
}
signal_images = ["rasm1.jpg", "rasm2.jpg", "rasm3.jpg", "rasm4.jpg", "rasm5.jpg"]

# ==== LINKLAR ====
kantora_links = {
    "1xbet": "https://t.me/SOFT_BONUS/19",
    "Linebet": "https://t.me/SOFT_BONUS/7",
    "Winwin": "https://t.me/SOFT_BONUS/15",
    "Dbbet": "https://t.me/SOFT_BONUS/13"
}

# === FOYDALANUVCHI HOLATLARI ===
user_choices = {}
waiting_for_photos = set()
user_photos = defaultdict(list)

# ==== BLOCK TEKSHIRUV ====
def is_blocked(user_id):
    cursor.execute("SELECT 1 FROM blocked_users WHERE user_id=?", (user_id,))
    return cursor.fetchone() is not None


# ==== START ====
@bot.message_handler(commands=['start'])
def start_message(message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    username = message.from_user.username

    if is_blocked(user_id):
        bot.send_message(user_id, "🚫 Siz botdan bloklangansiz.")
        return

    cursor.execute("INSERT OR IGNORE INTO users (user_id, first_name, username) VALUES (?, ?, ?)",
                   (user_id, first_name, username))
    conn.commit()

    try:
        status = bot.get_chat_member(CHANNEL_USERNAME, user_id).status
        if status in ["member", "administrator", "creator"]:
            show_kantora_menu(user_id)
        else:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📢 Kanal", url=f"https://t.me/{CHANNEL_USERNAME.strip('@')}"))
            markup.add(InlineKeyboardButton("✅ Obunani tasdiqlash", callback_data="check_sub"))
            bot.send_message(user_id,
                             "🚫 *Kanalga obuna bo‘ling.*\n\nA'zo bo‘lgach '✅ Obunani tasdiqlash' tugmasini bosing.",
                             parse_mode="Markdown", reply_markup=markup)
    except Exception as e:
        bot.send_message(user_id, f"❌ Kanal topilmadi yoki yopiq!\n\n{e}")


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
        bot.answer_callback_query(call.id, "❌ Kanal topilmadi yoki yopiq!", show_alert=True)


# ==== KANTORA MENYUSI ====
def show_kantora_menu(chat_id):
    if is_blocked(chat_id):
        bot.send_message(chat_id, "🚫 Siz botdan bloklangansiz!")
        return

    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🔵1xbet", callback_data="kantora_1xbet"),
        InlineKeyboardButton("🟢Linebet", callback_data="kantora_Linebet")
    )
    markup.row(
        InlineKeyboardButton("🟢Winwin", callback_data="kantora_Winwin"),
        InlineKeyboardButton("🔴Dbbet", callback_data="kantora_Dbbet")
    )
    bot.send_message(chat_id, "✅ Quyidagi kantoradan birini tanlang:", reply_markup=markup)


# ==== KANTORA TANLASH ====
@bot.callback_query_handler(func=lambda call: call.data.startswith("kantora_"))
def send_kantora(call):
    user_id = call.from_user.id
    if is_blocked(user_id):
        bot.answer_callback_query(call.id, "🚫 Siz botdan bloklangansiz!", show_alert=True)
        return

    kantora = call.data.split("_")[1]
    user_choices[user_id] = kantora

    imgs = kantora_images[kantora]
    caption = (
        f"📌 {kantora} 'Apple Of Fortune' uchun signal olish uchun:\n\n"
        f"1️⃣ LINK orqali ro‘yxatdan o‘ting.\n"
        f"2️⃣ Rasmda ko‘rsatilgan PROMOKODni kiriting.\n"
        f"3️⃣ Minimal depozit: 10 ming so‘m.\n\n"
        f"❗️2 ta rasm yuborishni unutmang!"
    )

    media = [InputMediaPhoto(open(imgs[0], "rb"), caption=caption),
             InputMediaPhoto(open(imgs[1], "rb"))]
    bot.send_media_group(call.message.chat.id, media)

    link = kantora_links.get(kantora, "https://t.me/SOFT_BONUS")
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Ro‘yxatdan o‘tish", url=link))
    bot.send_message(call.message.chat.id, "👇 Quyidagi havola orqali o‘ting:", reply_markup=markup)

    waiting_for_photos.add(user_id)
    cursor.execute("INSERT OR REPLACE INTO user_temp (user_id, kantora) VALUES (?, ?)", (user_id, kantora))
    conn.commit()


# ==== RASM QABUL QILISH ====
@bot.message_handler(content_types=['photo'])
def handle_photos(message):
    user_id = message.from_user.id
    username = message.from_user.username or "none"

    if is_blocked(user_id):
        bot.send_message(user_id, "🚫 Siz botdan bloklangansiz!")
        return

    if user_id not in waiting_for_photos:
        bot.send_message(user_id, "❌ Siz hozir rasm yubora olmaysiz.")
        return

    photo_id = message.photo[-1].file_id
    user_photos[user_id].append(photo_id)

    if len(user_photos[user_id]) == 1:
        cursor.execute("UPDATE user_temp SET photo1=? WHERE user_id=?", (photo_id, user_id))
    elif len(user_photos[user_id]) == 2:
        cursor.execute("UPDATE user_temp SET photo2=? WHERE user_id=?", (photo_id, user_id))
        conn.commit()

        bot.send_message(user_id, "✅ Rasmlar qabul qilindi! Tekshiruv jarayoni boshlandi ⏳")

        # Ma'lumotni bazadan olamiz
        cursor.execute("SELECT kantora, photo1, photo2 FROM user_temp WHERE user_id=?", (user_id,))
        data = cursor.fetchone()
        if data:
            kantora, p1, p2 = data
            caption = f"📩 Yangi foydalanuvchi!\n👤 @{username}\n🆔 {user_id}\n🏢 Kantora: {kantora}"

            bot.send_photo(ADMIN_ID, p1)
            bot.send_photo(ADMIN_ID, p2, caption=caption)

            markup = InlineKeyboardMarkup()
            markup.row(
                InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve_{user_id}"),
                InlineKeyboardButton("❌ Bekor qilish", callback_data=f"cancel_{user_id}")
            )
            markup.add(InlineKeyboardButton("🚫 Block qilish", callback_data=f"block_{user_id}"))
            bot.send_message(ADMIN_ID, "👇 Amaliyotni tanlang:", reply_markup=markup)

        waiting_for_photos.discard(user_id)
        user_photos[user_id].clear()


# ==== ADMIN CALLBACKLAR ====
@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_"))
def approve_user(call):
    user_id = int(call.data.split("_")[1])
    bot.send_message(user_id, "✅ Tekshiruv muvaffaqiyatli yakunlandi!\n📡 Endi signal olishingiz mumkin!")
    bot.answer_callback_query(call.id, "✅ Foydalanuvchi tasdiqlandi!")


@bot.callback_query_handler(func=lambda call: call.data.startswith("cancel_"))
def cancel_user(call):
    user_id = int(call.data.split("_")[1])
    bot.send_message(user_id, "❌ So‘rovingiz bekor qilindi.")
    bot.answer_callback_query(call.id, "❌ Bekor qilindi.")


@bot.callback_query_handler(func=lambda call: call.data.startswith("block_"))
def block_user(call):
    user_id = int(call.data.split("_")[1])
    cursor.execute("INSERT OR IGNORE INTO blocked_users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    bot.send_message(user_id, "🚫 Siz botdan bloklandingiz!")
    bot.answer_callback_query(call.id, "🚫 Foydalanuvchi bloklandi!")


# ==== SIGNAL YUBORISH ====
@bot.message_handler(func=lambda msg: msg.text == "📡 Signal olish")
def send_signal(message):
    img = random.choice(signal_images)
    bot.send_photo(message.chat.id, open(img, "rb"),
                   caption="📊 Agar stavkada mag‘lub bo‘lsangiz, keyingi stavkani 2 barobar oshiring!")


print("🤖 Bot ishga tushdi...")
bot.infinity_polling()
