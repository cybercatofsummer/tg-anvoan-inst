# core/data_manager.py
from abc import ABC, abstractmethod

class DataManager(ABC):
    @abstractmethod
    def get_user_data(self, key: str):
        pass

    @abstractmethod
    def set_user_data(self, key: str, value):
        pass

    @abstractmethod
    def get_bot_data(self, key: str):
        pass

    @abstractmethod
    def set_bot_data(self, key: str, value):
        pass

class TelegramDataManager(DataManager):
    def __init__(self, context):
        self.context = context

    def get_user_data(self, key: str):
        return self.context.user_data.get(key)

    def set_user_data(self, key: str, value):
        self.context.user_data[key] = value

    def get_bot_data(self, key: str):
        return self.context.bot_data.get(key)

    def set_bot_data(self, key: str, value):
        self.context.bot_data[key] = value
