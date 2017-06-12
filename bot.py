import sys
import time
import telepot
import telepot.helper
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from telepot.delegate import (
    per_chat_id, create_open, pave_event_space, include_callback_query_chat_id)
import navigator as nav
import os
import json
import textwrap
import logging

logging.basicConfig(filename='log.log',level=logging.INFO, format='%(asctime)s %(message)s')

class COMMANDS():
    FIRST_PAGE = "first"
    FIRST_PAGE_SHORT = "f"

    LAST_PAGE = "last"
    LAST_PAGE_SHORT = "l"

    NEXT_PAGE = "next"
    NEXT_PAGE_SHORT = "n"

    PREV_PAGE = "prev"
    PREV_PAGE_SHORT = "p"

    HOME = "home"

    BACK = "back"
    BACK_SHORT = "b"

    GET_FILE = "get"
    GET_FILE_SHORT = "g"
    GET_FILE_BUTTON = "g"

    HELP = "help"
    HELP_SHORT = "h"

    VIEW = "view"
    VIEW_SHORT = "v"

    @staticmethod
    def get_help():
        return "\n".join([
            "help - /h",
            "first page - /f",
            "last page - /l",
            "next page - /n",
            "go back to previous dir - /b",
            "get file - /g filename",
            "go to dir - dir name / dir number",
            "change list view - /v",
        ])


class Config():
    USER_CONFIGS = "user_configs"
    USER_ID = "user_id"
    SHARED_DIRS = "shared_dirs"
    ALIAS = "alias"
    PATH = "path"
    TOKEN = "token"

    @staticmethod
    def read_config(config_name="config.json"):
        result = {}
        with open(config_name) as data_file:
            data_loaded = json.load(data_file)

        token = data_loaded[Config.TOKEN]
        for user_config in data_loaded[Config.USER_CONFIGS]:
            user_id = user_config[Config.USER_ID]
            shared_directories = []
            for sd in user_config[Config.SHARED_DIRS]:
                shared_directories.append(SharedDirectory(alias=sd[Config.ALIAS], path=sd[Config.PATH]))
            result[user_id] = shared_directories
        return token, result


class SharedDirectory():
    def __init__(self, path, alias):
        self.path = path
        self.alias = alias


class NavigatorBot(telepot.helper.ChatHandler):
    def __init__(self, *args, **kwargs):
        super(NavigatorBot, self).__init__(*args, **kwargs)

        user_id = args[0][2]

        self._navigator = None
        self._editor = None
        self._is_table_view = True

        global global_config
        global global_files_tree_generators

        if user_id not in global_config:
            return

        shared_directories = global_config[user_id]
        navigator = nav.Navigator(page_size=10)
        for sd in shared_directories:
            navigator.add_files_tree(
                root=global_files_tree_generators[sd.path].root_dir,
                alias=sd.alias)

        self._navigator = navigator
        self._editor = None
        logging.info("NavigatorBot launched: {0}".format(user_id))


    def on_chat_message(self, msg):
        if self._navigator is None:
            return

        content_type, chat_type, chat_id = telepot.glance(msg)
        if content_type != 'text':
            return

        message = msg['text'].lower().partition(' ')
        logging.info("on_chat_message: {0} {1} {2} {3}".format(self.id, content_type, chat_type, message))
        command = message[0].strip()
        arg = " ".join(message[1:]).strip()
        self._execute_command(command=command, arg=arg, is_chat_message=True)


    def on_callback_query(self, msg):
        if self._navigator is None:
            return
        query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')
        logging.info("on_callback_query: {0} {1} {2}".format(self.id, query_id, query_data))
        self._execute_command(command=query_data, arg="", is_chat_message=False)

    def on__idle(self, event):
        self.close()

    def on_close(self, ex):
        logging.info("on_close: {0} {1}".format(self.id, ex))
        self._delete_message()


    def _execute_command(self, command, arg, is_chat_message):
        if command[0] == "/":
            command = command[1:]

        if command == COMMANDS.HELP or command == COMMANDS.HELP_SHORT:
            self._delete_message()
            self.sender.sendMessage(COMMANDS.get_help())
            return

        if self._editor is None:
            self._show_files_list(delete_prev_message=is_chat_message)
            return

        if command == COMMANDS.BACK or command == COMMANDS.BACK_SHORT:
            self._navigator.set_parent_dir()
            self._show_files_list(delete_prev_message=is_chat_message)

        elif command == COMMANDS.GET_FILE or command == COMMANDS.GET_FILE_SHORT:
            file = self._navigator.get_file(arg)
            if file is not None and os.path.isfile(file.path):
                self._delete_message()
                with open(file.path, "rb") as f:
                    self.sender.sendDocument(f)
                    logging.info("load file: {0} {1}".format(self.id, file.path))

        elif command == COMMANDS.FIRST_PAGE or command == COMMANDS.FIRST_PAGE_SHORT:
            if self._navigator.first_page():
                self._show_files_list(delete_prev_message=is_chat_message)

        elif command == COMMANDS.LAST_PAGE or command == COMMANDS.LAST_PAGE_SHORT:
            if self._navigator.last_page():
                self._show_files_list(delete_prev_message=is_chat_message)

        elif command == COMMANDS.NEXT_PAGE or command == COMMANDS.NEXT_PAGE_SHORT:
            if self._navigator.next_page():
                self._show_files_list(delete_prev_message=is_chat_message)

        elif command == COMMANDS.PREV_PAGE or command == COMMANDS.PREV_PAGE_SHORT:
            if self._navigator.prev_page():
                self._show_files_list(delete_prev_message=is_chat_message)

        elif command == COMMANDS.VIEW or command == COMMANDS.VIEW_SHORT:
            self._is_table_view = not self._is_table_view
            self._show_files_list(delete_prev_message=is_chat_message)

        else:
            self._navigator.set_dir(command)
            self._show_files_list(delete_prev_message=is_chat_message)


    def _show_files_list(self, delete_prev_message=False):
        if delete_prev_message:
            self._delete_message()

        files_list = self._navigator.get_current_page_files()
        if self._is_table_view:
            table_text = _create_table_view(files_list=files_list)
        else:
            table_text = _create_list_view(files_list=files_list, max_len=25)

        path = "path:{0}".format(self._navigator.current_dir.path)
        result = "``` {0}\n{1}\n```".format(path, table_text)
        markup = self._create_reply_markup()

        if self._editor is None:
            sent = self.sender.sendMessage(result, parse_mode="Markdown", reply_markup=markup)
            self._editor = telepot.helper.Editor(self.bot, sent)
        else:
            self._editor.editMessageText(result, parse_mode="Markdown", reply_markup=markup)


    def _create_reply_markup(self):
        inline_keyboard=[]
        current_page_num = self._navigator.pagination.current_page_num
        total_pages_num = self._navigator.pagination.total_pages_num

        if current_page_num > 2:
            inline_keyboard.append(InlineKeyboardButton(
                text='<0',
                callback_data=COMMANDS.FIRST_PAGE))

        if current_page_num > 1:
            inline_keyboard.append(InlineKeyboardButton(
                text='<{0}'.format(current_page_num - 1),
                callback_data=COMMANDS.PREV_PAGE))

        if current_page_num < total_pages_num:
            inline_keyboard.append(InlineKeyboardButton(
                text='{0}>'.format(current_page_num + 1),
                callback_data=COMMANDS.NEXT_PAGE))

        if current_page_num + 1 < total_pages_num:
            inline_keyboard.append(InlineKeyboardButton(
                text='{0}>'.format(total_pages_num),
                callback_data=COMMANDS.LAST_PAGE))

        if self._navigator.current_dir.parent is not None:
            inline_keyboard.append(InlineKeyboardButton(
                text='../',
                callback_data=COMMANDS.BACK))

        inline_keyboard.append(InlineKeyboardButton(
            text='v',
            callback_data=COMMANDS.VIEW))

        markup = InlineKeyboardMarkup(inline_keyboard=[inline_keyboard])
        return markup


    def _delete_message(self):
        if self._editor is not None:
            self._editor.deleteMessage()
            self._editor = None

