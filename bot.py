import json
import requests
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ContextTypes
)

# ========= الإعدادات =========
BOT_TOKEN = "6663550850:AAHgCWItUvQpIqr-1QDu94yYkDpf5mnlyV0"
ADMIN_ID = 5581457665   # ايديك
CHANNEL_ID = "@qd3qd"   # قناة الاشتراك الإجباري
API_KEY = "81db6d6480686d9da6f35ff2cf6a30b4"

# ملف المستخدمين
USERS_FILE = "users.json"

# تحميل بيانات المستخدمين
try:
    with open(USERS_FILE, "r") as f:
        users = json.load(f)
except FileNotFoundError:
    users = {}

# حفظ المستخدمين
def save_users():
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

# ========= الخدمات =========
SERVICES = {
    "15454": "لايكات تيك توك سريعه 👍😂",
    "13378": "مشاهدات تيك توك (مليون) 💁😂",
    "12316": "لايكات انستا جديده ❗️😂",
    "13723": "مشاهدات ريلز انستا (مليون) ▶️😂"
}

# ========= التحقق من الاشتراك =========
async def check_subscription(user_id, context):
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# ========= أوامر =========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)

    # تحقق من وجود المستخدم
    if user_id not in users:
        users[user_id] = {
            "points": 0,
            "orders": 0,
            "referrals": 0
        }
        # تحقق من وجود إحالة
        if context.args:
            ref = context.args[0]
            if ref.startswith("ref_"):
                ref_id = ref.replace("ref_", "")
                if ref_id in users and ref_id != user_id:
                    users[ref_id]["points"] += 180
                    users[ref_id]["referrals"] += 1
                    await context.bot.send_message(
                        chat_id=ref_id,
                        text=f"🎉😂 مبروك! دخل {user.mention_html()} من خلال رابطك.\nحصلت على ⭐️ 180 نقطة.",
                        parse_mode="HTML"
                    )
        save_users()

    # تحقق من الاشتراك
    subscribed = await check_subscription(user.id, context)
    if not subscribed:
        keyboard = [[InlineKeyboardButton("📢  مَـداار", url=f"https://t.me/{CHANNEL_ID[1:]}")]]
        await update.message.reply_text(
            f"⚠️ عذراً {user.first_name}, اشترك وارسل /start.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # القائمة الرئيسية
    keyboard = [
        [InlineKeyboardButton("😂🛠 الخدمات", callback_data="services")],
        [InlineKeyboardButton("📊 معلوماتي", callback_data="myinfo")],
        [InlineKeyboardButton("⭐️ تجميع النقاط", callback_data="collect_points")]
    ]
    if str(user.id) == str(ADMIN_ID):
        keyboard.append([InlineKeyboardButton("⚙️😂 لوحة التحكم", callback_data="admin_panel")])

    await update.message.reply_text(
        "👋 أهلاً بك في البوت.\n :",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ========= ردود الأزرار =========
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)

    # تحقق من الاشتراك
    subscribed = await check_subscription(query.from_user.id, context)
    if not subscribed:
        keyboard = [[InlineKeyboardButton("📢  مَـدار", url=f"https://t.me/{CHANNEL_ID[1:]}")]]
        await query.edit_message_text(
            "⚠️    اشترك يالطيـب.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if query.data == "services":
        keyboard = [[InlineKeyboardButton(name, callback_data=f"order_{sid}")]
                    for sid, name in SERVICES.items()]
        await query.edit_message_text("😂اختر خدمة:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "myinfo":
        u = users.get(user_id, {"points": 0, "orders": 0, "referrals": 0})
        await query.edit_message_text(
            f"👤 معلوماتك:\n\n"
            f"🔹 النقاط: {u['points']}\n"
            f"😂🔹 عدد الطلبات: {u['orders']}\n"
            f"🔹 عدد الإحالات: {u['referrals']}"
        )

    elif query.data == "collect_points":
        keyboard = [
            [InlineKeyboardButton("📢💰 اشترك بالقنوات", callback_data="join_channels")],
            [InlineKeyboardButton("🔗😎 مشاركة رابط الدعوة", url=f"https://t.me/share/url?url=https://t.me/inirBOT?start=ref_{user_id}")]
        ]
        await query.edit_message_text("⭐️✅ طرق تجميع النقاط:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "admin_panel" and str(query.from_user.id) == str(ADMIN_ID):
        keyboard = [
            [InlineKeyboardButton("➕ اضافة قناة", callback_data="add_channel")],
            [InlineKeyboardButton("📊 احصائيات", callback_data="stats")]
        ]
        await query.edit_message_text("😂⚙️ لوحة التحكم:", reply_markup=InlineKeyboardMarkup(keyboard))

    else:
        await query.edit_message_text("🚧 لم يتم برمجة هذا الزر بعد.")

# ========= التشغيل =========
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler))

print("✅ البوت يعمل الآن...")
app.run_polling()
