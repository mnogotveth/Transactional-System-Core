from __future__ import annotations

from decimal import Decimal

from rest_framework import serializers

from .models import Transaction


class TransferSerializer(serializers.Serializer):
    source_wallet_id = serializers.IntegerField()
    destination_wallet_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=19, decimal_places=2)

    def validate(self, attrs):
        if attrs["source_wallet_id"] == attrs["destination_wallet_id"]:
            raise serializers.ValidationError("source_wallet_id and destination_wallet_id must be different")
        if attrs["amount"] <= Decimal("0.00"):
            raise serializers.ValidationError("amount must be greater than zero")
        return attrs


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            "id",
            "source",
            "destination",
            "amount",
            "commission_amount",
            "total_debited",
            "created_at",
        ]
