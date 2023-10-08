# https://greentreesnakes.readthedocs.io/
# https://gitlab.com/blankX/sukuinote/-/blob/master/sukuinote/plugins/pyexec.py
import ast
from _ast import Module as TModule
import sys
import types as std_types
import inspect
import asyncio
from shortuuid import ShortUUID
from io import StringIO, BytesIO
from asyncio.tasks import Task as AsyncTask
from scp import user, bot
from scp.utils.selfInfo import info
from scp.utils.parser import(
    get_media_attr, 
    html_bold, 
    html_mono, 
    to_output_file,
)
from pyrogram.client import Client as pClient
from pyrogram.enums.parse_mode import ParseMode
from pyrogram.types import (
    Message,
    InlineQuery,
    CallbackQuery,
)
from pyrogram.raw.types.messages.bot_results import (
    BotResults,
)

exec_tasks = {}
EVAL_PRETEXT = """
async def input(prompt=None, **kwargs):
    return await user.get_user_input(prompt=prompt, message=message, **kwargs)


"""

@user.on_message(
    ~user.filters.forwarded
    & ~user.filters.sticker
    & ~user.filters.via_bot
    & user.owner
    & user.command(
        'eval',
    ),
)
async def eval_handler(_, message: Message):
    code = user.get_non_cmd(message)
    if len(code) == 0:
        if not message.reply_to_message:
            return
        code = message.reply_to_message.text
    
    await eval_base(user, message, code)
    

@user.on_message(
    ~user.filters.forwarded
    & ~user.filters.sticker
    & ~user.filters.via_bot
    & user.owner
    & user.command(
        'getsrc',
        prefixes=user.cmd_prefixes,
    ),
)
async def getsrc_handler(_, message: Message):
    code = user.get_non_cmd(message)
    if len(code) == 0:
        if not message.reply_to_message:
            return
        code = str(message.reply_to_message.text)
    
    code = (
f"""
import inspect
import struct
return inspect.getsource({code})
"""
    )

    await eval_base(user, message, code)

