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
START_POINTS = config.get("start_points", 100)
BOT_USERNAME = "inirBOT"

# -------------------------
# المستخدمين والنقاط والطلبات
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

try:
    with open("requests.json", "r") as f:
        requests_count = json.load(f)
except:
    requests_count = {}

try:
    with open("channels.json", "r") as f:
        channels = json.load(f)
except:
    channels = {}  # {"@channel": points_per_sub}

def save_channels():
    with open("channels.json", "w") as f:
        json.dump(channels, f)

try:
    with open("referrals.json", "r") as f:
        referrals = json.load(f)
except:
    referrals = {}  # {"new_user_id": "referrer_id"}

def save_referrals():
    with open("referrals.json", "w") as f:
        json.dump(referrals, f)

# -------------------------
# الخدمات
# -------------------------
SERVICES = {
    "like_tiktok": "لايكات تيك توك سريعه 👍😂",
    "views_tiktok": "مشاهدات تيك توك(مليون) 💁😂",
    "like_insta": "لايكات انستا جديده ❗️😂",
    "views_reels": "مشاهدات ريلز انستا(مليون) ▶️😂"
}

SERVICE_IDS = {
    "like_tiktok": 15454,
    "views_tiktok": 13378,
    "like_insta": 12316,
    "views_reels": 13723
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

    subscribed = await check_subscription(user_id, context)
    if not subscribed:
        channel_button = [[InlineKeyboardButton("📢  مَـدار", url=f"https://t.me/{CHANNEL_ID}")]]
        channel_markup = InlineKeyboardMarkup(channel_button)
        await update.message.reply_text(
            f"⚠️ اشترك بالقناة {CHANNEL_ID} يالطيب",
            reply_markup=channel_markup
        )
        return

    if user_id not in users:
        users.append(user_id)
        save_users()
        points[str(user_id)] = START_POINTS
        save_points()
        requests_count[str(user_id)] = 0
        msg = f"""🚀 دخول نَفـرر جديد للبوت
-----------------------
• الاسم😂: {user.full_name}
• المعرف😎: @{user.username if user.username else 'لا يوجد'}
• الآيدي🆔: {user.id}
-----------------------
• عدد المشتركين الحلوين: {len(users)}
• رصيد النقاط: {START_POINTS} نقطة
"""
        await context.bot.send_message(chat_id=ADMIN_ID, text=msg)

    # أزرار الخدمات
    keyboard = [[InlineKeyboardButton(name, callback_data=key)] for key, name in SERVICES.items()]
    keyboard.append([InlineKeyboardButton("🟢 تجميع النقاط", callback_data="collect_points")])
    keyboard.append([InlineKeyboardButton("ℹ️ معلوماتي", callback_data="my_info")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"أهلاً {user.full_name} 👋 اختر الخدمه:",
        reply_markup=reply_markup
    )

# -------------------------
# التعامل مع الأزرار
# -------------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    subscribed = await check_subscription(user_id, context)
    if not subscribed:
        await query.message.reply_text(
            f"⚠️ اشترك بالقناة {CHANNEL_ID}"
        )
        return

    # لوحة التحكم للأدمن
    if user_id == ADMIN_ID:
        if query.data == "admin_add_channel":
            await query.message.reply_text("✍️ أرسل معرف القناة الجديدة (@username):")
            context.user_data["admin_action"] = "add_channel"
            return
        elif query.data == "admin_remove_channel":
            if not channels:
                await query.message.reply_text("لا توجد قنوات لإزالتها.")
                return
            keyboard = [[InlineKeyboardButton(name, callback_data=f"remove_{name}")] for name in channels.keys()]
            await query.message.reply_text("اختر القناة لحذفها:", reply_markup=InlineKeyboardMarkup(keyboard))
            context.user_data["admin_action"] = "remove_channel"
            return
        elif query.data.startswith("remove_") and context.user_data.get("admin_action") == "remove_channel":
            ch = query.data.replace("remove_", "")
            if ch in channels:
                channels.pop(ch)
                save_channels()
                await query.message.reply_text(f"✅ تم حذف القناة {ch}")
            return

    # تجميع النقاط
    if query.data == "collect_points":
        if not channels:
            await query.message.reply_text("❌ لا توجد قنوات حالياً لتجميع النقاط.")
            return
        keyboard = [[InlineKeyboardButton(f"اشترك في {ch} (+{pts} نقطة)", url=f"https://t.me/{ch}")] for ch, pts in channels.items()]
        keyboard.append([InlineKeyboardButton("📤 شارك رابط الدعوة (+180 نقطة)", url=f"https://t.me/share/url?url=@{BOT_USERNAME}")])
        await query.message.reply_text("اختر طريقة لتجميع النقاط:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # معلوماتي
    if query.data == "my_info":
        user_points = points.get(str(user_id), 0)
        user_requests = requests_count.get(str(user_id), 0)
        msg = f"""ℹ️ معلوماتك:
- النقاط الحالية: {user_points}
- عدد الطلبات: {user_requests}
"""
        await query.message.reply_text(msg)
        return

    # الخدمات
    if query.data in SERVICES:
        service_key = query.data
        context.user_data["selected_service"] = service_key
        await query.message.reply_text("✍️ أرسل رابط المنشور:")
        context.user_data["manual_step"] = 1

# -------------------------
# استقبال الرسائل + تنفيذ الطلبات
# -------------------------
async def input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    subscribed = await check_subscription(user_id, context)
    if not subscribed:
        await update.message.reply_text(
            f"⚠️ اشترك بالقناة {CHANNEL_ID}"
        )
        return

    # إدارة إضافة قناة للأدمن
    if "admin_action" in context.user_data:
        action = context.user_data["admin_action"]
        if action == "add_channel":
            ch = update.message.text.strip()
            if not ch.startswith("@"):
                await update.message.reply_text("❌ يجب أن يبدأ معرف القناة بـ @")
                return
            channels[ch] = 10  # يمكن تحديد نقاط افتراضية لكل قناة
            save_channels()
            await update.message.reply_text(f"✅ تم إضافة القناة {ch}")
            context.user_data.pop("admin_action")
            return

    # خطوات الخدمة
    if "manual_step" in context.user_data:
        step = context.user_data["manual_step"]
        if step == 1:
            context.user_data["manual_link"] = update.message.text.strip()
            await update.message.reply_text("✍️ الآن أرسل العدد المطلوب:")
            context.user_data["manual_step"] = 2
        elif step == 2:
            try:
                quantity = int(update.message.text.strip())
                if quantity < MIN_ORDER or quantity > MAX_ORDER:
                    await update.message.reply_text(f"❌ العدد يجب أن يكون بين {MIN_ORDER} و{MAX_ORDER}")
                    return
                required_points = math.ceil(quantity / 2)
                user_points = points.get(str(user_id), 0)
                if user_points < required_points:
                    await update.message.reply_text(f"❌ ليس لديك رصيد كافي. رصيدك الحالي: {user_points} نقطة")
                    return
                link = context.user_data.get("manual_link", "")
                service_key = context.user_data.get("selected_service")
                service_id = SERVICE_IDS.get(service_key)
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
                    points[str(user_id)] = user_points - required_points
                    requests_count[str(user_id)] = requests_count.get(str(user_id), 0) + 1
                    save_points()
                    with open("requests.json", "w") as f:
                        json.dump(requests_count, f)
                    await update.message.reply_text(
                        f"✅ تم الطلب بنجاح\n🛠 الخدمة: {SERVICES[service_key]}"
                        f"\n📌 الرابط: {link}\n🔢 العدد: {quantity}"
                        f"\n🟢 النقاط المستهلكة: {required_points}\nرصيدك الحالي: {points[str(user_id)]} نقطة\n"
                        f"🆔 رقم الطلب: {res['order']}"
                    )
                else:
                    await update.message.reply_text(f"❌ فشل تنفيذ الطلب.\nالرد: {res}")
            except:
                await update.message.reply_text("❌ أدخل رقم صالح")
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
