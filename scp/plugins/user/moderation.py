import asyncio
import html
from io import BytesIO
from scp import user

@user.on_message(~user.filters.scheduled & 
	~user.filters.forwarded & 
	~user.filters.sticker & 
	~user.filters.via_bot & 
	~user.filters.edited & 
	user.owner & 
	user.filters.command(
        ['admins'],
        prefixes=user.cmd_prefixes,
    ))
async def admins_handler(_, message: user.types.Message):
    all_strs = message.text.split(' ')
    if len(all_strs) < 2:
        the_chat = message.chat.id
    else:
        the_chat = message.text.split(' ')[1]
        if the_chat.find('/') > 0:
            all_strs = the_chat.split('/')
            index = len(all_strs) - 1
            if all_strs[index].isdigit():
                index -= 1
            the_chat = all_strs[index]
        
    top_msg = await message.reply_text(f"<code>{html.escape('fetching group admins...')}</code>")
    txt = ''
    m = None
    try:
        m = await user.get_chat_members(the_chat)
    except Exception as ex:
        await top_msg.edit_text(text=f"<code>{ex}</code>")
        return
    creator = None
    admins = []
    bots = []
    for i in m:
        if i.status == 'creator':
            creator = i
        elif i.status == 'administrator':
            if i.user.is_bot:
                bots.append(i)
                continue
            admins.append(i)

    if not creator and len(admins) == 0:
        await top_msg.edit_text(text="Seems like all admins are anon...")
        return

    starter = "<code>" + " • " + "</code>"
    if creator:
        txt += "<bold>" + html.escape("The creator:") + "</bold>\n"
        txt += starter + f"<a href=tg://user?id={creator.user.id}>{html.escape(creator.user.first_name[:16])}</a>"
        txt += f": <code>{creator.user.id}</code>"
        txt += "\n\n"

    if len(admins) > 0:
        txt += "<bold>" + html.escape("Admins:\n") + "</bold>"
        for admin in admins:
            txt += starter + f"<a href=tg://user?id={admin.user.id}>{html.escape(admin.user.first_name[:16])}</a>"
            txt += f": <code>{admin.user.id}</code>"
            txt += "\n"
        txt += "\n"
    
    if len(bots) > 0:
        txt += "<bold>" + html.escape("Bots:\n") + "</bold>"
        for bot in bots:
            txt += starter + f"<a href=tg://user?id={bot.user.id}>{html.escape(bot.user.first_name[:16])}</a>"
            txt += f": <code>{bot.user.id}</code>"
            txt += "\n"
        txt += "\n"
    
    if len(txt) > 4096:
        f = BytesIO(txt.strip().encode('utf-8'))
        f.name = 'output.txt'
        await asyncio.gather(top_msg.delete(), message.reply_document(f))
        return

    await top_msg.edit_text(text=txt, parse_mode="html")
    
