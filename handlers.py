import logging
from aiogram import types
from aiogram.filters import Command
from aiogram.types import Message

from trello_api import TrelloManager
from utils import parse_message, format_card_description, validate_required_fields
from config import Config

logger = logging.getLogger(__name__)

# Инициализация менеджера Trello будет в основном файле
trello_manager = None


def setup_handlers(dp, manager):
    """Настройка обработчиков для диспетчера"""
    global trello_manager
    trello_manager = manager

    # Регистрируем обработчики команд
    dp.message.register(cmd_start, Command("start"))
    dp.message.register(cmd_help, Command("help"))
    dp.message.register(cmd_fields, Command("fields"))
    dp.message.register(handle_message)

    return dp


# ... импорты и остальной код ...

# обработка команды start ---------------------------------
async def cmd_start(message: Message):
    welcome_text = """👋 <b>Привет! Я бот для создания заказов в Trello.</b>

📝 <b>Отправьте мне сообщение с данными заказа в одном из форматов:</b>

<b>С кавычками:</b>
"имя карточки": "Название заказа"
"дата заказа": "10.09.2025"
"крайний срок": "25.10.2025"
"клиент": "Имя клиента"
"цвет": "цвет"
"телефон": "+7 XXX XXX XXXX"
"дополнительно": "информация"

<b>Без кавычек:</b>
имя карточки: Название заказа
дата заказа: 10.09.2025
крайний срок: 25.10.2025
клиент: Имя клиента
цвет: цвет
телефон: +7 XXX XXX XXXX
дополнительно: информация

💡 <b>Обязательное поле:</b> имя карточки
💡 <b>Автоматически добавляется</b> ваше имя пользователя Telegram
💡 <b>Даты можно указывать</b> без кавычек."""
    await message.answer(welcome_text, parse_mode="HTML")


# обработка команды help ----------------------------------
async def cmd_help(message: Message):
    help_text = """<b>Помощь по использованию бота:</b>

<b>Отправьте сообщение с данными заказа в одном из форматов:</b>

<b>С кавычками:</b>
"имя карточки": "Название заказа"
"дата заказа": "10.09.2025"
"крайний срок": "25.10.2025"
"клиент": "Имя клиента"
"цвет": "цвет"
"телефон": "+7 XXX XXX XXXX"
"дополнительно": "информация"

<b>Без кавычек:</b>
имя карточки: Название заказа
дата заказа: 10.09.2025
крайний срок: 25.10.2025
клиент: Имя клиента
цвет: цвет
телефон: +7 XXX XXX XXXX
дополнительно: информация

<b>Обязательное поле:</b> имя карточки
<b>Автоматически добавляется</b> ваше имя пользователя Telegram
<b>Даты можно указывать</b> без кавычек.

<b>Используйте</b> /fields <b>чтобы посмотреть доступные кастомные поля.</b>"""
    await message.answer(help_text, parse_mode="HTML")


# обработка команды fields --------------------------------
async def cmd_fields(message: Message):
    """Показать доступные кастомные поля"""
    try:
        custom_fields = trello_manager.get_custom_fields(
            Config.TRELLO_BOARD_ID)

        if custom_fields:
            fields_list = "\n".join(
                [f"• {field_name} ({field_info['type']})" for field_name, field_info in custom_fields.items()])
            response_text = f"<b>📊 Доступные кастомные поля на доске:</b>\n\n{fields_list}\n\n<b>Всего полей:</b> {len(custom_fields)}"

            # Проверяем есть ли поле для Telegram пользователя
            telegram_field_lower = Config.TELEGRAM_USER_FIELD.lower()
            if telegram_field_lower in custom_fields:
                response_text += f"\n\n✅ <b>Поле для Telegram пользователя найдено:</b> '{Config.TELEGRAM_USER_FIELD}'"
            else:
                response_text += f"\n\nℹ️ <b>Поле для Telegram пользователя не найдено:</b> '{Config.TELEGRAM_USER_FIELD}'. Имя пользователя будет добавляться только в описание."

            await message.answer(response_text, parse_mode="HTML")
        else:
            await message.answer("❌ <b>Не удалось получить кастомные поля или их нет на доске</b>", parse_mode="HTML")
    except Exception as e:
        await message.answer(f"❌ <b>Ошибка при получении кастомных полей:</b> {e}", parse_mode="HTML")


