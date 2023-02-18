import logging
import os

import requests
from http import HTTPStatus
import telegram
import time

from dotenv import load_dotenv 

load_dotenv()
def HttpResponseNotOk(message):
    pass


def WrongKeyHw():
    pass


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN1')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN1')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID1')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Функция проверяющая наличие токеннов"""
    try:
        PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID == None
    except Exception as error:
        logging.critical(f'Неверный токен или его отсутствие: {error}')
        return exit('Не удалось найти токен')

def send_message(bot, message):
    """Функция отправки сообщений от бота"""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.debug(f'send_message: Бот отправил сообщение: {message}')
    except Exception('send_message: Сообщение не отправленно'):
        logging.error(f'send_message: Сообщение с текстом {message} не отправленно')


def get_api_answer(timestamp):
    """Функция получения ответа от API"""
    payload = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
        if response.status_code != HTTPStatus.OK:
            logging.error(f'{ENDPOINT}, не передает данные')
            raise HttpResponseNotOk(f'{ENDPOINT} не передает данные')
    except requests.RequestException as i:
        logging.error(f'{ENDPOINT} не передает данные: {i}')
    return response.json


def check_response(response):
    """Функция проверки ответ API на соответствие документации"""
    error_message = f'check_response: Некоректный ответ {response}'
    if not isinstance(response, dict):
        logging.error('1' + error_message)
        raise TypeError(error_message)
    if not response.get('homeworks'):
        logging.error('2' + error_message)
        raise TypeError(error_message)
    if not isinstance(response.get('homeworks'), list):
        logging.error('3' + error_message)
        raise TypeError(error_message)


def parse_status(homework):
    """Функция извлечения статуса конкретной домашней работы"""
    homework_name = homework.get('homework_name')
    if not homework_name:
        error_message = 'В ответе API нет ключа "homework_name"'
        logging.error(error_message)
        raise WrongKeyHw(error_message)
    status = homework.get('status')
    verdict = HOMEWORK_VERDICTS.get(status)
    if not verdict:
        logging.error(f'Неожиданный статус {status} домашней работы'
                      f'{homework_name}, обнаруженный в ответе API')
        raise WrongKeyHw('Неожиданный статус домашней работы обнаруженный в ответе API')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    status_last_homework = ''
    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            if response.get('homeworks'):
                parse_status(check_response(response))
                status_current_homework = response.get('homeworks')[0]
                if status_last_homework != status_current_homework.get('status'):
                    status_last_homework = status_current_homework.get('status')
                    message = parse_status(status_current_homework)
                    send_message(bot, message)
                else:
                    logging.debug('Отсутсвие новвых статусов')
                    raise Exception(message)

        except Exception as error:  
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            send_message(bot, message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
