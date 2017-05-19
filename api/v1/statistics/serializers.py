import pytz
from datetime import timedelta

from dateutil import relativedelta
from django.db.models import F
from django.db.models import Sum, Max
from django.utils import timezone
from rest_framework import serializers

from accounts.models import User
from articles.models import Article
from statistics.models import ArticleViewsStatistics
from statistics.utils import get_article_day_views_chart_data, get_article_month_views_chart_data, \
    get_article_views_chart_data


class UserCommonStatisticsSerializer(serializers.ModelSerializer):
    date = serializers.SerializerMethodField()
    views_today = serializers.SerializerMethodField()
    views_month = serializers.SerializerMethodField()
    views_last_month = serializers.SerializerMethodField()
    views_total = serializers.SerializerMethodField()
    male_percent = serializers.SerializerMethodField()
    age_17 = serializers.SerializerMethodField()
    age_18 = serializers.SerializerMethodField()
    age_25 = serializers.SerializerMethodField()
    age_35 = serializers.SerializerMethodField()
    age_45 = serializers.SerializerMethodField()

    def get_date(self, obj):
        return obj.articles.aggregate(date=Max('statistics__date_to'))['date']

    def get_views_today(self, obj):
        return obj.articles.aggregate(views=Sum('statistics__views_today'))['views']

    def get_views_month(self, obj):
        return obj.articles.aggregate(views=Sum('statistics__views_month'))['views']

    def get_views_last_month(self, obj):
        return obj.articles.aggregate(views=Sum('statistics__views_last_month'))['views']

    def get_views_total(self, obj):
        return obj.articles.aggregate(views=Sum('statistics__views'))['views']

    def get_male_percent(self, obj):
        total_views = self.get_views_total(obj)
        return obj.articles.aggregate(male_percent=Sum(F('statistics__male_percent') * F('statistics__views') / total_views))['male_percent']

    def _get_age(self, obj, field_name=None):
        if field_name:
            total_views = self.get_views_total(obj)
            return obj.articles.aggregate(percent=Sum(F('statistics__%s' % field_name) * F('statistics__views') / total_views))['percent']

    def get_age_17(self, obj):
        return self._get_age(obj, 'age_17')

    def get_age_18(self, obj):
        return self._get_age(obj, 'age_18')

    def get_age_25(self, obj):
        return self._get_age(obj, 'age_25')

    def get_age_35(self, obj):
        return self._get_age(obj, 'age_35')

    def get_age_45(self, obj):
        return self._get_age(obj, 'age_45')

    class Meta:
        model = User
        fields = ['date', 'views_today', 'views_month', 'views_last_month', 'views_total',
                  'male_percent', 'age_17', 'age_18', 'age_25', 'age_35', 'age_45']


class ArticleCommonStatisticsSerializer(serializers.ModelSerializer):
    views_today = serializers.IntegerField(source='statistics.views_today')
    views_month = serializers.IntegerField(source='statistics.views_month')
    views_last_month = serializers.IntegerField(source='statistics.views_last_month')
    views_total = serializers.IntegerField(source='statistics.views')

    class Meta:
        model = Article
        fields = ['id', 'slug', 'title', 'views_today', 'views_month', 'views_last_month', 'views_total']


class ArticleStatisticsSerializer(serializers.ModelSerializer):
    views_today = serializers.IntegerField(source='statistics.views_today')
    views_month = serializers.IntegerField(source='statistics.views_month')
    views_last_month = serializers.IntegerField(source='statistics.views_last_month')
    views_total = serializers.IntegerField(source='statistics.views')

    male_percent = serializers.FloatField(source='statistics.male_percent')

    age_17 = serializers.FloatField(source='statistics.age_17')
    age_18 = serializers.FloatField(source='statistics.age_18')
    age_25 = serializers.FloatField(source='statistics.age_25')
    age_35 = serializers.FloatField(source='statistics.age_35')
    age_45 = serializers.FloatField(source='statistics.age_45')

    today_chart = serializers.SerializerMethodField()
    month_chart = serializers.SerializerMethodField()
    last_month_chart = serializers.SerializerMethodField()
    full_chart = serializers.SerializerMethodField()

    def get_today_chart(self, obj):
        return get_article_day_views_chart_data(obj, timezone.now())

    def get_month_chart(self, obj):
        return get_article_month_views_chart_data(obj, timezone.now())

    def get_last_month_chart(self, obj):
        return get_article_month_views_chart_data(obj, timezone.now() - relativedelta.relativedelta(months=1))

    def get_full_chart(self, obj):
        return get_article_views_chart_data(obj)

    class Meta:
        model = Article
        fields = ['id', 'slug', 'title', 'views_today', 'views_month', 'views_last_month', 'views_total',
                  'male_percent', 'age_17', 'age_18', 'age_25', 'age_35', 'age_45',
                  'today_chart', 'month_chart', 'last_month_chart', 'full_chart']
