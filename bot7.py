import os
import re
import time
import html
import threading
import urllib.request
from datetime import date
from flask import Flask
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Environment Variables မှ Token နှင့် Admin ID ယူခြင်း
BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
ADMIN_ID = os.environ.get("ADMIN_ID", "").strip() or None

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN မတွေ့ပါ! Render ၏ Environment Variables တွင် BOT_TOKEN ထည့်ပေးပါ။")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
app = Flask(__name__)

# အချက်အလက်နှင့် Link များ
KPAY_NUMBER = "09764199664"
KPAY_NAME = "Min Zayar Oo"
VIP_CHANNEL_LINK = "https://t.me/+Mv6q6XQxeRJhNjM1"
BOT_LINK = "http://t.me/translatemoviesken_bot"

daily_members_log = {}

# ----------------------------------------------------
# ၁။ Web Server နှင့် ၂၄ နာရီ Auto-Ping စနစ်
# ----------------------------------------------------
@app.route('/')
def home():
    return "Translate Movies VIP Bot is Live!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, use_reloader=False)

def keep_alive_ping():
    while True:
        time.sleep(600)
        url = os.environ.get("RENDER_EXTERNAL_URL")
        if url:
            try:
                urllib.request.urlopen(url, timeout=10)
            except Exception as e:
                print(f"Ping error: {e}")

# ----------------------------------------------------
# ၂။ Helper Functions နှင့် Buttons
# ----------------------------------------------------
def get_user_display(user):
    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    safe_name = html.escape(full_name) if full_name else "Customer"
    if user.username:
        return f"{safe_name} (@{html.escape(user.username)})"
    return safe_name

def get_customer_buttons():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("🎥 1 Movie – 1,000 Ks", callback_data="pkg_1"),
        InlineKeyboardButton("🎥 10 Movies – 5,000 Ks (Old Member 50% Off)", callback_data="pkg_10"),
        InlineKeyboardButton("🎥 20 Movies – 6,000 Ks", callback_data="pkg_20"),
        InlineKeyboardButton("📢 VIP Channel Join Request ရန်", url=VIP_CHANNEL_LINK),
    )
    return markup

def get_admin_action_buttons(user_id):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("✅ Approve လုပ်ပြီး", callback_data=f"approve_{user_id}"),
        InlineKeyboardButton("⚠️ Slip ပြန်ပို့ခိုင်းရန်", callback_data=f"reject_{user_id}"),
    )
    return markup

def build_price_list_message(user):
    display_name = get_user_display(user)
    return (
        f"မင်္ဂလာပါ <b>{display_name}</b> ခင်ဗျာ 🙏\n\n"
        f"🎬 <b>VIP MEMBER PRICE LIST</b> 🎬\n\n"
        f"📌 <b>VIP ဇာတ်ကားဈေးနှုန်းများ</b>\n"
        f"🎥 1 Movie – <b>1,000 Ks</b>\n"
        f"🎥 10 Movies – <b>5,000 Ks</b>\n"
        f"🎥 20 Movies – <b>6,000 Ks</b>\n\n"
        f"📍 <b>မှတ်ချက်</b>\n"
        f"အထူးဇာတ်ကားအချို့သည် <b>2,000 Ks</b> ကျသင့်နိုင်ပါသည်။\n\n"
        f"━━━━━━━━━━━━━━\n\n"
        f"🎁 <b>OLD MEMBER SPECIAL DISCOUNT</b>\n"
        f"မန်ဘာအဟောင်းများအတွက် အထူးလျှော့ဈေးအစီအစဉ် ရှိပါသည်။ ❤️\n"
        f"✨ 10 Movies ဝယ်ယူပါက <b>50% Discount</b> ရရှိပါမည်။\n\n"
        f"━━━━━━━━━━━━━━\n\n"
        f"💳 <b>KPay ငွေလွှဲရန်</b>\n"
        f"📱 KPay Number – <code>{KPAY_NUMBER}</code>\n"
        f"👤 Account Name – <b>{KPAY_NAME}</b>\n\n"
        f"⚠️ <b>အရေးကြီးအသိပေးချက်</b>\n"
        f"ငွေလွှဲပြီးပါက <b>ငွေလွှဲပြေစာ (Payment Slip)</b> ကို မဖြစ်မနေ ပေးပို့ပေးရန် လိုအပ်ပါသည်။\n"
        f"ငွေလွှဲပြေစာ ပေးပို့ထားသော Order များကိုသာ လက်ခံဆောင်ရွက်ပေးသွားမည် ဖြစ်ပါသည်။\n\n"
        f"━━━━━━━━━━━━━━\n\n"
        f"📢 <b>VIP CHANNEL JOIN ရန်</b>\n"
        f"အောက်ပါ Link မှတစ်ဆင့် Channel Join Request ပေးပို့ထားပေးပါ။\n"
        f"🔗 {VIP_CHANNEL_LINK}\n\n"
        f"━━━━━━━━━━━━━━\n\n"
        f"📩 <b>ဆက်သွယ်ရန်</b>\n"
        f"Telegram – {BOT_LINK}\n\n"
        f"❤️ အားပေးမှုအတွက် အထူးကျေးဇူးတင်ရှိပါသည်။"
    )

