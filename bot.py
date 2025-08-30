import json
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    CallbackQueryHandler, MessageHandler, filters
)

# -------------------------
# تحميل الإعدادات
# -------------------------
with open("config.json", "r") as f:
    config = json.load(f)

BOT_TOKEN = config["bot_token"]
API_KEY = config["api_key"]
ADMIN_ID = config["admin_id"]
API_URL = config["api_url"]

# -------------------------
# تخزين المستخدمين
# -------------------------
try:
    with open("users.json", "r") as f:
        users = json.load(f)
except:
    users = []

def save_users():
    with open("users.json", "w") as f:
        json.dump(users, f)

# -------------------------
# الخدمات
# -------------------------
SERVICES = {
    13021: "مشاهدات تيك توك رخيصه 😎",
    13400: "مشاهدات انستا رخيصه 🅰️",
    14527: "مشاهدات تلي ✅",
    15007: "لايكات تيك توك جوده عاليه 💎",
    14676: "لايكات انستا سريعه قويه وجوده عاليه 😎👍"
}

# -------------------------
# أمر /start
# -------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    # إضافة المستخدم إذا جديد
    if user_id not in users:
        users.append(user_id)
        save_users()
        msg = f"""🚀 دخول نفـرر جديد للبوت
-----------------------
• الاسم😂: {user.full_name}
• المعرف😎: @{user.username if user.username else 'لا يوجد'}
• الآيدي🆔: {user.id}
-----------------------
• عدد مشتركينك الكلي: {len(users)}
"""
        await context.bot.send_message(chat_id=ADMIN_ID, text=msg)

    # أزرار الخدمات
    keyboard = [[InlineKeyboardButton(f"{sid}: {name}", callback_data=f"service_{sid}")]
                for sid, name in SERVICES.items()]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"أهلاً {user.full_name} 👋\nاختر الخدمة  :",
        reply_markup=reply_markup
    )

# -------------------------
# التعامل مع الأزرار
# -------------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("service_"):
        service_id = int(query.data.split("_")[1])
        context.user_data["selected_service"] = service_id
        await query.message.reply_text("✍️😂 أرسل رابط المنشور:")
        context.user_data["manual_step"] = 1

# -------------------------
# استقبال روابط + عدد المشاهدات/اللايكات
# -------------------------
async def input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # خطوات اختيار الخدمة
    if "manual_step" in context.user_data:
        step = context.user_data["manual_step"]

        if step == 1:
            context.user_data["manual_link"] = update.message.text.strip()
            await update.message.reply_text("✍️😂 الآن أرسل العدد المطلوب:")
            context.user_data["manual_step"] = 2

        elif step == 2:
            try:
                quantity = int(update.message.text.strip())
                link = context.user_data.get("manual_link", "")
                service_id = context.user_data.get("selected_service")

                data = {
                    "key": API_KEY,
                    "action": "add",
                    "service": service_id,
                    "link": link,
                    "quantity": quantity
                }
                r = requests.post(API_URL, data=data)
                res = r.json()

                if "order" in res:
                    await update.message.reply_text(
                        f"😂✅ تمت إضافة طلبك.\n🛠 الخدمة: {SERVICES[service_id]}\n📌 الرابط: {link}\n🔢 😎العدد: {quantity}\nرقم الطلب: {res['order']}"
                    )
                else:
                    await update.message.reply_text(f"😑❌ فشل تنفيذ الطلب.\nالرد: {res}")
            except:
                await update.message.reply_text("❌ يرجى إدخال رقم صحيح.")

            context.user_data.pop("manual_step", None)
            context.user_data.pop("manual_link", None)
            context.user_data.pop("selected_service", None)

# -------------------------
# تشغيل البوت
# -------------------------
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, input_handler))

app.run_polling()
