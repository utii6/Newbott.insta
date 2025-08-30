import json
import math
import requests
from fastapi import FastAPI, Request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

# -------------------------
# إعدادات البوت
# -------------------------
with open("config.json", "r") as f:
    config = json.load(f)

BOT_TOKEN = config["bot_token"]
API_KEY = config["api_key"]
ADMIN_ID = config["admin_id"]
API_URL = config["api_url"]
CHANNEL_ID = config["channel_id"]
MIN_ORDER = config["min_order"]
MAX_ORDER = config["max_order"]

# -------------------------
# المستخدمين والنقاط
# -------------------------
try:
    with open("users.json", "r") as f:
        users = json.load(f)
except:
    users = []

def save_users():
    with open("users.json", "w") as f:
        json.dump(users, f)

try:
    with open("points.json", "r") as f:
        points = json.load(f)
except:
    points = {}

def save_points():
    with open("points.json", "w") as f:
        json.dump(points, f)

# -------------------------
# الخدمات الجديدة
# -------------------------
SERVICES = {
    15454: "لايكات تيك توك سريعه 👍😂",
    13378: "مشاهدات تيك توك(مليون) 💁😂",
    12316: "لايكات انستا جديده ❗️😂",
    13723: "مشاهدات ريلز انستا(مليون) ▶️😂"
}

# -------------------------
# التحقق من الاشتراك
# -------------------------
async def check_subscription(user_id, context):
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# -------------------------
# أمر /start
# -------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    # تحقق من الاشتراك
    subscribed = await check_subscription(user_id, context)
    if not subscribed:
        await update.message.reply_text(
            f"⚠️ يجب الاشتراك في القناة {CHANNEL_ID} لاستخدام البوت"
        )
        return

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
• 😂عدد المشتركين الكلي: {len(users)}
"""
        await context.bot.send_message(chat_id=ADMIN_ID, text=msg)

    # أزرار الخدمات
    keyboard = [[InlineKeyboardButton(f"{sid}: {name}", callback_data=f"service_{sid}")]
                for sid, name in SERVICES.items()]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"أهلاً {user.full_name} 👋\nاختر الخدمة التي تريد استخدامها:",
        reply_markup=reply_markup
    )

# -------------------------
# التعامل مع الأزرار
# -------------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    # تحقق الاشتراك
    subscribed = await check_subscription(user_id, context)
    if not subscribed:
        await query.message.reply_text(
            f"⚠️↗️ يجب الاشتراك في القناة {CHANNEL_ID} لاستخدام البوت"
        )
        return

    if query.data.startswith("service_"):
        service_id = int(query.data.split("_")[1])
        context.user_data["selected_service"] = service_id
        await query.message.reply_text("😂✍️ أرسل رابط المنشور:")
        context.user_data["manual_step"] = 1

# -------------------------
# استقبال الرابط وعدد المشاهدات + النقاط
# -------------------------
async def input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # تحقق الاشتراك
    subscribed = await check_subscription(user_id, context)
    if not subscribed:
        await update.message.reply_text(
            f"⚠️ اشترك بالقناه حبيبي {CHANNEL_ID} 
        )
        return

    if "manual_step" in context.user_data:
        step = context.user_data["manual_step"]

        if step == 1:
            context.user_data["manual_link"] = update.message.text.strip()
            await update.message.reply_text("✍️😂 الآن أرسل العدد المطلوب:")
            context.user_data["manual_step"] = 2

        elif step == 2:
            try:
                quantity = int(update.message.text.strip())
                if quantity < MIN_ORDER or quantity > MAX_ORDER:
                    await update.message.reply_text(
                        f"❌😑 العدد يجب أن يكون بين {MIN_ORDER} و{MAX_ORDER}"
                    )
                    return

                # حساب النقاط المطلوبة
                required_points = math.ceil(quantity / 2)
                user_points = points.get(str(user_id), 0)
                if user_points < required_points:
                    await update.message.reply_text(
                        f"❌ ليس لديك رصيد كافي من النقاط. رصيدك الحالي: {user_points} نقطة"
                    )
                    return

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
                    # خصم النقاط
                    points[str(user_id)] = user_points - required_points
                    save_points()
                    await update.message.reply_text(
                        f"✅😂 تمت إضافة طلبك.\n🛠 الخدمة: {SERVICES[service_id]}"
                        f"\n📌 الرابط: {link}\n🔢 العدد: {quantity}\n"
                        f"🟢 النقاط المستهلكة: {required_points}\n💁رصيدك الحالي: {points[str(user_id)]} نقطة\n"
                        f"رقم الطلب: {res['order']}"
                    )
                else:
                    await update.message.reply_text(f"😑❌ فشل تنفيذ الطلب.\nالرد: {res}")
            except:
                await update.message.reply_text("❗️❌ يرجى إدخال رقم صحيح.")

            context.user_data.clear()

# -------------------------
# FastAPI + Webhook
# -------------------------
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"https://newbott-insta.onrender.com{WEBHOOK_PATH}"

fastapi_app = FastAPI()
application = Application.builder().token(BOT_TOKEN).build()

application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button_handler))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, input_handler))

@fastapi_app.on_event("startup")
async def startup():
    await application.bot.set_webhook(WEBHOOK_URL)
    await application.initialize()
    await application.start()

@fastapi_app.post(WEBHOOK_PATH)
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"ok": True}
