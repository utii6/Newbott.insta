import json
import os

# -------------------------
# تحميل/حفظ بيانات المستخدمين والنقاط
# -------------------------
USERS_FILE = "users.json"
POINTS_FILE = "points.json"

if os.path.exists(USERS_FILE):
    with open(USERS_FILE, "r") as f:
        users = json.load(f)
else:
    users = {}

if os.path.exists(POINTS_FILE):
    with open(POINTS_FILE, "r") as f:
        points = json.load(f)
else:
    points = {}


def save_users():
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)


def save_points():
    with open(POINTS_FILE, "w") as f:
        json.dump(points, f)


# -------------------------
# فحص الاشتراك الإجباري
# -------------------------
async def check_subscription(user_id, context, channel_id):
    """
    يتحقق إذا كان المستخدم مشترك في القناة الإلزامية
    """
    try:
        member = await context.bot.get_chat_member(channel_id, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        return False
