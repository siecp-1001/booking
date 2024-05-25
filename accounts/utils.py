from django.urls import URLPattern, URLResolver, get_resolver

def list_urls(url_patterns=None, prefix=''):
    if url_patterns is None:
        url_patterns = get_resolver().url_patterns
    urls = []
    for pattern in url_patterns:
        if isinstance(pattern, URLPattern):
            urls.append(prefix + str(pattern.pattern))
        elif isinstance(pattern, URLResolver):
            urls.extend(list_urls(pattern.url_patterns, prefix + str(pattern.pattern)))
    return urls
