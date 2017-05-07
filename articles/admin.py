from django.contrib import admin

from articles.models import Article, ArticleView


class ArticleAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'slug']
    readonly_fields = ['slug', 'html']
    search_fields = ['title', 'slug']
    list_filter = ['status']

admin.site.register(Article, ArticleAdmin)


class ArticleViewAdmin(admin.ModelAdmin):
    list_display = ['article', 'user', 'fingerprint', 'monetization_enabled', 'created_at']

admin.site.register(ArticleView, ArticleViewAdmin)
