import os
import re
import time
import html
import threading
import urllib.request
from flask import Flask
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# False = VIP ဖွင့်ထားသည် (မန်ဘာလက်ခံမည်) / True = VIP ခဏပိတ်ထားမည်
VIP_CLOSED = False

# အချက်အလက်များနှင့် Link အသစ်များ
MEMBER_PRICE = "5,000 Ks"
KPAY_NUMBER = "09764199664"
KPAY_NAME = "Min Zayar Oo"
FREE_GROUP_LINK = "https://t.me/translatemoviesken"     # Free အတွက် link
VIP_GROUP_LINK = "https://t.me/+9DtdlPnxAKcxZWI1"       # Privacy (VIP) group အတွက် link

@app.route('/')
def home():
    status = "CLOSED" if VIP_CLOSED else "OPEN"
    return f"Translate Movies Bot is running 24/7! Current Status: {status}"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def keep_alive_ping():
    while True:
        time.sleep(600)
        url = os.environ.get("RENDER_EXTERNAL_URL")
        if url:
            try:
                urllib.request.urlopen(url, timeout=10)
            except Exception as e:
                print(f"Ping error: {e}")

def get_user_display(user):
    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    safe_name = html.escape(full_name) if full_name else "Customer"
    if user.username:
        return f"{safe_name} (@{html.escape(user.username)})"
    return safe_name

def get_customer_buttons():
    """Customer နှိပ်နိုင်မည့် Link ခလုတ်များ"""
    markup = InlineKeyboardMarkup(row_width=1)
    btn_free = InlineKeyboardButton("🎬 Free ဇာတ်ကားများကြည့်ရန် (Free Group)", url=FREE_GROUP_LINK)
    btn_vip = InlineKeyboardButton("🔗 Privacy (VIP) Group တွင် Request ထားရန်", url=VIP_GROUP_LINK)
    markup.add(btn_free, btn_vip)
    return markup

def get_admin_action_buttons(user_id):
    """Admin အတွက် တစ်ချက်နှိပ်ရုံဖြင့် စာပြန်နိုင်မည့် ခလုတ်များ"""
    markup = InlineKeyboardMarkup(row_width=2)
    btn_approve = InlineKeyboardButton("✅ စစ်ဆေးပြီး (Approve)", callback_data=f"approve_{user_id}")
    btn_reject = InlineKeyboardButton("⚠️ ပုံမရှင်း/ပြန်ပို့ရန်", callback_data=f"reject_{user_id}")
    markup.add(btn_approve, btn_reject)
    return markup

def build_auto_reply(user):
    display_name = get_user_display(user)
    
    if VIP_CLOSED:
        return (
            f"မင်္ဂလာပါ <b>{display_name}</b> ခင်ဗျာ 🙏\n\n"
            f"⚠️ <b>လက်ရှိတွင် VIP MEMBER ဝင်ခွင့် ခဏပိတ်ထားပါသည်ဗျ။</b>\n\n"
            f"🎬 <b>Free ဇာတ်ကားများကို အောက်ပါ Link တွင် ဝင်ရောက်ကြည့်ရှုနိုင်ပါသည် -</b>\n"
            f"{FREE_GROUP_LINK}\n\n"
            f"ပြန်လည်ဖွင့်လှစ်ပေးသည့်အခါ အသိပေးသွားပါမည်ခင်ဗျာ။ ကျေးဇူးတင်ပါတယ်ဗျ 🙏"
        )
    
    return (
        f"မင်္ဂလာပါ <b>{display_name}</b> ခင်ဗျာ 🙏\n\n"
        f"💎 <b>VIP Member Price - {MEMBER_PRICE}</b>\n"
        f"(တစ်ခါသွင်းရုံနဲ့ တစ်သက်စာပါဗျ)\n\n"
        f"💳 <b>ငွေလွှဲရန် အကောင့် -</b>\n"
        f"• KPay Number - <code>{KPAY_NUMBER}</code> (နံပါတ်ကိုနှိပ်ပြီး Copy ကူးနိုင်ပါသည်)\n"
        f"• Name - <b>{KPAY_NAME}</b>\n\n"
        f"⚠️ <b>သတိပေးချက် (အရေးကြီးပါသည်) -</b>\n"
        f"၁။ ငွေလွှဲမှတ်ချက် (Note) မှာ မိမိ၏ <b>Telegram Name</b> ထည့်ရေးပေးပါခင်ဗျာ။\n"
        f"၂။ ငွေလွှဲပြီးပါက <b>KPay ငွေလွှဲပြေစာ (Screenshot)</b> ကို ဒီ Bot ဆီသို့ မဖြစ်မနေ ပေးပို့ပေးရပါမည်ဗျ။\n\n"
        f"🎬 <b>Free ဇာတ်ကားများ ကြည့်ရန် ဒီ Link ကို Join ပါ -</b>\n"
        f"{FREE_GROUP_LINK}\n\n"
        f"🔗 <b>Privacy (VIP) Group တွင်လည်း Request (Join) ထားပေးပါ -</b>\n"
        f"{VIP_GROUP_LINK}"
    )