# ----------------------------------------------------
# ၃။ Admin Commands (/admin, /today)
# ----------------------------------------------------
@bot.message_handler(commands=['admin'])
def set_admin(message):
    global ADMIN_ID
    ADMIN_ID = str(message.chat.id)
    bot.reply_to(
        message,
        f"✅ <b>Admin အဖြစ် သတ်မှတ်ပြီးပါပြီ!</b>\n"
        f"🆔 Admin ID: <code>{ADMIN_ID}</code>\n\n"
        f"⚙️ <b>Command များ -</b>\n"
        f"• /today - ယနေ့ Bot ထဲ ဝင်ရောက်လာသူများ စာရင်းကြည့်ရန်",
        disable_web_page_preview=True,
    )

@bot.message_handler(commands=['today'])
def show_today_members(message):
    if ADMIN_ID and str(message.chat.id) != str(ADMIN_ID):
        return
    today_str = str(date.today())
    members = daily_members_log.get(today_str, set())
    if not members:
        bot.reply_to(message, f"📅 ယနေ့ ({today_str}) Bot ထဲသို့ ဝင်ရောက်လာသူ မရှိသေးပါ။")
    else:
        member_list = "\n".join(f"• {name}" for name in members)
        bot.reply_to(
            message,
            f"📅 <b>ယနေ့ ({today_str}) ဝင်ရောက်လာသူများ ({len(members)} ဦး):</b>\n\n{member_list}",
        )

