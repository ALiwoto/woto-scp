import asyncio
import threading
from scp import user
from pyrogram.types import (
    Message,
)
from typing import Callable

MAX_ATTEMPT = 30
YELLOW_COLOR = '🟨'
RED_COLOR = '🟥'
GREEN_COLOR = '🟩'
WORDS_LIST = []
VALID_EMOJIS = [YELLOW_COLOR, RED_COLOR, GREEN_COLOR]
INVALID_TEXTS = ['Joined Wordle', 'Created Wordle']
CHAT_LOCKS = {}

try:
    with open('scp/plugins/user/wordlist.txt') as f:
        for line in f:
            if not line or len(line) < 5: continue
            WORDS_LIST.append(line.strip())
except FileNotFoundError: pass


class WordleGlobalConfig:
    is_enabled: bool = False
    registered_chats = {}

class WordleChatConfig:
    chat_it: int = 0
    total_attempt: int = 0
    current_guess_list = []
    auto_reset: bool = False
    last_valid_text: str = ''
    last_word: str = ''
    invalid_error_count: int = 0
    last_sent_index: int = -1
    
    def __init__(self, chat_id: int):
        self.chat_it = chat_id
    
    def reset_values(self):
        self.total_attempt = 0
        self.last_word = ''
        self.last_valid_text = ''
        self.current_guess_list = []
        self.invalid_error_count = 0

wordle_global_config: WordleGlobalConfig = None

def wordle_lock(func: Callable) -> Callable:
    async def decorator(
        client, obj: Message, *args
    ):
        chat_id = obj.chat.id
        the_lock = CHAT_LOCKS.get(chat_id, None)
        if not the_lock:
            the_lock = asyncio.Lock()
            CHAT_LOCKS[chat_id] = the_lock
        
        #if obj.text.count(GREEN_COLOR * 5) == 1:
        #    return
        await the_lock.acquire()
        try:
            await func(client, obj, *args)
        except Exception as e: 
            print(e)
        the_lock.release()
            

    return decorator

def starts_with_valid_emoji(text: str) -> bool:
    for current in VALID_EMOJIS:
        if text.startswith(current):
            return True
    
    return False

def starts_with_invalid_text(text: str) -> bool:
    for current in INVALID_TEXTS:
        if text.startswith(current):
            return True
    
    return False

@user.on_message(
    user.wfilters.wordle_bot,
    group=143,
)
@wordle_lock
async def wordle_bot_message_handler(_, message: Message):
    if not isinstance(wordle_global_config, WordleGlobalConfig):
        return
    elif not wordle_global_config.is_enabled:
        return
    elif not starts_with_valid_emoji(message.text):
        if starts_with_invalid_text(message.text):
            return
        
        chat_settings = wordle_global_config.registered_chats.get(message.chat.id, None)
        if not isinstance(chat_settings, WordleChatConfig) or not chat_settings.auto_reset:
            return
        if message.text.find('/new') != -1:
            await asyncio.sleep(6)
            await user.send_message(message.chat.id, '/new@hiwordlebot')
            chat_settings.reset_values()
            await asyncio.sleep(2)
            return await user.send_message(message.chat.id, WORDS_LIST[message.message_id%len(WORDS_LIST)])
        elif message.text.find('Not a valid') != -1:
            chat_settings.invalid_error_count += 1
            if not chat_settings.last_valid_text:
                await asyncio.sleep(6)
                return await user.send_message(message.chat.id, WORDS_LIST[message.message_id%len(WORDS_LIST)])
            else:
                message.text = chat_settings.last_valid_text
        
    
    chat_settings = wordle_global_config.registered_chats.get(message.chat.id, None)
    if not isinstance(chat_settings, WordleChatConfig):
        return
    
    if chat_settings.last_valid_text != message.text:
        chat_settings.last_valid_text = message.text
        chat_settings.invalid_error_count = 0
    
    if chat_settings.total_attempt >= MAX_ATTEMPT:
        chat_settings.reset_values()
        await asyncio.sleep(4)
        return await user.send_message(message.chat.id, WORDS_LIST[message.message_id%len(WORDS_LIST)])
    elif chat_settings.total_attempt == 0:
        # copy WORDS_LIST to guess_list
        chat_settings.current_guess_list = WORDS_LIST[:]
    
    await asyncio.sleep(3)
    chat_settings.total_attempt += 1
    my_strs = user.split_message(message)
    guess = my_strs[len(my_strs)-1]
    feedback = my_strs[len(my_strs)-2]
    if feedback == (GREEN_COLOR * 5):
        chat_settings.reset_values()
        return
    
    if len(my_strs) >= MAX_ATTEMPT:
        if not chat_settings.auto_reset:
            return
        chat_settings.reset_values()
        await user.send_message(message.chat.id, '/new@hiwordlebot')
        await asyncio.sleep(5)
        return await user.send_message(message.chat.id, WORDS_LIST[message.message_id%len(WORDS_LIST)])

    temp_tuple = tuple(chat_settings.current_guess_list)
    for word in temp_tuple: # You can't iterate over a list you want to change, so using a tuple.
        for i in range(5):
            try:
                if feedback[i] == RED_COLOR and guess[i] in word:
                    chat_settings.current_guess_list.remove(word)
                    break
                elif feedback[i] == GREEN_COLOR and guess[i] != word[i]:
                    chat_settings.current_guess_list.remove(word)
                    break
                elif feedback[i] == YELLOW_COLOR and guess[i] not in word:
                    chat_settings.current_guess_list.remove(word)
                    break
                elif feedback[i] == YELLOW_COLOR and guess[i] == word[i]:
                    chat_settings.current_guess_list.remove(word)
                    break
            except Exception:
                pass
            

    the_word = ''
    if len(chat_settings.current_guess_list) == 0:
        the_word = WORDS_LIST[message.message_id%len(WORDS_LIST)]
    elif len(chat_settings.current_guess_list) < 5:
        if chat_settings.last_sent_index == -1:
            chat_settings.last_sent_index = 0
        elif len(chat_settings.current_guess_list) > chat_settings.last_sent_index + 1:
            # preferably try another index, so we can avoid the same word
            chat_settings.last_sent_index += 1
        the_word = chat_settings.current_guess_list[chat_settings.last_sent_index%len(chat_settings.current_guess_list)]
    else:
        if chat_settings.last_sent_index == -1:
            chat_settings.last_sent_index = 3
        elif len(chat_settings.current_guess_list) > chat_settings.last_sent_index + 1:
            # preferably try another index, so we can avoid the same word
            chat_settings.last_sent_index += 1
        the_word = chat_settings.current_guess_list[chat_settings.last_sent_index%len(chat_settings.current_guess_list)]
    
    if len(chat_settings.last_word) > 0 and the_word == chat_settings.last_word:
        if chat_settings.invalid_error_count >= 5:
            await user.send_message(message.chat.id, '/new@hiwordlebot')
            chat_settings.reset_values()
            await asyncio.sleep(6)
            return await user.send_message(message.chat.id, WORDS_LIST[message.message_id%len(WORDS_LIST)])
        elif chat_settings.invalid_error_count >= 1:
            the_word = WORDS_LIST[message.message_id%len(WORDS_LIST)]
    
    chat_settings.last_word = the_word
    await user.send_message(message.chat.id, the_word)

