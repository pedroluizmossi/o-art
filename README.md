# Projeto "Art Engine" (Nome Sugerido, Sinta-se Livre Para Mudar!) 🎨🤖

Seja bem-vindo ao cérebro (ou talvez apenas ao sistema nervoso central) por trás de uma operação de arte gerada por IA! Este projeto é uma API robusta construída com FastAPI, projetada para orquestrar a geração de imagens usando o poderoso [ComfyUI](https://github.com/comfyanonymous/ComfyUI), enquanto lida com toda a burocracia chata de usuários, filas e armazenamento.

Pense nisso como o maestro de uma orquestra de macacos pintores digitais, garantindo que eles usem as tintas certas (parâmetros) e entreguem suas... obras-primas... de forma organizada.

## 🔥 Funcionalidades Principais

* **Geração de Imagens Mágicas:** Envie o nome de um workflow do ComfyUI e seus parâmetros, e *voilà* (ou talvez depois de um tempinho na fila), uma imagem aparece!
* **Workflows Parametrizáveis:** Use arquivos JSON (`comfy/workflows`) como templates. Insira valores dinamicamente usando placeholders `{{como_magica}}`.
* **Autenticação e Gerenciamento de Usuários:** Integração com [Fief](https://www.fief.dev/) para lidar com o drama de login, registro e webhooks de usuário (criação, atualização, exclusão). Porque reinventar a roda da autenticação é masoquismo.
* **Processamento Assíncrono de Jobs:** Usa Celery com Redis para enfileirar as solicitações de geração. Ninguém gosta de ficar olhando para um spinner de carregamento eterno.
* **Status da Fila em Tempo Real:** Um endpoint WebSocket (`/websocket/queue-status`) cospe atualizações sobre o quão desesperadoramente longa está a fila de espera.
* **Métricas para os Nerds:** Envia dados operacionais (status da fila, etc.) para o InfluxDB. Para você poder fazer gráficos bonitos e fingir que entende o que está acontecendo.
* **Configuração Flexível:** Lê configurações de um arquivo `config.ini` e variáveis de ambiente (`.env`).

## 💻 Pilha Tecnológica (O Que Faz a Mágica Acontecer)

* **Backend API:** FastAPI
* **Tarefas Assíncronas:** Celery
* **Banco de Dados:** PostgreSQL (com SQLModel como ORM)
* **Broker/Cache Celery:** Redis
* **Autenticação:** Fief
* **Geração de Imagem:** ComfyUI (rodando separadamente)
* **Armazenamento de Objetos (Futuro/Implícito):** MinIO
* **Banco de Dados Time-Series (Métricas):** InfluxDB
* **Containerização:** Docker & Docker Compose

## 🚦 API Endpoints Principais

* `POST /image/generate`: Envia um job para gerar uma imagem. Requer autenticação.
    * **Body (JSON):** `{ "workflow_name": "nome_do_workflow.json", "parameters": { "chave": "valor", ... } }`
* `GET /auth/user`: Retorna informações do usuário autenticado (requer token Bearer).
* `POST /webhook/user`: Endpoint para receber webhooks do Fief (valida assinatura). Não chame diretamente!
* `WS /websocket/queue-status`: Conecta via WebSocket para receber status da fila do ComfyUI.

## 🎨 Workflows

* Os workflows do ComfyUI residem em `comfy/workflows` como arquivos JSON.
* Use placeholders `{{nome_do_parametro}}` dentro do JSON do workflow.
* A API substituirá esses placeholders pelos valores fornecidos no campo `"parameters"` da requisição `/image/generate`.
* Marque seu nó de saída principal (geralmente `SaveImage`) com `{{output_node_id}}` no campo `_meta.title` para fácil identificação (embora haja um fallback para o primeiro `SaveImage`).
