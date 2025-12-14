from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from django.core.validators import MinValueValidator
from django.db import models


class Wallet(models.Model):
    owner = models.CharField(max_length=255, unique=True)
    balance = models.DecimalField(
        max_digits=19,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    is_system = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:  
        return f"{self.owner} ({self.pk})"


class Transaction(models.Model):
    class Status(models.TextChoices):
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    source = models.ForeignKey(Wallet, on_delete=models.PROTECT, related_name="outgoing_transactions")
    destination = models.ForeignKey(
        Wallet,
        on_delete=models.PROTECT,
        related_name="incoming_transactions",
    )
    commission_wallet = models.ForeignKey(
        Wallet,
        on_delete=models.PROTECT,
        related_name="commission_transactions",
        null=True,
        blank=True,
    )
    amount = models.DecimalField(max_digits=19, decimal_places=2)
    commission_amount = models.DecimalField(max_digits=19, decimal_places=2, default=Decimal("0.00"))
    total_debited = models.DecimalField(max_digits=19, decimal_places=2)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.COMPLETED)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def describes_commission(self) -> bool:
        return self.commission_amount > 0 and self.commission_wallet_id is not None
