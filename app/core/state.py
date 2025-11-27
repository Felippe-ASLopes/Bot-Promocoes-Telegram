from app.core import database

user_states = {}
temp_data = {}
cached_products = []

STATE_WAIT_ADD_NAME = "wait_add_name"
STATE_WAIT_ADD_PRICE = "wait_add_price"
STATE_WAIT_ADD_LIMIT_OPTION = "wait_add_limit_option"
STATE_WAIT_ADD_LIMIT_VALUE = "wait_add_limit_value"
STATE_WAIT_DEL_KEYWORD = "wait_del_keyword"
STATE_WAIT_SEARCH_KEYWORD = "wait_search_keyword"
STATE_WAIT_EDIT_KEYWORD = "wait_edit_keyword"
STATE_WAIT_EDIT_PRICE = "wait_edit_price"
STATE_WAIT_EDIT_CHOOSE_FIELD = "wait_edit_choose_field"
STATE_WAIT_EDIT_LIMIT_OPTION = "wait_edit_limit_option"
STATE_WAIT_EDIT_LIMIT_VALUE = "wait_edit_limit_value"

def reload_cache():
    global cached_products
    cached_products[:] = database.get_all_monitored_products()
    print(f"Cache atualizado: {len(cached_products)} produtos monitorados.")

def cancel_state(user_id):
    if user_id in user_states: del user_states[user_id]
    if user_id in temp_data: del temp_data[user_id]