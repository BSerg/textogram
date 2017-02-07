from django.contrib import admin

from articles.models import Article


class ArticleAdmin(admin.ModelAdmin):
    list_display = ['id', 'slug', 'get_title']
    readonly_fields = ['slug', 'html']

    def get_title(self, obj):
        return obj.content.get('title')

admin.site.register(Article, ArticleAdmin)
