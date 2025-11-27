from telethon import events
from app.core import database, config, state
from app.flows import add_flow, edit_flow, remove_flow, search_flow

async def show_menu(event):
    state.cancel_state(event.sender_id)
    msg = "🤖 **MENU**\n\n🆕 /adicionar\n✏️ /editar\n🗑️ /remover\n📋 /listar\n🕵️‍♂️ /buscar\n❌ /cancelar"
    await event.reply(msg)

async def cmd_list(event):
    state.cancel_state(event.sender_id)
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
        limit_fmt = f"R$ {limit_val:.2f}" if limit_val > 0 else "Sem limite"
        msg += (
            f"📦 **{p['keyword']}**\n"
            f"🎯 Meta: R$ {p['my_target']:.2f}\n"
            f"🛡️ Limite: {limit_fmt}\n"
            f"📉 Menor Preço Histórico: {low_fmt}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
        )
    await event.reply(msg)

async def cmd_cancel(event):
    state.cancel_state(event.sender_id)
    await event.reply("✅ Cancelado.")

async def dialogue_manager(event):
    text = event.text
    user_id = event.sender_id
    if text.startswith('/') or user_id not in state.user_states: return
    
    current_state = state.user_states[user_id]
    
    if current_state == state.STATE_WAIT_ADD_NAME:
        await add_flow.handle_name(event, text)
    elif current_state == state.STATE_WAIT_ADD_PRICE:
        await add_flow.handle_price(event, text)
    elif current_state == state.STATE_WAIT_ADD_LIMIT_OPTION:
        await add_flow.handle_limit_option(event, text)
    elif current_state == state.STATE_WAIT_ADD_LIMIT_VALUE:
        await add_flow.handle_limit_value(event, text)

    elif current_state == state.STATE_WAIT_DEL_KEYWORD:
        await remove_flow.handle_keyword(event, text)

    elif current_state == state.STATE_WAIT_SEARCH_KEYWORD:
        await search_flow.handle_keyword(event, text)

    elif current_state == state.STATE_WAIT_EDIT_KEYWORD:
        await edit_flow.handle_keyword(event, text)
    elif current_state == state.STATE_WAIT_EDIT_CHOOSE_FIELD:
        await edit_flow.handle_field_choice(event, text)
    elif current_state == state.STATE_WAIT_EDIT_PRICE:
        await edit_flow.handle_new_price(event, text)
    elif current_state == state.STATE_WAIT_EDIT_LIMIT_OPTION:
        await edit_flow.handle_limit_option(event, text)
    elif current_state == state.STATE_WAIT_EDIT_LIMIT_VALUE:
        await edit_flow.handle_limit_value(event, text)

def register_handlers(client):
    client.add_event_handler(show_menu, events.NewMessage(from_users=config.USER_IDS, pattern=r'^/(start|help|menu)'))
    client.add_event_handler(cmd_list, events.NewMessage(from_users=config.USER_IDS, pattern=r'^/listar'))
    client.add_event_handler(cmd_cancel, events.NewMessage(from_users=config.USER_IDS, pattern=r'^/cancelar'))
    
    client.add_event_handler(add_flow.start, events.NewMessage(from_users=config.USER_IDS, pattern=r'^/adicionar'))
    client.add_event_handler(remove_flow.start, events.NewMessage(from_users=config.USER_IDS, pattern=r'^/remover'))
    client.add_event_handler(edit_flow.start, events.NewMessage(from_users=config.USER_IDS, pattern=r'^/editar'))
    client.add_event_handler(search_flow.start, events.NewMessage(from_users=config.USER_IDS, pattern=r'^/buscar'))
    
    client.add_event_handler(dialogue_manager, events.NewMessage(from_users=config.USER_IDS))