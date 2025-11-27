from app.core import database, state
from app.flows import common

async def start(event):
    my_products = database.list_user_products(event.sender_id)
    if not my_products:
        await event.reply("📭 Nada para editar.")
        return
    msg = "✏️ **Copie para editar:**\n\n"
    for p in my_products: msg += f"• `{p['keyword']}` (R$ {p['my_target']:.2f})\n"
    state.user_states[event.sender_id] = state.STATE_WAIT_EDIT_KEYWORD
    await event.reply(msg)

async def handle_keyword(event, text):
    keyword = text.strip()
    my_prods = database.list_user_products(event.sender_id)
    target_prod = next((p for p in my_prods if p['keyword'] == keyword), None)
    
    if not target_prod:
        await event.reply("❌ Você não segue esse produto.")
        return
    
    state.temp_data[event.sender_id] = {
        'keyword': keyword,
        'current_target': target_prod['my_target']
    }
    state.user_states[event.sender_id] = state.STATE_WAIT_EDIT_CHOOSE_FIELD
    msg = (
        f"📝 Editando **{keyword}**\n"
        f"O que deseja alterar?\n\n"
        f"1️⃣ **Meta de Preço** (Atual: R$ {target_prod['my_target']:.2f})\n"
        f"2️⃣ **Limite Mínimo**\n"
    )
    await event.reply(msg)

async def handle_field_choice(event, text):
    choice = text.strip()
    if choice == '1':
        state.user_states[event.sender_id] = state.STATE_WAIT_EDIT_PRICE
        await event.reply("💰 Digite a **Nova Meta** de preço:")
    elif choice == '2':
        state.user_states[event.sender_id] = state.STATE_WAIT_EDIT_LIMIT_OPTION
        await common.send_limit_menu(event)
    else:
        await event.reply("❌ Opção inválida. Digite 1 ou 2.")

async def handle_new_price(event, text):
    try:
        new_price = common.parse_float(text)
        keyword = state.temp_data[event.sender_id]['keyword']
        if database.update_user_subscription(event.sender_id, keyword, new_target=new_price):
            state.reload_cache()
            await event.reply(f"✅ Meta de **{keyword}** atualizada para R$ {new_price:.2f}")
        else:
            await event.reply("❌ Erro ao atualizar.")
        state.cancel_state(event.sender_id)
    except ValueError:
        await event.reply("❌ Valor inválido.")

async def handle_limit_option(event, text):
    user_id = event.sender_id
    choice = text.strip()
    keyword = state.temp_data[user_id]['keyword']
    current_target = state.temp_data[user_id]['current_target']

    limit_val, is_manual = common.resolve_limit_choice(choice, current_target)

    if is_manual:
        state.user_states[user_id] = state.STATE_WAIT_EDIT_LIMIT_VALUE
        await event.reply(f"🔢 Digite o **novo valor mínimo**:")
        return

    if limit_val is not None:
        database.update_user_subscription(user_id, keyword, new_min=limit_val)
        state.reload_cache()
        await event.reply(f"✅ Limite de **{keyword}** atualizado para R$ {limit_val:.2f}.")
        state.cancel_state(user_id)
    else:
        await event.reply("❌ Opção inválida.")

async def handle_limit_value(event, text):
    try:
        custom_limit = common.parse_float(text)
        keyword = state.temp_data[event.sender_id]['keyword']
        current_target = state.temp_data[event.sender_id]['current_target']

        if custom_limit >= current_target:
            await event.reply("⚠️ O limite mínimo deve ser menor que a meta!")
            return

        database.update_user_subscription(event.sender_id, keyword, new_min=custom_limit)
        state.reload_cache()
        await event.reply(f"✅ Limite de **{keyword}** atualizado para R$ {custom_limit:.2f}")
        state.cancel_state(event.sender_id)
    except ValueError:
        await event.reply("❌ Valor inválido.")