@bot.message_handler(commands=['admin'])
def set_admin(message):
    global ADMIN_ID
    ADMIN_ID = str(message.chat.id)
    status_text = "🔒 ပိတ်ထားသည် (CLOSED)" if VIP_CLOSED else "🔓 ဖွင့်ထားသည် (OPEN - 5,000 Ks)"
    bot.reply_to(
        message,
        f"✅ <b>သင့်အကောင့်ကို Admin အဖြစ် သတ်မှတ်ပြီးပါပြီ!</b>\n"
        f"🆔 Admin ID: <code>{ADMIN_ID}</code>\n"
        f"📊 လက်ရှိ VIP အခြေအနေ: <b>{status_text}</b>\n\n"
        f"⚙️ <b>Admin အသုံးပြုနိုင်သော Command များ -</b>\n"
        f"• /open - VIP ဖွင့်ရန်\n"
        f"• /close - VIP ပိတ်ရန်\n"
        f"• /status - အခြေအနေစစ်ရန်",
        parse_mode="HTML"
    )

@bot.message_handler(commands=['open'])
def open_vip(message):
    global VIP_CLOSED
    if not ADMIN_ID or str(message.chat.id) == str(ADMIN_ID):
        VIP_CLOSED = False
        bot.reply_to(message, "🔓 VIP Member လက်ခံသည့် စာသား (5,000 Ks) သို့ ဖွင့်ပေးထားပါပြီ။")

@bot.message_handler(commands=['close'])
def close_vip(message):
    global VIP_CLOSED
    if not ADMIN_ID or str(message.chat.id) == str(ADMIN_ID):
        VIP_CLOSED = True
        bot.reply_to(message, "🔒 'VIP MEMBER ခဏပိတ်ထားပါသည်' စာသားသို့ ပြောင်းလဲလိုက်ပါပြီ။")

@bot.message_handler(commands=['status'])
def check_status(message):
    if not ADMIN_ID or str(message.chat.id) == str(ADMIN_ID):
        status_text = "🔒 ပိတ်ထားသည် (CLOSED)" if VIP_CLOSED else "🔓 ဖွင့်ထားသည် (OPEN - 5,000 Ks)"
        bot.reply_to(message, f"📊 လက်ရှိ VIP Status: {status_text}")

@bot.callback_query_handler(func=lambda call: True)
def handle_admin_callbacks(call):
    if ADMIN_ID and str(call.message.chat.id) != str(ADMIN_ID):
        return

    data = call.data
    if data.startswith("approve_"):
        target_id = int(data.split("_")[1])
        try:
            bot.send_message(
                target_id,
                f"🎉 <b>ဂုဏ်ယူပါတယ်ခင်ဗျာ!</b>\n\n"
                f"✅ လူကြီးမင်း၏ KPay ငွေလွှဲပြေစာကို Admin မှ စစ်ဆေးအတည်ပြုပြီးပါပြီ။\n"
                f"🔗 Privacy (VIP) Group တွင် Request မနှိပ်ရသေးပါက နှိပ်ပေးပါ၊ Admin မှ လက်ခံပေးထားပါပြီဗျ -\n"
                f"{VIP_GROUP_LINK}",
                parse_mode="HTML",
                reply_markup=get_customer_buttons()
            )
            bot.answer_callback_query(call.id, "✅ Customer ဆီ Approve စာပို့ပြီးပါပြီ!")
            bot.edit_message_text(
                call.message.text + "\n\n✅ [Admin မှ Approve စာပို့ပြီးပါပြီ]",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id
            )
        except Exception as e:
            bot.answer_callback_query(call.id, f"ပို့မရပါ: {e}", show_alert=True)

    elif data.startswith("reject_"):
        target_id = int(data.split("_")[1])
        try:
            bot.send_message(
                target_id,
                f"⚠️ <b>Admin မှ အကြောင်းကြားစာ</b>\n\n"
                f"လူကြီးမင်း ပေးပို့ထားသော ငွေလွှဲပြေစာ ပုံမရှင်းလင်းပါသဖြင့် (သို့မဟုတ်) အချက်အလက် မပြည့်စုံပါသဖြင့် "
                f"<b>KPay ပြေစာ Screenshot အပြည့်အစုံ</b> ကို ပြန်လည်ပေးပို့ပေးပါခင်ဗျာ 🙏",
                parse_mode="HTML"
            )
            bot.answer_callback_query(call.id, "⚠️ ပြေစာပြန်ပို့ခိုင်းသည့်စာ ပို့ပြီးပါပြီ!")
            bot.edit_message_text(
                call.message.text + "\n\n⚠️ [ပြေစာပြန်ပို့ရန် အကြောင်းကြားပြီးပါပြီ]",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id
            )
        except Exception as e:
            bot.answer_callback_query(call.id, f"ပို့မရပါ: {e}", show_alert=True)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user = message.from_user
    display_name = get_user_display(user)

    if ADMIN_ID and str(message.chat.id) != str(ADMIN_ID):
        bot.send_message(
            ADMIN_ID,
            f"🔔 <b>Customer အသစ် Bot ကို စတင်နှိပ်လိုက်ပါသည်</b>\n"
            f"👤 အမည်: {display_name}\n"
            f"🆔 User ID: <code>{user.id}</code>",
            parse_mode="HTML"
        )

    bot.reply_to(
        message,
        build_auto_reply(user),
        parse_mode="HTML",
        reply_markup=get_customer_buttons(),
        disable_web_page_preview=True
    )

