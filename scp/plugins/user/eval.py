# https://greentreesnakes.readthedocs.io/
# https://gitlab.com/blankX/sukuinote/-/blob/master/sukuinote/plugins/pyexec.py
import ast
from _ast import Module as TModule
import sys
import html
import inspect
import asyncio
from shortuuid import ShortUUID
from io import StringIO, BytesIO
from scp import user, bot
from scp.utils.selfInfo import info
from scp.utils.parser import getMediaAttr, html_bold, html_mono, html_normal, to_output_file
from pyrogram.types import (
    Message,
)

exec_tasks = {}


@user.on_message(
    ~user.filters.forwarded
    & ~user.filters.sticker
    & ~user.filters.via_bot
    & ~user.filters.edited
    & user.owner
    & user.filters.command(
        'eval',
        prefixes=user.cmd_prefixes,
    ),
)
async def pyexec(client: user, message: Message):
    code = user.get_non_cmd(message)
    if len(code) == 0:
        if not message.reply_to_message:
            return
        code = message.reply_to_message.text
    
    tree: TModule = None
    try:
        tree = ast.parse(code)
    except Exception as ex:
        str_err = str(ex)
        if len(str_err) > 4096:
            await message.reply_document(to_output_file(str_err))
            return
        txt = html_mono(str_err)
        return await message.reply_text(txt, parse_mode='html')
    
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
            return await message.reply_text(txt, parse_mode='html')
        exx = _gf(o_body)
    rnd_id = '#' + str(ShortUUID().random(length=8))
    reply = await message.reply_text(
        html_bold('Executing task ') + html_mono(rnd_id, '...'),
        quote=True,
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
        task = asyncio.create_task(async_obj())
        exec_tasks[rnd_id] = task
        try:
            returned = await task
        except Exception as err:
            returned = err
            return await reply.edit_text(
                user.md.KanTeXDocument(
                    user.md.Section('Error:', user.md.Code(err)),
                ),
            )
    except asyncio.CancelledError:
        sys.stdout = stdout
        sys.stderr = stderr
        exec_tasks.pop(rnd_id, None)
        return await reply.edit_text(
            user.md.KanTeXDocument(
                user.md.Section(
                    'Task Cancelled:',
                    user.md.Code(f'{rnd_id} has been canceled.'),
                ),
            ),
        )
    except Exception as e:
        str_err = str(e)
        if len(str_err) > 4096:
            await asyncio.gather(reply.delete(), message.reply_document(to_output_file(str_err)))
            return
        txt = html_bold('Error for task')
        txt += html_mono(f' {rnd_id} ', ':\n')
        txt += html_mono(f' {str(e)} ')
        return await reply.edit_text()
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

    if len(output) > 4096:
        out = wrapped_stdout_text + '\n'
        for i in returned:
            out += str(i).strip() + '\n'
        f = BytesIO(out.strip().encode('utf-8'))
        f.name = f'output-{rnd_id}.txt'
        await asyncio.gather(reply.delete(), message.reply_document(f))
    else:
        txt = html_bold('Output for') + html_mono(' ' + rnd_id, ':\n    ')
        txt += html_mono(output)
        await reply.edit_text(txt, parse_mode='html')


@user.on_message(
    ~user.filters.forwarded
    & ~user.filters.sticker
    & ~user.filters.via_bot
    & ~user.filters.edited
    & user.owner
    & user.filters.command(
        'exit',
        prefixes=user.cmd_prefixes,
    ),
)
async def exitexec(_, message: user.types.Message):
    if message.reply_to_message:
        return
    exit(0)


@user.on_message(user.owner & user.command('listEval'))
async def listexec(_, message: user.types.Message):
    try:
        x = await user.get_inline_bot_results(
            info['_bot_username'],
            '_listEval',
        )
    except (
        user.exceptions.PeerIdInvalid,
        user.exceptions.BotResponseTimeout,
    ):
        return await message.reply('no tasks', quote=True)
    for m in x.results:
        await message.reply_inline_bot_result(x.query_id, m.id, quote=True)


@bot.on_inline_query(
    user.filters.user(info['_user_id'])
    & user.filters.regex('^_listEval'),
)
async def _(_, query: user.types.InlineQuery):
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
async def cancelexec(_, query: user.types.CallbackQuery):
    Type = query.data.split('_')[1]
    taskID = query.data.split('_')[2]
    if Type == 'eval':
        if taskID == 'all':
            for _, i in exec_tasks.items():
                i.cancel()
            return await query.edit_message_text(
                'All tasks has been cancelled',
            )
        else:
            try:
                task = exec_tasks.get(taskID)
            except IndexError:
                return
        if not task:
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
async def _(_, message: user.types.Message):
    message = message.reply_to_message or message
    media = getMediaAttr(
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
        return await message.reply(user.md.KanTeXDocument(text))
    medias = [
        user.md.KeyValueItem(
            user.md.Bold('fileID'),
            user.md.Code(media.file_id),
        ),
        user.md.KeyValueItem(
            user.md.Bold('fileUniqueID'),
            user.md.Code(media.file_unique_id),
        ),
    ]
    for media in medias:
        appendable.append(media)
    for a in appendable:
        text.append(a)
    return await message.reply(user.md.KanTeXDocument(text))


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
