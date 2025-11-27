from app.core import state

def parse_float(text):
    return float(text.replace(',', '.').strip())

async def send_limit_menu(event):
    msg = (
        "🛡️ **Configurar Limite de Preço Mínimo**\n"
        "Ajuda a ignorar acessórios ou alarmes falsos.\n\n"
        "1️⃣ **Sem limite** (Notificar qualquer valor)\n"
        "2️⃣ **Padrão** (40% da meta - Recomendado)\n"
        "3️⃣ **Definir manualmente**\n\n"
        "Digite o número da opção (1, 2 ou 3):"
    )
    await event.reply(msg)

def resolve_limit_choice(choice, target_price):
    if choice == '1':
        return 0.0, False 
    elif choice == '2':
        return target_price * 0.40, False
    elif choice == '3':
        return None, True 
    return None, None