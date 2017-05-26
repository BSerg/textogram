from common.models import CounterCode
from textogram import settings
from textogram.settings import BOT_USER_AGENTS


def extra_context_processor(request):
    return {
        'DEBUG': settings.DEBUG,
        'IS_LENTACH': settings.IS_LENTACH,
        'COUNTERS': CounterCode.objects.filter(is_active=True)
    }


def is_bot_processor(request):
    is_bot = False
    user_agent = request.META.get('HTTP_USER_AGENT', None)
    if user_agent:
        for bot_name in BOT_USER_AGENTS:
            if bot_name in user_agent.lower():
                is_bot = True
    return {'IS_BOT': is_bot}
