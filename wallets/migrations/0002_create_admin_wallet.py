from django.conf import settings
from django.db import migrations


def create_admin_wallet(apps, schema_editor):
    Wallet = apps.get_model("wallets", "Wallet")
    Wallet.objects.update_or_create(
        owner=settings.ADMIN_WALLET_IDENTIFIER,
        defaults={"is_system": True},
    )


class Migration(migrations.Migration):

    dependencies = [
        ("wallets", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_admin_wallet, migrations.RunPython.noop),
    ]
