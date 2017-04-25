from textogram import settings


def debug_processor(request):
    return {'DEBUG': settings.DEBUG}


def is_lentach_processor(request):
    return {'IS_LENTACH': settings.IS_LENTACH}
