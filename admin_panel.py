from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import json

CONFIG_FILE = "config.json"

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE, CONFIG):
    keyboard = [
        [InlineKeyboardButton("➕ إضافة قناة", callback_data="add_channel")],
        [InlineKeyboardButton("➖ حذف قناة", callback_data="remove_channel")],
        [InlineKeyboardButton("📊 إحصائيات", callback_data="stats")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text("⚙️😂 لوحة التحكم", reply_markup=reply_markup)

async def handle_admin_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    with open(CONFIG_FILE, "r") as f:
        CONFIG = json.load(f)

    if query.data == "add_channel":
        await query.message.reply_text("✍️😂 أرسل معرف القناة (مثال: @mychannel)")
        context.user_data["awaiting_channel"] = "add"

    elif query.data == "remove_channel":
        if CONFIG["channels"]:
            channels_list = "\n".join(CONFIG["channels"])
            await query.message.reply_text(f"📋 القنوات الحالية:\n{channels_list}\n\n✍️ أرسل المعرف الذي تريد حذفه")
            context.user_data["awaiting_channel"] = "remove"
        else:
            await query.message.reply_text("😑🚫 لا توجد قنوات مضافة حالياً.")

    elif query.data == "stats":
        await query.message.reply_text("😑📊 الإحصائيات ستتم إضافتها لاحقاً.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    text = update.message.text.strip()

    with open(CONFIG_FILE, "r") as f:
        CONFIG = json.load(f)

    if "awaiting_channel" in context.user_data:
        if context.user_data["awaiting_channel"] == "add":
            if text not in CONFIG["channels"]:
                CONFIG["channels"].append(text)
                save_config(CONFIG)
                await update.message.reply_text(f"😂✅ تم إضافة القناة: {text}")
            else:
                await update.message.reply_text("⚠️ ❗️القناة موجودة بالفعل.")

        elif context.user_data["awaiting_channel"] == "remove":
            if text in CONFIG["channels"]:
                CONFIG["channels"].remove(text)
                save_config(CONFIG)
                await update.message.reply_text(f"✅😂 تم حذف القناة: {text}")
            else:
                await update.message.reply_text("⚠️ القناة غير موجودة.")

        del context.user_data["awaiting_channel"]
