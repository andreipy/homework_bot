import json
import logging
import os
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

from exceptions import (JSONDecodeException,
                        TelegramException,
                        TokenException,
                        VerdictException)

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logger = logging.getLogger(__name__)


def send_message(bot, message):
    """Отправка сообщения об изменившемся статусе через бота-ассистента."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.info(
            'Сообщение отправлено успешно.')
    except error.TelegramError as error:
        logger.error(
            f'Не удалось отправить сообщение. Ошибка: {error}')
        TelegramException({error})


def get_api_answer(current_timestamp):
    """Получение данных через API Практикум.Домашки."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=params
        )
    except Exception as error:
        logger.error(f'Сбой в работе программы: Ошибка: {error}')
        raise ConnectionError(f'Сбой в работе программы: Ошибка: {error}')
    if response.status_code != HTTPStatus.OK:
        logger.error(
            f'Бот не может получить доступ к API, код ошибки:'
            f' {response.status_code}'
        )
        raise ConnectionError(f'Бот не может получить доступ к API, '
                              f'код ошибки: {response.status_code}'
                              )
    try:
        homework_statuses = response.json()
    except json.decoder.JSONDecodeError:
        JSONDecodeException()
    return homework_statuses


def check_response(response):
    """Проверка типа возвращенных API данных."""
    if not isinstance(response, dict):
        logger.error('Формат ответа API неверен')
        raise TypeError('Формат ответа API неверен')
    homeworks = response.get('homeworks')
    if homeworks is None:
        logger.error('Ответ API не содержит '
                     'ключ \'homeworks\'')
        raise KeyError('Ответ API не содержит ключ \'homeworks\'')
    if not isinstance(homeworks, list):
        logger.error('Тип домашки неверен')
        raise TypeError('Тип домашки неверен')
    return homeworks[0]


def parse_status(homework):
    """Проверка имени и статуса домашней работы."""
    if 'homework_name' not in homework:
        logger.error('Ответ API не содержит homework_name')
        raise KeyError('Ответ API не содержит homework_name')
    if not isinstance(homework, dict):
        logger.error('Формат ответа API неверен')
        raise TypeError('Формат ответа API неверен')
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status is None:
        logger.error('Ответ API не содержит homework_status')
        raise KeyError('Ответ API не содержит homework_status')
    try:
        verdict = HOMEWORK_VERDICTS[homework_status]
    except Exception as status:
        logger.error(f'Невозможно соотнести полученный статус '
                     f'ни с одним из ожидаемых: получен {status}'
                     )
        VerdictException()
    if verdict is None:
        logger.error('Ответ API не содержит verdict')
        raise KeyError('Ответ API не содержит verdict')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка всех трёх токенов на наличие в переменных окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    if not check_tokens():
        logger.critical(
            'Нет одного или нескольких токенов для работы бота')
        TokenException()
    while True:
        try:
            response = get_api_answer(current_timestamp)
            try:
                homework = check_response(response)
                if not homework:
                    logger.debug('Статус домашек не обновлялся')
                    homework = 'Статус домашек не обновлялся'
                    send_message(bot, message=homework)
            except Exception:
                logger.debug('Статус домашек не обновлялся')
                homework = 'Статус домашек не обновлялся'
                send_message(bot, message=homework)
            send_message(bot, parse_status(homework))
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(f'Сбой в работе программы: {error}')
            return message
        finally:
            current_timestamp = int(time.time())
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    logger.setLevel(logging.INFO)
    logger_handler = logging.StreamHandler()
    logger.addHandler(logger_handler)
    main()
