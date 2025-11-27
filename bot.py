import sys
import asyncio
from app.core import config, state
from app.services import processor
from app.flows import commands
from telethon import TelegramClient, events

sys.stdout.reconfigure(encoding='utf-8')
client = TelegramClient(config.SESSION_PATH, config.API_ID, config.API_HASH)

def parse_log_mode():
    if len(sys.argv) <= 1:
        print("ℹ️ Nenhum modo especificado. Usando padrão Silencioso.")
        return

    arg = sys.argv[1].lower().strip()

    if arg in ['-silent', '-s', '-silencioso']:
        config.LOG_MODE = 1
        print("MODO SILENCIOSO ATIVADO")

    elif arg in ['-debug', '-d']:
        config.LOG_MODE = 2
        print("MODO DEBUG ATIVADO (Todos os logs)")

    elif arg in ['-clean', '-c', '-limpo']:
        config.LOG_MODE = 3
        print("MODO LIMPO ATIVADO (Ocultando 'Ignorados')")

    elif arg in ['-sniper', '-offer', '-ofertas']:
        config.LOG_MODE = 4
        print("MODO SNIPER ATIVADO (Apenas Ofertas)")

    else:
        print(f"Argumento '{arg}' desconhecido. Usando padrão Silencioso.")
        print("Opções: -silent, -debug, -clean, -sniper")

async def main():
    parse_log_mode()
    print("\nIniciando Bot...")
    
    commands.register_handlers(client)
    
    client.add_event_handler(processor.process_message, events.NewMessage(incoming=True))
    
    await client.start()
    
    state.reload_cache()
    
    dialogs = await client.get_dialogs()
    count = len([d for d in dialogs if d.is_channel or d.is_group])
    
    print(f"Monitorando {count} canais.")
    print(f"Usuários ativos: {config.USER_IDS}")
    print("-" * 50)
    
    await client.run_until_disconnected()

if __name__ == '__main__':
    try: asyncio.run(main())
    except KeyboardInterrupt: print("\nBot Encerrado.")