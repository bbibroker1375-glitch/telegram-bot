import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler, filters, ContextTypes

import gspread
from google.oauth2.service_account import Credentials

# ------------------ Google Sheet Setup ------------------
creds = Credentials.from_service_account_file("telegramsheeetbot-6ba732501adb.json")
client = gspread.authorize(creds)
sheet = client.open("TelegramBotData").sheet1

# ستون‌های شیت باید این باشند:
# user_id | name | phone | reason


# ------------------ Conversation States ------------------
ASK_NAME, ASK_PHONE, ASK_REASON = range(3)

reasons = ["اعتبار", "بورس کالا", "بورس انرژی", "سایر موارد"]
reason_keyboard = ReplyKeyboardMarkup([[r] for r in reasons], resize_keyboard=True)


# ------------------ Validation ------------------
def is_valid_name(text):
    import re
    return bool(re.match(r'^[آ-ی\s]{3,}$', text))


def is_valid_phone(text):
    return text.isdigit() and text.startswith("09") and len(text) == 11


# ---------- پیدا کردن ردیف کاربر ----------
def find_user_row(user_id):
    users = sheet.col_values(1)  # ستون user_id
    if str(user_id) in users:
        return users.index(str(user_id)) + 1
    return None


# ---------- ذخیره / آپدیت در Google Sheet ----------
def save_to_sheet(user_id, name=None, phone=None, reason=None):

    row = find_user_row(user_id)

    if row is None:
        # کاربر جدید → ایجاد ردیف
        sheet.append_row([str(user_id), name or "", phone or "", reason or ""])
    else:
        # آپدیت کاربر موجود
        if name is not None:
            sheet.update_cell(row, 2, name)
        if phone is not None:
            sheet.update_cell(row, 3, phone)
        if reason is not None:
            sheet.update_cell(row, 4, reason)


# ------------------ Bot Handlers ------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    # ایجاد ردیف برای کاربر اگر وجود ندارد
    save_to_sheet(user_id)

    await update.message.reply_text(
        "سلام به ربات کارگزاری بورس بیمه ایران خوش آمدید.\n"
        "ما اینجاییم تا شما با راحتی هر چه تمام‌تر درخواست‌های خودتون رو ثبت و پیگیری کنید.\n\n"
        "لطفاً نام و نام خانوادگی خود را وارد نمایید:"
    )
    return ASK_NAME


async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    name = update.message.text.strip()

    if not is_valid_name(name):
        await update.message.reply_text("❌ لطفاً نام و نام خانوادگی صحیح وارد نمایید. مثال: علی محمدی")
        return ASK_NAME

    save_to_sheet(user_id, name=name)

    await update.message.reply_text("لطفاً شماره تماس خود را وارد نمایید:")
    return ASK_PHONE


async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    phone = update.message.text.strip()

    if not is_valid_phone(phone):
        await update.message.reply_text("❌ شماره تلفن نامعتبر است.\nلطفاً یک شماره ۱۱ رقمی وارد کنید که با 09 شروع شود.")
        return ASK_PHONE

    save_to_sheet(user_id, phone=phone)

    await update.message.reply_text(
        "لطفاً درخواست خود را از بین گزینه‌های زیر انتخاب نمایید:",
        reply_markup=reason_keyboard
    )
    return ASK_REASON


async def ask_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    reason = update.message.text.strip()

    if reason not in reasons:
        await update.message.reply_text("❌ لطفاً فقط از گزینه‌های موجود انتخاب نمایید.")
        return ASK_REASON

    save_to_sheet(user_id, reason=reason)

    await update.message.reply_text(
        "اطلاعات شما با موفقیت ثبت شد ✔️\n"
        "به زودی با شما تماس می‌گیریم.",
        reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


# ------------------ Run Bot ------------------
def main():
    app = ApplicationBuilder().token("8545256794:AAEjB-NfzJ_LdRQl1yfhemX9gyjaeJhHIrU").build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT, ask_name)],
            ASK_PHONE: [MessageHandler(filters.TEXT, ask_phone)],
            ASK_REASON: [MessageHandler(filters.TEXT, ask_reason)],
        },
        fallbacks=[],
    )

    app.add_handler(conv)
    app.run_polling()


if __name__ == "__main__":
    main()