@bot.message_handler(content_types=['photo', 'document'])
def handle_media(message):
    user = message.from_user
    display_name = get_user_display(user)
    caption = html.escape(message.caption) if message.caption else "မှတ်ချက်စာသား မပါပါ"

    if ADMIN_ID:
        info_text = (
            f"🧾 <b>KPay ငွေလွှဲပြေစာ (SS) အသစ်ရောက်ရှိလာပါသည်!</b>\n"
            f"👤 ပေးပို့သူ: {display_name}\n"
            f"🆔 User ID: <code>{user.id}</code>\n"
            f"📝 မှတ်ချက်: {caption}\n\n"
            f"💡 <i>(ဤစာကို Reply ထောက်ပြီးလည်း Customer ဆီ တိုက်ရိုက်စာပြန်နိုင်ပါသည်)</i>"
        )
        bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
        bot.send_message(
            ADMIN_ID,
            info_text,
            parse_mode="HTML",
            reply_markup=get_admin_action_buttons(user.id)
        )

    bot.reply_to(
        message,
        f"ကျေးဇူးတင်ပါတယ် <b>{display_name}</b> ခင်ဗျာ 🙏\n\n"
        f"✅ လူကြီးမင်း ပေးပို့သော <b>KPay ငွေလွှဲပြေစာ (Screenshot)</b> ကို Admin ထံ ပေးပို့ထားပြီး ဖြစ်ပါသည်။\n\n"
        f"🎬 <b>Free ဇာတ်ကားများ ကြည့်ရန် ဒီ Link ကို Join ပါ -</b>\n"
        f"{FREE_GROUP_LINK}\n\n"
        f"🔗 <b>Privacy (VIP) Group တွင် Request (Join) နှိပ်ထားပေးပါ၊ မကြာမီ စစ်ဆေးပြီး Approve လုပ်ပေးပါမည်ဗျ -</b>\n"
        f"{VIP_GROUP_LINK}",
        parse_mode="HTML",
        reply_markup=get_customer_buttons(),
        disable_web_page_preview=True
    )

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user = message.from_user
    display_name = get_user_display(user)

    if ADMIN_ID and str(message.chat.id) == str(ADMIN_ID):
        if message.reply_to_message:
            # Reply မှ Target ID ရှာဖွေခြင်း
            target_id = None
            if message.reply_to_message.forward_from:
                target_id = message.reply_to_message.forward_from.id
            else:
                text_to_search = message.reply_to_message.text or message.reply_to_message.caption or ""
                match = re.search(r"User ID:\s*(\d+)", text_to_search)
                if match:
                    target_id = int(match.group(1))

            if target_id:
                try:
                    bot.send_message(
                        target_id,
                        f"📩 <b>Admin မှ အကြောင်းကြားစာ -</b>\n\n{html.escape(message.text)}",
                        parse_mode="HTML"
                    )
                    bot.reply_to(message, "✅ Customer ဆီသို့ စာပို့ပြီးပါပြီ။")
                    return
                except Exception as e:
                    bot.reply_to(message, f"❌ ပို့မရပါ: {e}")
                    return

    if ADMIN_ID and str(message.chat.id) != str(ADMIN_ID):
        info_text = (
            f"💬 <b>Customer ဆီမှ စာအသစ် ရောက်ရှိလာပါသည်</b>\n"
            f"👤 ပေးပို့သူ: {display_name}\n"
            f"🆔 User ID: <code>{user.id}</code>\n"
            f"✉️ စာသား: {html.escape(message.text)}\n\n"
            f"💡 <i>(ဤစာကို Reply ထောက်ပြီး Customer ဆီ တိုက်ရိုက်စာပြန်နိုင်ပါသည်)</i>"
        )
        bot.send_message(ADMIN_ID, info_text, parse_mode="HTML")

    bot.reply_to(
        message,
        build_auto_reply(user),
        parse_mode="HTML",
        reply_markup=get_customer_buttons(),
        disable_web_page_preview=True
    )

def start_bot_polling():
    while True:
        try:
            bot.remove_webhook()
            time.sleep(2)
            bot.polling(non_stop=True, interval=1, timeout=20)
        except Exception as e:
            print(f"Polling error (restarting in 5s): {e}")
            time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    threading.Thread(target=keep_alive_ping, daemon=True).start()
    print("Bot စတင်အလုပ်လုပ်နေပါပြီ...")
    start_bot_polling()
