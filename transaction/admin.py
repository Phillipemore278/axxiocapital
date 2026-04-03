from django.contrib import admin
from .models import Coin, Wallet, Transaction

admin.site.register(Coin)
admin.site.register(Wallet)
admin.site.register(Transaction)
