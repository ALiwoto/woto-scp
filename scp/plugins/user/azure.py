from enum import Enum
from pyrogram.types import (
    Message,
)
from scp import user
from gpytranslate import Translator

trl_client = Translator()

class VoiceGender(Enum):
    FEMALE = 0
    MALE = 1
    FEMALE_CHILD = 2
    MALE_CHILD = 1

_AZURE_SHORT_TO_LANG = {
    'af':'af-ZA',
    'am':'am-ET',
    'ar':'ar-AE',
    'az':'az-AZ',
    'bg':'bg-BG',
    'bn':'bn-BD',
    'bs':'bs-BA',
    'ca':'ca-ES',
    'cs':'cs-CZ',
    'cy':'cy-GB',
    'da':'da-DK',
    'de':'de-DE',
    'el':'el-GR',
    'en':'en-US',
    'es':'es-ES',
    'et':'et-EE',
    'eu':'eu-ES',
    'fa':'fa-IR',
    'fi':'fi-FI',
    'fil':'fil-PH',
    'fr':'fr-FR',
    'ga':'ga-IE',
    'gl':'gl-ES',
    'gu':'gu-IN',
    'he':'he-IL',
    'hi':'hi-IN',
    'hr':'hr-HR',
    'hu':'hu-HU',
    'hy':'hy-AM',
    'id':'id-ID',
    'is':'is-IS',
    'it':'it-IT',
    'ja':'ja-JP',
    'jv':'jv-ID',
    'ka':'ka-GE',
    'kk':'kk-KZ',
    'km':'km-KH',
    'ko':'ko-KR',
    'lo':'lo-LA',
    'lt':'lt-LT',
    'lv':'lv-LV',
    'mk':'mk-MK',
    'ml':'ml-IN',
    'mn':'mn-MN',
    'mr':'mr-IN',
    'ms':'ms-MY',
    'mt':'mt-MT',
    'my':'my-MM',
    'nb':'nb-NO',
    'ne':'ne-NP',
    'nl':'nl-BE',
    'pl':'pl-PL',
    'ps':'ps-AF',
    'pt':'pt-BR',
}

_AZURE_LANG_TO_VOICE = {
    'en-AU': [
        ('en-AU-AnnetteNeural', VoiceGender.FEMALE),
        ('en-AU-CarlyNeural', VoiceGender.FEMALE),
        ('en-AU-DarrenNeural', VoiceGender.MALE),
        ('en-AU-DuncanNeural', VoiceGender.MALE),
    ],
    'en-IN': [
        ('en-IN-NeerjaNeural', VoiceGender.FEMALE),
        ('en-IN-PrabhatNeural', VoiceGender.MALE)
    ],
    'en-GB': [
        ('en-GB-AbbiNeural', VoiceGender.FEMALE),
        ('en-GB-AlfieNeural', VoiceGender.MALE)
    ],
    'en-US': [
        ('en-US-AmberNeural', VoiceGender.FEMALE),
        ('en-US-AnaNeural', VoiceGender.FEMALE_CHILD),
        ('en-US-AriaNeural', VoiceGender.FEMALE),
        ('en-US-AshleyNeural', VoiceGender.FEMALE),
        ('en-US-BrandonNeural', VoiceGender.MALE)
    ],
    'fa-IR': [
        ('fa-IR-DilaraNeural', VoiceGender.FEMALE),
        ('fa-IR-FaridNeural', VoiceGender.FEMALE)
    ],
    'fil-PH': [
        ('fil-PH-AngeloNeural', VoiceGender.MALE),
        ('fil-PH-BlessicaNeural', VoiceGender.FEMALE)
    ],
    'fr-FR': [
        ('fr-FR-AlainNeural', VoiceGender.MALE),
        ('fr-FR-BrigitteNeural', VoiceGender.FEMALE)
    ],
    'ja-JP': [
        ('ja-JP-AoiNeural', VoiceGender.FEMALE),
        ('ja-JP-DaichiNeural', VoiceGender.MALE),
        ('ja-JP-KeitaNeural', VoiceGender.MALE),
        ('ja-JP-MayuNeural', VoiceGender.FEMALE),
        ('ja-JP-NanamiNeural', VoiceGender.FEMALE),
        ('ja-JP-NaokiNeural', VoiceGender.MALE),
        ('ja-JP-ShioriNeural', VoiceGender.FEMALE)
    ],
    'jv-ID': [
        ('jv-ID-DimasNeural', VoiceGender.MALE),
        ('jv-ID-SitiNeural', VoiceGender.FEMALE)
    ],
    'he-IL': [
        ('he-IL-AvriNeural', VoiceGender.MALE),
        ('he-IL-HilaNeural', VoiceGender.MALE)
    ],
    'hi-IN': [
        ('hi-IN-MadhurNeural', VoiceGender.MALE),
        ('hi-IN-SwaraNeural', VoiceGender.FEMALE)
    ],
    'pt-BR': [
        ('pt-BR-AntonioNeural', VoiceGender.MALE),
        ('pt-BR-BrendaNeural', VoiceGender.FEMALE),
    ]
}