async def eval_base(client: pClient, message: Message, code: str, silent: bool = False):
    code = EVAL_PRETEXT + user.fix_eval_text(code)
    
    is_private: bool = code.find("SEND_PRIVATE") != -1
    tree: TModule = None
    try:
        tree = ast.parse(code)
    except Exception as ex:
        return await user.reply_exception(message=message, e=ex, is_private=is_private)
    
    o_body = tree.body
    body = o_body.copy()
    body.append(ast.Return(ast.Name('_ueri', ast.Load())))
    try:
        exx = _gf(body)
    except SyntaxError as ex:
        if ex.msg != "'return' with value in async generator":
            str_err = str(ex)
            if len(str_err) > 4000:
                await message.reply_document(to_output_file(str_err))
                return
            txt = html_mono(str_err)
            return await message.reply_text(txt, parse_mode=ParseMode.HTML)
        exx = _gf(o_body)
    rnd_id = '#' + str(ShortUUID().random(length=8))
    reply: Message = None
    if message != None and not silent:
        reply = await message.reply_text(
            html_bold('Executing task ') + html_mono(rnd_id, '...'),
            quote=True,
            disable_notification=True,
            disable_web_page_preview=True,
        )
    oasync_obj = exx(
        client,
        client,
        message,
        message,
        reply,
        message.reply_to_message,
        message.reply_to_message,
        UniqueExecReturnIdentifier,
    )
    if inspect.isasyncgen(oasync_obj):
        async def async_obj():
            return [i async for i in oasync_obj]
    else:
        async def async_obj():
            to_return = [await oasync_obj]
            return [] if to_return == [
                UniqueExecReturnIdentifier,
            ] else to_return
    stdout = sys.stdout
    stderr = sys.stderr
    wrapped_stdout = StringIO()
    try:
        sys.stdout = sys.stderr = wrapped_stdout
        task: AsyncTask = asyncio.create_task(async_obj())
        exec_tasks[rnd_id] = task
        try:
            returned = await task
        except Exception as err:
            return await user.reply_exception(message=message, e=err, is_private=is_private)
    except asyncio.CancelledError:
        sys.stdout = stdout
        sys.stderr = stderr
        exec_tasks.pop(rnd_id, None)
        txt = user.html_bold('Task Cancelled: \n')
        txt += user.html_normal(f'{rnd_id} has been canceled.')
        return await reply.edit_text(text=txt, parse_mode=ParseMode.HTML)
    except Exception as e:
        str_err = str(e)
        if len(str_err) > 4096:
            await asyncio.gather(reply.delete(), message.reply_document(to_output_file(str_err)))
            return
        txt = html_bold('Error for task')
        txt += html_mono(f' {rnd_id} ', ':\n')
        txt += html_mono(f' {str(e)} ')
        return await reply.edit_text(
            text=txt,
            parse_mode=ParseMode.HTML,
            quote=True,
            disable_web_page_preview=True,
        )
    finally:
        sys.stdout = stdout
        sys.stderr = stderr
        exec_tasks.pop(rnd_id, None)
    wrapped_stdout.seek(0)
    output = ''
    wrapped_stdout_text = wrapped_stdout.read().strip()
    if wrapped_stdout_text:
        output += wrapped_stdout_text + '\n'
    for i in returned:
        output += str(i).strip() + '\n'
    if not output.strip():
        output = 'Success'
    
    if silent or reply == None:
        return
    output = output.replace(user.original_phone_number, '$PHONE_NUMBER')

    if len(output) > 4096:
        out = wrapped_stdout_text + '\n'
        out = out.replace(user.original_phone_number, '$PHONE_NUMBER')
        for i in returned:
            out += str(i).strip() + '\n'
        f = BytesIO(out.strip().encode('utf-8'))
        f.name = f'output-{rnd_id}.txt'
        await asyncio.gather(reply.delete(), message.reply_document(f))
    else:
        txt = html_bold('Output for') + html_mono(' ' + rnd_id, ':\n    ')
        txt += html_mono(output)
        await reply.edit_text(
            txt, 
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )

user.eval_base = std_types.MethodType(eval_base, user)
user.the_bot.eval_base = std_types.MethodType(eval_base, user.the_bot)

@user.on_message(
    ~user.filters.forwarded
    & ~user.filters.sticker
    & ~user.filters.via_bot
    & user.owner
    & user.command(
        'exit',
        prefixes=user.cmd_prefixes,
    ),
)
async def exit_exec(_, message: Message):
    if message.reply_to_message:
        return
    exit(0)


@user.on_message(user.owner & user.command('listEval'))
async def list_exec(_, message: Message):
    try:
        x: BotResults = await user.get_inline_bot_results(
            info['_bot_username'],
            '_listEval',
        )
    except (
        user.exceptions.PeerIdInvalid,
        user.exceptions.BotResponseTimeout,
    ):
        return await message.reply_text(
            'no tasks', 
            quote=True,
        )
    for m in x.results:
        await message.reply_inline_bot_result(
            x.query_id, 
            m.id, 
            quote=True,
        )


@bot.on_inline_query(
    user.filters.user(info['_user_id'])
    & user.filters.regex('^_listEval'),
)
async def _(_, query: InlineQuery):
    buttons = [[
        user.types.InlineKeyboardButton(
            text='cancel all',
            callback_data='cancel_eval_all',
        ),
    ]]
    for x, _ in exec_tasks.items():
        buttons.append(
            [
                user.types.InlineKeyboardButton(
                    text=x, callback_data=f'cancel_eval_{x}',
                ),
            ],
        )
    await query.answer(
        results=[
            user.types.InlineQueryResultArticle(
                title='list eval tasks',
                input_message_content=user.types.InputTextMessageContent(
                    user.md.KanTeXDocument(
                        user.md.Section(
                            'ListEvalTasks',
                            user.md.KeyValueItem(
                                'Tasks Running',
                                str(len(exec_tasks)),
                            ),
                        ),
                    ),
                ),
                reply_markup=user.types.InlineKeyboardMarkup(buttons),
            ),
        ],
        cache_time=0,
    )


