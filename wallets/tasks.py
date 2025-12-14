from __future__ import annotations

import logging
import time

from celery import shared_task

from .models import Transaction

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=False,
    retry_kwargs={"max_retries": 3},
    default_retry_delay=3,
)
def send_transfer_notification(self, transaction_id: str) -> None:
    """Simulate a long-running notification delivery."""
    time.sleep(5)
    transaction = Transaction.objects.select_related("destination").get(pk=transaction_id)
    logger.info(
        "Notified wallet %s about incoming amount %s",
        transaction.destination_id,
        transaction.amount,
    )
