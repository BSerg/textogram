from django.contrib import admin

from accounts.models import User, MultiAccount, MultiAccountUser, SocialLink


class UserAdmin(admin.ModelAdmin):
    pass

admin.site.register(User, UserAdmin)
admin.site.register(MultiAccount)
admin.site.register(MultiAccountUser)
admin.site.register(SocialLink)
