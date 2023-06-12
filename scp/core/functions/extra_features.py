from scp.utils.null_type import nullable
from pyrogram.types import (
    Message,
    User
)

def make_types_nullable():
    nullable(Message)
    nullable(User)

# loads extra features
def load_extra_features():
    # make_types_nullable()
    pass


