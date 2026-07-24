"""Localization support for problem titles and details.

RFC 9457 explicitly anticipates that a "problem type" generator may return
localized ``title``/``detail`` text negotiated via the standard HTTP
``Accept-Language`` mechanism (section 3). This module provides a thin
integration layer on top of Django's built-in translation machinery so that
text produced by :mod:`~drf_error_response_standardizer.handler` and
:mod:`~drf_error_response_standardizer.codes` is translated according to the
requesting client's preferred language, even on API-only projects that do
not install Django's ``LocaleMiddleware``.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from django.http import HttpRequest
from django.utils import translation
from django.utils.translation import gettext as _translate_gettext


def resolve_language(request: HttpRequest) -> str:
    """Resolve the best-matching language code for ``request``.

    Uses Django's standard ``Accept-Language`` negotiation
    (:func:`django.utils.translation.get_language_from_request`), which
    respects the project's ``LANGUAGES``/``LANGUAGE_CODE`` settings.

    Args:
        request: The current request.

    Returns:
        A language code, e.g. ``"en"``, ``"fr"``, ``"pt-br"``.
    """
    return translation.get_language_from_request(request, check_path=False)


@contextmanager
def activate_for_request(request: HttpRequest) -> Iterator[None]:
    """Temporarily activate the language resolved from ``request``.

    Wrap problem-response construction in this context manager so that
    strings translated with :func:`translate` come out in the client's
    preferred language, even on projects that do not run Django's
    ``LocaleMiddleware`` (which would otherwise be responsible for
    activating a language per request).

    Args:
        request: The current request.

    Yields:
        Nothing; used purely for its context-manager side effect.
    """
    language = resolve_language(request)
    with translation.override(language):
        yield


def translate(text: str) -> str:
    """Translate ``text`` using the currently active language.

    A thin wrapper around :func:`django.utils.translation.gettext`, kept in
    this module so callers do not need a direct Django i18n import and so
    the translation catalog lookup point is centralized (see
    ``docs/faq.md`` for how to supply your own ``.po`` translations for
    this package's built-in titles and messages).

    Args:
        text: The source (English) string to translate.

    Returns:
        The translated string for the currently active language, or
        ``text`` unchanged if no translation is registered.
    """
    return _translate_gettext(text)
