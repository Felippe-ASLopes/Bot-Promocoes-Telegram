from telethon import types

def get_full_message_text(message):
    msg_text = message.raw_text or message.message or ""
    
    if message.media and isinstance(message.media, types.MessageMediaWebPage):
        wp = message.media.webpage
        if wp and not isinstance(wp, types.WebPageEmpty):
            if hasattr(wp, 'title') and wp.title: 
                msg_text += f" | WP_TITLE: {wp.title}"
            if hasattr(wp, 'description') and wp.description: 
                msg_text += f" | WP_DESC: {wp.description}"
    return msg_text

def get_message_link(chat, message):
    msg_link = f"https://t.me/c/{chat.id}/{message.id}".replace("-100", "")
    if hasattr(chat, 'username') and chat.username:
        msg_link = f"https://t.me/{chat.username}/{message.id}"
    return msg_link