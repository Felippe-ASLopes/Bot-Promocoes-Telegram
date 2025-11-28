# 🤖 Bot de Monitoramento de Promoções - Telegram

Este projeto é um **Userbot** para Telegram desenvolvido em Python. Ele monitora automaticamente canais e grupos em tempo real, buscando por produtos específicos definidos pelo usuário. Quando uma oferta que atende aos critérios de preço (meta e limite mínimo) é encontrada, o bot envia um alerta privado imediato.

---

## 🚀 Funcionalidades

- **Monitoramento em Tempo Real:** Escaneia mensagens de todos os grupos/canais onde o usuário está.
- **Extração Inteligente de Preços:** Utiliza Regex avançado para identificar preços em diferentes formatos, ignorando parcelas ou datas.
- **Critérios de Alerta:**
  - **Meta de Preço:** Valor máximo que você deseja pagar.
  - **Limite Mínimo:** Valor mínimo para ignorar acessórios ou alarmes falsos (ex: ignorar capa de iPhone quando se busca o aparelho).
- **Busca Histórica (`/buscar`):** Pesquisa em mensagens passadas dos canais para encontrar menor preço histórico, média de valor e ofertas anteriores .
- **Gestão via Chat:** Comandos simples (`/adicionar`, `/editar`, `/listar`) enviados diretamente no "Mensagens Salvas" ou chat privado.
- **Modos de Log (CLI):** Diferentes níveis de verbosidade no terminal (Silent, Debug, Sniper).

---

## 🛠️ Arquitetura e Tecnologias

O projeto desenvolvido em uma arquitetura modular, separando a lógica de negócio, fluxo de usuário e configuração.

