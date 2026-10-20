import logging
from pathlib import Path
from typing import Any

from fluent.runtime import FluentBundle, FluentResource

logger = logging.getLogger(__name__)

LOCALES_DIR = Path(__file__).parent / "locales"


class Translator:
    def __init__(self, bundle: FluentBundle, fallback: FluentBundle | None, locale: str, global_args: dict[str, Any]):
        self._bundle = bundle
        self._fallback = fallback
        self.locale = locale
        self._global_args = global_args

    def __call__(self, key: str, **kwargs: Any) -> str:
        for bundle in (self._bundle, self._fallback):
            if bundle is not None and bundle.has_message(key):
                message = bundle.get_message(key)
                text, errors = bundle.format_pattern(message.value, {**self._global_args, **kwargs})
                if errors:
                    logger.warning("Fluent errors in %s/%s: %s", self.locale, key, errors)
                return text
        logger.error("Missing translation key %s for %s", key, self.locale)
        return key


class I18n:
    def __init__(self, default_locale: str = "ru", global_args: dict[str, Any] | None = None, path: Path = LOCALES_DIR):
        self.default_locale = default_locale
        self._global_args = global_args or {}
        self._bundles: dict[str, FluentBundle] = {}
        for locale_dir in sorted(p for p in path.iterdir() if p.is_dir()):
            bundle = FluentBundle([locale_dir.name], use_isolating=False)
            for ftl in sorted(locale_dir.glob("*.ftl")):
                bundle.add_resource(FluentResource(ftl.read_text(encoding="utf-8")))
            self._bundles[locale_dir.name] = bundle

    @property
    def locales(self) -> list[str]:
        return list(self._bundles)

    def translator(self, locale: str | None) -> Translator:
        locale = locale if locale in self._bundles else self.default_locale
        fallback = self._bundles[self.default_locale] if locale != self.default_locale else None
        return Translator(self._bundles[locale], fallback, locale, self._global_args)
