from scp.utils.null_type import make_nullable
from pyrogram.types import Message

def make_types_nullable():
    make_nullable(Message)

# loads extra features
def load_extra_features():
    make_types_nullable()


