from django.contrib import admin

from articles.models import Article, ArticleView, ArticleImage, ArticleUserAccess


class ArticleImageInline(admin.TabularInline):
    model = ArticleImage
    extra = 0


class ArticleAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'slug']
    readonly_fields = ['slug', 'html']
    search_fields = ['title', 'slug']
    list_filter = ['status']
    inlines = [ArticleImageInline]

admin.site.register(Article, ArticleAdmin)


class ArticleViewAdmin(admin.ModelAdmin):
    list_display = ['article', 'user', 'fingerprint', 'monetization_enabled', 'created_at']

admin.site.register(ArticleView, ArticleViewAdmin)


class ArticleUserAccessAdmin(admin.ModelAdmin):
    pass

admin.site.register(ArticleUserAccess, ArticleUserAccessAdmin)
