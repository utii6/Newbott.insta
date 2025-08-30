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
# المستخدمين والنقاط والبيانات
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
    with open("user_data.json", "r") as f:
        user_data = json.load(f)
except:
    user_data = {}

def save_user_data():
    with open("user_data.json", "w") as f:
        json.dump(user_data, f)

try:
    with open("channels.json", "r") as f:
        channels_list = json.load(f)
except:
    channels_list = []

def save_channels():
    with open("channels.json", "w") as f:
        json.dump(channels_list, f)

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

async def check_all_channels(user_id, context):
    for ch in channels_list:
        try:
            member = await context.bot.get_chat_member(ch, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

# -------------------------
# /start
# -------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    subscribed = await check_subscription(user_id, context)
    if not subscribed:
        channel_button = [[InlineKeyboardButton("📢مَـداار", url=f"https://t.me/{CHANNEL_ID}")]]
        await update.message.reply_text(
            f"⚠️❗️ اشترك بالقناة {CHANNEL_ID} لتتمكن من استخدام البوت",
            reply_markup=InlineKeyboardMarkup(channel_button)
        )
        return

    if user_id not in users:
        users.append(user_id)
        save_users()
        points[str(user_id)] = START_POINTS
        save_points()
        msg = f"""🚀💁 دخل نَفـرر جديد للبوت
-----------------------
• الاسم😂: {user.full_name}
• المعرف😎: @{user.username if user.username else 'لا يوجد'}
• الايدي🆔: {user.id}
-----------------------
• عدد متركينك 😂: {len(users)}
• رصيد النقاط: {START_POINTS} نقطة
"""
        await context.bot.send_message(chat_id=ADMIN_ID, text=msg)

    # أزرار الخدمات + زر معلوماتي + تجميع نقاط
    keyboard = [[InlineKeyboardButton("📊 معلوماتي", callback_data="my_info")]] + \
               [[InlineKeyboardButton(name, callback_data=key)] for key, name in SERVICES.items()] + \
               [[InlineKeyboardButton("💎 تجميع النقاط", callback_data="collect_points")]]
    await update.message.reply_text(
        f"أهلاً {user.full_name} 👋 اختر الخدمة :", 
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    # لوحة تحكم الأدمن
    if user_id == ADMIN_ID:
        admin_keyboard = [
            [InlineKeyboardButton("➕ إضافة قناة جديدة", callback_data="admin_add_channel")],
            [InlineKeyboardButton("😂💰 إضافة نقاط", callback_data="admin_add")],
            [InlineKeyboardButton("➖💔 سحب نقاط", callback_data="admin_remove")],
            [InlineKeyboardButton("📊 عرض رصيد المستخدمين", callback_data="admin_balance")]
        ]
        await update.message.reply_text(
            "🔧 لوحة تحكم المدير:", 
            reply_markup=InlineKeyboardMarkup(admin_keyboard)
        )

# -------------------------
# التعامل مع الأزرار
# -------------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    # التحقق من الاشتراك بالقناة الرئيسية
    subscribed = await check_subscription(user_id, context)
    if not subscribed:
        await query.message.reply_text(f"⚠️  اشترك حبيبي {CHANNEL_ID}")
        return

    # إدارة لوحة التحكم للأدمن
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
                await query.message.reply_text("😂✍️ أدخل معرف القناة أو رابطها:")
                context.user_data["admin_action"] = "add_channel"
                return

    # زر معلوماتي
    if query.data == "my_info":
        user_points = points.get(str(user_id), 0)
        user_orders = user_data.get(str(user_id), {}).get("orders", 0)
        last_service = user_data.get(str(user_id), {}).get("last_service", "لا يوجد")
        await query.message.reply_text(
            f"📊 معلوماتك:\n• النقاط: {user_points}\n• عدد الطلبات: {user_orders}\n• آخر خدمة: {last_service}"
        )
        return

    # زر تجميع النقاط
    if query.data == "collect_points":
        if not await check_all_channels(user_id, context):
            msg = "⚠️ يجب الاشتراك في جميع القنوات لإضافة النقاط:\n"
            for ch in channels_list:
                msg += f"• {ch}\n"
            await query.message.reply_text(msg)
            return
        await query.message.reply_text("😂🎉 يمكنك الآن استخدام النقاط لطلب الخدمات!")
        return

    # الخدمات
    if query.data in SERVICES:
        context.user_data["selected_service"] = query.data
        await query.message.reply_text("✍️😎 أرسل رابط المنشور:")
        context.user_data["manual_step"] = 1

# -------------------------
# استقبال الرسائل + تنفيذ الطلبات
# -------------------------
async def input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # الاشتراك بالقناة الرئيسية
    if not await check_subscription(user_id, context):
        await update.message.reply_text(f"⚠️  اشترك يالطيـب {CHANNEL_ID}")
        return

    # لوحة تحكم الأدمن
    if "admin_action" in context.user_data:
        action = context.user_data["admin_action"]
        if action in ["add", "remove"]:
            if "admin_user_id" not in context.user_data:
                try:
                    uid = int(update.message.text.strip())
                    context.user_data["admin_user_id"] = uid
                    await update.message.reply_text("✍️😎 الآن أرسل عدد النقاط:")
                    return
                except:
                    await update.message.reply_text("❌ أدخل رقم ID صالح")
                    return
            try:
                pts = int(update.message.text.strip())
                uid = context.user_data["admin_user_id"]
                if str(uid) not in points:
                    points[str(uid)] = 0
                if action == "add":
                    points[str(uid)] += pts
                    await update.message.reply_text(f"✅😂 تمت إضافة {pts} نقطة للمستخدم {uid}")
                else:
                    points[str(uid)] = max(0, points[str(uid)] - pts)
                    await update.message.reply_text(f"✅😂 تم خصم {pts} نقطة من المستخدم {uid}")
                save_points()
                context.user_data.pop("admin_action")
                context.user_data.pop("admin_user_id")
                return
            except:
                await update.message.reply_text("❌ أدخل رقم صالح للنقاط")
                return
        elif action == "add_channel":
            channel_id = update.message.text.strip()
            channels_list.append(channel_id)
            save_channels()
            await update.message.reply_text(f"😂✅ تم إضافة القناة: {channel_id}")
            context.user_data.pop("admin_action")
            return

    # خطوات الخدمة
    if "manual_step" in context.user_data:
        step = context.user_data["manual_step"]
        if step == 1:
            context.user_data["manual_link"] = update.message.text.strip()
            await update.message.reply_text("😎✍️ الآن أرسل العدد المطلوب:")
            context.user_data["manual_step"] = 2
        elif step == 2:
            try:
                quantity = int(update.message.text.strip())
                if quantity < MIN_ORDER or quantity > MAX_ORDER:
                    await update.message.reply_text(f"❌😂 العدد يجب أن يكون بين {MIN_ORDER} و {MAX_ORDER}")
                    return
                required_points = math.ceil(quantity / 2)
                user_points = points.get(str(user_id), 0)
                if user_points < required_points:
                    await update.message.reply_text(f"❌😂 ليس لديك رصيد كافي. رصيدك الحالي: {user_points} نقطة")
                    return
                link = context.user_data.get("manual_link")
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
                    points[str(user_id)] -= required_points
                    save_points()
                    # حفظ بيانات المستخدم
                    if str(user_id) not in user_data:
                        user_data[str(user_id)] = {"orders": 0, "last_service": ""}
                    user_data[str(user_id)]["orders"] += 1
                    user_data[str(user_id)]["last_service"] = SERVICES[service_key]
                    save_user_data()
                    await update.message.reply_text(
                        f"😂✅ تم الطلب بنجاح\n🛠 الخدمة: {SERVICES[service_key]}"
                        f"\n📌 الرابط: {link}\n🔢 العدد: {quantity}\n"
                        f"🟢 النقاط المستهلكة: {required_points}\nرصيدك الحالي😂: {points[str(user_id)]} نقطة\n"
                        f"🆔 رقم الطلب: {res['order']}"
                    )
                else:
                    await update.message.reply_text(f"❗️❌ فشل تنفيذ الطلب.\nالرد: {res}")
            except:
                await update.message.reply_text("😑❌ أدخل رقم صالح")
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
