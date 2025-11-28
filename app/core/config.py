import os

# --- Caminhos de Arquivos ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, 'data', 'db.json')
SESSION_PATH = os.path.join(BASE_DIR, 'data', 'sessao_userbot')

# --- Configurações do BOT ---
# Substitua pelo ID e API_HASH do BOT
API_ID = 12345678
API_HASH = 'SUA_API_HASH_AQUI'
USER_IDS = [
    # Substitua pelos IDs dos usuários autorizados a usar o bot
    1234567890,
    1234567891
]

SESSION_NAME = 'sessao_userbot'
DB_NAME = 'db.json'

# --- Configurações de Limites e Segurança ---
SEARCH_LIMIT = 500 # Quantidade máxima de mensagens para processar na busca
SEARCH_DELAY = 1.5 # Tempo de espera (em segundos) entre canais para evitar FloodWait durante a busca

# --- Configurações de Busca (Regex) ---
# Palavras que indicam que um preço vem a seguir
PRICE_TRIGGERS = [ 'por', 'valor', 'pix', 'vista', 'r\$' ]

# Prefixos que devem ser removidos para não confundir (ex: "em 12x de R$ 100")
IGNORE_PREFIXES = [ 'em', 'de', 'acima de', 'compras de' ]

# Unidades de tempo para remover antes de buscar preço (evita confundir "por 30 dias" com "por R$ 30")
TIME_UNITS = [ 'dias', 'meses', 'anos', 'horas', 'minutos', 'segundos' ]

# --- Configuração dos Logs ---
# 1 = Silencioso
# 2 = Debug (Tudo)
# 3 = Filtrado (Sem 'IGNORADO')
# 4 = Apenas Ofertas
LOG_MODE = 1