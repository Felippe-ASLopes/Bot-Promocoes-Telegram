import sys
import asyncio
import re
sys.stdout.reconfigure(encoding='utf-8')

from telethon import TelegramClient, events, types
from datetime import datetime, timezone, timedelta
import config
import database
from utils import extract_price, split_message_blocks, get_search_ranges

BR_TZ = timezone(timedelta(hours=-3))
client = TelegramClient(config.SESSION_NAME, config.API_ID, config.API_HASH)

user_states = {}
temp_data = {}
cached_products = []

STATE_WAIT_ADD_NAME = "wait_add_name"
STATE_WAIT_ADD_PRICE = "wait_add_price"
STATE_WAIT_ADD_LIMIT_OPTION = "wait_add_limit_option"
STATE_WAIT_ADD_LIMIT_VALUE = "wait_add_limit_value"
STATE_WAIT_DEL_KEYWORD = "wait_del_keyword"
STATE_WAIT_SEARCH_KEYWORD = "wait_search_keyword"
STATE_WAIT_EDIT_KEYWORD = "wait_edit_keyword"
STATE_WAIT_EDIT_PRICE = "wait_edit_price"
STATE_WAIT_EDIT_CHOOSE_FIELD = "wait_edit_choose_field"
STATE_WAIT_EDIT_LIMIT_OPTION = "wait_edit_limit_option"
STATE_WAIT_EDIT_LIMIT_VALUE = "wait_edit_limit_value"

def reload_cache():
    global cached_products
    cached_products = database.get_all_monitored_products()
    print(f"Cache atualizado: {len(cached_products)} produtos monitorados.")

def cancel_state(user_id):
    if user_id in user_states: del user_states[user_id]
    if user_id in temp_data: del temp_data[user_id]

def log_analysis(channel, text, status, color_code="\033[0m"):
    clean_text = text.replace('\n', ' ')[:40]
    time_now = datetime.now().strftime('%H:%M:%S')
    print(f"{color_code}[{time_now}] [{channel[:15]:<15}] {status:<20} | Text: \"{clean_text}...\"\033[0m")

@client.on(events.NewMessage(from_users=config.USER_IDS, pattern=r'^/(start|help|menu)'))
async def show_menu(event):
    cancel_state(event.sender_id)
    msg = "🤖 **MENU**\n\n🆕 /adicionar\n✏️ /editar\n🗑️ /remover\n📋 /listar\n🕵️‍♂️ /buscar\n❌ /cancelar"
    await event.reply(msg)

@client.on(events.NewMessage(from_users=config.USER_IDS, pattern=r'^/listar'))
async def cmd_list(event):
    cancel_state(event.sender_id)
    my_products = database.list_user_products(event.sender_id)
    
    if not my_products:
        await event.reply("📭 Lista vazia.")
        return
    
    msg = "📋 **SEUS PRODUTOS MONITORADOS:**\n\n"
    for p in my_products:
        stats = p.get('stats', {})
        lowest = stats.get('lowest_price')
        low_fmt = f"R$ {lowest:.2f}" if lowest else "N/A"
        limit_val = p.get('my_limit', 0)
        if limit_val > 0:
            limit_fmt = f"R$ {limit_val:.2f}"
        else:
            limit_fmt = "Sem limite"

        msg += (
            f"📦 **{p['keyword']}**\n"
            f"🎯 Meta: R$ {p['my_target']:.2f}\n"
            f"🛡️ Limite: {limit_fmt}\n"
            f"📉 Menor Preço Histórico: {low_fmt}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
        )
        
    await event.reply(msg)

@client.on(events.NewMessage(from_users=config.USER_IDS, pattern=r'^/cancelar'))
async def cmd_cancel(event):
    cancel_state(event.sender_id)
    await event.reply("✅ Cancelado.")

@client.on(events.NewMessage(from_users=config.USER_IDS, pattern=r'^/adicionar'))
async def start_add(event):
    user_states[event.sender_id] = STATE_WAIT_ADD_NAME
    await event.reply("🆕 Nome do produto:")

