import logging
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import TelegramError
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Bot Token နှင့် Admin ID (numeric Telegram user/chat ID) ကို ထည့်ပါ
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "123456789"))
PORT = int(os.getenv("PORT", "8080"))

KPAY_INFO = {
    "number": "09764199664",
    "name": "Min Zayar Oo",
    "channel_link": "https://t.me/+Mv6q6XQxeRJhNjM1",
    "contact_bot": "http://t.me/translatemoviesken_bot",
}

PRICE_LIST_TEXT = (
    "🎬 *VIP MEMBER PRICE LIST*\n\n"
    "📌 *VIP ဇာတ်ကားဈေးနှုန်းများ*\n"
    "🎥 1 Movie – 1,000 Ks\n"
    "🎥 10 Movies – 5,000 Ks\n"
    "🎥 20 Movies – 6,000 Ks\n\n"
    "📍 *မှတ်ချက်*\n"
    "အချို့သော ဇာတ်ကားများသည် 2,000 Ks ကျသင့်မည်ဖြစ်ပါသည်။\n\n"
    "━━━━━━━━━━━━━━\n\n"
    "🎁 *OLD MEMBER SPECIAL DISCOUNT*\n"
    "မန်ဘာအဟောင်းများအတွက် အထူးလျှော့ဈေးအစီအစဉ်ရှိပါတယ်။ ❤️\n"
    "✨ 10 Movies ဝယ်ယူပါက 50% Discount ရရှိပါမည်။\n\n"
    "━━━━━━━━━━━━━━\n\n"
    "💳 *KPay ငွေလွှဲရန်*\n"
    f"📱 KPay Number – `{KPAY_INFO['number']}`\n"
    f"👤 Account Name – {KPAY_INFO['name']}\n\n"
    "⚠️ *အရေးကြီးအသိပေးချက်*\n"
    "ငွေလွှဲပြီးပါက ငွေလွှဲပြေစာ (Payment Slip) ကို မဖြစ်မနေပေးပို့ပေးရန် လိုအပ်ပါသည်။\n"
    "ငွေလွှဲပြေစာ ပေးပို့ထားသော Order များကိုသာ လက်ခံဆောင်ရွက်ပေးသွားမည်ဖြစ်ပါသည်။\n\n"
    "━━━━━━━━━━━━━━\n\n"
    "📢 *VIP CHANNEL JOIN ရန်*\n"
    f"🔗 {KPAY_INFO['channel_link']}\n\n"
    "📩 *ဆက်သွယ်ရန်*\n"
    f"Telegram – {KPAY_INFO['contact_bot']}\n\n"
    "❤️ အားပေးမှုအတွက် အထူးကျေးဇူးတင်ရှိပါတယ်။"
)

# Conversation states
ASK_STANDARD, ASK_SPECIAL, ASK_OLD_MEMBER, ASK_PAYMENT_SLIP = range(4)


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"VIP Movie Bot is alive 24/7")

    def log_message(self, format: str, *args) -> None:
        return


