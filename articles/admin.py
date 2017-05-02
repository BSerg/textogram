from django.contrib import admin

from articles.models import Article, ArticleView


class ArticleAdmin(admin.ModelAdmin):
    list_display = ['id', 'slug', 'get_title']
    readonly_fields = ['slug', 'html']

    def get_title(self, obj):
        return obj.content.get('title')

admin.site.register(Article, ArticleAdmin)


class ArticleViewAdmin(admin.ModelAdmin):
    list_display = ['article', 'user', 'fingerprint', 'monetization_enabled', 'created_at']

admin.site.register(ArticleView, ArticleViewAdmin)
