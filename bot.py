import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import random
from collections import defaultdict
import sqlite3
# Bot token va admin ID
BOT_TOKEN = "7904634489:AAEkhLW00VLlebw0lc82Qa3Vs3TqIq4pI_w"
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
conn.commit()

conn.commit()






# Random signal rasmlar
# signal_images = ["rasm1.jpg", "rasm2.jpg", "rasm3.jpg", "rasm4.jpg", "rasm5.jpg"]

# Foydalanuvchi tanlagan kantorani saqlash
user_choices = {}
waiting_for_photos = set()

# ==== Kantoralar rasmlari ====
kantora_images = {
    "DbBet": ["dbbet1.jpg", "dbbet2.jpg"],
    "Betwinner": ["betwinner1.jpg", "betwinner2.jpg"],
    "Mosbet": ["mosbet1.jpg"],   # faqat 1 ta rasm
    "1xbet": ["xbet1.jpg", "xbet2.jpg"],
    "Melbet": ["melbet1.jpg", "melbet2.jpg"]
}

# ==== Har bir kantoraga alohida link ====
kantora_links = {
    "DbBet": "https://t.me/SOFT_BONUS/20",
    "Betwinner": "https://t.me/SOFT_BONUS/14",
    "Mosbet": "https://t.me/SOFT_BONUS/18",
    "1xbet": "https://t.me/SOFT_BONUS/19",
    "Melbet": "https://t.me/SOFT_BONUS/6"
}


# ==== Kantora tanlash menyusi ====
def show_kantora_menu(chat_id):
    # Avval block qilinganmi tekshiramiz
    cursor.execute("SELECT 1 FROM blocked_users WHERE user_id = ?", (chat_id,))
    if cursor.fetchone():
        bot.send_message(chat_id, "🚫 Siz botdan bloklangansiz!\n\n❌ Kantora tanlash mumkin emas.")
        return

    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🟢 Db Bet", callback_data="kantora_DbBet"),
        InlineKeyboardButton("🟣 Betwinner", callback_data="kantora_Betwinner")
    )
    markup.row(
        InlineKeyboardButton("🟡 Mosbet", callback_data="kantora_Mosbet"),
        InlineKeyboardButton("🔵 1xbet", callback_data="kantora_1xbet")
    )
    markup.row(
        InlineKeyboardButton("🔴 Melbet", callback_data="kantora_Melbet")
    )

    bot.send_message(
        chat_id,
        "✅ Obuna tasdiqlandi!\n\nQuyidagi kantoradan birini tanlang:",
        reply_markup=markup
    )



# ==== BLOCK tekshiruv funksiyasi ====
def is_blocked(user_id):
    cursor.execute("SELECT 1 FROM blocked_users WHERE user_id=?", (user_id,))
    return cursor.fetchone() is not None


# ==== START komandasi ====
@bot.message_handler(commands=['start'])
def start_message(message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    username = message.from_user.username

    # 🚫 Agar user block qilingan bo‘lsa → hech narsa ishlamasin
    if is_blocked(user_id):
        bot.send_message(message.chat.id, "🚫 Siz botdan bloklangansiz.")
        return

    # ✅ Agar user bazada bo‘lmasa → qo‘shib qo‘yamiz
    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id, first_name, username) VALUES (?, ?, ?)",
        (user_id, first_name, username)
    )
    conn.commit()

    try:
        # 🔍 Kanalga obuna bo‘lganini tekshiramiz
        status = bot.get_chat_member(CHANNEL_USERNAME, user_id).status
        if status in ["member", "administrator", "creator"]:
            show_kantora_menu(message.chat.id)
        else:
            markup = InlineKeyboardMarkup()
            markup.add(
                InlineKeyboardButton("📢 Kanal", url=f"https://t.me/{CHANNEL_USERNAME.strip('@')}")
            )
            markup.add(
                InlineKeyboardButton("✅ Obunani tasdiqlash", callback_data="check_sub")
            )
            text = (
                "🚫 *Quyidagi kanalimizga obuna bo'ling.*\n\n"
                "A'zo bo‘lib '✅ Obunani tasdiqlash' tugmasini bosing, "
                "shunda botdan to‘liq foydalanishingiz mumkin."
            )
            bot.send_message(
                message.chat.id,
                text,
                reply_markup=markup,
                parse_mode="Markdown"
            )
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Kanal topilmadi yoki yopiq!\n\n{e}")

# ==== Obunani tekshirish ====
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


# ==== Kantora tanlash ====
from telebot.types import InputMediaPhoto

# Har bir kantoraga alohida link


