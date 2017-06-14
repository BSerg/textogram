from django.contrib import admin

from accounts.models import User, SocialLink, Subscription, PhoneCode


class UserAdmin(admin.ModelAdmin):
    pass

admin.site.register(User, UserAdmin)
admin.site.register(SocialLink)
admin.site.register(Subscription)
admin.site.register(PhoneCode )
