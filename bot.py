import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
)
from admin_panel import handle_admin_actions, show_admin_panel
from services import show_services

# ==================== الإعدادات ====================
BOT_TOKEN = "6663550850:AAHgCWItUvQpIqr-1QDu94yYkDpf5mnlyV0"
ADMIN_ID = 5581457665
USERS_FILE = "users.json"
CONFIG_FILE = "config.json"

# ==================== اللوجات ====================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== تحميل المستخدمين ====================
try:
    with open(USERS_FILE, "r") as f:
        USERS = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    USERS = {}
    with open(USERS_FILE, "w") as f:
        json.dump(USERS, f)

# ==================== تحميل القنوات ====================
try:
    with open(CONFIG_FILE, "r") as f:
        CONFIG = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    CONFIG = {"channels": []}
    with open(CONFIG_FILE, "w") as f:
        json.dump(CONFIG, f)

# ==================== حفظ المستخدمين ====================
def save_users():
    with open(USERS_FILE, "w") as f:
        json.dump(USERS, f, indent=2)

# ==================== حفظ القنوات ====================
def save_config():
    with open(CONFIG_FILE, "w") as f:
        json.dump(CONFIG, f, indent=2)

# ==================== أوامر البوت ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    referrer_id = None

    # تحقق من رابط الدعوة
    if context.args:
        referrer_id = context.args[0]

    if user_id not in USERS:
        USERS[user_id] = {"points": 0, "orders": 0, "referrals": []}
        save_users()

        # تحقق من الدعوة
        if referrer_id and referrer_id in USERS and referrer_id != user_id:
            USERS[referrer_id]["points"] += 180
            USERS[referrer_id]["referrals"].append(user_id)
            save_users()
            await context.bot.send_message(
                chat_id=int(referrer_id),
                text=f"😂🎉 مبروك! دخل @{user.username or user.first_name} عبر رابط الدعوة الخاص بك وحصلت على 180 نقطة ⭐️"
            )

    # واجهة المستخدم
    keyboard = [
        [InlineKeyboardButton("💎 الخدمات", callback_data="services")],
        [InlineKeyboardButton("📥 تجميع النقاط", callback_data="earn_points")],
        [InlineKeyboardButton("ℹ️ معلوماتي", callback_data="my_info")]
    ]

    if str(user.id) == str(ADMIN_ID):
        keyboard.append([InlineKeyboardButton("⚙️✅ لوحة التحكم", callback_data="admin_panel")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🩵👋 أهلاً بك في البوت!", reply_markup=reply_markup)

# ==================== الأزرار ====================
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)

    if query.data == "services":
        await show_services(update, context)

    elif query.data == "earn_points":
        # زر مشاركة الرابط
        share_link = f"https://t.me/share/url?url=https://t.me/inirBOT?start={user_id}"
        keyboard = [
            [InlineKeyboardButton("💁🔗 مشاركة الرابط", url=share_link)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(
            "💡 شارك رابط الدعوة مع أصدقائك، وكل شخص جديد يسجل عبره يعطيك 180 نقطة ⭐️",
            reply_markup=reply_markup
        )

    elif query.data == "my_info":
        user_data = USERS.get(user_id, {"points": 0, "orders": 0, "referrals": []})
        points = user_data["points"]
        orders = user_data["orders"]
        referrals = len(user_data["referrals"])
        await query.message.reply_text(
            f"📊 معلوماتك:\n\n"
            f"🔹 النقاط: {points}\n"
            f"🔹 عدد الطلبات: {orders}\n"
            f"🔹 عدد الدعوات: {referrals}"
        )

    elif query.data == "admin_panel" and str(query.from_user.id) == str(ADMIN_ID):
        await show_admin_panel(update, context, CONFIG)

# ==================== تشغيل البوت ====================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_admin_actions, pattern="^add_channel|remove_channel|stats$"))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.run_polling()

if __name__ == "__main__":
    main()
