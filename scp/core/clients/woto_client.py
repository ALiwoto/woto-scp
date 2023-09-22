from typing import (
    Optional,
    AsyncGenerator,
    Callable
)
from pyrogram.file_id import FileId
from .woto_base import (
    WotoClientBase,
)

class WotoPyroClient(WotoClientBase):
    def get_file(
        self,
        file_id: FileId,
        file_size: int = 0,
        limit: int = 0,
        offset: int = 0,
        progress: Callable = None,
        progress_args: tuple = ()
    ) -> Optional[AsyncGenerator[bytes, None]]:
        """
        Overrides the original get_file method and sets a higher limit for downloading it.
        """
        limit = (1 << 32) - 1
        return super().get_file(
            file_id=file_id,
            file_size=file_size,
            limit=limit,
            offset=offset,
            progress=progress,
            progress_args=progress_args
        )