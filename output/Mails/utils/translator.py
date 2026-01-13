from fluent_compiler.bundle import FluentBundle
from fluentogram import TranslatorHub, FluentTranslator
from ..loader import prefix_folder
test_file_ids = {
    "start_message-file_id": "AgACAgIAAxkBAAIBBWklkdEyA6Mry-AZ4RyOtZXlRNWoAALdDGsbwAkxSYTWg-Hn0ifHAQADAgADeQADNgQ",
    "faq-img_paypal_beatstars": "AgACAgIAAxkBAAIBB2klkfrKKmqiztLVU6ktT715BDBCAALeDGsbwAkxSQpU7DIkU-NzAQADAgADeQADNgQ",
    "faq-img_bs_wallet": "AgACAgIAAxkBAAIBCWklkhStnnBNIOYjqJl2HNEvFvSgAALfDGsbwAkxSZNBAAGpb0ULHwEAAwIAA3kAAzYE",
    "monetization-img_youtube": "AgACAgIAAxkBAAJ-IWkhjY-AyJ8_QfeVgBPfy2S5DLICAAI5DWsbp4MISfEXhZkolYCHAQADAgADeQADNgQ",
    "monetization-img_tiktok": "AgACAgIAAxkBAAIBBWklkdEyA6Mry-AZ4RyOtZXlRNWoAALdDGsbwAkxSYTWg-Hn0ifHAQADAgADeQADNgQ",

}
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
