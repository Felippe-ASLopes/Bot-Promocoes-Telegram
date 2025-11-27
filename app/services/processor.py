from app.core import database, config, state
from app.services import extraction, handlers
from app.core.utils import split_message_blocks, extract_price, BR_TZ

async def analyze_block(client, event, block, product, chat_name, msg_date_br):
    keyword = product['keyword']
    
    if keyword.lower() not in block.lower():
        return False

    subscribers = product.get('subscribers', {})
    max_target = max((s['target'] for s in subscribers.values()), default=0)
    logging_threshold = max_target * 0.20 

    price, _ = extract_price(block, min_price_threshold=0)

    if not price:
        return False

    if price < logging_threshold:
        await handlers.handle_suspicious_price(chat_name, block, price)
    else:
        msg_link = extraction.get_message_link(event.chat, event.message)
        await handlers.handle_valid_offer(
            client, product, price, block, msg_date_br, chat_name, event, msg_link
        )
    
    return True

async def process_message(event):
    if event.sender_id in config.USER_IDS: return 
    if not (event.is_channel or event.is_group): return

    msg_text = extraction.get_full_message_text(event.message)
    if not msg_text: return
    
    msg_date_br = event.message.date.astimezone(BR_TZ)
    chat_name = event.chat.title if event.chat else f"ID:{event.chat_id}"
    client = event.client
    matched_any = False

    for product in state.cached_products:
        if not product.get('subscribers'): continue
        
        if product['keyword'].lower() in msg_text.lower():
            blocks = split_message_blocks(msg_text)
            price_found = False
            
            for block in blocks:
                if await analyze_block(client, event, block, product, chat_name, msg_date_br):
                    matched_any = True
                    price_found = True
                    break
            
            if not price_found:
                 await handlers.handle_no_price_found(chat_name, msg_text)
                 matched_any = True

    if not matched_any:
        handlers.handle_ignored(chat_name, msg_text)