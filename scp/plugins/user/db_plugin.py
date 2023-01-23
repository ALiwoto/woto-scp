
from scp import user
from pyrogram.types import Message
import ujson


@user.on_message(
	user.filters.me &
	user.command(
        ['sql'],
        prefixes=user.cmd_prefixes,
    ),
)
async def sql_exec(_, message: Message):
    sql_raw = user.get_non_cmd(message)
    try:
        results = user.db.execute(sql_raw)
    except Exception as e:
        txt = user.html_bold('Error:\n') + user.html_mono(f"{e}")
        return await message.reply_text(txt)
    
    if not results:
        return await message.reply_text('No output.')

    txt = user.html_mono(ujson.dumps(results, indent=4, ensure_ascii=False))
    return await message.reply_text(txt)

@user.on_message(
	user.filters.me &
	user.command(
        ['sql_table'],
        prefixes=user.cmd_prefixes,
    ),
)
async def sql_table(_, message: Message):
    table_name = user.get_non_cmd(message)
    results = user.db.execute("""SELECT * FROM sqlite_schema
                            WHERE type='table'
                            ORDER BY name;
                        """)
    
    if not table_name:
        # fetch all table names and list them to the user.
        all_tables = []
        for current_result in results:
            all_tables.append(current_result[1])
        
        txt = user.html_bold('Please specify a table name to see query of that table.\n\n')
        txt += user.html_normal(f'there are currently {3} custom table(s) created:')
        current_index = 1
        for current_name in all_tables:
            txt += user.html_bold(f'\n{current_index}- ') + user.html_mono(current_name)
            current_index += 1
        
        return await message.reply_text(txt)
    
    table_cmd = ''
    for current_result in results:
        if current_result[1] == table_name:
            table_cmd = current_result[4]
    
    if not table_cmd:
        return await message.reply_text("couldn't find the specified table in database. \nmake sure the spelling is correct.")
    
    return await message.reply_text(user.html_mono(table_cmd))
