import re
import logging
from typing import Dict, Optional, Tuple, List

logger = logging.getLogger(__name__)


# парсинг сообщения и извлечение данных
def parse_message(text: str) -> Dict[str, str]:
    data = {}

    # Удаляем все лишние пробелы в начале и конце строк
    text = text.strip()

    # Разбиваем текст на строки
    lines = text.split('\n')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Пытаемся найти паттерн: "поле": "значение"
        quoted_match = re.match(r'"([^"]+)":\s*"([^"]+)"', line, re.IGNORECASE)
        if quoted_match:
            field_name = quoted_match.group(1).strip().lower()
            field_value = quoted_match.group(2).strip()

            # Для дат убираем кавычки и оставляем только дату
            if field_name in ['дата заказа', 'крайний срок']:
                field_value = field_value.replace(
                    '"', '').replace("'", "").split()[0]

            data[field_name] = field_value
            logger.info(
                f"Обнаружено поле (с кавычками): {field_name} = {field_value}")
            continue

        # Пытаемся найти паттерн: поле: значение (без кавычек)
        unquoted_match = re.match(r'([^:]+):\s*(.+)', line, re.IGNORECASE)
        if unquoted_match:
            field_name = unquoted_match.group(1).strip().lower()
            field_value = unquoted_match.group(2).strip()

            # Убираем кавычки из названия поля, если они есть
            if field_name.startswith('"') and field_name.endswith('"'):
                field_name = field_name[1:-1].strip()

            # Убираем кавычки из значения, если они есть
            if field_value.startswith('"') and field_value.endswith('"'):
                field_value = field_value[1:-1].strip()
            elif field_value.startswith("'") and field_value.endswith("'"):
                field_value = field_value[1:-1].strip()

            # Для дат убираем кавычки и оставляем только дату
            if field_name in ['дата заказа', 'крайний срок']:
                field_value = field_value.replace(
                    '"', '').replace("'", "").split()[0]

            # Пропускаем пустые значения
            if not field_value:
                continue

            data[field_name] = field_value
            logger.info(
                f"Обнаружено поле (без кавычек): {field_name} = {field_value}")

    return data


# форматирование описания карточки
def format_card_description(data: Dict[str, str]) -> str:
    description = f"""📋 **Детали заказа:**

"""

    # Стандартные поля с красивыми labels
    fields_mapping = {
        "имя карточки": "📝 **Название карточки:**",
        "дата заказа": "📅 **Дата заказа:**",
        "крайний срок": "⏰ **Крайний срок:**",
        "клиент": "👥 **Клиент:**",
        "цвет": "🎨 **Цвет:**",
        "имя": "👤 **Имя:**",
        "телефон": "📞 **Телефон:**",
        "дополнительно": "📝 **Дополнительно:**",
        "telegram пользователь": "👤 **Создал:**"
    }

    # Сначала добавляем стандартные поля
    for field_key, field_label in fields_mapping.items():
        if field_key in data:
            description += f"{field_label} {data[field_key]}\n"

    # Затем добавляем все остальные поля (которые не являются стандартными)
    other_fields = [key for key in data.keys() if key not in fields_mapping]
    if other_fields:
        description += "\n📋 **Дополнительные поля:**\n"
        for field in other_fields:
            description += f"• **{field}:** {data[field]}\n"

    return description


# проверка наличия обязательных полей
def validate_required_fields(data: Dict[str, str], required_fields: List[str]) -> Tuple[bool, List[str]]:
    missing_fields = [
        field for field in required_fields if field not in data or not data[field]]
    return len(missing_fields) == 0, missing_fields