def start_health_server() -> None:
    server = ThreadingHTTPServer(("0.0.0.0", PORT), HealthHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    logger.info("Health check server listening on port %s", PORT)


def calculate_bundle_price(movie_count: int, is_old_member: bool = False) -> tuple[int, list[str]]:
    if movie_count <= 0:
        return 0, []

    remaining = movie_count
    total = 0
    breakdown = []

    if remaining >= 20:
        packs_20 = remaining // 20
        cost_20 = packs_20 * 6000
        total += cost_20
        remaining %= 20
        breakdown.append(f"20 Movies x {packs_20} = {cost_20:,} Ks")

    if remaining >= 10:
        packs_10 = remaining // 10
        unit_10 = 2500 if is_old_member else 5000
        cost_10 = packs_10 * unit_10
        total += cost_10
        remaining %= 10
        note = " (50% Old Member)" if is_old_member else ""
        breakdown.append(f"10 Movies x {packs_10}{note} = {cost_10:,} Ks")

    if remaining > 0:
        cost_single = remaining * 1000
        total += cost_single
        breakdown.append(f"Single Movies x {remaining} = {cost_single:,} Ks")

    return total, breakdown


def build_order_summary(standard_movies: int, special_movies: int, is_old_member: bool) -> tuple[str, int]:
    bundle_total, breakdown = calculate_bundle_price(standard_movies, is_old_member)
    special_total = special_movies * 2000
    grand_total = bundle_total + special_total

    lines = [
        "🧾 *VIP MOVIE ORDER SUMMARY*",
        "────────────────────",
        f"• Member: {'Old Member' if is_old_member else 'Regular / New'}",
        f"• Standard Movies: {standard_movies}",
        f"• Special Movies (2,000 Ks): {special_movies}",
        "────────────────────",
    ]
    lines.extend([f"  - {b}" for b in breakdown])
    if special_movies > 0:
        lines.append(f"  - Special Movies x {special_movies} = {special_total:,} Ks")

    lines.extend([
        "────────────────────",
        f"💰 *TOTAL AMOUNT: {grand_total:,} Ks*",
        "",
        "💳 *KPay ငွေလွှဲရန်*",
        f"• Number: `{KPAY_INFO['number']}`",
        f"• Name: {KPAY_INFO['name']}",
        "",
        f"📢 Channel: {KPAY_INFO['channel_link']}",
        f"📩 Slip ပို့ရန်: {KPAY_INFO['contact_bot']}",
        "⚠️ *ငွေလွှဲပြီးပါက အောက်ပါခလုတ်ကိုနှိပ်၍ Payment Slip ပုံ ပေးပို့ပါ။*",
    ])
    return "\n".join(lines), grand_total


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Price List ကြည့်ရန်", callback_data="show_prices")],
        [InlineKeyboardButton("🧮 Order ဈေးနှုန်း တွက်ချက်ရန်", callback_data="start_calc")],
        [InlineKeyboardButton("📸 Payment Slip ပို့ရန်", callback_data="send_slip_direct")],
    ])


def slip_action_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📸 Payment Slip ပုံ ပို့မည်", callback_data="ready_to_send_slip")],
        [InlineKeyboardButton("🔙 ပင်မမီနူးသို့", callback_data="back_menu")],
    ])


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "မင်္ဂလာပါ! 🎬 VIP Movie Bot မှ ကြိုဆိုပါတယ်။\nအောက်ပါ ခလုတ်များမှ တစ်ဆင့် ရွေးချယ်နိုင်ပါတယ်:",
        reply_markup=main_menu_keyboard(),
    )


async def prices_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        PRICE_LIST_TEXT,
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(),
    )


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "show_prices":
        await query.message.reply_text(
            PRICE_LIST_TEXT,
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(),
        )
        return ConversationHandler.END

    if query.data == "start_calc":
        context.user_data.clear()
        await query.message.reply_text(
            "ပုံမှန် ဇာတ်ကား အရေအတွက် ထည့်သွင်းပါ (ဥပမာ - `10` သို့မဟုတ် `0`):",
            parse_mode="Markdown",
        )
        return ASK_STANDARD

    if query.data == "send_slip_direct":
        await query.message.reply_text(
            "📸 ငွေလွှဲပြေစာ (Payment Slip) ဓာတ်ပုံကို ယခု ပေးပို့နိုင်ပါပြီ။\n(ပယ်ဖျက်လိုပါက `/cancel` ဟု ရိုက်ပါ)",
            parse_mode="Markdown",
        )
        return ASK_PAYMENT_SLIP

    return ConversationHandler.END


async def calc_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "ပုံမှန် ဇာတ်ကား အရေအတွက် ထည့်သွင်းပါ (ဥပမာ - `10` သို့မဟုတ် `0`):",
        parse_mode="Markdown",
    )
    return ASK_STANDARD


async def receive_standard_count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("❌ ကိန်းဂဏန်းသာ ထည့်သွင်းပါ (ဥပမာ - `5`):")
        return ASK_STANDARD

    context.user_data["standard_movies"] = int(text)
    await update.message.reply_text(
        "2,000 Ks တန် Special ဇာတ်ကား အရေအတွက် ထည့်သွင်းပါ (မရှိပါက `0` ဟု ရိုက်ပါ):",
        parse_mode="Markdown",
    )
    return ASK_SPECIAL


async def receive_special_count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("❌ ကိန်းဂဏန်းသာ ထည့်သွင်းပါ (ဥပမာ - `0` သို့မဟုတ် `2`):")
        return ASK_SPECIAL

    context.user_data["special_movies"] = int(text)
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Old Member (50% off 10-pack)", callback_data="member_yes"),
            InlineKeyboardButton("🆕 Regular / New Member", callback_data="member_no"),
        ]
    ])
    await update.message.reply_text("Old Member ဖြစ်ပါသလား?", reply_markup=keyboard)
    return ASK_OLD_MEMBER


