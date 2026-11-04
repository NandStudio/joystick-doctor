from __future__ import annotations

import ssl
import urllib.error
import urllib.request

import certifi
import truststore


def _native_context() -> ssl.SSLContext:
    # OpenSSL only sees roots already in the Windows store. The native check
    # can fetch a missing root and trusts what the system trusts.
    return truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)


def _bundled_context() -> ssl.SSLContext:
    return ssl.create_default_context(cafile=certifi.where())


def urlopen(request: urllib.request.Request, timeout: float):
    try:
        return urllib.request.urlopen(request, timeout=timeout, context=_native_context())
    except urllib.error.URLError as exc:
        if not isinstance(exc.reason, ssl.SSLCertVerificationError):
            raise
    return urllib.request.urlopen(request, timeout=timeout, context=_bundled_context())
