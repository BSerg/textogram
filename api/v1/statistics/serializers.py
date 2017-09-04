from django.db.models import F
from django.db.models import Sum, Max
from redis import StrictRedis
from rest_framework import serializers

from accounts.models import User
from articles.models import Article
from textogram.settings import REDIS_CACHE_KEY_PREFIX, REDIS_CACHE_HOST, REDIS_CACHE_PORT, REDIS_CACHE_DB

r = StrictRedis(host=REDIS_CACHE_HOST, port=REDIS_CACHE_PORT, db=REDIS_CACHE_DB)


class UserCommonStatisticsSerializer(serializers.ModelSerializer):
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
    age_55 = serializers.SerializerMethodField()

    def get_data(self, obj, field, typ=int):
        key = '%s:author:%s:statistics:views' % (REDIS_CACHE_KEY_PREFIX, obj.id)
        res = r.hget(key, field)
        return typ(res) if res else None

    def get_views_today(self, obj):
        return self.get_data(obj, 'views_today')

    def get_views_month(self, obj):
        return self.get_data(obj, 'views_month')

    def get_views_last_month(self, obj):
        return self.get_data(obj, 'views_prev_month')

    def get_views_total(self, obj):
        return self.get_data(obj, 'views_total')

    def get_male_percent(self, obj):
        total_views = self.get_views_total(obj)
        s = 0

        for article in obj.articles.all():
            key = '%s:article:%s:statistics:common' % (REDIS_CACHE_KEY_PREFIX, article.slug)
            male_persent = r.hget(key, 'male_percent')
            views = r.hget(key, 'views_total')
            if male_persent is not None and views is not None:
                s += float(male_persent) * int(views)

        return s / int(total_views) if total_views else None

    def _get_age(self, obj, field_name=None):
        total_views = self.get_views_total(obj)
        s = 0

        for article in obj.articles.all():
            key = '%s:article:%s:statistics:common' % (REDIS_CACHE_KEY_PREFIX, article.slug)
            age_views = r.hget(key, field_name)
            views = r.hget(key, 'views_total')
            if age_views is not None and views is not None:
                s += float(age_views) * float(views)

        return s / float(total_views) if total_views else None

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

    def get_age_55(self, obj):
        return self._get_age(obj, 'age_55')

    class Meta:
        model = User
        fields = ['views_today', 'views_month', 'views_last_month', 'views_total',
                  'male_percent', 'age_17', 'age_18', 'age_25', 'age_35', 'age_45', 'age_55']


class ArticleCommonStatisticsSerializer(serializers.ModelSerializer):
    views_today = serializers.SerializerMethodField()
    views_month = serializers.SerializerMethodField()
    views_last_month = serializers.SerializerMethodField()
    views_total = serializers.SerializerMethodField()

    def get_data(self, article_slug):
        key = '%s:article:%s:statistics:common' % (REDIS_CACHE_KEY_PREFIX, article_slug)
        return r.hgetall(key)

    def get_views_today(self, obj):
        return self.get_data(obj.slug).get('views_today')

    def get_views_month(self, obj):
        return self.get_data(obj.slug).get('views_month')

    def get_views_last_month(self, obj):
        return self.get_data(obj.slug).get('views_prev_month')

    def get_views_total(self, obj):
        return self.get_data(obj.slug).get('views_total')

    class Meta:
        model = Article
        fields = ['id', 'slug', 'title', 'views_today', 'views_month', 'views_last_month', 'views_total']


class ArticleStatisticsSerializer(ArticleCommonStatisticsSerializer):
    male_percent = serializers.SerializerMethodField()

    age_17 = serializers.SerializerMethodField()
    age_18 = serializers.SerializerMethodField()
    age_25 = serializers.SerializerMethodField()
    age_35 = serializers.SerializerMethodField()
    age_45 = serializers.SerializerMethodField()
    age_55 = serializers.SerializerMethodField()

    views_chart = serializers.SerializerMethodField()

    def get_male_percent(self, obj):
        return self.get_data(obj.slug).get('male_percent')

    def get_age_17(self, obj):
        return self.get_data(obj.slug).get('age_17')

    def get_age_18(self, obj):
        return self.get_data(obj.slug).get('age_18')

    def get_age_25(self, obj):
        return self.get_data(obj.slug).get('age_25')

    def get_age_35(self, obj):
        return self.get_data(obj.slug).get('age_35')

    def get_age_45(self, obj):
        return self.get_data(obj.slug).get('age_45')

    def get_age_55(self, obj):
        return self.get_data(obj.slug).get('age_55')

    def get_views_chart(self, obj):
        key = '%s:article:%s:statistics:views' % (REDIS_CACHE_KEY_PREFIX, obj.slug)
        return [(int(i.split(':')[0]), int(i.split(':')[1])) for i in r.zrangebyscore(key, '-inf', '+inf')]

    class Meta:
        model = Article
        fields = ['id', 'slug', 'title', 'views_today', 'views_month', 'views_last_month', 'views_total',
                  'male_percent', 'age_17', 'age_18', 'age_25', 'age_35', 'age_45', 'age_55', 'views_chart']


class ArticleStatsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Article
        fields = ['id', 'slug', 'title']