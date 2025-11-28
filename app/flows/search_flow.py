import asyncio
from app.core import database, state, config
from app.core.utils import extract_price, split_message_blocks, get_search_ranges, BR_TZ
from telethon import types

async def start(event):
    my_products = database.list_user_products(event.sender_id)
    
    msg = "🔎 **CENTRAL DE BUSCA**\n\n"
    msg += "Deseja pesquisar o histórico de preços de qual produto?\n\n"
    
    if my_products:
        msg += "📋 **Seus itens monitorados** (Toque para copiar):\n"
        for p in my_products: 
            msg += f"• `{p['keyword']}`\n"
        msg += "\n"
    
    msg += "✨ **Busca Avulsa:**\n"
    msg += "Digite o nome de qualquer outro produto para fazer uma varredura rápida sem salvar na lista.\n\n"
    
    msg += "👇 **Responda com o nome do produto:**"
    
    state.user_states[event.sender_id] = state.STATE_WAIT_SEARCH_KEYWORD
    await event.reply(msg)

async def handle_keyword(event, text):
    user_id = event.sender_id
    keyword = text.strip()
    my_prods = database.list_user_products(user_id)
    target_prod = next((p for p in my_prods if p['keyword'] == keyword), None)
    
    if target_prod:
        is_registered = True
        target_price = target_prod['my_target']
        min_threshold = target_price * 0.40
    else:
        is_registered = False
        target_price = 0.0
        min_threshold = 5.0
        
        await event.reply(f"⚠️ **{keyword}** não está monitorado.\n🔎 Realizando busca avulsa sem salvar histórico...")

    state.cancel_state(user_id)
    
    try:
        limit_val = config.SEARCH_LIMIT
        delay_val = config.SEARCH_DELAY
    except:
        limit_val = 500
        delay_val = 1.5
    
    status_msg = await event.reply(f"⏳ Buscando `{keyword}`...\nLimite: {limit_val} registros.")
    
    limit_date, allowed_months = get_search_ranges()
    total_processed = 0
    total_price_sum = 0.0
    offers_found_count = 0
    limit_reached = False
    best_offer = None
    
    client = event.client
    dialogs = await client.get_dialogs()
    chats = [d for d in dialogs if d.is_channel or d.is_group]

    for chat in chats:
        if delay_val > 0: await asyncio.sleep(delay_val)

        if total_processed >= limit_val:
            limit_reached = True
            break
        try:
            async for message in client.iter_messages(chat, search=keyword, limit=None):
                if total_processed >= limit_val:
                    limit_reached = True
                    break
                
                content = message.raw_text or message.message or ""
                if message.media and isinstance(message.media, types.MessageMediaWebPage):
                    wp = message.media.webpage
                    if wp:
                        if hasattr(wp, 'title') and wp.title: content += f"\n{wp.title}"
                        if hasattr(wp, 'description') and wp.description: content += f"\n{wp.description}"

                if content:
                    msg_date_br = message.date.astimezone(BR_TZ)
                    if msg_date_br.replace(tzinfo=None) < limit_date: continue
                    if allowed_months and (msg_date_br.year, msg_date_br.month) not in allowed_months: continue

                    blocks = split_message_blocks(content)
                    for block in blocks:
                        if keyword.lower() in block.lower():
                            price, _ = extract_price(block, min_threshold)
                            if price:
                                if is_registered:
                                    database.update_product_stats(keyword, price, msg_date_br, chat.id, message.id)
                                
                                total_processed += 1
                                total_price_sum += price
                                
                                msg_link = f"https://t.me/c/{chat.id}/{message.id}".replace("-100", "")
                                if hasattr(chat, 'username') and chat.username:
                                    msg_link = f"https://t.me/{chat.username}/{message.id}"
                                
                                if is_registered and price <= target_price: 
                                    offers_found_count += 1
                                
                                if best_offer is None or price < best_offer['price']:
                                    chat_title = chat.title if chat.title else "Canal"
                                    best_offer = {'price': price, 'date': msg_date_br, 'link': msg_link, 'chat': chat_title}
                                break
        except: continue
    
    average_price = total_price_sum / total_processed if total_processed > 0 else 0.0
    
    limit_text = f"\n⚠️ Limite atingido" if limit_reached else ""
    
    offers_text = f"📉 Ofertas abaixo da meta: {offers_found_count}" if is_registered else "📉 Meta não definida (Busca Livre)"

    if best_offer:
        summary = (
            f"🏁 **BUSCA: {keyword.upper()}**\n{limit_text}\n"
            f"📊 Analisados: {total_processed}\n"
            f"⚖️ Média: R$ {average_price:.2f}\n"
            f"{offers_text}\n━━━━━━━━━━━━\n"
            f"🏆 **MELHOR:** R$ {best_offer['price']:.2f}\n"
            f"📅 {best_offer['date'].strftime('%d/%m/%y %H:%M')} | {best_offer['chat']}\n"
            f"🔗 [VER OFERTA]({best_offer['link']})"
        )
    else: summary = f"🏁 **BUSCA: {keyword.upper()}**\n❌ Nenhuma oferta encontrada."
    
    await status_msg.edit(summary, link_preview=False)