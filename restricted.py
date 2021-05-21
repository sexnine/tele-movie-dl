from functools import partial, wraps
from config import config


RESTRICTED_IDS = config.get("ALLOWED_TELEGRAM_IDS")


class Restricted(object):
    """
    Decorator class used to restrict usage of commands.
    Sends a "disallowed" reply if necessary. Works on functions and methods.
    """
    def __init__(self, func):
        self._func = func
        self._obj = None
        self._wrapped = None

    def __call__(self, *args, **kwargs):
        if not self._wrapped:
            if self._obj:
                self._wrapped = self._wrap_method(self._func)
                self._wrapped = partial(self._wrapped, self._obj)
            else:
                self._wrapped = self._wrap_function(self._func)
        return self._wrapped(*args, **kwargs)

    def __get__(self, obj, type_=None):
        self._obj = obj
        return self

    def _wrap_method(self, method):  # Wrapper called in case of a method
        @wraps(method)
        def inner(self, *args, **kwargs):  # `self` is the *inner* class' `self` here
            user_id = args[0].effective_user.id  # args[0]: update
            if user_id not in RESTRICTED_IDS:
                print(f'Unauthorized access denied on {method.__name__} '
                      f'for {user_id} : {args[0].message.chat.username}.')
                args[0].message.reply_text('This is a private bot, please do not interact with me.')
                return None  # quit handling command
            return method(self, *args, **kwargs)
        return inner

    def _wrap_function(self, function):  # Wrapper called in case of a function
        @wraps(function)
        def inner(*args, **kwargs):  # `self` would be the *restricted* class' `self` here
            user_id = args[0].effective_user.id  # args[0]: update
            if user_id not in RESTRICTED_IDS:
                print(f'Unauthorized access denied on {function.__name__} '
                      f'for {user_id} : {args[0].message.chat.username}.')
                args[0].message.reply_text('This is a private bot, please do not interact with me.')
                return None  # quit handling command
            return function(*args, **kwargs)
        return inner
