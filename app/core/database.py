from tinydb import TinyDB, Query
from datetime import datetime
from app.core import config

db = TinyDB(config.DB_PATH)
products_table = db.table('produtos')

def add_product_subscription(keyword, target_price, user_id, min_price=0):
    Product = Query()
    existing = products_table.search(Product.keyword == keyword)
    user_id_str = str(user_id)

    subscription_data = {
        'target': target_price,
        'min_price': min_price
    }

    if existing:
        item = existing[0]
        subscribers = item.get('subscribers', {})
        
        subscribers[user_id_str] = subscription_data
        
        products_table.update({'subscribers': subscribers}, Product.keyword == keyword)
        print(f"✅ Usuário {user_id} inscrito em '{keyword}' com meta {target_price} e min {min_price}")
    else:
        initial_stats = {
            'lowest_price': None,
            'lowest_price_date': None,
            'last_price': None,
            'average_price': 0,
            'total_mentions': 0,
            'processed_ids': []
        }
        
        item = {
            'keyword': keyword,
            'created_at': datetime.now().isoformat(),
            'subscribers': {
                user_id_str: subscription_data
            },
            'stats': initial_stats
        }
        products_table.insert(item)
        print(f"✅ Produto '{keyword}' criado e usuário {user_id} inscrito (min: {min_price}).")

def remove_product_subscription(keyword, user_id):
    Product = Query()
    result = products_table.search(Product.keyword == keyword)
    
    if not result:
        return False

    item = result[0]
    subscribers = item.get('subscribers', {})
    user_id_str = str(user_id)

    if user_id_str in subscribers:
        del subscribers[user_id_str]
        
        if not subscribers:
            products_table.remove(Product.keyword == keyword)
            print(f"🗑️ Produto '{keyword}' removido (sem assinantes).")
        else:
            products_table.update({'subscribers': subscribers}, Product.keyword == keyword)
            print(f"❌ Assinatura de {user_id} removida de '{keyword}'.")
        return True
    
    return False

def list_user_products(user_id):
    all_products = products_table.all()
    user_products = []
    user_id_str = str(user_id)

    for p in all_products:
        subs = p.get('subscribers', {})
        if user_id_str in subs:
            user_view = p.copy()
            user_view['my_target'] = subs[user_id_str]['target']
            user_view['my_limit'] = subs[user_id_str].get('min_price', 0)
            user_products.append(user_view)
            
    return user_products

def get_all_monitored_products():
    return products_table.all()

def update_user_subscription(user_id, keyword, new_target=None, new_min=None):
    Product = Query()
    result = products_table.search(Product.keyword == keyword)
    
    if not result: return False
    
    item = result[0]
    subscribers = item.get('subscribers', {})
    user_id_str = str(user_id)
    
    if user_id_str in subscribers:
        if new_target is not None:
            subscribers[user_id_str]['target'] = new_target
            print(f"✅ Meta de {user_id} para '{keyword}' atualizada para {new_target}")

        if new_min is not None:
            subscribers[user_id_str]['min_price'] = new_min
            print(f"✅ Limite Mínimo de {user_id} para '{keyword}' atualizado para {new_min}")

        products_table.update({'subscribers': subscribers}, Product.keyword == keyword)
        return True
    
    return False

def update_product_stats(keyword, price, date_obj, chat_id, message_id):
    Product = Query()
    item = products_table.search(Product.keyword == keyword)
    if not item: return

    stats = item[0]['stats']
    date_str = date_obj.isoformat()

    if 'processed_ids' not in stats: stats['processed_ids'] = []
    unique_id = f"{chat_id}_{message_id}"
    if unique_id in stats['processed_ids']: return 
    stats['processed_ids'].append(unique_id)

    stats['total_mentions'] += 1
    
    current_lowest = stats['lowest_price']
    
    if current_lowest is None or price < current_lowest:
        stats['lowest_price'] = price
        stats['lowest_price_date'] = date_str
    elif price == current_lowest:
        try:
            saved_date = datetime.fromisoformat(stats['lowest_price_date'])
            if date_obj < saved_date:
                stats['lowest_price_date'] = date_str
        except: pass

    current_avg = stats['average_price']
    count = stats['total_mentions']
    if count == 1: new_avg = price
    else: new_avg = ((current_avg * (count - 1)) + price) / count
        
    stats['average_price'] = round(new_avg, 2)
    stats['last_price'] = price

    products_table.update({'stats': stats}, Product.keyword == keyword)