# ----------------------------------------------------
# ၄။ Callback ခလုတ်များ
# ----------------------------------------------------
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    data = call.data

    if data in ("pkg_1", "pkg_10", "pkg_20"):
        pkg_map = {
            "pkg_1": ("1 Movie", "1,000 Ks"),
            "pkg_10": ("10 Movies", "5,000 Ks (Old Member 50% Discount = 2,500 Ks)"),
            "pkg_20": ("20 Movies", "6,000 Ks"),
        }
        pkg_name, price_text = pkg_map[data]
        bot.answer_callback_query(call.id, f"{pkg_name} ရွေးချယ်ပြီးပါပြီ")
        bot.send_message(
            call.message.chat.id,
            f"🎬 <b>ရွေးချယ်ထားသော Package:</b> {pkg_name}\n"
            f"💰 <b>ကျသင့်ငွေ:</b> {price_text}\n\n"
            f"💳 <b>KPay ငွေလွှဲရန် -</b>\n"
            f"📱 KPay Number – <code>{KPAY_NUMBER}</code>\n"
            f"👤 Account Name – <b>{KPAY_NAME}</b>\n\n"
            f"⚠️ ငွေလွှဲပြီးပါက <b>Payment Slip (SS)</b> ကို ဒီ Bot ဆီသို့ ပို့ပေးပြီး "
            f"အောက်ပါ VIP Channel တွင် Join Request နှိပ်ထားပေးပါ -\n"
            f"🔗 {VIP_CHANNEL_LINK}",
            disable_web_page_preview=True,
        )
        return

    if ADMIN_ID and str(call.message.chat.id) != str(ADMIN_ID):
        return

    if data.startswith("approve_"):
        target_id = int(data.split("_")[1])
        try:
            bot.send_message(
                target_id,
                f"🎉 <b>ဂုဏ်ယူပါတယ်ခင်ဗျာ!</b>\n\n"
                f"✅ လူကြီးမင်း၏ Payment Slip ကို Admin မှ စစ်ဆေးအတည်ပြုပြီးပါပြီ။\n"
                f"📢 VIP Channel တွင် Join Request မနှိပ်ရသေးပါက နှိပ်ထားပေးပါ -\n"
                f"🔗 {VIP_CHANNEL_LINK}",
                disable_web_page_preview=True,
            )
            bot.answer_callback_query(call.id, "✅ Approve စာပို့ပြီးပါပြီ!")
            if call.message.text:
                bot.edit_message_text(
                    call.message.text + "\n\n✅ [Admin မှ Approve စာပို့ပြီးပါပြီ]",
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                )
        except Exception as e:
            bot.answer_callback_query(call.id, f"ပို့မရပါ: {e}", show_alert=True)

    elif data.startswith("reject_"):
        target_id = int(data.split("_")[1])
        try:
            bot.send_message(
                target_id,
                "⚠️ <b>Admin မှ အကြောင်းကြားစာ</b>\n\n"
                "လူကြီးမင်း ပေးပို့ထားသော Payment Slip ပုံမရှင်းလင်းပါသဖြင့် "
                "<b>ငွေလွှဲပြေစာ (Payment Slip)</b> ကို ပြန်လည်ပေးပို့ပေးပါခင်ဗျာ 🙏",
            )
            bot.answer_callback_query(call.id, "⚠️ ပြေစာပြန်ပို့ခိုင်းသည့်စာ ပို့ပြီးပါပြီ!")
            if call.message.text:
                bot.edit_message_text(
                    call.message.text + "\n\n⚠️ [Slip ပြန်ပို့ရန် အကြောင်းကြားပြီးပါပြီ]",
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                )
        except Exception as e:
            bot.answer_callback_query(call.id, f"ပို့မရပါ: {e}", show_alert=True)

# ----------------------------------------------------
# ၅။ /start နှင့် /help
# ----------------------------------------------------
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user = message.from_user
    display_name = get_user_display(user)

    today_str = str(date.today())
    daily_members_log.setdefault(today_str, set()).add(display_name)

    if ADMIN_ID and str(message.chat.id) != str(ADMIN_ID):
        try:
            bot.send_message(
                ADMIN_ID,
                f"🔔 <b>Customer အသစ် Bot ကို စတင်နှိပ်လိုက်ပါသည်</b>\n"
                f"👤 အမည်: {display_name}\n"
                f"🆔 User ID: <code>{user.id}</code>",
            )
        except Exception as e:
            print(f"Notify admin error: {e}")

    bot.reply_to(
        message,
        build_price_list_message(user),
        reply_markup=get_customer_buttons(),
        disable_web_page_preview=True,
    )

