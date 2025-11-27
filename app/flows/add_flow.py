from app.core import database, state
from app.flows import common

async def start(event):
    state.user_states[event.sender_id] = state.STATE_WAIT_ADD_NAME
    await event.reply("🆕 Nome do produto:")

async def handle_name(event, text):
    state.temp_data[event.sender_id] = {'keyword': text.strip()}
    state.user_states[event.sender_id] = state.STATE_WAIT_ADD_PRICE
    await event.reply(f"📝 **{text}**\nQual a **Meta de Preço**?")

async def handle_price(event, text):
    try:
        price = common.parse_float(text)
        state.temp_data[event.sender_id]['price'] = price
        state.user_states[event.sender_id] = state.STATE_WAIT_ADD_LIMIT_OPTION
        await event.reply(f"💰 Meta definida: **R$ {price:.2f}**")
        await common.send_limit_menu(event)
    except ValueError:
        await event.reply("❌ Valor inválido. Digite apenas números.")

async def handle_limit_option(event, text):
    user_id = event.sender_id
    choice = text.strip()
    keyword = state.temp_data[user_id]['keyword']
    target_price = state.temp_data[user_id]['price']

    limit_val, is_manual = common.resolve_limit_choice(choice, target_price)

    if is_manual:
        state.user_states[user_id] = state.STATE_WAIT_ADD_LIMIT_VALUE
        await event.reply(f"🔢 Digite o **valor mínimo** em R$:")
        return

    if limit_val is not None:
        database.add_product_subscription(keyword, target_price, user_id, min_price=limit_val)
        state.reload_cache()
        await event.reply(f"✅ Monitorando **{keyword}**\n🎯 Meta: R$ {target_price:.2f}\n🛡️ Mínimo: R$ {limit_val:.2f}")
        state.cancel_state(user_id)
    else:
        await event.reply("❌ Opção inválida. Escolha 1, 2 ou 3.")

async def handle_limit_value(event, text):
    try:
        user_id = event.sender_id
        custom_limit = common.parse_float(text)
        keyword = state.temp_data[user_id]['keyword']
        target_price = state.temp_data[user_id]['price']

        if custom_limit >= target_price:
            await event.reply("⚠️ O limite mínimo deve ser menor que a meta!")
            return

        database.add_product_subscription(keyword, target_price, user_id, min_price=custom_limit)
        state.reload_cache()
        await event.reply(f"✅ Monitorando **{keyword}**\n🎯 Meta: R$ {target_price:.2f}\n🛡️ Mínimo: R$ {custom_limit:.2f}")
        state.cancel_state(user_id)
    except ValueError:
        await event.reply("❌ Valor inválido.")