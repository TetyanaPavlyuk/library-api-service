import telegram
from django.conf import settings
import logging


def send_telegram_message(message: str) -> None:
    """Send message to the telegram channel"""

    try:
        bot = telegram.Bot(token=settings.TELEGRAM_BOT_TOKEN)
        bot.send_message(chat_id=settings.TELEGRAM_CHAT_ID, text=message)
        logging.info(f"Message sent successfully: {message}")
    except Exception as e:
        logging.info(f"Failed to send message: {e}")
