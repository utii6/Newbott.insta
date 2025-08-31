import json
import math
import requests
from fastapi import FastAPI, Request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)
from services import SERVICES, SERVICE_IDS
from admin_panel import admin_panel_buttons
from channels import CHANNELS
from utils import check_subscription, save_points, save_users, points, users
from config import BOT_TOKEN, API_KEY, ADMIN_ID, API_URL, CHANNEL_ID, MIN_ORDER, MAX_ORDER, START_POINTS

# -------------------------
# FastAPI + Webhook
# -------------------------
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"https://newbott-insta.onrender.com{WEBHOOK_PATH}"

fastapi_app = FastAPI()
application = Application.builder().token(BOT_TOKEN).build()

# -------------------------
# /start command
# -------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("تم الاتصال بالبوت بنجاح ✅")
    user_id = user.id

    # تحقق الاشتراك الاجباري
    subscribed = await check_subscription(user_id, context, CHANNEL_ID)
    if not subscribed:
        channel_button = [[InlineKeyboardButton("📢  مَـدار", url=f"https://t.me/{CHANNEL_ID}")]]
        channel_markup = InlineKeyboardMarkup(channel_button)
        await update.message.reply_text(
            f"⚠️ اشترك بالقناة {CHANNEL_ID} وارسل /start.",
            reply_markup=channel_markup
        )
        return

    # إضافة مستخدم جديد
    if user_id not in users:
        users.append(user_id)
        save_users()
        points[str(user_id)] = START_POINTS
        save_points()
        msg = f"""😂🚀 دخول نَفـرر جديد للبوت
-----------------------
• الاسم😂: {user.full_name}
• المعرف😎: @{user.username if user.username else 'لا يوجد'}
• الآيدي🆔: {user.id}
-----------------------
• عدد النفرات يمك: {len(users)}
• رصيد النقاط: {START_POINTS} نقطة
"""
        await context.bot.send_message(chat_id=ADMIN_ID, text=msg)

    # أزرار رئيسية: الخدمات + معلوماتي + تجميع نقاط
    main_buttons = [
        [InlineKeyboardButton("🛠 الخدمات", callback_data="show_services")],
        [InlineKeyboardButton("ℹ️ معلوماتي", callback_data="my_info")],
        [InlineKeyboardButton("🎁 تجميع النقاط", callback_data="collect_points")]
    ]
    main_markup = InlineKeyboardMarkup(main_buttons)
    await update.message.reply_text("أهلاً بك 😎 :", reply_markup=main_markup)

    # لوحة تحكم الأدمن
    if user_id == ADMIN_ID:
        await admin_panel_buttons(update, context)

# -------------------------
# Callback handler
# -------------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    # الاشتراك الاجباري
    subscribed = await check_subscription(user_id, context, CHANNEL_ID)
    if not subscribed:
        await query.message.reply_text(f"⚠️ اشترك بالقناة {CHANNEL_ID}")
        return

    # عرض الخدمات
    if query.data == "show_services":
        service_buttons = [[InlineKeyboardButton(name, callback_data=f"service_{key}")] for key, name in SERVICES.items()]
        await query.message.reply_text("😂اختر الخدمة:", reply_markup=InlineKeyboardMarkup(service_buttons))
        return

    # معلومات المستخدم
    if query.data == "my_info":
        user_points = points.get(str(user_id), 0)
        await query.message.reply_text(f"ℹ️ معلوماتك:\n• النقاط😂: {user_points}\n• عدد الطلبات😳: 0")
        return

    # تجميع النقاط
    if query.data == "collect_points":
        # زر مشاركة رابط الدعوة
        share_url = f"https://t.me/share/url?url=@inirBOT"
        share_buttons = [
            [InlineKeyboardButton("🔗 مشاركة رابط الدعوة", url=share_url)]
        ]
        # إضافة القنوات لتجميع نقاط الاشتراك
        for ch in CHANNELS:
            share_buttons.append([InlineKeyboardButton(f"اشترك بالقناة {ch['name']}", url=f"https://t.me/{ch['username']}")])
        await query.message.reply_text("😂🎁 تجميع النقاط:", reply_markup=InlineKeyboardMarkup(share_buttons))
        return

    # التعامل مع خدمات الطلب
    if query.data.startswith("service_"):
        service_key = query.data.split("_")[1]
        context.user_data["selected_service"] = service_key
        await query.message.reply_text("✍️😂 أرسل رابط المنشور:")
        context.user_data["manual_step"] = 1
        return

    # الأدمن
    if user_id == ADMIN_ID:
        await admin_panel_buttons(update, context, query_data=query.data)

# -------------------------
# استقبال الرسائل
# -------------------------
async def input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # التحقق من الاشتراك الاجباري
    subscribed = await check_subscription(user_id, context, CHANNEL_ID)
    if not subscribed:
        await update.message.reply_text(f"⚠️  اشترك حبيبي {CHANNEL_ID}")
        return

    # طلب الخدمة
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
                    await update.message.reply_text(f"❌😑 العدد يجب أن يكون بين {MIN_ORDER} و{MAX_ORDER}")
                    return
                service_key = context.user_data.get("selected_service")
                service_id = SERVICE_IDS.get(service_key)
                link = context.user_data.get("manual_link", "")
                data = {"key": API_KEY, "action": "add", "service": service_id, "link": link, "quantity": quantity}
                r = requests.post(API_URL, data=data).json()
                if "order" in r:
                    required_points = math.ceil(quantity / 2)
                    user_points = points.get(str(user_id), 0)
                    points[str(user_id)] = user_points - required_points
                    save_points()
                    await update.message.reply_text(f"✅😂 تم الطلب بنجاح\nخدمة: {SERVICES[service_key]}\nالرابط😂: {link}\nالعدد😂: {quantity}\nالنقاط المستهلكة😑: {required_points}\nرصيدك الحالي💁: {points[str(user_id)]}\nرقم الطلب: {r['order']}")
                else:
                    await update.message.reply_text(f"❌❗️ فشل تنفيذ الطلب.\nالرد: {r}")
            except:
                await update.message.reply_text("❌😑 أدخل رقم صالح")
            context.user_data.clear()

# -------------------------
# تشغيل البوت
# -------------------------
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button_handler))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, input_handler))


# -------------------------
# FastAPI Events
# -------------------------
@fastapi_app.on_event("startup")
async def startup():
    await application.bot.set_webhook(WEBHOOK_URL)
    await application.initialize()


# -------------------------
# Webhook Endpoint
# -------------------------
@fastapi_app.post(WEBHOOK_PATH)
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"ok": True}
