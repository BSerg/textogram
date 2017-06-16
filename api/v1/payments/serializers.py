#! coding: utf-8

from __future__ import unicode_literals

from rest_framework import serializers

from payments.models import PayWallOrder


class PayWallOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayWallOrder
        fields = ['id', 'article', 'customer', 'status', 'price', 'currency', 'created_at']