# ----------------------------------------------------
# ၆။ Payment Slip (Photo / Document) လက်ခံခြင်း
# ----------------------------------------------------
@bot.message_handler(content_types=['photo', 'document'])
def handle_media(message):
    user = message.from_user
    display_name = get_user_display(user)
    caption = html.escape(message.caption) if message.caption else "မှတ်ချက်စာသား မပါပါ"

    if ADMIN_ID and str(message.chat.id) != str(ADMIN_ID):
        try:
            bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
            bot.send_message(
                ADMIN_ID,
                f"🧾 <b>Payment Slip အသစ်ရောက်ရှိလာပါသည်!</b>\n"
                f"👤 ပေးပို့သူ: {display_name}\n"
                f"🆔 User ID: <code>{user.id}</code>\n"
                f"📝 မှတ်ချက်: {caption}\n\n"
                f"💡 <i>(ဤစာကို Reply ထောက်ပြီး Customer ဆီ စာပြန်နိုင်ပါသည်)</i>",
                reply_markup=get_admin_action_buttons(user.id),
            )
        except Exception as e:
            print(f"Forward media error: {e}")

    bot.reply_to(
        message,
        f"ကျေးဇူးတင်ပါတယ် <b>{display_name}</b> ခင်ဗျာ 🙏\n\n"
        f"✅ လူကြီးမင်း ပေးပို့သော <b>ငွေလွှဲပြေစာ (Payment Slip)</b> ကို Admin ထံ ပေးပို့ထားပြီး ဖြစ်ပါသည်။\n"
        f"ငွေလွှဲပြေစာ ပေးပို့ထားသော Order များကို စစ်ဆေးပြီး ဆောင်ရွက်ပေးသွားပါမည်ဗျ။\n\n"
        f"📢 <b>VIP CHANNEL JOIN ရန် -</b>\n"
        f"🔗 {VIP_CHANNEL_LINK}",
        reply_markup=get_customer_buttons(),
        disable_web_page_preview=True,
    )

# ----------------------------------------------------
# ၇။ စာသားများနှင့် Admin Reply
# ----------------------------------------------------
def extract_target_user_id(reply_msg):
    if reply_msg.forward_from:
        return reply_msg.forward_from.id
    text_to_search = reply_msg.text or reply_msg.caption or ""
    match = re.search(r"User ID:\s*(\d+)", text_to_search)
    return int(match.group(1)) if match else None

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user = message.from_user
    display_name = get_user_display(user)

    if ADMIN_ID and str(message.chat.id) == str(ADMIN_ID):
        if message.reply_to_message:
            target_id = extract_target_user_id(message.reply_to_message)
            if target_id:
                try:
                    bot.send_message(
                        target_id,
                        f"📩 <b>Admin မှ အကြောင်းကြားစာ -</b>\n\n{html.escape(message.text)}",
                    )
                    bot.reply_to(message, "✅ Customer ဆီသို့ စာပို့ပြီးပါပြီ။")
                    return
                except Exception as e:
                    bot.reply_to(message, f"❌ ပို့မရပါ: {e}")
                    return

    if ADMIN_ID and str(message.chat.id) != str(ADMIN_ID):
        try:
            bot.send_message(
                ADMIN_ID,
                f"💬 <b>Customer ဆီမှ စာအသစ် ရောက်ရှိလာပါသည်</b>\n"
                f"👤 ပေးပို့သူ: {display_name}\n"
                f"🆔 User ID: <code>{user.id}</code>\n"
                f"✉️ စာသား: {html.escape(message.text)}\n\n"
                f"💡 <i>(ဤစာကို Reply ထောက်ပြီး Customer ဆီ စာပြန်နိုင်ပါသည်)</i>",
            )
        except Exception as e:
            print(f"Forward text error: {e}")

    bot.reply_to(
        message,
        build_price_list_message(user),
        reply_markup=get_customer_buttons(),
        disable_web_page_preview=True,
    )

# ----------------------------------------------------
# ၈။ Bot စတင်ခြင်း (Error တက်လည်း မရပ်သွားအောင်)
# ----------------------------------------------------
def start_bot_polling():
    while True:
        try:
            bot.remove_webhook()
            time.sleep(2)
            print("Bot စတင်အလုပ်လုပ်နေပါပြီ...")
            bot.infinity_polling(timeout=20, long_polling_timeout=10)
        except Exception as e:
            print(f"Polling error (restarting in 5s): {e}")
            time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    threading.Thread(target=keep_alive_ping, daemon=True).start()
    start_bot_polling()