### Tecnologias
- **Linguagem:** Python 3.8+
- **Core:** [Telethon](https://docs.telethon.dev/) (Biblioteca assíncrona para API do Telegram)
- **Banco de Dados:** [TinyDB](https://tinydb.readthedocs.io/) (NoSQL leve baseado em JSON)
- **Utilitários:** [python-dateutil](https://fluency.io/br/blog/dateutil-python-como-utilizar-a-biblioteca-dateutil-para-manipulacao-de-datas-em-python/?utm_source=google&utm_medium=organic&utm_content=home&utm_term=blog-dateutil-python-como-utilizar-a-biblioteca-dateutil-para-manipulacao-de-datas-em-python&utm_campaign=FLA%7CE1-PPL%7CESPERA%7CT2-BASE%7CBR%7CSITE%7CCONV%7C2025-11-27) para manipulação de datas.

### Estrutura de Pastas
```text
Bot-Promocoes-Telegram/
├── app/
│   ├── core/       # Configurações, Estado Global e Banco de Dados
│   ├── flows/      # Lógica de interação com o usuário (/comandos)
│   └── services/   # Lógica pesada (Processamento, Extração, Logs)
├── data/           # (Gerado auto) Armazena db.json e sessão
└── bot.py          # Ponto de entrada da aplicação
```

## 📋 Pré-requisitos

1. **Python 3.8** ou superior instalado
2. **Credenciais do Telegram**
3. **Dois números cadastrados no Telegram** (opcional, mas altamente recomendado, pois o fluxo de conversa e notificação do BOT funcionará melhor se feito por um número secundário)

---

## 🚀 Como executar

### 🔑 Passo 1: Obtendo as Credenciais (API ID e Hash)

O Telegram exige essas credenciais para qualquer aplicação que se conecte à API, inclusive Userbots. O processo é gratuito.

1. Acesse **[my.telegram.org](https://my.telegram.org)**.
2. Faça login com o número de telefone (incluindo código do país) que será usado pelo bot.
3. Insira o código de confirmação que chegará no seu app do Telegram.
4. Clique na opção **"API Development tools"**.
5. Preencha o formulário.

⚠️ **Importante:** O formulário costuma exibir uma mensagem de ERRO genérica com status ``200``. Para evitar isso, sigas estas dicas:

* **App title:** `MonitorSys_HASH` (Aparentemente esse campo deve ser único, então substitua ``HASH`` por uma sequencia de números aleatórios, não inclua espaços nem a  palavra ``Telegram``).
* **Short name:** `monitor_HASH` (Siga as regras do campo acima).
* **URL:** `http://localhost` (costuma dar erro se deixar vazio).
* **Platform:** `Desktop`.
* **Description:** `Personal project for automation`.

> ⚠️ Se o erro persistir tente desativar o ADBlock ou VPN

Após criar a aplicação com sucesso, copie os valores de **api_id** e **api_hash**.

### 🆔 Passo 2: Obtendo seu ID de Usuário

Esse passo é opcional mas é **altamente recomendado** se você deseja receber notificações corretamente. Para garantir que você possa receber e enviar mensagens ao bot, precisamos do ID de uma conta Telegram diferente do BOT (repita esse processo com os números que você deseja permitir acesso ao BOT, deixar a lista vazia não garante que todos tenham acesso).

1. Abra o Telegram e procure pelo bot **[@userinfobot](https://t.me/userinfobot)**.
2. Envie `/start`.
3. Ele responderá com um bloco de informações. Copie o campo **Id** 

### 🔐 Passo 3: Configurando as Credenciais

Edite o arquivo ``app/core/config.py``:

``` Python
API_ID = 12345678 # Substitua pelo API_ID do BOT, capturado no passo 1
API_HASH = 'SUA_API_HASH_AQUI' # Substitua pelo API_HASH do BOT, capturado no passo 1, mantenha entre aspas simples
USER_IDS = [
    # Substitua pelos IDs dos usuários autorizados a usar o bot, capturados no passo 1.2
    1234567890,
    1234567891
]
```

### 🤖 Passo 4: Instalando as dependências e executando

Abra o ``Powershell`` na pasta raiz do projeto e execute:

``` bash
pip install telethon tinydb python-dateutil
```

Após isso execute o bot usando um dos modos de execução a seguir.

> ⚠️ Durante a primeira execução o terminal irá solicitar o número do BOT  (código do país sem '+', DDD, número sem '-'), após isso você deve enviar o código de confirmação que será enviado ao seu Telegram

## ⚙️ Modos de execução
Você pode controlar o nível de detalhe dos logs exibido no terminal ao iniciar o bot:

**Padrão Silencioso:** O bot roda sem exibir nenhum log no terminal
``` bash
python bot.py -silent
```

**Debug:** Mostra todos os logs (ofertas encontradas, mensagens ignoradas por preço baixo, erros, etc.)
``` bash
python bot.py -debug
```

**Modo Limpo:** Mostra ofertas e erros, mas esconde o fluxo contínuo de mensagens ignoradas
``` bash
python bot.py -clean
```

**Modo Sniper:** O terminal permanece vazio e só exibe mensagens quando uma oferta é encontrada
``` bash
python bot.py -sniper
```

> 📡 Assim que iniciado, o Bot monitorará automaticamente **todos** os canais e grupos em for membro. Para adicionar novas fontes de monitoramento, basta compartilhar o link do convite e entrar no canal desejado através do Telegram do bot.

> ⚠️ **Segurança e FloodWait:** O arquivo ``config.py`` possui variáveis de segurança para evitar restrições da API. Se estiver enfrentando problemas com FloodWait, experimente abaixar o valor de SEARCH_LIMIT e aumentar o SEARCH_DELAY, além disso diminua a quantidade de canais monitorados e usuários ativos.

--- 

## 💬 Comandos do Bot

Envie estes comandos para o contato do seu BOT, ou (não recomendado) para o chat "Mensagens Salvas" do próprio BOT.

| Comando | Função |
| :--- | :--- |
| `/adicionar` | Inicia o fluxo interativo para cadastrar um novo produto, definindo meta de preço e limite mínimo. |
| `/listar` | Exibe a lista de todos os produtos que você está monitorando, com estatísticas de preço (menor valor histórico e média). |
| `/editar` | Permite alterar a meta de preço ou o limite mínimo de um produto já cadastrado. |
| `/remover` | Remove um produto da lista de monitoramento. |
| `/buscar` | Realiza uma varredura no histórico de mensagens dos canais buscando ofertas passadas. |
| `/cancelar` | Interrompe qualquer operação atual (como adicionar ou editar). |
| `/help` | Exibe o menu de ajuda com a lista de comandos. |

## 📜 Licença e Uso

Este projeto é público e de código aberto (**Open Source**).

Sinta-se totalmente à vontade para:
- **Usar** o código como base para seus próprios projetos (pessoais ou comerciais).
- **Modificar**, refatorar e adaptar conforme suas necessidades.
- **Distribuir** cópias ou versões modificadas.

Não é necessário pedir permissão prévia. Se este projeto for útil para você, uma menção ou uma ⭐ estrela no repositório será muito bem-vinda!