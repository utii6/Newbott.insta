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
# القنوات لتجميع النقاط
# -------------------------
try:
    with open("channels.json", "r") as f:
        channels = json.load(f)
except:
    channels = []

def save_channels():
    with open("channels.json", "w") as f:
        json.dump(channels, f, ensure_ascii=False, indent=2)

# -------------------------
# الخدمات الجديدة
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
            f"⚠️ اشترك بالقناة يالطيب {CHANNEL_ID}  ",
            reply_markup=channel_markup
        )
        return

    if user_id not in users:
        users.append(user_id)
        save_users()
        points[str(user_id)] = START_POINTS
        save_points()
        msg = f"""🚀 دخول نَفـرر جديد للبوت
-----------------------
• الاسم😂: {user.full_name}
• المعرف😎: @{user.username if user.username else 'لا يوجد'}
• الآيدي🆔: {user.id}
-----------------------
• عدد الحلوين بالبوت💕: {len(users)}
•😂 رصيد النقاط: {START_POINTS} نقطة
"""
        await context.bot.send_message(chat_id=ADMIN_ID, text=msg)

    # أزرار الخدمات
    keyboard = [[InlineKeyboardButton(name, callback_data=key)] for key, name in SERVICES.items()]
    keyboard.append([InlineKeyboardButton("💎 تجميع النقاط", callback_data="collect_points")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"أهلاً {user.full_name} 😎👋\nاختر الخدمة أو تجميع النقاط:",
        reply_markup=reply_markup
    )

    # زر القناة الشفاف
    channel_button = [[InlineKeyboardButton("📢 مَـدار", url=f"https://t.me/{CHANNEL_ID}")]]
    channel_markup = InlineKeyboardMarkup(channel_button)
    await update.message.reply_text(
        "🔔  مَــدار  :",
        reply_markup=channel_markup
    )

    # لوحة تحكم للأدمن
    if user_id == ADMIN_ID:
        admin_keyboard = [
            [InlineKeyboardButton("😂💰 إضافة نقاط", callback_data="admin_add")],
            [InlineKeyboardButton("➖💔 سحب نقاط", callback_data="admin_remove")],
            [InlineKeyboardButton("📊😭 عرض رصيد المستخدمين", callback_data="admin_balance")],
            [InlineKeyboardButton("➕ إضافة قناة", callback_data="admin_add_channel")]
        ]
        admin_markup = InlineKeyboardMarkup(admin_keyboard)
        await update.message.reply_text(
            "🔧 لوحة تحكم المدير:",
            reply_markup=admin_markup
        )

# -------------------------
# زر تجميع النقاط
# -------------------------
async def collect_points(update, context):
    if not channels:
        await update.callback_query.message.reply_text("⚠️ لا توجد قنوات حالياً لتجميع النقاط.")
        return

    keyboard = [[InlineKeyboardButton(ch["name"], url=f"https://t.me/{ch['username']}")] for ch in channels]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text(
        "🔔 اختر القناة واشترك بها لتكسب نقاط:",
        reply_markup=reply_markup
    )

# -------------------------
# زر إضافة قناة (Admin)
# -------------------------
async def add_channel(update, context):
    user_id = update.callback_query.from_user.id
    if user_id != ADMIN_ID:
        await update.callback_query.message.reply_text("❌ هذا الزر خاص بالمدير فقط.")
        return

    await update.callback_query.message.reply_text("✍️ أدخل اسم القناة الجديد:")
    context.user_data["add_channel_step"] = "name"

async def channel_input_handler(update, context):
    if "add_channel_step" in context.user_data:
        step = context.user_data["add_channel_step"]
        if step == "name":
            context.user_data["new_channel_name"] = update.message.text.strip()
            await update.message.reply_text("✍️ أدخل معرف القناة بدون @:")
            context.user_data["add_channel_step"] = "username"
        elif step == "username":
            username = update.message.text.strip()
            name = context.user_data.get("new_channel_name")
            channels.append({"name": name, "username": username})
            save_channels()
            await update.message.reply_text(f"✅ تم إضافة القناة {name} بنجاح!")
            context.user_data.pop("add_channel_step", None)
            context.user_data.pop("new_channel_name", None)

# -------------------------
# التعامل مع الأزرار
# -------------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    subscribed = await check_subscription(user_id, context)
    if not subscribed:
        await query.message.reply_text(f"⚠️  مَـدار {CHANNEL_ID}")
        return

    # لوحة تحكم الأدمن
    if user_id == ADMIN_ID:
        if query.data.startswith("admin_"):
            action = query.data.split("_")[1]
            if action == "balance":
                msg = "😂💎 رصيد النقاط للمستخدمين:\n"
                for uid, pts in points.items():
                    msg += f"ID: {uid} → {pts} نقطة\n"
                await query.message.reply_text(msg)
                return
            elif action in ["add", "remove"]:
                await query.message.reply_text("✍️ أرسل ID المستخدم:")
                context.user_data["admin_action"] = action
                return
            elif action == "add_channel":
                await add_channel(update, context)
                return

    # زر تجميع النقاط
    if query.data == "collect_points":
        await collect_points(update, context)
        return

    # التعامل مع الخدمات
    if query.data in SERVICES:
        service_key = query.data
        context.user_data["selected_service"] = service_key
        await query.message.reply_text("✍️😂 أرسل رابط المنشور:")
        context.user_data["manual_step"] = 1

# -------------------------
# استقبال الرسائل + تنفيذ الطلبات
# -------------------------
async def input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # إدخال بيانات قناة جديدة
    await channel_input_handler(update, context)

    # باقي الكود الخاص بالنقاط والخدمات كما في النسخة السابقة
    # ... (يمكنك دمج بقية input_handler الخاصة بالطلبات والنقاط)

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
