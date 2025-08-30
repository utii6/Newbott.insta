from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def admin_keyboard_markup():
    keyboard = [
        [InlineKeyboardButton("😂💰 إضافة نقاط", callback_data="admin_add")],
        [InlineKeyboardButton("➖💔 سحب نقاط", callback_data="admin_remove")],
        [InlineKeyboardButton("📊😭 عرض رصيد المستخدمين", callback_data="admin_balance")],
        [InlineKeyboardButton("➕ إضافة قناة", callback_data="admin_add_channel")],
        [InlineKeyboardButton("➖ حذف قناة", callback_data="admin_remove_channel")]
    ]
    return InlineKeyboardMarkup(keyboard)
