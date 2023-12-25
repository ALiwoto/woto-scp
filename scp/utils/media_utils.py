

class PixivIllustInfo:
    is_multiple: bool = False
    meta_pages: list = None

    has_error: bool = False
    error_message: str = None
    user_error_message: str = None
    error_reason: str = None

    def __init__(self, illust_json) -> None:
        if illust_json.error:
            self.has_error = True
            self.error_message = illust_json.error.message
            self.user_error_message = illust_json.error.user_message
            self.error_reason = illust_json.error.reason
            return
        self.is_multiple = illust_json.illust.meta_pages != None \
            and len(illust_json.illust.meta_pages) > 0
        if self.is_multiple:
            self.meta_pages = illust_json.illust.meta_pages

    def get_original_image_url(self) -> str:
        pass

