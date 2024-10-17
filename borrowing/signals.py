import asyncio

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from borrowing.models import Borrowing
from utils.telegram import send_telegram_message


@receiver(post_save, sender=Borrowing)
def send_borrowing_notification(sender, instance, created, **kwargs):
    if created:
        transaction.on_commit(lambda: _send_borrowing_notification(instance))


def _send_borrowing_notification(instance):
    message = (f"New borrowing created: {instance.books_in_borrowing} "
               f"by {instance.user.full_name}")
    asyncio.run(send_telegram_message(message))
