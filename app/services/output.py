from datetime import datetime
from app.core import config

def logger(channel, text, status_type, price=None):
    mode = config.LOG_MODE

    if mode == 1:
        return

    if mode == 3 and status_type == 'ignored':
        return

    if mode == 4 and status_type != 'offer':
        return

    clean_text = text.replace('\n', ' ')[:40]
    time_now = datetime.now().strftime('%H:%M:%S')

    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    GRAY = "\033[90m"
    RESET = "\033[0m"

    if status_type == 'offer':
        status_msg = f"{GREEN}OFERTA ENCONTRADA: R$ {price:.0f}{RESET}"
    elif status_type == 'ignored':
        if price:
            status_msg = f"{YELLOW}ABAIXO DO MÍNIMO: R${price:.0f}{RESET}"
        else:
            status_msg = f"{GRAY}IGNORADO{RESET}"
    elif status_type == 'no_price':
        status_msg = f"{YELLOW}PREÇO NÃO ENCONTRADO{RESET}"
    else:
        status_msg = f"{GRAY}STATUS: {status_type}{RESET}"

    print(f"[{time_now}] [{channel[:20]:<20}] {status_msg:<35} | Msg: \"{clean_text}...\"")

async def notify_users(client, users, keyword, price, msg_link, chat_name):
    for user_id_str, prefs in users.items():
        user_target = prefs['target']
        user_min = prefs.get('min_price', 0)
        user_id = int(user_id_str)

        if price <= user_target and price >= user_min:
            response = (
                f"🚨 **ALERTA DE OFERTA!**\n\n"
                f"📦 Produto: **{keyword.upper()}**\n"
                f"💰 Valor: **R$ {price:.2f}** (Meta: {user_target:.0f})\n"
                f"🏪 Canal: {chat_name}\n"
                f"🔗 Link: [VER OFERTA]({msg_link})"
            )
            try:
                await client.send_message(user_id, response, link_preview=False)
            except Exception as e:
                print(f"Erro ao enviar notificação para {user_id}: {e}")