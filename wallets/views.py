from __future__ import annotations

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import TransactionSerializer, TransferSerializer
from .services import InsufficientFundsError, InvalidTransferError, TransferError, WalletNotFoundError, execute_transfer
from .tasks import send_transfer_notification


class TransferView(APIView):
    serializer_class = TransferSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = execute_transfer(**serializer.validated_data)
        except (WalletNotFoundError, InvalidTransferError, InsufficientFundsError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except TransferError as exc:
            return Response({"detail": "Transfer failed", "reason": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        send_transfer_notification.delay(str(result.transaction.id))

        transaction_payload = TransactionSerializer(result.transaction).data
        transaction_payload["commission_applied"] = result.commission_applied

        return Response(transaction_payload, status=status.HTTP_201_CREATED)
