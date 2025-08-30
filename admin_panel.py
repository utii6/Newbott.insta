# admin_panel.py

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# -------------------------
# دالة ترجع أزرار لوحة تحكم الأدمن
# -------------------------
def admin_panel_buttons():
    keyboard = [
        [InlineKeyboardButton("😂💰 إضافة نقاط", callback_data="admin_add")],
        [InlineKeyboardButton("➖💔 سحب نقاط", callback_data="admin_remove")],
        [InlineKeyboardButton("📊😭 عرض رصيد المستخدمين", callback_data="admin_balance")],
        [InlineKeyboardButton("➕📢 إدارة القنوات", callback_data="admin_channels")]
    ]
    return InlineKeyboardMarkup(keyboard)

# -------------------------
# دالة لإرسال رسالة لوحة التحكم للأدمن
# -------------------------
async def send_admin_panel(update, context):
    from bot import ADMIN_ID  # تأكد أن ADMIN_ID موجود في config
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        await update.message.reply_text(
            "🔧 لوحة تحكم المدير:",
            reply_markup=admin_panel_buttons()
        )
