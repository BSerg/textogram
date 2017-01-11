#! coding:utf-8
from __future__ import unicode_literals
from rest_framework import viewsets
from api.v1.notifications.serializers import NotificationSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response

from notifications.models import Notification


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    queryset = Notification.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @list_route(methods=['GET'])
    def check_new(self, request):
        qs = self.get_queryset().filter(is_read=False)
        obj = qs.first()
        return Response({'count': qs.count(), 'last': NotificationSerializer(qs.first()).data if obj else None})

    @detail_route(methods=['POST'])
    def mark_read(self, request, pk=None):
        obj = self.get_object()
        obj.is_read = True
        obj.save()
        return Response(NotificationSerializer(obj).data)

    @list_route(methods=['POST'])
    def mark_read_all(self, requet):
        qs = self.get_queryset().filter(is_read=False)
        qs.update(is_read=True)
        return Response({'msg': 'success'})



