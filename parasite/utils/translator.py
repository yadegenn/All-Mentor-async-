from fluent_compiler.bundle import FluentBundle
from fluentogram import TranslatorHub, FluentTranslator

from loader import prefix_folder

translator_hub = None

def translator_create_or_update():
    global translator_hub
    translator_hub = TranslatorHub(
        locales_map={
            "ru": "ru"
        },
        translators=[
            FluentTranslator(
                locale="ru",
                translator=FluentBundle.from_files(
                    locale="ru-RU", filenames=[f"{prefix_folder}locales/ru.ftl"]
                )
            ),
        ],
        root_locale="ru"
    )
translator_create_or_update()
def _(key: str, **kwargs) -> str:
    translator = translator_hub.get_translator_by_locale("ru")
    return translator.get(key, **kwargs)