@user.on_message(
	~user.filters.forwarded &
	~user.filters.sticker & 
	~user.filters.via_bot & 
	~user.filters.edited & 
	user.owner & 
	user.filters.command(
        ['wordle'],
        prefixes=user.cmd_prefixes,
    ),
)
async def enable_wordle_handler(_, message: Message):
    global wordle_global_config
    txt = ''
    if wordle_global_config == None:
        wordle_global_config = WordleGlobalConfig()
        wordle_global_config.is_enabled = True
        txt = 'wordle plugin enabled.'
    else:
        wordle_global_config = None
        txt = 'wordle plugin disabled.'
    
    await message.reply_text(txt)
    

@user.on_message(
	~user.filters.sticker & 
	~user.filters.via_bot & 
	~user.filters.edited & 
	user.owner & 
	user.filters.command(
        ['cWordle'],
        prefixes=user.cmd_prefixes,
    ),
)
async def cWordle_handler(_, message: Message):
    if wordle_global_config == None:
        return await message.reply_text('wordle plugin is not enabled.')
    all_strs = message.text.split(' ')
    if len(all_strs) < 2:
        if not message.reply_to_message:
            the_chat = message.chat.id
        else:
            replied = message.reply_to_message
            if replied.text.isdigit() and replied.text.startswith('-100'):
                the_chat = int(replied.text)
            else:
                the_chat = message.chat.id
    else:
        the_chat = message.text.split(' ')[1]
        if the_chat.find('/') > 0:
            all_strs = the_chat.split('/')
            index = len(all_strs) - 1
            if all_strs[index].isdigit():
                index -= 1
            if all_strs[index].isdigit():
                all_strs[index] = '-100' + all_strs[index]
            the_chat = all_strs[index]
    
    chat = await user.get_chat(the_chat)
    txt = ''
    chat_settings = wordle_global_config.registered_chats.get(chat.id, None)
    if not isinstance(chat_settings, WordleChatConfig):
        wordle_global_config.registered_chats[chat.id] = WordleChatConfig(chat.id)
        txt = 'wordle enabled for the chat.'
    else:
        wordle_global_config.registered_chats.pop(chat.id, None)
        txt = 'wordle disabled for the chat.'
    
    await message.reply_text(txt)


@user.on_message(
	~user.filters.sticker & 
	~user.filters.via_bot & 
	~user.filters.edited & 
	user.owner & 
	user.filters.command(
        ['aWordle'],
        prefixes=user.cmd_prefixes,
    ),
)
async def aWordle_handler(_, message: Message):
    if wordle_global_config == None:
        return await message.reply_text('wordle plugin is not enabled.')
    all_strs = message.text.split(' ')
    if len(all_strs) < 2:
        if not message.reply_to_message:
            the_chat = message.chat.id
        else:
            replied = message.reply_to_message
            if replied.text.isdigit() and replied.text.startswith('-100'):
                the_chat = int(replied.text)
            else:
                the_chat = message.chat.id
    else:
        the_chat = message.text.split(' ')[1]
        if the_chat.find('/') > 0:
            all_strs = the_chat.split('/')
            index = len(all_strs) - 1
            if all_strs[index].isdigit():
                index -= 1
            if all_strs[index].isdigit():
                all_strs[index] = '-100' + all_strs[index]
            the_chat = all_strs[index]
    
    chat = await user.get_chat(the_chat)
    txt = ''
    chat_settings = wordle_global_config.registered_chats.get(chat.id, None)
    if not isinstance(chat_settings, WordleChatConfig):
        txt = 'wordle plugin is not enabled for this chat!'
        return await message.reply_text(txt)
    
    if not chat_settings.auto_reset:
        chat_settings.auto_reset = True
        txt = 'auto reset enabled for the chat.'
    else:
        chat_settings.auto_reset = False
        txt = 'auto reset disabled for the chat.'
    
    await message.reply_text(txt)