# Обработчик всех сообщений -------------------------------
async def handle_message(message: Message):
    try:
        # Парсим сообщение
        data = parse_message(message.text)
        logger.info(f"Распарсенные данные: {data}")

        # Проверяем обязательные поля (только имя карточки)
        is_valid, missing_fields = validate_required_fields(
            data, Config.REQUIRED_FIELDS)

        if not is_valid:
            await message.answer(
                f"❌ <b>Отсутствует обязательное поле:</b> {', '.join(missing_fields)}\n\n"
                "<b>Используйте</b> /help <b>для просмотра формата.</b>",
                parse_mode="HTML"
            )
            return

        # Получаем ID списка в Trello
        list_id = trello_manager.get_list_id(
            Config.TRELLO_BOARD_ID, Config.TRELLO_LIST)
        if not list_id:
            await message.answer("❌ <b>Не удалось найти указанный список в Trello. Проверьте настройки.</b>", parse_mode="HTML")
            return

        # Добавляем информацию о пользователе Telegram
        user_info = f"@{message.from_user.username}" if message.from_user.username else f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
        data['telegram пользователь'] = user_info
        logger.info(f"Добавлен пользователь Telegram: {user_info}")

        # форматируем данные для карточки
        card_name = data['имя карточки']
        card_description = format_card_description(data)

        # Получаем кастомные поля доски
        custom_fields = trello_manager.get_custom_fields(
            Config.TRELLO_BOARD_ID)
        logger.info(
            f"Доступные кастомные поля в Trello: {list(custom_fields.keys())}")

        # Подготавливаем данные для кастомных полей
        custom_fields_data = {}

        # Маппинг полей сообщения на кастомные поля Trello
        field_mapping = {
            "дата заказа": "дата заказа",
            "крайний срок": "крайний срок",
            "клиент": "клиент",
            "цвет": "цвет",
            "имя": "имя",
            "телефон": "телефон",
            "telegram пользователь": Config.TELEGRAM_USER_FIELD.lower()
        }

        # Проходим по всем полям из сообщения (включая добавленного пользователя)
        for message_field, field_value in data.items():
            # Пропускаем обязательное поле "имя карточки"
            if message_field == "имя карточки":
                continue

            # Проверяем, есть ли такое поле в Trello (прямое совпадение или через маппинг)
            trello_field = field_mapping.get(message_field, message_field)

            if trello_field in custom_fields:
                # Добавляем информацию о поле для Trello API
                custom_fields_data[trello_field] = {
                    'id': custom_fields[trello_field]['id'],
                    'type': custom_fields[trello_field]['type'],
                    'value': field_value
                }
                logger.info(
                    f"Подготовлено поле для Trello: {trello_field} = {field_value}")
            else:
                logger.info(
                    f"Поле '{message_field}' отсутствует в Trello, будет добавлено только в описание")

        logger.info(f"Данные для кастомных полей: {custom_fields_data}")

        # Создаем карточку в Trello с кастомными полей
        success, result = trello_manager.create_card_with_custom_fields(
            list_id,
            card_name,
            card_description,
            custom_fields_data,
            Config.TRELLO_BOARD_ID
        )

        if success:
            card_url = result.get('shortUrl', result.get('url', ''))
            filled_fields = list(custom_fields_data.keys())

            response_text = f"✅ <b>Карточка успешно создана в Trello!</b>\n\n<b>📋 Название:</b> {card_name}\n<b>🔗 Ссылка:</b> {card_url}"

            if filled_fields:
                response_text += f"\n<b>📊 Заполнены кастомные поля:</b> {', '.join(filled_fields)}"

            # Показываем поля, которые попали только в описание
            description_only_fields = [field for field in data.keys()
                                       if field != "имя карточки" and field not in field_mapping and field_mapping.get(field) not in custom_fields_data]
            if description_only_fields:
                response_text += f"\n<b>📝 Только в описании:</b> {', '.join(description_only_fields)}"

            response_text += f"\n<b>👤 Создал:</b> {user_info}"

            await message.answer(response_text, parse_mode="HTML")
        else:
            await message.answer(f"❌ <b>Ошибка при создании карточки:</b> {result}", parse_mode="HTML")

    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {e}", exc_info=True)
        await message.answer(
            "❌ <b>Произошла ошибка при обработке сообщения.</b> Проверьте формат и попробуйте еще раз.\n\n"
            "<b>Используйте</b> /help <b>для просмотра формата.</b>",
            parse_mode="HTML"
        )
