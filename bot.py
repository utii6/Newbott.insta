# bot.py

import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from services import SERVICES
from admin_panel import show_admin_panel, handle_admin_actions

CONFIG_FILE = "config.json"
USERS_FILE = "users.json"

with open(CONFIG_FILE, "r") as f:
    config = json.load(f)

BOT_TOKEN = config["bot_token"]
ADMIN_ID = config["admin_id"]

# تحميل بيانات المستخدمين
try:
    with open(USERS_FILE, "r") as f:
        USERS = json.load(f)
except FileNotFoundError:
    USERS = {}
    with open(USERS_FILE, "w") as f:
        json.dump(USERS, f)


def save_users():
    with open(USERS_FILE, "w") as f:
        json.dump(USERS, f)


# ✅ أمر /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "بدون معرف"

    if user_id not in USERS:
        USERS[user_id] = {"points": config["start_points"], "orders": 0, "referrals": 0}
        save_users()

    # لوحة التحكم للأدمن
    if int(user_id) == ADMIN_ID:
        await show_admin_panel(update, context)

    keyboard = [
        [InlineKeyboardButton("📦 الخدمات", callback_data="services")],
        [InlineKeyboardButton("⭐️ تجميع النقاط", callback_data="collect_points")],
        [InlineKeyboardButton("ℹ️ معلوماتي", callback_data="my_info")]
    ]
    await update.message.reply_text("👋 أهلاً بك في البوت!", reply_markup=InlineKeyboardMarkup(keyboard))


# ✅ التعامل مع الأزرار
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)

    if query.data == "services":
        keyboard = []
        for sid, name in SERVICES.items():
            keyboard.append([InlineKeyboardButton(name, callback_data=f"service_{sid}")])
        await query.message.reply_text("📦 اختر خدمة:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "my_info":
        user_data = USERS.get(user_id, {"points": 0, "orders": 0, "referrals": 0})
        await query.message.reply_text(
            f"ℹ️ معلوماتك:\n"
            f"🛒 عدد الطلبات: {user_data['orders']}\n"
            f"⭐️ نقاطك: {user_data['points']}\n"
            f"👥 الدعوات: {user_data['referrals']}"
        )

    elif query.data == "collect_points":
        share_link = f"https://t.me/share/url?url=https://t.me/inirBOT?start={user_id}"
        keyboard = [
            [InlineKeyboardButton("😑📢 مشاركة الرابط", url=share_link)]
        ]
        await query.message.reply_text(
            "⭐️ اجمع النقاط عبر دعوة أصدقائك!\n"
            "كل شخص يسجل عبر رابطك يمنحك 180 نقطة ✅",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data.startswith("service_"):
        sid = query.data.split("_")[1]
        await query.message.reply_text(f"😂✅ اخترت الخدمة: {SERVICES[sid]}")


# ✅ متابعة الدعوات (referrals)
async def check_referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    args = context.args

    if args:
        ref_id = args[0]
        if ref_id != user_id and ref_id in USERS:
            USERS[ref_id]["points"] += 180
            USERS[ref_id]["referrals"] += 1
            save_users()
            await context.bot.send_message(
                chat_id=int(ref_id),
                text=f"✅⭐️ مبروك! دخل {update.effective_user.username} عبر رابطك وحصلت على 180 نقطة."
            )


# ✅ تشغيل البوت
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("start", check_referral))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.add_handler(CallbackQueryHandler(handle_admin_actions))

    app.run_polling()


if __name__ == "__main__":
    main()
