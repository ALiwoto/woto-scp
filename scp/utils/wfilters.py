from pyrogram import (
    types,
    filters,
)


async def my_contacts_filter(_, __, m: types.Message) -> bool:
    return m and m.from_user and m.from_user.is_contact

my_contacts = filters.create(my_contacts_filter)
"""Filter messages sent by contact users."""