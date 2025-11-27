from database import add_product, list_products, update_product_data
from datetime import datetime

def format_currency(value):
    return f"R$ {value:.2f}" if value is not None else "N/A"

def format_date(date_str):
    if not date_str: return "N/A"
    try:
        dt = datetime.fromisoformat(date_str)
        return dt.strftime('%d/%m/%Y às %H:%M')
    except ValueError: return date_str 

def menu():
    while True:
        print("\n" + "="*30)
        print("   🤖 GERENCIADOR DE BOT   ")
        print("="*30)
        print("1. ➕ Cadastrar Novo Produto")
        print("2. ✏️  Editar Produto (Nome/Preço)")
        print("3. 📋 Listar Estatísticas")
        print("4. 🚪 Sair")
        
        choice = input("\nEscolha uma opção: ")

        if choice == '1':
            keyword = input("Digite o NOME do produto: ").strip()
            if not keyword: continue
            try:
                price = float(input("Digite o preço META: ").replace(',', '.'))
                add_product(keyword, price)
            except ValueError: print("❌ Preço inválido.")

        elif choice == '2':
            items = list_products()
            if not items:
                print("⚠️ Nenhum produto cadastrado.")
                continue

            print("\nSelecione o produto para editar:")
            for i, item in enumerate(items):
                print(f"{i+1}. {item['keyword']} (Meta: {format_currency(item['target_price'])})")
            
            try:
                idx = int(input("\nNúmero do produto (0 para cancelar): ")) - 1
                if idx == -1: continue
                if 0 <= idx < len(items):
                    selected = items[idx]
                    print(f"\nEditando: {selected['keyword']}")
                    print("1. Alterar Nome")
                    print("2. Alterar Preço Meta")
                    
                    sub_choice = input("Opção: ")
                    
                    if sub_choice == '1':
                        new_name = input("Novo nome: ").strip()
                        if new_name:
                            update_product_data(selected['keyword'], new_keyword=new_name)
                    
                    elif sub_choice == '2':
                        try:
                            new_price = float(input("Novo preço meta: ").replace(',', '.'))
                            update_product_data(selected['keyword'], new_price=new_price)
                        except ValueError: print("❌ Valor inválido.")
                else:
                    print("❌ Produto inválido.")
            except ValueError:
                print("❌ Entrada inválida.")

        elif choice == '3':
            items = list_products()
            print(f"\n📊 Monitorando {len(items)} produtos:\n")
            for item in items:
                stats = item.get('stats', {})
                target = item.get('target_price')
                lowest = stats.get('lowest_price')
                average = stats.get('average_price')
                low_date = stats.get('lowest_price_date')
                total = stats.get('total_mentions', 0)
                below_count = stats.get('below_target_count', 0)

                print(f"📦 {item['keyword'].upper()}")
                print(f"   🎯 Meta: {format_currency(target)} | 🔥 Oportunidades: {below_count}")
                print(f"   📉 Menor: {format_currency(lowest)} ({format_date(low_date)})")
                print(f"   👁️  Total: {total} registros")
                print("-" * 30)
        
        elif choice == '4': break
        else: print("Opção inválida.")

if __name__ == "__main__":
    menu()