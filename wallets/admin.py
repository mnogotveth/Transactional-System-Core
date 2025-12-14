from django.contrib import admin

from .models import Transaction, Wallet


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ("id", "owner", "balance", "is_system", "updated_at")
    search_fields = ("owner",)
    list_filter = ("is_system",)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "source",
        "destination",
        "amount",
        "commission_amount",
        "total_debited",
        "status",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("id", "source__owner", "destination__owner")
