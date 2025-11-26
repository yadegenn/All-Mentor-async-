import requests
import xml.etree.ElementTree as ET
import json
from pathlib import Path

JSON_PATH = Path("../currency_rate.json")


URL = "https://www.cbr.ru/scripts/XML_daily.asp"


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


if __name__ == "__main__":
    update_rates()