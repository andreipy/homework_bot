import logging
import os
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv


load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = 505143542

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    level=logging.INFO,
    filename='program.log',
    format='%(asctime)s, %(levelname)s, %(message)s'
)
logger = logging.getLogger(__name__)


def send_message(bot, message):
    """Отправка сообщения об изменившемся статусе через бота-ассистента"""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.info('Сообщение отправлено успешно.')
    except error.TelegramError as error:
        logging.error(f'Не удалось отправить сообщение. Ошибка: {error}')
        raise AssertionError({error})


def get_api_answer(current_timestamp):
    """Получение данных через API Практикум.Домашки"""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=params
        )
    except Exception as error:
        logging.error(f'Сбой в работе программы: Ошибка: {error}')
        raise ConnectionError('blabla')
    homework_statuses = response.json()
    if response.status_code is not HTTPStatus.OK:
        logging.error(f'Бот не может получить доступ к API, код ошибки:'
                      f' {response.status_code}'
                      )
        raise ConnectionError(f'Бот не может получить доступ к API, '
                              f'код ошибки: {response.status_code}'
                              )
    return homework_statuses


def check_response(response):
    """Проверка типа возвращенных API данных"""
    if type(response) is not dict:
        logging.error('Формат ответа API неверен')
        raise TypeError('Формат ответа API неверен')
    homeworks = response.get('homeworks')
    if homeworks is None:
        logging.error('Ответ API не содержит ключ \'homeworks\'')
        raise KeyError('Ответ API не содержит ключ \'homeworks\'')
    if type(homeworks) is not list:
        logging.error('Тип домашки неверен')
        raise TypeError('Тип домашки неверен')
    return homeworks


def parse_status(homework):
    """Проверка имени и статуса домашней работы"""
    homework_name = homework.get('homework_name')
    if homework_name is None:
        logging.error('Ответ API не содержит homework_name)')
        raise KeyError('Ответ API не содержит homework_name')
    homework_status = homework.get('status')
    if homework_status is None:
        logging.error('Ответ API не содержит homework_status')
        raise KeyError('Ответ API не содержит homework_status')
    verdict = HOMEWORK_STATUSES[homework_status]
    if verdict is None:
        logging.error('Ответ API не содержит verdict')
        raise KeyError('Ответ API не содержит verdict')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """"Проверка всех трёх токенов на наличие в переменных окружения"""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    if not check_tokens():
        logging.critical('Нет одного или нескольких токенов для работы бота')
        raise KeyError('Нет одного или нескольких токенов для работы бота')
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework_valid = check_response(response)
            if homework_valid:
                send_message(bot, parse_status(homework_valid))
            current_timestamp = int(time.time()) + RETRY_TIME
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(f'Сбой в работе программы: {error}')
            time.sleep(RETRY_TIME)
        else:
            return message


if __name__ == '__main__':
    main()
