from django.contrib import admin

from articles.models import Article, ArticleContent


class ArticleContentInline(admin.StackedInline):
    model = ArticleContent
    extra = 0
    fields = ['id', 'position', 'created_at', 'last_modified']
    readonly_fields = ['id', 'created_at', 'last_modified']


class ArticleAdmin(admin.ModelAdmin):
    inlines = [ArticleContentInline]


admin.site.register(Article, ArticleAdmin)
