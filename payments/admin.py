from django.contrib import admin

from payments.models import Account, Transaction, PayWallOrder


class AccountAdmin(admin.ModelAdmin):
    pass

admin.site.register(Account, AccountAdmin)


class TransactionAdmin(admin.ModelAdmin):
    pass

admin.site.register(Transaction, TransactionAdmin)


class PayWallOrderAdmin(admin.ModelAdmin):
    pass

admin.site.register(PayWallOrder, PayWallOrderAdmin)
