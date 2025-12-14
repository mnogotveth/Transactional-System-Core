from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Wallet",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("owner", models.CharField(max_length=255, unique=True)),
                (
                    "balance",
                    models.DecimalField(
                        decimal_places=2, default=Decimal("0.00"), max_digits=19
                    ),
                ),
                ("is_system", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["id"],
            },
        ),
        migrations.CreateModel(
            name="Transaction",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=19)),
                ("commission_amount", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=19)),
                ("total_debited", models.DecimalField(decimal_places=2, max_digits=19)),
                (
                    "status",
                    models.CharField(
                        choices=[("completed", "Completed"), ("failed", "Failed")],
                        default="completed",
                        max_length=24,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "commission_wallet",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="commission_transactions",
                        to="wallets.wallet",
                    ),
                ),
                (
                    "destination",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="incoming_transactions",
                        to="wallets.wallet",
                    ),
                ),
                (
                    "source",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="outgoing_transactions",
                        to="wallets.wallet",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
