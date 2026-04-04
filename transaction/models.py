from django.db import models
from decimal import Decimal
import qrcode
from io import BytesIO
from django.core.files import File

class Coin(models.Model):
    name = models.CharField(max_length=50)
    symbol = models.CharField(max_length=10, unique=True)
    network = models.CharField(max_length=50, blank=True, null=True)
    icon = models.ImageField(upload_to="coin_icons/", blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.symbol})"


class Wallet(models.Model):

    coin = models.ForeignKey(
        Coin,
        on_delete=models.CASCADE,
        related_name="wallets"
    )

    wallet_address = models.CharField(max_length=200)

    qr_code = models.ImageField(
        upload_to="wallet_qr/",
        blank=True,
        null=True
    )

    def save(self, *args, **kwargs):

        qr = qrcode.make(self.wallet_address)

        buffer = BytesIO()
        qr.save(buffer, format="PNG")

        buffer.seek(0)  # VERY IMPORTANT

        filename = f"{self.coin.symbol}_qr.png"

        self.qr_code.save(filename, File(buffer), save=False)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.coin.symbol} Wallet"


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('DEPOSIT', 'Deposit'),
        ('WITHDRAW', 'Withdraw'),
        ('DIVIDEND', 'Dividend'),
        ('REBALANCE', 'Rebalance'),
    ]

    CURRENCY_CHOICES = [
        ('USD', 'USD'),
        ('EUR', 'EUR'),
        ('GBP', 'GBP'),
    ]

    PAYMENT_METHODS = [
        ('WIRE', 'Wire Transfer'),
        ('CRYPTO', 'Crypto'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SUCCESSFUL', 'Successful'),
        ('FAILED', 'Failed'),
    ]

    COIN_CHOICES = [
        ('BTC', 'Bitcoin'),
        ('ETH', 'Ethereum'),
        ('USDT', 'USDT'),
    ]

    portfolio = models.ForeignKey(
        'customer.Portfolio',
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPES
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS,
        null=True,
        blank=True
    )
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        null=True,
        blank=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    amount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal('0')
    )
    balance = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal('0')
    )

    destination_bank = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )
    account_number = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )
    coin_type = models.CharField(
        max_length=10,
        choices=COIN_CHOICES,
        null=True,
        blank=True
    )
    coin = models.ForeignKey(
    Coin,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    wallet_id = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.transaction_type} - {self.payment_method} - {self.amount} ({self.status})"