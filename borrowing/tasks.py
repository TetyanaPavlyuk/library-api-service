import asyncio
from datetime import date, timedelta
from celery import shared_task

from borrowing.models import Borrowing
from utils.telegram import send_telegram_message


@shared_task
def check_borrowings_overdue():
    overdue_date = date.today() + timedelta(days=1)
    overdue_borrowings = Borrowing.objects.filter(
        expected_return_date__lte=overdue_date, actual_return_date__isnull=True
    )

    if overdue_borrowings.exists():
        for borrowing in overdue_borrowings:
            message = (
                f"Overdue borrowing:\n"
                f"User: {borrowing.user.full_name}\n"
                f"Books: {[book.title for book in borrowing.book.all()]}\n"
                f"Expected return: {borrowing.expected_return_date}\n"
                f"Borrow on: {borrowing.borrow_date}\n\n"
            )
            asyncio.run(send_telegram_message(message))
    else:
        asyncio.run(send_telegram_message("No borrowings overdue today."))