@client.on(events.NewMessage(from_users=config.USER_IDS, pattern=r'^/remover'))
async def start_del(event):
    my_products = database.list_user_products(event.sender_id)
    if not my_products:
        await event.reply("📭 Nada para remover.")
        return
    msg = "🗑️ **Copie para remover:**\n\n"
    for p in my_products: msg += f"• `{p['keyword']}`\n"
    user_states[event.sender_id] = STATE_WAIT_DEL_KEYWORD
    await event.reply(msg)

@client.on(events.NewMessage(from_users=config.USER_IDS, pattern=r'^/editar'))
async def start_edit(event):
    my_products = database.list_user_products(event.sender_id)
    if not my_products:
        await event.reply("📭 Nada para editar.")
        return
    msg = "✏️ **Copie para editar:**\n\n"
    for p in my_products: msg += f"• `{p['keyword']}` (R$ {p['my_target']:.2f})\n"
    user_states[event.sender_id] = STATE_WAIT_EDIT_KEYWORD
    await event.reply(msg)

@client.on(events.NewMessage(from_users=config.USER_IDS, pattern=r'^/buscar'))
async def start_search(event):
    my_products = database.list_user_products(event.sender_id)
    if not my_products:
        await event.reply("📭 Nada para buscar.")
        return
    msg = "🕵️‍♂️ **Copie para pesquisar:**\n\n"
    for p in my_products: msg += f"• `{p['keyword']}`\n"
    user_states[event.sender_id] = STATE_WAIT_SEARCH_KEYWORD
    await event.reply(msg)

