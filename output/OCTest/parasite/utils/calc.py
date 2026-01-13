from decimal import Decimal

import requests
import xml.etree.ElementTree as ET
import json
from pathlib import Path

JSON_PATH = Path("../currency_rate.json")

_SERVICES = {
    "ff": 0,
    "c": Decimal("0.94"),
    "a": Decimal("0.94"),
    "s": Decimal("0.94"),
    "y": Decimal(10),
    "bs": Decimal("0.94"),
}
URL = "https://www.cbr.ru/scripts/XML_daily.asp"
PAYPAL_FIX = Decimal("5.00")
YOUTUBE_FIX = Decimal("10.00")
PAYPAL_PERCENT = Decimal("6.00")
CRYPTO_RATE = Decimal("0.98")
MAX_AMOUNT_NUM = 999999999999999999

# Получает данные курс волют из файла
def load_currency() -> tuple:
    data = json.loads(JSON_PATH.read_bytes())

    rates = data.get("rates")
    usd_to_rub = Decimal(rates.get("USD").replace(",", "."))
    usd_to_uah = Decimal(rates.get("UAH").replace(",", "."))
    usd_to_byn = Decimal(rates.get("BYN").replace(",", "."))

    return usd_to_rub, usd_to_uah, usd_to_byn

# Обновляет курсы волют из интернета
def update_rates():
    try:
        response = requests.get(URL)
        response.raise_for_status()

        # Парсим XML
        tree = ET.fromstring(response.content)

        rates = {}
        target_codes = ["USD", "UAH", "BYN"]

        for valute in tree.findall("Valute"):
            char_code = valute.find("CharCode").text

            if char_code in target_codes:
                # ЦБ отдает значение с запятой (напр. "105,1234")
                # Вашему боту именно это и нужно
                value = valute.find("Value").text
                rates[char_code] = value

        # Проверяем, всё ли нашли
        if len(rates) != 3:
            print("Внимание! Не все валюты найдены.")

        data = {"rates": rates}

        # Сохраняем в JSON
        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    except Exception as e:
        print(f"Ошибка при обновлении: {e}")

