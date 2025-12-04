from decimal import Decimal, ROUND_HALF_UP

from loader import conflicted_commands


def quantize(num: Decimal) -> Decimal:
    """Округляет до 2 знаков после запятой"""
    return num.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

# Проверяет является ли переменная числом
def is_number(s) -> bool:
    try:
        float(s)
    except ValueError:
        return False
    else:
        return True

def check_conflicted_commands(text):
    is_conflict = False
    for i in conflicted_commands:
        if(i in str(text) or i==str(text)):
            is_conflict = True
    return is_conflict