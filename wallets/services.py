from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable

from django.conf import settings
from django.db import transaction
from django.db.models import Q

from .models import Transaction, Wallet

CENT = Decimal("0.01")
COMMISSION_THRESHOLD = Decimal("1000.00")
COMMISSION_RATE = Decimal("0.10")


class TransferError(Exception):
    """Base class for domain-specific transfer errors."""


class WalletNotFoundError(TransferError):
    pass


class InvalidTransferError(TransferError):
    pass


class InsufficientFundsError(TransferError):
    pass


@dataclass
class TransferResult:
    transaction: Transaction
    commission_applied: bool


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _fetch_locked_wallets(wallet_ids: Iterable[int]) -> list[Wallet]:
    filters = Q(id__in=wallet_ids) | Q(owner=settings.ADMIN_WALLET_IDENTIFIER)
    wallets = list(Wallet.objects.select_for_update().filter(filters).order_by("id"))
    if not wallets:
        raise WalletNotFoundError("No wallets found for transfer")
    return wallets


def execute_transfer(*, source_wallet_id: int, destination_wallet_id: int, amount: Decimal) -> TransferResult:
    if source_wallet_id == destination_wallet_id:
        raise InvalidTransferError("Cannot transfer to the same wallet")
    normalized_amount = _quantize(amount)
    if normalized_amount <= Decimal("0.00"):
        raise InvalidTransferError("Amount must be greater than zero")

    with transaction.atomic():
        locked_wallets = _fetch_locked_wallets({source_wallet_id, destination_wallet_id})
        source_wallet = destination_wallet = admin_wallet = None

        for wallet in locked_wallets:
            if wallet.id == source_wallet_id:
                source_wallet = wallet
            elif wallet.id == destination_wallet_id:
                destination_wallet = wallet

            if wallet.owner == settings.ADMIN_WALLET_IDENTIFIER:
                admin_wallet = wallet

        if admin_wallet is None:
            raise WalletNotFoundError("Admin wallet is not configured")

        if source_wallet is None or destination_wallet is None:
            raise WalletNotFoundError("Source or destination wallet does not exist")

        commission = (
            _quantize(normalized_amount * COMMISSION_RATE) if normalized_amount > COMMISSION_THRESHOLD else Decimal("0.00")
        )
        total_debit = normalized_amount + commission

        if source_wallet.balance < total_debit:
            raise InsufficientFundsError("Insufficient funds for transfer")

        source_wallet.balance = _quantize(source_wallet.balance - total_debit)
        destination_wallet.balance = _quantize(destination_wallet.balance + normalized_amount)

        if commission > Decimal("0.00"):
            admin_wallet.balance = _quantize(admin_wallet.balance + commission)

        source_wallet.save(update_fields=["balance", "updated_at"])
        destination_wallet.save(update_fields=["balance", "updated_at"])
        if commission > Decimal("0.00"):
            admin_wallet.save(update_fields=["balance", "updated_at"])

        transaction_record = Transaction.objects.create(
            source=source_wallet,
            destination=destination_wallet,
            commission_wallet=admin_wallet if commission > Decimal("0.00") else None,
            amount=normalized_amount,
            commission_amount=commission,
            total_debited=total_debit,
        )

    return TransferResult(transaction=transaction_record, commission_applied=commission > Decimal("0.00"))
