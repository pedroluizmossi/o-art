from urllib.parse import urlparse
from urllib.request import Request, urlopen


def safe_urlopen(url_or_req, *args, **kwargs):
    # Se for Request, obtenha a string URL
    if isinstance(url_or_req, Request):
        url = url_or_req.full_url  # ou url_or_req.get_full_url()
    elif isinstance(url_or_req, str):
        url = url_or_req
    else:
        raise TypeError("URL deve ser string ou urllib.request.Request")
    allowed_schemes = ["http", "https"]
    parsed = urlparse(url)
    if parsed.scheme not in allowed_schemes:
        raise ValueError(f"Invalid URL scheme: {parsed.scheme}.")
    return urlopen(url_or_req, *args, **kwargs)# nosec: esquema já validado acima
