from django.contrib import admin

from accounts.models import User, SocialLink, Subscription, PhoneCode
from payments.models import Account


class AccountInline(admin.StackedInline):
    model = Account
    extra = 0


class UserAdmin(admin.ModelAdmin):
    inlines = [AccountInline]


admin.site.register(User, UserAdmin)
admin.site.register(SocialLink)
admin.site.register(Subscription)
admin.site.register(PhoneCode )