@bot.on_callback_query(
    user.filters.user(info['_user_id'])
    & user.filters.regex('^cancel_'),
)
async def cancel_exec(_, query: CallbackQuery):
    Type = query.data.split('_')[1]
    taskID = query.data.split('_')[2]
    if Type == 'eval':
        if taskID == 'all':
            for _, i in exec_tasks.items():
                if not isinstance(i, AsyncTask):
                    continue
                i.cancel()
            return await query.edit_message_text(
                'All tasks have been cancelled.',
            )
        else:
            try:
                task = exec_tasks.get(taskID)
            except IndexError:
                return
        if not isinstance(task, AsyncTask):
            return await query.answer(
                'Task does not exist anymore',
                show_alert=True,
            )
        task.cancel()
        return await query.edit_message_text(f'{taskID} has been cancelled')


@user.on_message(
    user.sudo
    & user.command('GetID'),
)
async def get_id_handler(_, message: Message):
    user_input = user.get_non_cmd(message)
    if user_input:
        text = user.html_bold("Result:")
        for current in await user.get_my_dialogs():
            my_title: str = ''
            if current.chat.first_name: my_title += current.chat.first_name
            if current.chat.last_name: my_title += current.chat.last_name
            if current.chat.username: my_title += current.chat.username
            if current.chat.title: my_title += current.chat.title
            if not my_title: continue

            my_title = my_title.lower()
            if my_title.find(user_input) != -1:
                the_name = current.chat.title or f"{current.chat.first_name} {current.chat.last_name}"[:24]
                text += f"\n  {await user.html_mention(current.chat, the_name)} "
                if current.chat.username: text += f"(@{current.chat.username})"
                text += f" - {user.html_mono(current.chat.id)}"
        return await message.reply_text(text)
    
    message = message.reply_to_message or message
    media = get_media_attr(
        message,
        [
            'audio',
            'document',
            'photo',
            'sticker',
            'animation',
            'video',
            'voice',
            'video_note',
            'new_chat_photo',
        ],
    )
    appendable = [
        user.md.KeyValueItem(
            user.md.Bold('chatID'),
            user.md.Code(message.chat.id),
        ),
        user.md.KeyValueItem(
            user.md.Bold('fromUserID'),
            user.md.Code(message.from_user.id),
        ),
    ]
    text = user.md.Section('getID')
    if not media:
        for a in appendable:
            text.append(a)
        return await message.reply_text(user.md.KanTeXDocument(text))

    f_id = getattr(media, 'file_id', None)
    f_unique_id = getattr(media, 'file_unique_id', None)
    medias = [
        user.md.KeyValueItem(
            user.md.Bold('fileID'),
            user.md.Code(f_id),
        ),
        user.md.KeyValueItem(
            user.md.Bold('fileUniqueID'),
            user.md.Code(f_unique_id),
        ),
    ]
    for media in medias:
        appendable.append(media)
    for a in appendable:
        text.append(a)
    return await message.reply_text(user.md.KanTeXDocument(text))


def _gf(body):
    func = ast.AsyncFunctionDef(
        'ex',
        ast.arguments(
            [],
            [
                ast.arg(
                    i, None, None,
                ) for i in [
                    'c',
                    'client',
                    'm',
                    'message',
                    'executing',
                    'r',
                    'reply',
                    '_ueri',
                ]
            ],
            None,
            [],
            [],
            None,
            [],
        ),
        body,
        [],
        None,
        None,
    )
    ast.fix_missing_locations(func)
    mod = ast.parse('')
    mod.body = [func]
    fl = locals().copy()
    exec(compile(mod, '<ast>', 'exec'), globals(), fl)
    return fl['ex']


class UniqueExecReturnIdentifier:
    pass
