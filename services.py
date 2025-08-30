from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

SERVICES = {
    "tiktok_likes": "لايكات تيك توك سريعة 👍😂",
    "tiktok_views": "مشاهدات تيك توك (مليون) 💁😂",
    "insta_likes": "لايكات انستا جديدة ❗️😂",
    "insta_reels": "مشاهدات ريلز انستا (مليون) ▶️😂"
}

async def show_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    for service_id, service_name in SERVICES.items():
        keyboard.append([InlineKeyboardButton(service_name, callback_data=f"service_{service_id}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text("😎💎 اختر الخدمة:", reply_markup=reply_markup)
