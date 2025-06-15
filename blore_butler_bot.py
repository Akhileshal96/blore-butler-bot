import telebot
import json
import openpyxl
import os

# === CONFIGURATION SECTION ===

# Bot Token (keep this safe in production, ideally via env variables)
TOKEN = '7817780868:AAEd39YD3hDr1JAsQTCmeN9hgrMAtAHnKe4'
bot = telebot.TeleBot(TOKEN)

# Telegram Group ID (only members of this group can register)
GROUP_ID = -1001518197115

# Files used for storing admins and registration data
ADMINS_FILE = "admins.json"
EXCEL_FILE = "registrations.xlsx"

# === INITIAL SETUP ===

# Ensure admins file exists
if not os.path.exists(ADMINS_FILE):
    with open(ADMINS_FILE, "w") as f:
        json.dump(["728623146"], f)

# Ensure Excel file exists with headers
if not os.path.exists(EXCEL_FILE):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Telegram ID", "Telegram Name", "Phone Number"])
    wb.save(EXCEL_FILE)


# === HELPER FUNCTIONS ===

def load_admins():
    with open(ADMINS_FILE, "r") as f:
        return json.load(f)

def save_admins(admins):
    with open(ADMINS_FILE, "w") as f:
        json.dump(admins, f)

def is_group_member(user_id):
    try:
        member = bot.get_chat_member(GROUP_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception:
        return False


# === BOT COMMAND HANDLERS ===

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if not is_group_member(user_id):
        bot.reply_to(message, "❌ You must be a member of the Bangalore Meetups group to register.")
        return

    msg = bot.reply_to(message, "Welcome! Please enter your 10-digit phone number:")
    bot.register_next_step_handler(msg, process_phone)


def process_phone(message):
    user_id = message.from_user.id
    username = message.from_user.username or ""
    name = message.from_user.first_name or ""

    phone = message.text.strip()

    if not phone.isdigit() or len(phone) != 10:
        msg = bot.reply_to(message, "⚠ Invalid phone number. Please enter a valid 10-digit phone number:")
        bot.register_next_step_handler(msg, process_phone)
        return

    wb = openpyxl.load_workbook(EXCEL_FILE)
    ws = wb.active
    ws.append([user_id, f"{name} (@{username})", phone])
    wb.save(EXCEL_FILE)

    bot.reply_to(message, "✅ You have been successfully registered for the guest list!")


@bot.message_handler(commands=['reset'])
def reset(message):
    user_id = str(message.from_user.id)
    admins = load_admins()

    if user_id not in admins:
        bot.reply_to(message, "❌ Unauthorized: Only admins can reset the list.")
        return

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Telegram ID", "Telegram Name", "Phone Number"])
    wb.save(EXCEL_FILE)

    bot.reply_to(message, "✅ Registration list has been reset.")


@bot.message_handler(commands=['addadmin'])
def addadmin(message):
    user_id = str(message.from_user.id)
    admins = load_admins()

    if user_id not in admins:
        bot.reply_to(message, "❌ Unauthorized: Only admins can add new admins.")
        return

    try:
        new_admin_id = message.text.split(" ")[1]
        if new_admin_id not in admins:
            admins.append(new_admin_id)
            save_admins(admins)
            bot.reply_to(message, f"✅ Admin {new_admin_id} added successfully.")
        else:
            bot.reply_to(message, "⚠ User is already an admin.")
    except:
        bot.reply_to(message, "⚠ Usage: /addadmin <telegram_user_id>")


@bot.message_handler(commands=['download'])
def download(message):
    user_id = str(message.from_user.id)
    admins = load_admins()

    if user_id not in admins:
        bot.reply_to(message, "❌ Unauthorized: Only admins can download data.")
        return

    with open(EXCEL_FILE, "rb") as f:
        bot.send_document(message.chat.id, f)


@bot.message_handler(func=lambda m: True)
def fallback(message):
    bot.reply_to(message, "🤖 Use /start to begin your registration process.")


# === START POLLING ===

if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
