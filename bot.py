import logging
import os
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)


load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
RECIPIENT_CHAT_ID = os.getenv("RECIPIENT_CHAT_ID")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
RENDER_EXTERNAL_HOSTNAME = os.getenv("RENDER_EXTERNAL_HOSTNAME")
PORT = int(os.getenv("PORT", "8000"))
RECIPIENT_FILE = "recipient_chat_id.txt"

QUESTIONS = [
    "Как вас зовут?",
    "Сколько вам лет?",
    "С чем вы хотели бы обратиться к психологу?",
    "Как давно это вас беспокоит?",
    "Был ли у вас раньше опыт работы с психологом или психотерапевтом?",
    "Есть ли у вас сейчас диагнозы, лечение или прием препаратов, о которых важно знать специалисту?",
    "Бывают ли у вас мысли о причинении вреда себе или другим?",
    "Какой формат консультации вам удобнее: онлайн или очно?",
    "В какие дни и время вам обычно удобно записаться?",
    "Оставьте, пожалуйста, номер телефона или другой удобный способ связи.",
]

ASKING = 1

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def escape_html(value: object) -> str:
    text = str(value)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def get_recipient_chat_id() -> Optional[str]:
    if RECIPIENT_CHAT_ID:
        return RECIPIENT_CHAT_ID

    if os.path.exists(RECIPIENT_FILE):
        with open(RECIPIENT_FILE, "r", encoding="utf-8") as file:
            chat_id = file.read().strip()
            if chat_id:
                return chat_id

    return None


def save_recipient_chat_id(chat_id: int) -> None:
    with open(RECIPIENT_FILE, "w", encoding="utf-8") as file:
        file.write(str(chat_id))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    context.user_data["answers"] = []
    context.user_data["question_index"] = 0

    await update.message.reply_text(
        "Здравствуйте. Я задам несколько вопросов перед записью к психологу.\n\n"
        "Если захотите остановиться, отправьте /cancel."
    )
    await update.message.reply_text(QUESTIONS[0])
    return ASKING


async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    answer = update.message.text.strip()
    question_index = context.user_data.get("question_index", 0)
    answers = context.user_data.setdefault("answers", [])

    answers.append(
        {
            "question": QUESTIONS[question_index],
            "answer": answer,
        }
    )

    question_index += 1
    context.user_data["question_index"] = question_index

    if question_index < len(QUESTIONS):
        await update.message.reply_text(QUESTIONS[question_index])
        return ASKING

    await send_summary(update, context, answers)
    await update.message.reply_text(
        "Спасибо. Ваши ответы отправлены специалисту. С вами свяжутся для записи."
    )
    context.user_data.clear()
    return ConversationHandler.END


async def send_summary(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    answers: list[dict[str, str]],
) -> None:
    user = update.effective_user
    username = f"@{user.username}" if user and user.username else "не указан"
    full_name = user.full_name if user else "не указано"
    user_id = user.id if user else "не указан"
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        "<b>Новая анкета перед записью</b>",
        f"<b>Дата:</b> {escape_html(created_at)}",
        f"<b>Имя в Telegram:</b> {escape_html(full_name)}",
        f"<b>Username:</b> {escape_html(username)}",
        f"<b>User ID:</b> <code>{escape_html(user_id)}</code>",
        "",
    ]

    for index, item in enumerate(answers, start=1):
        lines.append(f"<b>{index}. {escape_html(item['question'])}</b>")
        lines.append(escape_html(item["answer"]))
        lines.append("")

    message = "\n".join(lines)

    recipient_chat_id = get_recipient_chat_id()

    if not recipient_chat_id:
        logger.error("Recipient chat id is not set")
        await update.message.reply_text(
            "Анкета заполнена, но получатель не настроен. "
            "Попросите специалиста написать /admin в личном чате с ботом "
            "или в рабочей группе, куда должны приходить анкеты."
        )
        return

    await context.bot.send_message(
        chat_id=recipient_chat_id,
        text=message,
        parse_mode=ParseMode.HTML,
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("Опрос остановлен. Чтобы начать заново, отправьте /start.")
    return ConversationHandler.END


async def show_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    user = update.effective_user
    await update.message.reply_text(
        f"Chat ID: {chat.id}\nUser ID: {user.id if user else 'неизвестно'}"
    )


async def set_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    save_recipient_chat_id(chat.id)
    chat_kind = "группа" if chat.type in {"group", "supergroup"} else "чат"
    await update.message.reply_text(
        f"Готово. Этот {chat_kind} сохранен как получатель анкет перед записью."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Команды:\n"
        "/start - начать анкету\n"
        "/cancel - остановить анкету\n"
        "/id - показать ID текущего чата"
        "\n/admin - сделать этот чат или группу получателем анкет"
    )


def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set. Copy .env.example to .env and fill it in.")

    application = Application.builder().token(BOT_TOKEN).build()

    conversation = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASKING: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conversation)
    application.add_handler(CommandHandler("id", show_id))
    application.add_handler(CommandHandler("admin", set_admin))
    application.add_handler(CommandHandler("help", help_command))

    if WEBHOOK_URL or RENDER_EXTERNAL_HOSTNAME:
        webhook_base_url = WEBHOOK_URL or f"https://{RENDER_EXTERNAL_HOSTNAME}"
        webhook_path = f"telegram/{BOT_TOKEN}"
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=webhook_path,
            webhook_url=f"{webhook_base_url.rstrip('/')}/{webhook_path}",
            allowed_updates=Update.ALL_TYPES,
        )
        return

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
