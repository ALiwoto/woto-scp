from scp.utils.mdparser import escapeAny
from scp import user


async def report_error(e, module, the_user):
    await user.send_message(user.log_channel,
            f"**{escapeAny('Failed due to: ')}** " +
            f"`{escapeAny(e)}` \n " +
            f"{escapeAny('by user:')} {escapeAny(the_user)}" +
            f"{escapeAny('in module: ')} {escapeAny(module)}")


