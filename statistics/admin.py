from django.contrib import admin

from statistics.models import ArticleAggregatedStatistics, ArticleViewsStatistics


class ArticleAggregatedStatisticsAdmin(admin.ModelAdmin):
    list_display = ['article', 'views', 'views_yandex', 'male_percent', 'age_17', 'age_18', 'age_25', 'age_35', 'age_45']
    search_fields = ['article__slug', 'article__title']


admin.site.register(ArticleAggregatedStatistics, ArticleAggregatedStatisticsAdmin)


class ArticleViewsStatisticsAdmin(admin.ModelAdmin):
    pass


admin.site.register(ArticleViewsStatistics, ArticleViewsStatisticsAdmin)