@client.on(events.NewMessage(from_users=config.USER_IDS))
async def dialogue_manager(event):
    text = event.text
    user_id = event.sender_id
    if text.startswith('/') or user_id not in user_states: return
    state = user_states[user_id]

    if state == STATE_WAIT_ADD_NAME:
        temp_data[user_id] = {'keyword': text.strip()}
        user_states[user_id] = STATE_WAIT_ADD_PRICE
        await event.reply(f"📝 **{text}**\nQual a **Meta de Preço**?")
    
    elif state == STATE_WAIT_ADD_PRICE:
        try:
            price = float(text.replace(',', '.').strip())
            temp_data[user_id]['price'] = price
            
            user_states[user_id] = STATE_WAIT_ADD_LIMIT_OPTION
            
            msg = (
                f"💰 Meta definida: **R$ {price:.2f}**\n\n"
                "🛡️ **Configurar Limite de Preço Mínimo**\n"
                "Ajuda a ignorar acessórios ou alarmes falsos.\n\n"
                "1️⃣ **Sem limite** (Notificar qualquer valor)\n"
                "2️⃣ **Padrão** (40% da meta - Recomendado)\n"
                "3️⃣ **Definir manualmente**\n\n"
                "Digite o número da opção (1, 2 ou 3):"
            )
            await event.reply(msg)
        except ValueError: 
            await event.reply("❌ Valor inválido. Digite apenas números (ex: 150.00).")

    elif state == STATE_WAIT_ADD_LIMIT_OPTION:
        choice = text.strip()
        keyword = temp_data[user_id]['keyword']
        target_price = temp_data[user_id]['price']
        
        if choice == '1':
            database.add_product_subscription(keyword, target_price, user_id, min_price=0)
            reload_cache()
            await event.reply(f"✅ Monitorando **{keyword}**\n🎯 Meta: R$ {target_price:.2f}\n⚡ Sem limite mínimo.")
            cancel_state(user_id)
            
        elif choice == '2':
            limit = target_price * 0.40
            database.add_product_subscription(keyword, target_price, user_id, min_price=limit)
            reload_cache()
            await event.reply(f"✅ Monitorando **{keyword}**\n🎯 Meta: R$ {target_price:.2f}\n🛡️ Mínimo auto: R$ {limit:.2f}")
            cancel_state(user_id)
            
        elif choice == '3':
            user_states[user_id] = STATE_WAIT_ADD_LIMIT_VALUE
            await event.reply(f"🔢 Digite o **valor mínimo** em R$ para ser notificado:")
            
        else:
            await event.reply("❌ Opção inválida. Escolha 1, 2 ou 3.")

    elif state == STATE_WAIT_ADD_LIMIT_VALUE:
        try:
            custom_limit = float(text.replace(',', '.').strip())
            keyword = temp_data[user_id]['keyword']
            target_price = temp_data[user_id]['price']
            
            if custom_limit >= target_price:
                await event.reply("⚠️ O limite mínimo deve ser menor que a meta! Tente novamente:")
                return

            database.add_product_subscription(keyword, target_price, user_id, min_price=custom_limit)
            reload_cache()
            await event.reply(f"✅ Monitorando **{keyword}**\n🎯 Meta: R$ {target_price:.2f}\n🛡️ Mínimo: R$ {custom_limit:.2f}")
            cancel_state(user_id)
        except ValueError:
            await event.reply("❌ Valor inválido.")

    elif state == STATE_WAIT_DEL_KEYWORD:
        keyword = text.strip()
        if database.remove_product_subscription(keyword, user_id):
            reload_cache()
            await event.reply(f"🗑️ Removido: **{keyword}**")
        else: await event.reply(f"❌ Não encontrado.")
        cancel_state(user_id)

    elif state == STATE_WAIT_EDIT_KEYWORD:
        keyword = text.strip()
        my_prods = database.list_user_products(user_id)
        
        target_prod = next((p for p in my_prods if p['keyword'] == keyword), None)

        if not target_prod:
            await event.reply("❌ Você não segue esse produto.")
            return
        
        temp_data[user_id] = {
            'keyword': keyword,
            'current_target': target_prod['my_target']
        }
        
        user_states[user_id] = STATE_WAIT_EDIT_CHOOSE_FIELD
        msg = (
            f"📝 Editando **{keyword}**\n"
            f"O que deseja alterar?\n\n"
            f"1️⃣ **Meta de Preço** (Atual: R$ {target_prod['my_target']:.2f})\n"
            f"2️⃣ **Limite Mínimo** (Ignorar preços baixos)\n"
        )
        await event.reply(msg)

    elif state == STATE_WAIT_EDIT_CHOOSE_FIELD:
        if text.strip() == '1':
            user_states[user_id] = STATE_WAIT_EDIT_PRICE
            await event.reply("💰 Digite a **Nova Meta** de preço:")
        
        elif text.strip() == '2':
            user_states[user_id] = STATE_WAIT_EDIT_LIMIT_OPTION
            msg = (
                "🛡️ **Configurar Limite de Preço Baixo**\n\n"
                "1️⃣ **Sem limite** (Notificar tudo)\n"
                "2️⃣ **Padrão** (40% da meta atual)\n"
                "3️⃣ **Definir valor manualmente**"
            )
            await event.reply(msg)
        else:
            await event.reply("❌ Opção inválida. Digite 1 ou 2.")

    elif state == STATE_WAIT_EDIT_PRICE:
        try:
            new_price = float(text.replace(',', '.').strip())
            keyword = temp_data[user_id]['keyword']
            
            if database.update_user_subscription(user_id, keyword, new_target=new_price):
                reload_cache()
                await event.reply(f"✅ Meta de **{keyword}** atualizada para R$ {new_price:.2f}")
            else: 
                await event.reply("❌ Erro ao atualizar.")
            cancel_state(user_id)
        except ValueError: 
            await event.reply("❌ Valor inválido.")

    elif state == STATE_WAIT_EDIT_LIMIT_OPTION:
        choice = text.strip()
        keyword = temp_data[user_id]['keyword']
        current_target = temp_data[user_id]['current_target']
        if choice == '1':
            database.update_user_subscription(user_id, keyword, new_min=0)
            reload_cache()
            await event.reply(f"✅ Limite de **{keyword}** removido (Notificar tudo).")
            cancel_state(user_id)
            
        elif choice == '2':
            limit = current_target * 0.40
            database.update_user_subscription(user_id, keyword, new_min=limit)
            reload_cache()
            await event.reply(f"✅ Limite de **{keyword}** definido para R$ {limit:.2f}.")
            cancel_state(user_id)
            
        elif choice == '3':
            user_states[user_id] = STATE_WAIT_EDIT_LIMIT_VALUE
            await event.reply(f"🔢 Digite o **novo valor mínimo**:")
            
        else:
            await event.reply("❌ Opção inválida.")

    elif state == STATE_WAIT_EDIT_LIMIT_VALUE:
        try:
            custom_limit = float(text.replace(',', '.').strip())
            keyword = temp_data[user_id]['keyword']
            current_target = temp_data[user_id]['current_target']

            if custom_limit >= current_target:
                await event.reply("⚠️ O limite mínimo deve ser menor que a meta de preço!")
                return

            database.update_user_subscription(user_id, keyword, new_min=custom_limit)
            reload_cache()
            await event.reply(f"✅ Limite de **{keyword}** atualizado para R$ {custom_limit:.2f}")
            cancel_state(user_id)
        except ValueError:
            await event.reply("❌ Valor inválido.")

    elif state == STATE_WAIT_EDIT_PRICE:
        try:
            price = float(text.replace(',', '.').strip())
            keyword = temp_data[user_id]['keyword']
            if database.update_user_subscription(user_id, keyword, price):
                reload_cache()
                await event.reply(f"✅ Atualizado: **{keyword}** -> R$ {price:.2f}")
            else: await event.reply("❌ Erro.")
            cancel_state(user_id)
        except ValueError: await event.reply("❌ Valor inválido.")

    elif state == STATE_WAIT_SEARCH_KEYWORD:
        keyword = text.strip()
        my_prods = database.list_user_products(user_id)
        target_prod = next((p for p in my_prods if p['keyword'] == keyword), None)
        
        if not target_prod:
            await event.reply("❌ Produto não encontrado.")
            cancel_state(user_id)
            return

        cancel_state(user_id)
        target_price = target_prod['my_target']
        min_threshold = target_price * 0.40
        MAX_SEARCH_LIMIT = 500
        
        status_msg = await event.reply(f"⏳ Buscando `{keyword}`...\nLimite: {MAX_SEARCH_LIMIT} registros.")
        
        limit_date, allowed_months = get_search_ranges()
        total_processed = 0
        total_price_sum = 0.0
        offers_found_count = 0
        limit_reached = False
        best_offer = None
        
        dialogs = await client.get_dialogs()
        chats = [d for d in dialogs if d.is_channel or d.is_group]

        for chat in chats:
            if total_processed >= MAX_SEARCH_LIMIT:
                limit_reached = True
                break
            try:
                async for message in client.iter_messages(chat, search=keyword, limit=None):
                    if total_processed >= MAX_SEARCH_LIMIT:
                        limit_reached = True
                        break
                    
                    content_to_scan = message.raw_text or message.message or ""
                    if message.media and isinstance(message.media, types.MessageMediaWebPage):
                        wp = message.media.webpage
                        if wp and hasattr(wp, 'title') and wp.title: content_to_scan += f"\n{wp.title}"
                        if wp and hasattr(wp, 'description') and wp.description: content_to_scan += f"\n{wp.description}"

                    if content_to_scan:
                        msg_date_br = message.date.astimezone(BR_TZ)
                        if msg_date_br.replace(tzinfo=None) < limit_date: continue
                        if allowed_months and (msg_date_br.year, msg_date_br.month) not in allowed_months: continue

                        blocks = split_message_blocks(content_to_scan)
                        for block in blocks:
                            if keyword.lower() in block.lower():
                                price, _ = extract_price(block, min_threshold)
                                if price:
                                    database.update_product_stats(keyword, price, msg_date_br, chat.id, message.id)
                                    total_processed += 1
                                    total_price_sum += price
                                    
                                    msg_link = f"https://t.me/c/{chat.id}/{message.id}".replace("-100", "")
                                    if hasattr(chat, 'username') and chat.username:
                                        msg_link = f"https://t.me/{chat.username}/{message.id}"
                                    
                                    if price <= target_price: offers_found_count += 1
                                    
                                    if best_offer is None or price < best_offer['price']:
                                        chat_title = chat.title if chat.title else "Canal"
                                        best_offer = {'price': price, 'date': msg_date_br, 'link': msg_link, 'chat': chat_title}
                                    break
            except: continue
        
        average_price = 0.0
        if total_processed > 0: average_price = total_price_sum / total_processed
        
        limit_text = f"\n⚠️ Limite atingido" if limit_reached else ""
        if best_offer:
            summary = (
                f"🏁 **BUSCA: {keyword.upper()}**\n{limit_text}\n"
                f"📊 Analisados: {total_processed}\n"
                f"⚖️ Média: R$ {average_price:.2f}\n"
                f"📉 Ofertas abaixo da meta: {offers_found_count}\n━━━━━━━━━━━━\n"
                f"🏆 **MELHOR:** R$ {best_offer['price']:.2f}\n"
                f"📅 {best_offer['date'].strftime('%d/%m/%y %H:%M')} | {best_offer['chat']}\n"
                f"🔗 [VER OFERTA]({best_offer['link']})"
            )
        else: summary = f"🏁 **BUSCA: {keyword.upper()}**\n❌ Nenhuma oferta encontrada."
        await status_msg.edit(summary, link_preview=False)

