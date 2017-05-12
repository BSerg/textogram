from textogram import settings
from textogram.settings import BOT_USER_AGENTS


def debug_processor(request):
    return {
        'DEBUG': settings.DEBUG,
    }


def is_lentach_processor(request):
    return {'IS_LENTACH': settings.IS_LENTACH}


def is_bot_processor(request):
    is_bot = False
    user_agent = request.META.get('HTTP_USER_AGENT', None)
    if user_agent:
        for bot_name in BOT_USER_AGENTS:
            if bot_name in user_agent.lower():
                is_bot = True
                print bot_name
    return {'IS_BOT': is_bot}
