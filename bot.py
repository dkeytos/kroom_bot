import logging
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler
)
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import re  # For email validation

# Replace with your BotFather token and your personal (owner) chat ID
TOKEN = '7553175499:AAE44asU_QYGcYHJdDAASYcaR1aekB7m2L8'
OWNER_CHAT_ID = 7341033870  # Replace with your actual Telegram user ID

# Set up logging so you can see what’s happening
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Conversation state constants
WAITING_FOR_PHOTO = 1
CHOOSING_OPTION = 2
WAITING_FOR_EMAIL = 3  # New state for registered email input

# Add mapping for language flags
lang_flags = {
    "eng": "🇬🇧",
    "ita": "🇮🇹",
    "spa": "🇪🇸"
}

# Add language-specific messages and helper function
language_msgs = {
    "eng": {
        "ask_photo": "Hey there! 😊 Please send a photo as proof of deposit. 📸 Only a picture is accepted!",
        "invalid_photo": "Oops! 😕 Kindly note, only a photo can be used as proof of deposit. 📸 Please send a picture. 👍",
        "invalid_photo_reset": "Oops! 😕 Only a photo works. Please send a picture.\n\nOr press {reset_button} to start over! 🔄",
        "success": "Awesome! 😊 Our support team will contact you shortly to get you into KeyRoom! 🚀",
        "choose_option": "Please choose an option below: 👇",
        "deposit_proof_button": "Deposit Proof 📸",
        "already_registered_button": "Already Registered ✅",
        "reset_button": "Reset 🔄",
        "ask_email": "Great! Now, please enter your registered email address 📧",
        "invalid_email": "Hmm... That doesn't look like a valid email address 😕. Please send a valid email address 📧"
    },
    "ita": {
        "ask_photo": "Ciao! 😊 Per favore, invia una foto come prova del deposito. 📸 Solo una foto è accettata!",
        "invalid_photo": "Ops! 😕 Nota bene, solo una foto può essere usata come prova del deposito. 📸 Per favore, invia una foto. 👍",
        "invalid_photo_reset": "Ops! 😕 Solo una foto funziona. Invia una foto.\n\nO premi {reset_button} per ricominciare! 🔄",
        "success": "Fantastico! 😊 Il nostro team di supporto ti contatterà a breve per farti entrare in KeyRoom! 🚀",
        "choose_option": "Per favore, scegli un'opzione qui sotto: 👇",
        "deposit_proof_button": "Prova di deposito 📸",
        "already_registered_button": "Già registrato ✅",
        "reset_button": "Reimposta 🔄",
        "ask_email": "Perfetto! Ora, inserisci l'indirizzo email con cui ti sei registrato 📧",
        "invalid_email": "Ops... L'indirizzo email non sembra valido 😕. Invia un indirizzo email valido 📧"
    },
    "spa": {
        "ask_photo": "¡Hola! 😊 Por favor, envíe una foto como prueba de depósito. 📸 ¡Solo se acepta una imagen!",
        "invalid_photo": "Uy! 😕 Tenga en cuenta que solo se puede usar una foto como prueba de depósito. 📸 Por favor, envíe una imagen. 👍",
        "invalid_photo_reset": "Uy! 😕 Solo se acepta una imagen. Envíe una imagen.\n\nO presione {reset_button} para reiniciar! 🔄",
        "success": "¡Genial! 😊 Nuestro equipo de soporte se pondrá en contacto con usted en breve para que pueda ingresar a KeyRoom! 🚀",
        "choose_option": "Por favor, elija una opción a continuación: 👇",
        "deposit_proof_button": "Comprobante de depósito 📸",
        "already_registered_button": "Ya registrado ✅",
        "reset_button": "Reiniciar 🔄",
        "ask_email": "¡Perfecto! Ahora, ingrese el correo electrónico con el que se registró 📧",
        "invalid_email": "¡Uy! 😕 El correo electrónico ingresado no es válido. Por favor, ingrese un correo electrónico válido 📧"
    }
}

