from app.core import database, state

async def start(event):
    my_products = database.list_user_products(event.sender_id)
    if not my_products:
        await event.reply("📭 Nada para remover.")
        return
    msg = "🗑️ **Copie para remover:**\n\n"
    for p in my_products: msg += f"• `{p['keyword']}`\n"
    state.user_states[event.sender_id] = state.STATE_WAIT_DEL_KEYWORD
    await event.reply(msg)

async def handle_keyword(event, text):
    keyword = text.strip()
    if database.remove_product_subscription(keyword, event.sender_id):
        state.reload_cache()
        await event.reply(f"🗑️ Removido: **{keyword}**")
    else:
        await event.reply(f"❌ Não encontrado.")
    state.cancel_state(event.sender_id)