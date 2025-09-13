import asyncio
from aiogram import Bot, Dispatcher, types

from trello_api import TrelloManager
from config import Config, validate_config
from handlers import setup_handlers
from logging_setup import setup_logging


async def main():
    try:
        setup_logging()

        import logging
        logger = logging.getLogger(__name__)

        validate_config()
        logger.info("Конфигурация проверена успешно")

        bot = Bot(token=Config.TELEGRAM_BOT_TOKEN)
        dp = Dispatcher()

        trello_manager = TrelloManager(
            Config.TRELLO_API_KEY, Config.TRELLO_TOKEN)

        # Настраиваем обработчики
        dp = setup_handlers(dp, trello_manager)
        logger.info("Обработчики настроены")

        # Регистрируем команды меню
        commands = [
            types.BotCommand(
                command="start", description="Начать работу с ботом"),
            types.BotCommand(
                command="help", description="Получить справку по использованию"),
            types.BotCommand(command="fields",
                             description="Показать доступные поля Trello")
        ]
        await bot.set_my_commands(commands)
        logger.info("Команды меню зарегистрированы")

        # Запускаем бота
        logger.info("Бот запущен")
        await dp.start_polling(bot)

    except Exception as e:
        import logging
        logging.error(f"Ошибка при запуске бота: {e}")

if __name__ == "__main__":
    asyncio.run(main())
