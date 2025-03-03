# core/data_manager.py
from abc import ABC, abstractmethod
from telegram import Update
from telegram.ext import CallbackContext
from services.constants import IMAGES
import json


class DataManager:
    def __init__(self, context: CallbackContext, update: Update, handle_callback: bool = False):
        self.context = context
        self.update = update

        if handle_callback:
            self.__handle_callback()
        self.init_user()
    
    def init_user(self):
        if self.user_id not in self.bot_data and not self.is_admin_chat_id:
            self.bot_data[self.user_id] = {
                "images": [],
                "username": self.user.username,
                "chat_id": self.message.chat_id,
                "state": IMAGES
            }
    @property
    def user_id(self):
        return self.context.user_data.get('proceeded_user_id', self.user.id if self.user else None)

    @user_id.setter
    def user_id(self, value):
        self.context.user_data['proceeded_user_id'] = value

    @property
    def user(self):
        if self.message:
            return self.message.from_user
        return None

    @property
    def user_data(self):
        return self.context.user_data if self.is_admin_chat_id else self.context.bot_data[self.user_id]

    @property
    def bot_data(self):
        return self.context.bot_data

    @property
    def query(self):
        return self.update.callback_query

    @property
    def query_data(self):
        return json.loads(self.query.data)

    @property
    def action(self):
        return self.query_data['action']

    @property
    def state(self):
        return self.user_data['state']

    @state.setter
    def state(self, value):
        self.user_data['state'] = value

    @property
    def images(self):
        return self.user_data["images"]

    @images.setter
    def images(self, value):
        self.user_data["images"] = value

    @property
    def message_ids_to_delete(self):
        return self.user_data["message_ids_to_delete"]

    @message_ids_to_delete.setter
    def message_ids_to_delete(self, value):
        self.user_data["message_ids_to_delete"] = value

    @property
    def message(self):
        return self.update.message

    @property
    def chat_id(self):
        return self.user_data['chat_id']

    @property
    def username(self):
        return self.user_data['username']

    @property
    def instagram_name(self):
        return self.user_data['instagram_name']

    @instagram_name.setter
    def instagram_name(self, value):
        self.user_data['instagram_name'] = value

    @property
    def bot(self):
        return self.context.bot

    @property
    def is_admin_chat_id(self):
        return False and str(self.message.chat_id) == ADMIN_TG_CHAT_ID

    def __handle_callback(self):
        self.query.answer() # This ends the loading state on the button
        self.user_id = self.query_data['user_id']