async def receive_old_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    is_old = query.data == "member_yes"
    standard_movies = context.user_data.get("standard_movies", 0)
    special_movies = context.user_data.get("special_movies", 0)

    summary, grand_total = build_order_summary(standard_movies, special_movies, is_old)
    context.user_data["last_order_summary"] = summary
    context.user_data["last_order_total"] = grand_total

    await query.message.reply_text(
        summary,
        parse_mode="Markdown",
        reply_markup=slip_action_keyboard(),
    )
    return ASK_PAYMENT_SLIP


async def slip_step_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "ready_to_send_slip":
        await query.message.reply_text(
            "📸 ငွေလွှဲပြေစာ (Payment Slip) ဓာတ်ပုံကို ယခု ပို့ပေးပါ:"
        )
        return ASK_PAYMENT_SLIP

    if query.data == "back_menu":
        await query.message.reply_text(
            "ပင်မမီနူးသို့ ပြန်ရောက်ပါပြီ။",
            reply_markup=main_menu_keyboard(),
        )
        return ConversationHandler.END

    return ASK_PAYMENT_SLIP


async def receive_payment_slip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    username_str = f"@{user.username}" if user.username else "(No Username)"
    order_summary = context.user_data.get("last_order_summary")

    admin_caption = (
        "📥 *NEW PAYMENT SLIP RECEIVED*\n"
        "────────────────────\n"
        f"• Name: {user.full_name}\n"
        f"• Username: {username_str}\n"
        f"• User ID: `{user.id}`\n"
    )
    if order_summary:
        admin_caption += f"\n{order_summary}"

    try:
        await update.message.forward(chat_id=ADMIN_CHAT_ID)
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=admin_caption,
            parse_mode="Markdown",
        )
    except TelegramError as exc:
        logger.error("Failed to forward slip to admin: %s", exc)
        await update.message.reply_text(
            "⚠️ Admin ဆီ ပို့ရာတွင် ယာယီအခက်အခဲ ရှိနေပါသည်။ ကျေးဇူးပြု၍ "
            f"{KPAY_INFO['contact_bot']} သို့ တိုက်ရိုက် ပို့ပေးပါ။"
        )
        return ASK_PAYMENT_SLIP

    await update.message.reply_text(
        "✅ *Payment Slip ကို Admin ဆီ ပေးပို့ပြီးပါပြီ။*\n"
        "Admin မှ စစ်ဆေးပြီး VIP Channel Access ကို ဆောင်ရွက်ပေးပါမည်။\n\n"
        f"📢 Channel Link: {KPAY_INFO['channel_link']}",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(),
    )
    context.user_data.clear()
    return ConversationHandler.END


async def invalid_slip_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "⚠️ ကျေးဇူးပြု၍ ငွေလွှဲပြေစာ **ဓာတ်ပုံ (Photo)** သို့မဟုတ် **ပုံဖိုင်** ကို ပေးပို့ပါ။\n"
        "(ပယ်ဖျက်လိုပါက `/cancel` ဟု ရိုက်ပါ)",
        parse_mode="Markdown",
    )
    return ASK_PAYMENT_SLIP


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("လုပ်ဆောင်ချက်ကို ပယ်ဖျက်လိုက်ပါပြီ။", reply_markup=main_menu_keyboard())
    return ConversationHandler.END


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling an update: %s", context.error)


def main() -> None:
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        raise ValueError("TELEGRAM_BOT_TOKEN ကို ထည့်သွင်းရန် လိုအပ်ပါသည်။")

    start_health_server()

    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("calc", calc_command),
            CallbackQueryHandler(menu_callback, pattern="^(show_prices|start_calc|send_slip_direct)$"),
        ],
        states={
            ASK_STANDARD: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_standard_count)],
            ASK_SPECIAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_special_count)],
            ASK_OLD_MEMBER: [CallbackQueryHandler(receive_old_member, pattern="^member_(yes|no)$")],
            ASK_PAYMENT_SLIP: [
                CallbackQueryHandler(slip_step_callback, pattern="^(ready_to_send_slip|back_menu)$"),
                MessageHandler(filters.PHOTO | filters.Document.IMAGE, receive_payment_slip),
                MessageHandler(~filters.COMMAND, invalid_slip_input),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_command)],
    )

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("prices", prices_command))
    app.add_handler(conv_handler)
    app.add_error_handler(error_handler)

    logger.info("Bot is running 24/7...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
