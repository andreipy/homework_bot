class TokenException(Exception):
    """Исключение, связанное с токенами в переменных окружения."""

    def __init__(self):
        self.message = 'Нет одного или нескольких токенов для работы бота'
        super().__init__(self.message)

    def __str__(self):
        return f'{self.message}'


class TelegramException(Exception):
    """Ошибка, связанная с Telegram."""

    def __init__(self, error):
        self.error = error
        self.message = f'Не удалось отправить сообщение. Ошибка {error}'
        super().__init__(self.message)

    def __str__(self):
        return f'{self.message}'


class JSONDecodeException(Exception):
    """Ошибка, связанная с приведением в JSON."""

    def __init__(self, error):
        self.message = ('При декодировании ответа API в формат'
                        + ' JSON произошла ошибка')
        super().__init__(self.message)

    def __str__(self):
        return f'{self.message}'


class VerdictException(Exception):
    """Ошибка, связанная с получением некорректного статуса домашки."""

    def __init__(self, error):
        self.message = ('Невозможно соотнести полученный статус '
                        'ни с одним из ожидаемых')
        super().__init__(self.message)

    def __str__(self):
        return f'{self.message}'
