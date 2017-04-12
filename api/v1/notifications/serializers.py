from rest_framework import serializers
from notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):

    date = serializers.SerializerMethodField(read_only=True)

    def get_date(self, obj):
        return obj.created_at

    class Meta:
        model = Notification
        fields = ['id', 'text', 'is_read', 'date']
        read_only_fields = ['id', 'text', 'date']
