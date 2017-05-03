#!coding:utf-8
import uuid


def generate_paywall_order_number():
    return uuid.uuid4().upper().replace('-', '')[:8]
