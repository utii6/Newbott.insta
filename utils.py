import json
from telegram.ext import ContextTypes  # تصحيح الاستيراد

# -------------------------
# نقاط المستخدمين
# -------------------------
try:
    with open("points.json", "r") as f:
        points = json.load(f)
except:
    points = {}

def save_points():
    with open("points.json", "w") as f:
        json.dump(points, f, indent=4)

# -------------------------
# المستخدمين
# -------------------------
try:
    with open("users.json", "r") as f:
        users = json.load(f)
except:
    users = []

def save_users():
    with open("users.json", "w") as f:
        json.dump(users, f, indent=4)

# -------------------------
# التحقق من الاشتراك في القناة
# -------------------------
async def check_subscription(user_id, context: ContextTypes.DEFAULT_TYPE):
    CHANNEL_ID = "@qd3qd"  # ضع هنا معرف قناتك
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False
