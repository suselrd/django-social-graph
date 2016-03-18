from django.http import HttpResponse


def someview(request):
    from django.core.cache import get_cache
    cache = get_cache('redis_cache.cache://127.0.0.1:6379')
    cache.set("foo", "bar")
    return HttpResponse("Pants")
