from django.contrib import admin

from accounts.models import User, MultiAccount, MultiAccountUser, SocialLink, Subscription, PhoneCode


class UserAdmin(admin.ModelAdmin):
    pass

admin.site.register(User, UserAdmin)
admin.site.register(MultiAccount)
admin.site.register(MultiAccountUser)
admin.site.register(SocialLink)
admin.site.register(Subscription)
admin.site.register(PhoneCode )
