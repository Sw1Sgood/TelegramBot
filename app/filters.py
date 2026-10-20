from aiogram.types import Message


def not_command(message: Message) -> bool:
    """Пропускает сообщения, которые не являются командами (/menu и т.п.).

    Нужен в хэндлерах ввода внутри FSM, чтобы команды не принимались за ответ.
    """
    return not (message.text or "").startswith("/")
