import sys
import io
import asyncio
from telethon import TelegramClient, events
from datetime import datetime, timezone, timedelta
import config
import database
from utils import extract_price, split_message_blocks

BR_TZ = timezone(timedelta(hours=-3))

client = TelegramClient(config.SESSION_NAME, config.API_ID, config.API_HASH)

cached_products = database.list_products()

@client.on(events.NewMessage(incoming=True))
async def handler(event):
    if not (event.is_channel or event.is_group):
        return

    msg_text = event.message.text
    if not msg_text:
        return

    msg_date_br = event.message.date.astimezone(BR_TZ)
    
    for product in cached_products:
        keyword = product['keyword']
        target_price = product['target_price']
        min_threshold = target_price * 0.40
        
        if keyword.lower() in msg_text.lower():
            
            blocks = split_message_blocks(msg_text)
            
            for block in blocks:
                if keyword.lower() not in block.lower():
                    continue

                price, raw_match = extract_price(block, min_price_threshold=min_threshold)
                
                if price:
                    chat_name = event.chat.title if event.chat else "Canal Desconhecido"
                    
                    database.update_product_stats(
                        keyword, 
                        price, 
                        msg_date_br, 
                        target_price,
                        event.chat_id,
                        event.message.id
                    )

                    msg_link = f"https://t.me/c/{event.chat_id}/{event.message.id}".replace("-100", "")
                    if event.chat and hasattr(event.chat, 'username') and event.chat.username:
                        msg_link = f"https://t.me/{event.chat.username}/{event.message.id}"

                    if price <= target_price:
                        diff = target_price - price
                        response = (
                            f"🚨 <b>OFERTA DETECTADA!</b> 🚨\n\n"
                            f"📦 <b>Produto:</b> {keyword.upper()}\n"
                            f"📉 <b>Preço:</b> R$ {price:.2f}\n"
                            f"🎯 <b>Sua Meta:</b> R$ {target_price:.2f} (Economia de R$ {diff:.2f}!)\n"
                            f"🏪 <b>Canal:</b> {chat_name}\n"
                            f"📅 <b>Data:</b> {msg_date_br.strftime('%H:%M')}\n\n"
                            f"🔗 <a href='{msg_link}'>IR PARA A OFERTA</a>"
                        )
                        await client.send_message('me', response, parse_mode='html', link_preview=False)
                        print(f"🔥 ALERTA: {keyword} por R$ {price:.2f} em '{chat_name}'")

                    else:
                        response = (
                            f"🔔 <b>Monitoramento:</b> {keyword.title()}\n"
                            f"Preço: R$ {price:.2f} (Acima da meta de {target_price:.2f})\n"
                            f"Canal: {chat_name} \n"
                            f"<a href='{msg_link}'>IR PARA A OFERTA</a>"
                        )
                        await client.send_message('me', response, parse_mode='html', link_preview=False)
                        print(f"👀 Visto: {keyword} por R$ {price:.2f} (Alto)")

                    break 

async def main():
    print("\n" + "="*60)
    print("   🎧 INICIANDO MONITORAMENTO EM TEMPO REAL")
    print("="*60)

    print("🔌 Conectando ao Telegram...")
    await client.start()
    
    dialogs = await client.get_dialogs()
    channels_count = len([d for d in dialogs if d.is_channel or d.is_group])

    print(f"📡 monitorando {channels_count} canais.")
    
    print("-" * 40)
    print(f"📦 Produtos Ativos ({len(cached_products)}):")
    for p in cached_products:
        print(f"   - {p['keyword']} (Meta: R$ {p['target_price']:.2f})")
    print("="*40)
    print("🚀 Aguardando novas ofertas... (Ctrl+C para parar)")

    await client.run_until_disconnected()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Monitoramento encerrado pelo usuário.")