@client.on(events.NewMessage(incoming=True))
async def background_listener(event):
    if event.sender_id in config.USER_IDS: return 
    if not (event.is_channel or event.is_group): return

    msg_text = event.message.raw_text or event.message.message or ""
    
    if event.message.media and isinstance(event.message.media, types.MessageMediaWebPage):
        wp = event.message.media.webpage
        if wp and not isinstance(wp, types.WebPageEmpty):
            if hasattr(wp, 'title') and wp.title: msg_text += f" | WP_TITLE: {wp.title}"
            if hasattr(wp, 'description') and wp.description: msg_text += f" | WP_DESC: {wp.description}"

    if not msg_text: return
    
    msg_date_br = event.message.date.astimezone(BR_TZ)
    chat_name = event.chat.title if event.chat else f"ID:{event.chat_id}"
    matched_any = False

    for product in cached_products:
        keyword = product['keyword']
        subscribers = product.get('subscribers', {})
        if not subscribers: continue

        if keyword.lower() in msg_text.lower():
            matched_any = True
            
            max_target = max(s['target'] for s in subscribers.values())
            logging_threshold = max_target * 0.20 
            
            blocks = split_message_blocks(msg_text)
            price_found_in_msg = False
            
            for block in blocks:
                if keyword.lower() not in block.lower(): continue

                price, raw_match = extract_price(block, min_price_threshold=0)
                
                if price:
                    price_found_in_msg = True

                    if price < logging_threshold:
                        log_analysis(chat_name, block, f"\033[93mPREÇO ABAIXO DO MÍNIMO: R${price:.0f})\033[0m")
                        continue

                    log_analysis(chat_name, block, f"\033[92mOFERTA ENCONTRADA: R$ {price:.0f}\033[0m")
                    
                    database.update_product_stats(keyword, price, msg_date_br, event.chat_id, event.message.id)
                    
                    msg_link = f"https://t.me/c/{event.chat_id}/{event.message.id}".replace("-100", "")
                    if event.chat and hasattr(event.chat, 'username') and event.chat.username:
                        msg_link = f"https://t.me/{event.chat.username}/{event.message.id}"

                    for user_id_str, prefs in subscribers.items():
                        user_target = prefs['target']
                        user_id = int(user_id_str)

                        if price <= user_target:
                            diff = user_target - price
                            response = (
                                f"🚨 **ALERTA!**\n📦 **{keyword.upper()}**\n"
                                f"📉 **R$ {price:.2f}** (Meta: {user_target:.0f})\n"
                                f"🏪 {chat_name}\n🔗 [VER OFERTA]({msg_link})"
                            )
                            try: await client.send_message(user_id, response, link_preview=False)
                            except: pass
                    break 
            
            if not price_found_in_msg:
                log_analysis(chat_name, msg_text, "\033[93mPREÇO NÃO ENCONTRADO\033[0m")

    if not matched_any:
        log_analysis(chat_name, msg_text, "\033[90mIGNORADO\033[0m")
        pass

async def main():
    print("Iniciando Bot...")
    await client.start()
    reload_cache()
    dialogs = await client.get_dialogs()
    count = len([d for d in dialogs if d.is_channel or d.is_group])
    print(f"Monitorando {count} canais.")
    print(f"Usuários ativos: {config.USER_IDS}")
    print("-" * 50)
    await client.run_until_disconnected()

if __name__ == '__main__':
    try: asyncio.run(main())
    except KeyboardInterrupt: print("\nBot Encerrado.")