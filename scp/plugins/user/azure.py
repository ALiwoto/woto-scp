from pyrogram.types import (
    Message,
)
from scp import user

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
    
    if not speech_config.speech_synthesis_voice_name:
        # set this as default voice name, we can change it later on
        speech_config.speech_synthesis_voice_name='en-US-JennyNeural'
    
    speech_syn = getattr(user, 'speech_syn', None)
    if not speech_syn:
        speech_syn = speech_sdk.SpeechSynthesizer(
            speech_config=speech_config,
            audio_config=audio_config
        )
        setattr(user, 'speech_syn', speech_syn)
    
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

