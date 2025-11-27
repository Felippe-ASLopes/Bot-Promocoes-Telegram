import asyncio
import sys
from telethon import TelegramClient
from telethon.errors import FloodWaitError
from datetime import datetime, timezone, timedelta
import config
import database
from utils import get_search_ranges, extract_price, split_message_blocks 

BR_TZ = timezone(timedelta(hours=-3))

async def run_backfill(keyword):
    product_data = database.get_product(keyword)
    if not product_data:
        print(f"❌ Produto '{keyword}' não encontrado no banco. Use manager.py primeiro.")
        return

    target_price = product_data['target_price']
    min_threshold = target_price * 0.40 
    
    print(f"\n🕵️‍♂️ INICIANDO VARREDURA: '{keyword}'")
    print(f"🎯 Meta: R$ {target_price:.2f} | Mínimo Lógico: R$ {min_threshold:.2f}")
    
    limit_date, allowed_months = get_search_ranges()
    print(f"📅 Buscando histórico até: {limit_date.strftime('%d/%m/%Y')}")

    async with TelegramClient(config.SESSION_NAME, config.API_ID, config.API_HASH) as client:
        dialogs = await client.get_dialogs()
        target_chats = [d for d in dialogs if d.is_channel or d.is_group]
        print(f"📡 Monitorando {len(target_chats)} canais.")
        
        total_found = 0
        keyword_lower = keyword.lower()

        for chat in target_chats:
            try:
                async for message in client.iter_messages(chat, search=keyword, limit=None):
                    
                    msg_date_br = message.date.astimezone(BR_TZ)
                    
                    if msg_date_br.replace(tzinfo=None) < limit_date: continue 
                    if allowed_months and (msg_date_br.year, msg_date_br.month) not in allowed_months:
                        continue

                    if message.text:
                        blocks = split_message_blocks(message.text)
                        for block in blocks:
                            if keyword_lower not in block.lower(): continue
                            
                            price, raw_match = extract_price(block, min_price_threshold=min_threshold)
                            
                            if price:
                                database.update_product_stats(
                                    keyword, 
                                    price, 
                                    msg_date_br, 
                                    target_price,
                                    chat.id,
                                    message.id
                                )
                                
                                total_found += 1
                                emoji = "🔥" if price <= target_price else "✅"
                                
                                print("-" * 50)
                                print(f"{emoji} R$ {price:.2f} | {msg_date_br.strftime('%d/%m/%y %H:%M')} | {chat.name}")
                                clean_text = block.replace('\n', ' ')[:100]
                                print(f"   📝 Mensagem: \"{clean_text}...\"")
                                break 

            except FloodWaitError as e:
                print(f"⚠️ FloodWait: {e.seconds}s...")
                await asyncio.sleep(e.seconds)
            except Exception as e:
                print(f"Erro no chat {chat.name}: {e}")

    final_data = database.get_product(keyword)
    stats = final_data['stats']
    
    lowest = stats.get('lowest_price')
    low_date_str = stats.get('lowest_price_date')
    below_count = stats.get('below_target_count', 0)

    low_date_display = "N/A"
    if low_date_str:
        try:
            dt = datetime.fromisoformat(low_date_str)
            low_date_display = dt.strftime('%d/%m/%Y às %H:%M')
        except:
            low_date_display = low_date_str

    low_price_display = f"R$ {lowest:.2f}" if lowest else "N/A"

    print("\n" + "="*50)
    print(f"🏁 Varredura Finalizada para: {keyword}")
    print(f"📊 Registros encontrados: {total_found}")
    print(f"🏆 Menor Preço: {low_price_display} (em {low_date_display})")
    print(f"📉 Ofertas Abaixo da Meta: {below_count}")
    print("="*50)

def main_menu():
    while True:
        items = database.list_products()
        if not items:
            print("❌ Nenhum produto cadastrado. Use o manager.py primeiro.")
            return

        print("\n" + "="*30)
        print("   🕵️‍♂️ MENU DE VARREDURA")
        print("="*30)
        print("Selecione o produto para buscar histórico:")
        
        for i, item in enumerate(items):
            print(f"{i+1}. {item['keyword']}")
        
        print("0. Sair")
        
        try:
            choice = int(input("\nDigite o número: "))
            if choice == 0:
                break
            
            if 1 <= choice <= len(items):
                selected_keyword = items[choice-1]['keyword']
                asyncio.run(run_backfill(selected_keyword))
                input("\nPressione ENTER para voltar ao menu...")
            else:
                print("❌ Opção inválida.")
        except ValueError:
            print("❌ Digite um número válido.")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        asyncio.run(run_backfill(sys.argv[1]))
    else:
        main_menu()