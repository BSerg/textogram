import random
from collections import defaultdict

from advertisement.models import BannerGroup, Banner
from api.v1.advertisement.serializers import BannerSerializer


def serialize_banners():
    def get_weighted_choice(weighted_ids):
        total = sum([w for _, w in weighted_ids])
        r = random.uniform(0, total)
        upto = 0
        for _id, w in _weighted_ids:
            if w + upto >= r:
                return _id
            upto += w

    groups = BannerGroup.objects.filter(is_active=True).prefetch_related('banners')
    if not groups.exists():
        return None

    _banners = defaultdict(lambda: defaultdict(lambda: []))
    for group in groups:
        key = 'desktop' if not group.is_mobile else 'mobile'
        if group.banners.filter(is_active=True, is_ab=False).exists():
            _banners[key][group.identifier] = BannerSerializer(group.banners.filter(is_active=True),
                                                               many=True).data
        if group.banners.filter(is_active=True, is_ab=True).exists():
            _weighted_ids = group.banners.filter(is_active=True, is_ab=True).values_list('id', 'weight')
            _id = get_weighted_choice(_weighted_ids)
            if _id:
                _banners[key][group.identifier].append(BannerSerializer(group.banners.get(pk=_id)).data)

    return _banners


def serialize_banners2():
    banners = Banner.objects.filter(is_active=True)
    _banners = defaultdict(lambda: [])
    for b in banners:
        _banners['%dx%d' % (b.width, b.height)].append(BannerSerializer(b).data)
    return {'map': _banners, 'banners': BannerSerializer(banners, many=True).data}