@bot.callback_query_handler(func=lambda call: call.data.startswith("kantora_"))
def send_kantora(call):
    user_id = call.from_user.id

    # 🚫 Agar blokda bo‘lsa → hech narsa qilmaymiz
    if is_blocked(user_id):
        bot.answer_callback_query(call.id, "🚫 Siz botdan bloklangansiz!", show_alert=True)
        return

    kantora = call.data.split("_")[1]
    user_choices[user_id] = kantora
    imgs = kantora_images[kantora]

    caption = (
        f"📌 {kantora} 'Apple Of Fortune' o'yinida siz uchun mahsus SIGNAL tayyorlashim uchun...\n\n"
        f"Mahsus LINK orqali APKni yuklab oling va ro‘yxatdan o‘ting.\n\n"
        f"❗️Eski akkaunt ishlamaydi, faqat yangi ro‘yxatdan o‘tganlarga signal to‘g‘ri ko‘rsatadi!\n\n"
        f"1. Ro‘yxatdan o‘tishda 'rasm'dagi promocodni kiriting.\n\n❗️Minimal depozit 10 ming so'm"
        f"\n\n❗️ESLATMA: 2 ta rasm yuboring va promokodni kiritishni unutmang!"
    )

    imgs = kantora_images[kantora]

    media = []
    if len(imgs) == 1:
        media.append(InputMediaPhoto(open(imgs[0], "rb"), caption=caption))
    else:
        media.append(InputMediaPhoto(open(imgs[0], "rb"), caption=caption))
        media.append(InputMediaPhoto(open(imgs[1], "rb")))

    bot.send_media_group(call.message.chat.id, media)

    link = kantora_links.get(kantora, "https://t.me/SOFT_BONUS")

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Ro‘yxatdan o‘tish", url=link))
    bot.send_message(call.message.chat.id, "Maxsus apk orqali ro‘yxatdan o‘ting 👇", reply_markup=markup)

    waiting_for_photos.add(user_id)



# ==== Foydalanuvchi rasm yuborsa ====
user_photos = defaultdict(list)


# ==== Foydalanuvchi rasm yuborsa ====
@bot.message_handler(content_types=['photo'])
def handle_photos(message):
    if message.from_user.id in waiting_for_photos:
        kantora = user_choices.get(message.from_user.id, "Noma'lum")

        # Rasmlarni vaqtincha saqlaymiz
        user_photos[message.from_user.id].append(message.photo[-1].file_id)

        # Agar 2 ta rasm yig‘ilsa → admin paneliga yuboramiz
        if len(user_photos[message.from_user.id]) == 2:
            bot.send_message(message.chat.id,
                             "✅ Tekshiruv boshlandi.\n⏳ Bu jarayon 5 daqiqadan 24 soatgacha davom etadi.\n\n"
                             "❗️ Botni bloklamang, aks holda signal ololmaysiz!")

            caption = (
                f"📩 Yangi foydalanuvchi rasm yubordi!\n\n"
                f"👤 User: @{message.from_user.username}\n"
                f"🆔 ID: {message.from_user.id}\n"
                f"🏢 Kantora: {kantora}\n\n"
                f"👇 Quyida tugmalardan birini tanlang:"
            )

            media = [
                InputMediaPhoto(user_photos[message.from_user.id][0]),
                InputMediaPhoto(user_photos[message.from_user.id][1], caption=caption)
            ]

            # Rasm guruhini yuboramiz
            bot.send_media_group(ADMIN_ID, media)

            # Tugmalar
            # ==== Foydalanuvchi rasm yuborganda admin tugmalari ====
            markup = InlineKeyboardMarkup()
            markup.row(
                InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve_{message.from_user.id}"),
                InlineKeyboardButton("❌ Bekor qilish", callback_data=f"cancel_{message.from_user.id}")
            )
            markup.add(
                InlineKeyboardButton("🚫 Block qilish", callback_data=f"block_{message.from_user.id}")
            )

            bot.send_message(ADMIN_ID, "👇 Amaliyotni tanlang:", reply_markup=markup)

            # Tozalab tashlaymiz
            user_photos[message.from_user.id].clear()

from telebot.types import WebAppInfo

# ==== Signal rasmlari (15 ta) ====
signal_images = [f"olma{i}.jpg" for i in range(1, 15)]


# ==== ADMIN tasdiqlasa ====
@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_"))
def approve_user(call):
    user_id = int(call.data.split("_")[1])

    # Foydalanuvchini kutish ro‘yxatidan o‘chiramiz
    if user_id in waiting_for_photos:
        waiting_for_photos.remove(user_id)

    # ✅ Oddiy keyboard tugma
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("📡 Signal olish"))

    bot.send_message(
        user_id,
        "✅ Tekshiruv muvaffaqiyatli yakunlandi!\n📡 Endi '📡 Signal olish' tugmasini bosing va random signal oling:",
        reply_markup=markup
    )

    bot.answer_callback_query(call.id, "✅ Foydalanuvchi tasdiqlandi!")


# ==== Signal tugmasi bosilganda ====
@bot.message_handler(func=lambda msg: msg.text == "📡 Signal olish")
def send_signal(message):
    img = random.choice(signal_images)
    caption = "📊 Signal olindi! Stavkada yutqazsangiz keyingi stavkani 2 barobar qiling."
    bot.send_photo(message.chat.id, open(img, "rb"), caption=caption)