def get_language(context: ContextTypes.DEFAULT_TYPE):
    reg_param = context.user_data.get("reg_param", "")
    if "_" in reg_param:
        return reg_param.split("_")[0]
    return "eng"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = update.message.text.split()
    param = args[1] if len(args) > 1 else "Not provided"
    if param == "Not provided":
        # Delete the /start command message to clear the chat.
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=update.message.message_id)
        except Exception as e:
            logger.error("Failed to delete /start command message: %s", e)
        # If a starting menu is already open, delete it.
        prev_menu_msg_id = context.user_data.get("menu_msg_id")
        if prev_menu_msg_id:
            try:
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=prev_menu_msg_id)
            except Exception as e:
                logger.error("Failed to delete previous menu: %s", e)
        # Create and store the new menu message.
        keyboard = [
            [InlineKeyboardButton("🇬🇧", callback_data="eng"),
             InlineKeyboardButton("🇮🇹", callback_data="ita"),
             InlineKeyboardButton("🇪🇸", callback_data="spa")],
            [InlineKeyboardButton("US Residents", callback_data="us")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        new_menu = await update.message.reply_text(language_msgs["eng"]["choose_option"], reply_markup=reply_markup)
        context.user_data["menu_msg_id"] = new_menu.message_id
        return CHOOSING_OPTION
    else:
        context.user_data["reg_param"] = param
        if param.endswith("_deposit"):
            lang = get_language(context)
            await update.message.reply_text(language_msgs[lang]["ask_photo"])
            return WAITING_FOR_PHOTO
        elif param.endswith("_register"):
            lang = get_language(context)
            await update.message.reply_text(language_msgs[lang]["ask_email"])
            return WAITING_FOR_EMAIL
        else:
            user = update.message.from_user
            username = f"@{user.username}" if user.username else "Not set"
            user_id = user.id
            forward_msg = (
                f"New Contact:\n"
                f"Username: {username}\n"
                f"User ID: {user_id}\n"
                f"Registration Info: {param}"
            )
            await context.bot.send_message(chat_id=OWNER_CHAT_ID, text=forward_msg)
            await update.message.reply_text("Thanks! Your information has been forwarded.")
            logger.info("Forwarded contact info: %s", forward_msg)
            return ConversationHandler.END

async def send_start_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🇬🇧", callback_data="eng"),
         InlineKeyboardButton("🇮🇹", callback_data="ita"),
         InlineKeyboardButton("🇪🇸", callback_data="spa")],
        [InlineKeyboardButton("US Residents", callback_data="us")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # If the reset came from a callback, use edit_message_text
    if update.callback_query:
        await update.callback_query.edit_message_text(language_msgs["eng"]["choose_option"], reply_markup=reply_markup)
    else:
        await update.message.reply_text(language_msgs["eng"]["choose_option"], reply_markup=reply_markup)
    return CHOOSING_OPTION

async def choice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    # First level: language selection
    if query.data in ["eng", "ita", "spa"]:
        context.user_data["lang"] = query.data  # save chosen language
        keyboard = [
            [InlineKeyboardButton(language_msgs[query.data]["deposit_proof_button"], callback_data="deposit_proof"),
             InlineKeyboardButton(language_msgs[query.data]["already_registered_button"], callback_data="already_registered")],
            [InlineKeyboardButton(language_msgs[query.data]["reset_button"], callback_data="reset")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(language_msgs[query.data]["choose_option"], reply_markup=reply_markup)
        return CHOOSING_OPTION
    # Second level: user option selection
    elif query.data == "deposit_proof":
        lang = context.user_data.get("lang", "eng")
        context.user_data["reg_param"] = lang + "_deposit"
        await query.edit_message_text(language_msgs[lang]["ask_photo"])
        return WAITING_FOR_PHOTO
    elif query.data == "already_registered":
        lang = context.user_data.get("lang", "eng")
        context.user_data["reg_param"] = lang + "_register"
        await query.edit_message_text(language_msgs[lang]["ask_email"])
        return WAITING_FOR_EMAIL
    elif query.data == "us":
        context.user_data["reg_param"] = "us_resident"
        user = query.from_user
        username = f"@{user.username}" if user.username else "Not set"
        language_line = ""
        lang = context.user_data.get("lang", "eng")
        if lang in lang_flags:
            language_line = f"\n**Language:** {lang_flags[lang]}"
        forward_msg = (
            f"New Contact (US Resident):\n"
            f"**Username:** {username}{language_line}"
        )
        await context.bot.send_message(chat_id=OWNER_CHAT_ID, text=forward_msg)
        await query.edit_message_text(language_msgs[lang]["success"])
        return ConversationHandler.END
    elif query.data == "reset":
        return await send_start_menu(update, context)

async def deposit_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        lang = get_language(context)
        await update.message.reply_text(language_msgs[lang]["invalid_photo"])
        return WAITING_FOR_PHOTO
    # Select the highest-resolution photo available
    photo = update.message.photo[-1]
    user = update.message.from_user
    username = f"@{user.username}" if user.username else "Not set"
    caption = (
        f"New Deposit Proof:\n"
        f"**Username:** {username}"
    )
    # Append language flag if available
    lang = context.user_data.get("lang", "eng")
    if lang in lang_flags:
        caption += f"\n**Language:** {lang_flags[lang]}"
    await context.bot.send_photo(chat_id=OWNER_CHAT_ID, photo=photo.file_id, caption=caption)
    await update.message.reply_text(language_msgs[lang]["success"])
    logger.info("Forwarded deposit proof from user %s", username)
    return ConversationHandler.END

async def deposit_invalid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_language(context)
    # Build a reset button that returns to the main menu when pressed.
    keyboard = [[InlineKeyboardButton(language_msgs[lang]["reset_button"], callback_data="reset")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    error_msg = language_msgs[lang]["invalid_photo_reset"].format(reset_button=language_msgs[lang]["reset_button"])
    await update.message.reply_text(error_msg, reply_markup=reply_markup)
    return WAITING_FOR_PHOTO

# Add a new handler to process reset callback in WAITING_FOR_PHOTO state
async def reset_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await send_start_menu(update, context)

# Email validation helper
def is_valid_email(email: str) -> bool:
    return bool(re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email))

# Handler for processing already registered email input.
async def registered_email_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email_input = update.message.text.strip()
    reg_param = context.user_data.get("reg_param", "")
    lang = reg_param.split("_")[0] if "_" in reg_param else "eng"
    if not is_valid_email(email_input):
        keyboard = [[InlineKeyboardButton(language_msgs[lang]["reset_button"], callback_data="reset")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(language_msgs[lang]["invalid_email"], reply_markup=reply_markup)
        return WAITING_FOR_EMAIL
    # Forward the contact info along with the email address.
    user = update.message.from_user
    username = f"@{user.username}" if user.username else "Not set"
    language_line = ""
    if lang in lang_flags:
        language_line = f"\n**Language:** {lang_flags[lang]}"
    forward_msg = (
        f"New Contact (Already Registered):\n"
        f"**Username:** {username}\n"
        f"**Email:** {email_input}{language_line}"
    )
    await context.bot.send_message(chat_id=OWNER_CHAT_ID, text=forward_msg)
    await update.message.reply_text(language_msgs[lang]["success"])
    return ConversationHandler.END

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Instruct user to use /start instead of sending arbitrary texts.
    await update.message.reply_text("Please type /start to begin the conversation.")

# Modify reset_command to call send_start_menu
async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await reset_command.__self__.logger.info("Reset command received.")  # Optional logging
    return await send_start_menu(update, context)

async def main():
    application = ApplicationBuilder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_OPTION: [CallbackQueryHandler(choice_handler)],
            WAITING_FOR_PHOTO: [
                CallbackQueryHandler(reset_button_handler, pattern='^reset$'),
                MessageHandler(filters.PHOTO, deposit_photo),
                MessageHandler(~filters.PHOTO, deposit_invalid)
            ],
            WAITING_FOR_EMAIL: [
                CallbackQueryHandler(reset_button_handler, pattern='^reset$'),  # New handler for reset in WAITING_FOR_EMAIL
                MessageHandler(filters.TEXT & ~filters.COMMAND, registered_email_handler)
            ]
        },
        fallbacks=[CommandHandler("reset", reset_command)],
        allow_reentry=True  # Allow /start to be processed even if conversation is active.
    )
    application.add_handler(conv_handler)
    # Replace the echo handler to force /start usage.
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    
    await application.run_polling()

if __name__ == '__main__':
    import asyncio
    try:
        import nest_asyncio
        nest_asyncio.apply()
    except ImportError:
        pass
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if "Cannot close a running event loop" in str(e):
            logger.warning("Event loop error suppressed: %s", e)
        else:
            raise
