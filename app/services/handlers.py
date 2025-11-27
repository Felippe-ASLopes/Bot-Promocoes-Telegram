from app.core import database
from app.services import output

async def handle_valid_offer(client, product, price, block, msg_date_br, chat_name, event, msg_link):
    keyword = product['keyword']
    subscribers = product.get('subscribers', {})
    
    output.logger(chat_name, block, 'offer', price)
    
    database.update_product_stats(keyword, price, msg_date_br, event.chat_id, event.message.id)
    
    await output.notify_users(client, subscribers, keyword, price, msg_link, chat_name)

async def handle_suspicious_price(chat_name, block, price):
    output.logger(chat_name, block, 'ignored', price)

async def handle_no_price_found(chat_name, text):
    output.logger(chat_name, text, 'no_price')

def handle_ignored(chat_name, text):
    output.logger(chat_name, text, 'ignored')