def _create_table_view(files_list):
    data_list = []
    data_list.append(["filename", "size", "key"])
    for idx, file in enumerate(files_list):
        if file.is_dir:
            data_list.append(["{0}/".format(file.name), "", "{0}".format(idx)])
        else:
            data_list.append([file.name, nav.sizeof_fmt(file.size), "{0}".format(idx)])

    columns_size_list=[30, 10, 4]
    separator = " | "
    head_width = sum(columns_size_list) + (len(separator) * (len(columns_size_list) - 1))

    result = []
    result.append("".rjust(head_width, "-"))

    for idx, data_row in enumerate(data_list):
        if(idx == 1):
            result.append("".rjust(head_width, "-"))
        result_row = []
        for i in range(len(data_row)):
            column_size = columns_size_list[i]
            text = "{0}".format(data_row[i])
            t = column_size - len(text)
            if(t < 0):
                text = text[:t - 3] + "..."
            else:
                text = text.ljust(column_size, " ")
            result_row.append(text)
        result.append(" | ".join(result_row))
    return "\n".join(result)


def _create_list_view(files_list, max_len):
    data_list = []
    data_list.append(["filename", "size", "key"])
    for idx, file in enumerate(files_list):
        if file.is_dir:
            data_list.append(["{0}/".format(file.name), "", "{0}".format(idx)])
        else:
            data_list.append([file.name, nav.sizeof_fmt(file.size), "{0}".format(idx)])

    result = []

    for idx, data_row in enumerate(data_list):
        result.append("".ljust(max_len, "-"))

        file_name = "{0}".format(data_row[0])
        t = max_len - len(file_name)
        if(t < 0):
            lines = textwrap.wrap(file_name, max_len - 2)
            lines_frmt = ["|{}|".format(l.ljust(max_len - 2)) for l in lines[:-1]]
            lines_frmt.append("|{}|".format(lines[-1].ljust(max_len - 2, ".")))
            file_name = "\n".join(lines_frmt)
        else:
            file_name = "|{0}|".format(file_name.ljust(max_len - 2, "."))

        file_size = "|{0}".format(data_row[1])
        if file_size == "|":
            file_size = "| -"
        file_idx = "{0}|".format(data_row[2])

        t = max_len - len(file_idx)
        if(t > 0):
            file_size = file_size.ljust(t)

        result.append("{0}\n{1}{2}".format(file_name, file_size, file_idx))
    return "\n".join(result)


global_files_tree_generators = {}
global_config = {}

def run_bot(token, config):
    logging.info("Listening started")

    files_tree_generators= {}
    for shared_directories in config.values():
        for sd in shared_directories:
            if sd.path not in files_tree_generators:
                files_tree_generators[sd.path] = nav.FilesTreeGenerator(sd.path)

    global global_config
    global_config = config
    global global_files_tree_generators
    global_files_tree_generators = files_tree_generators

    bot = telepot.DelegatorBot(token, [
        include_callback_query_chat_id(
            pave_event_space())(
            per_chat_id(types=['private']), create_open, NavigatorBot, timeout=300),
    ])
    MessageLoop(bot).run_as_thread()
    print('Listening ...')

    while 1:
        time.sleep(10)
