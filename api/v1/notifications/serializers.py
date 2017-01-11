from rest_framework import serializers
from notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):

    date = serializers.SerializerMethodField()

    def get_date(self, obj):
        return obj.created_at

    class Meta:
        model = Notification
        fields = ['id', 'text', 'is_read', 'date']