@bot.callback_query_handler(func=lambda call: call.data.startswith("cancel_"))
def cancel_user(call):
    user_id = int(call.data.split("_")[1])

    # Kutishdan o‘chiramiz
    if user_id in waiting_for_photos:
        waiting_for_photos.remove(user_id)

    bot.send_message(user_id, "❌ So‘rovingiz bekor qilindi.")
    bot.answer_callback_query(call.id, "❌ So‘rov bekor qilindi!")


@bot.callback_query_handler(func=lambda call: call.data.startswith("block_"))
def block_user(call):
    user_id = int(call.data.split("_")[1])

    # Kutishdan o‘chiramiz
    if user_id in waiting_for_photos:
        waiting_for_photos.remove(user_id)

    # Block jadvaliga qo‘shamiz
    cursor.execute("INSERT OR IGNORE INTO blocked_users (user_id) VALUES (?)", (user_id,))
    conn.commit()

    try:
        bot.send_message(user_id, "🚫 Siz botdan bloklandingiz! Endi hech qanday funksiyadan foydalana olmaysiz.")
    except:
        pass

    bot.answer_callback_query(call.id, "🚫 Foydalanuvchi bloklandi!")


# ==== Signal tugmasi bosilganda ====
@bot.message_handler(func=lambda msg: msg.text == "📡 Signal olish")
def send_signal(message):
    img = random.choice(signal_images)
    caption = "📊 Agar stavkada mag‘lubiyat bo‘lsa, keyingi stavkani 2 barobar oshiring!"
    bot.send_photo(message.chat.id, open(img, "rb"), caption=caption)



# ==== ADMIN PANEL ====
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id == ADMIN_ID:
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row("📊 Statistika", "✉️ Habar yuborish")
        markup.add("❌ Chiqish")
        bot.send_message(message.chat.id, "🔐 Admin panelga xush kelibsiz!", reply_markup=markup)


# ==== Statistika ====
@bot.message_handler(func=lambda msg: msg.text == "📊 Statistika" and msg.from_user.id == ADMIN_ID)
def show_stats(message):
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()

    total = len(users)
    active = 0
    blocked = 0

    for (user_id,) in users:
        try:
            bot.send_chat_action(user_id, "typing")
            active += 1
        except:
            blocked += 1

    text = (
        f"📊 Statistika:\n\n"
        f"👥 Umumiy foydalanuvchilar: {total}\n"
        f"✅ Aktiv: {active}\n"
        f"⛔️ Block qilganlar: {blocked}"
    )
    bot.send_message(message.chat.id, text)


# ==== Habar yuborish ====
broadcast_mode = {}

# ✉️ Habar yuborish tugmasi
@bot.message_handler(func=lambda msg: msg.text == "✉️ Habar yuborish" and msg.from_user.id == ADMIN_ID)
def enable_broadcast(message):
    broadcast_mode[message.from_user.id] = True
    bot.send_message(message.chat.id, "✉️ Yubormoqchi bo‘lgan xabarni kiriting (matn, rasm, video, ovozli, GIF, sticker, hujjat, premium emoji...)")

# Barcha turdagi kontentlarni ushlash
@bot.message_handler(content_types=['text', 'photo', 'video', 'voice', 'video_note', 'sticker', 'animation', 'document'])
def broadcast_message(message):
    if message.from_user.id == ADMIN_ID and broadcast_mode.get(message.from_user.id):
        cursor.execute("SELECT user_id FROM users")
        users = cursor.fetchall()

        sent = 0
        failed = 0

        for (user_id,) in users:
            try:
                if message.content_type == "text":
                    # Premium emoji ham text sifatida ketadi
                    bot.send_message(user_id, message.text)
                elif message.content_type == "photo":
                    bot.send_photo(user_id, message.photo[-1].file_id, caption=message.caption or "")
                elif message.content_type == "video":
                    bot.send_video(user_id, message.video.file_id, caption=message.caption or "")
                elif message.content_type == "voice":
                    bot.send_voice(user_id, message.voice.file_id, caption=message.caption or "")
                elif message.content_type == "video_note":
                    bot.send_video_note(user_id, message.video_note.file_id)
                elif message.content_type == "sticker":
                    bot.send_sticker(user_id, message.sticker.file_id)
                elif message.content_type == "animation":
                    bot.send_animation(user_id, message.animation.file_id, caption=message.caption or "")
                elif message.content_type == "document":
                    bot.send_document(user_id, message.document.file_id, caption=message.caption or "")
                sent += 1
            except Exception as e:
                failed += 1
                # Xohlasa log qilishingiz mumkin
                # print(f"Xato {user_id}: {e}")

        broadcast_mode[message.from_user.id] = False
        bot.send_message(
            message.chat.id,
            f"✅ Yuborildi: {sent}\n❌ Yetib bormadi: {failed}"
        )

    elif message.from_user.id == ADMIN_ID and message.text == "❌ Chiqish":
        broadcast_mode[message.from_user.id] = False
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        bot.send_message(message.chat.id, "❌ Admin paneldan chiqdingiz", reply_markup=markup)



print("🤖 Bot ishga tushdi...")
bot.infinity_polling()