@user.on_message(
    ~user.filters.forwarded
    & ~user.filters.sticker
    & ~user.filters.via_bot
    & user.filters.me
    & user.command(
        'toVoice',
        prefixes=user.cmd_prefixes,
    ),
)
async def to_voice_handler(_, message: Message):
    the_text = user.get_non_cmd(message=message)
    if not the_text:
        if not message.reply_to_message:
            return await message.reply_text("Please give a text or reply to a message.")
        the_text = message.reply_to_message.text or message.reply_to_message.caption
    
    if not the_text:
        return await message.reply_text("Please give a text or reply to a message.")
    
    detected_language = await trl_client.detect(the_text)

    try:
        import azure.cognitiveservices.speech as speech_sdk
    except Exception as ex:
        return await user.reply_exception(
            message='Failed to import azure library (azure.cognitiveservices.speech)',
            e=ex,
            limit=2
        )

    audio_config = getattr(user, 'audio_config', None)
    if not audio_config:
        audio_config = speech_sdk.audio.AudioOutputConfig(use_default_speaker=True)
        setattr(user,  'audio_config', audio_config)
    
    speech_config = getattr(user, 'speech_config', None)
    if not speech_config:
        speech_config = speech_sdk.SpeechConfig(
            subscription=user.scp_config.azure_api_key,
            region=user.scp_config.azure_api_region)
        setattr(user, 'speech_config', speech_config)
    
    the_lang = _AZURE_SHORT_TO_LANG.get(detected_language, None)
    if not the_lang:
        return await message.reply_text(
            message=f'The language \'{detected_language}\' detected but is not registered.'
        )
    
    voice_name = _AZURE_LANG_TO_VOICE.get(the_lang, None)
    if not voice_name:
        return await message.reply_text(
            message=f'The language \'{the_lang}\' is registered but has no voice.'
        )
    
    speech_config.speech_recognition_language = the_lang
    user_selected_voice = getattr(speech_config, 'user_selected_voice', None)
    if user_selected_voice:
        # The full list of supported voices can be found here:
        # https://aka.ms/csspeech/voicenames
        speech_config.speech_synthesis_voice_name = user_selected_voice
    else:
        speech_config.speech_synthesis_voice_name = voice_name[0][0]
    
    speech_syn = speech_sdk.SpeechSynthesizer(
        speech_config=speech_config,
        audio_config=audio_config
    )
    
    top_message = await message.reply_text(
        text=user.html_mono('Generating voice for the given text...')
    )
    speech_result = speech_syn.speak_text_async(the_text).get()
    audio_data: bytes = getattr(speech_result, 'audio_data', None)
    if not audio_data:
        return await message.reply_text('Failed to retrieve audio data from azure servers.')
    
    await top_message.delete()
    await message.reply_document(
        document=user.to_output_file(audio_data, 'output.wav')
    )

