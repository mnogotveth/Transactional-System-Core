from django.urls import path

from .views import TransferView

urlpatterns = [
    path("transfer", TransferView.as_view(), name="wallet-transfer"),
]
