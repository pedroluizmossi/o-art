# O-Art 🎨🤖

Bem-vindo ao O-Art, uma API robusta construída com `FastAPI` e projetada para orquestrar a geração de imagens utilizando o `ComfyUI`. Este projeto gerencia usuários, planos, workflows, filas de processamento, armazenamento de imagens e muito mais, atuando como um maestro para a criação de arte digital gerada por IA.

[![Python Quality Check Status](https://github.com/pedroluizmossi1/o-art/actions/workflows/pylint.yml/badge.svg)](https://github.com/pedroluizmossi1/o-art/actions/workflows/pylint.yml) [![Bandit Analysis Status](https://github.com/pedroluizmossi1/o-art/actions/workflows/Bandit.yml/badge.svg)](https://github.com/pedroluizmossi1/o-art/actions/workflows/Bandit.yml) [![Ruff Quality Check Status](https://github.com/pedroluizmossi1/o-art/actions/workflows/ruff.yml/badge.svg)](https://github.com/pedroluizmossi1/o-art/actions/workflows/ruff.yml)

## 🔥 Funcionalidades Principais

* **Geração de Imagens Avançada**: Envie o ID de um workflow do `ComfyUI` e seus parâmetros para gerar imagens personalizadas.
* **Workflows Dinâmicos e Parametrizáveis**:
    * Utiliza `JSON` armazenado no banco de dados como templates para workflows.
    * Permite a inserção dinâmica de valores através de placeholders (ex: `{{nome_do_parametro}}`).
    * Suporte para randomização de parâmetros (ex: `SEED`) com base em `min_value` e `max_value` definidos nos metadados do workflow ou do modelo.
    * Parâmetros de modelos (`MODEL_ID`) são integrados dinamicamente aos workflows.
* **Autenticação e Gerenciamento de Usuários**:
    * Integração com `Fief` para autenticação OAuth2.
    * Webhooks para sincronização de dados de usuários (criação, atualização, exclusão) com verificação de assinatura HMAC-SHA256.
    * Sincronização inicial de usuários do Fief.
* **Status da Fila e Pré-visualização em Tempo Real**:
    * Endpoint WebSocket (`/websocket/queue-status`) para atualizações em tempo real sobre o status da fila de geração do `ComfyUI`.
    * Endpoint WebSocket (`/websocket/preview`) para receber pré-visualizações de imagens durante o processo de geração.
* **Métricas Operacionais**: Envia dados operacionais (ex: status da fila, tamanho da fila de preview) para o `InfluxDB`.
* **Configuração Flexível**: Suporta configuração através de um arquivo `config.ini` e variáveis de ambiente (`.env`).
* **Gerenciamento de Entidades**: CRUD completo para Modelos, Planos e Workflows.
* **Gerenciamento de Pastas de Usuário**: Permite que os usuários organizem suas imagens em pastas.
* **Gerenciamento de Planos**:
    * Suporta diferentes planos de usuário com parâmetros e permissões variados.
    * Associações muitos-para-muitos entre Planos e Modelos (`PlanModel`) e Planos e Workflows (`PlanWorkflow`).
    * Usuários são atribuídos a um plano gratuito (`price: 0`) por padrão na criação.
* **Armazenamento de Imagens**: Utiliza o `MinIO` para armazenar as imagens geradas e imagens de perfil dos usuários.
* **Documentação da API Interativa**: Oferece documentação da API através do `Scalar`.

## 💻 Pilha Tecnológica

* **Backend API**: `FastAPI`
* **Banco de Dados**: `PostgreSQL` (com `SQLModel` como ORM Async)
* **Broker/Cache Celery**: `Redis`
* **Autenticação**: `Fief`
* **Geração de Imagem**: `ComfyUI` (rodando separadamente)
* **Armazenamento de Objetos**: `MinIO`
* **Banco de Dados Time-Series (Métricas)**: `InfluxDB`
* **Containerização**: `Docker` & `Docker Compose`

## 🚦 Endpoints Principais da API

A API é organizada em torno de recursos principais, cada um com seus próprios endpoints. A autenticação (`auth.authenticated()`) é aplicada à maioria dos endpoints que manipulam dados de usuário ou realizam ações sensíveis.

### Autenticação (`/auth`)

* `GET /user`: Retorna informações do token de acesso do usuário autenticado.

### Imagens (`/image`)

* `POST /generate`: Envia um job para gerar uma imagem. Requer autenticação.
    * **Request Body**: `GenerateImageRequest` (contendo `workflow_id`, `folder_id` opcional, e `parameters` para o workflow).
    * **Query Param**: `retrieve_image` (bool, opcional) para retornar a imagem diretamente na resposta.

### Usuários (`/user`)

* `GET /me`: Retorna os detalhes do usuário autenticado (do banco de dados).
* `PUT /me/profileImage`: Atualiza a imagem de perfil do usuário autenticado. Aceita um `UploadFile`.

### Pastas de Usuário (`/user/folder`)

* `GET /`: Lista todas as pastas do usuário (ID do usuário pode ser opcionalmente fornecido, senão usa o do token).
* `GET /{folder_id}`: Retorna uma pasta específica pelo ID.
* `GET /name/{folder_name}`: Retorna uma pasta específica pelo nome.
* `POST /`: Cria uma nova pasta para um usuário específico (requer `folder_name` e `user_id`).
* `DELETE /{folder_id}`: Remove uma pasta (requer `folder_id` e `user_id`).

### Imagens do Usuário (`/user/image`)

* `GET /`: Lista todas as imagens do usuário autenticado.
* `GET /{folder_id}`: Lista todas as imagens do usuário autenticado dentro de uma pasta específica.
* `DELETE /{image_id}`: Remove uma imagem pelo ID para o usuário autenticado.

### Modelos (`/model`)

* `GET /`: Lista todos os modelos disponíveis.
* `GET /{model_id}`: Retorna um modelo específico pelo seu ID.
* `POST /`: Cria um novo modelo (`ModelCreate`).
* `PATCH /{model_id}`: Atualiza um modelo específico (`ModelUpdate`).
* `DELETE /{model_id}`: Deleta um modelo específico.

### Planos (`/plan`)

* `GET /`: Lista todos os planos disponíveis.
* `GET /{plan_id}`: Retorna um plano específico pelo seu ID.
* `POST /`: Cria um novo plano (`PlanCreate`).
* `PATCH /{plan_id}`: Atualiza um plano específico (`PlanUpdate`).
* `DELETE /{plan_id}`: Deleta um plano específico.

### Webhooks (`/webhook`)

* `POST /user`: Endpoint para receber webhooks do `Fief` relacionados a eventos de usuário (criação, atualização, exclusão). Protegido por verificação de assinatura.

### WebSockets (`/websocket`)

* `WS /queue-status`: Conecta via WebSocket para receber o status da fila do `ComfyUI` em tempo real. Requer `access_token` no header para validação.
* `WS /preview`: Conecta via WebSocket para receber pré-visualizações de imagens durante a geração. Requer `access_token` no header para validação.

### Workflows (`/workflow`)

* `GET /`: Lista todos os workflows disponíveis.
* `GET /simplified`: Lista todos os workflows com detalhes simplificados (ID, nome, descrição, tipo de modelo, ID do modelo, data de criação).
* `GET /{workflow_id}`: Retorna um workflow específico pelo seu ID.
* `POST /`: Cria um novo workflow (`WorkflowCreate`).
* `PATCH /{workflow_id}`: Atualiza um workflow existente (`WorkflowUpdate`).
* `DELETE /{workflow_id}`: Remove um workflow pelo ID.

### Documentação (`/docs`)

* `GET /scalar`: Acesso à documentação interativa da API via `Scalar`.

## 🎨 Workflows

* Os workflows do `ComfyUI` são definidos como objetos `JSON` e armazenados no banco de dados. Podem ser semeados a partir de arquivos como `resources/postgres/workflows.json`.
* Placeholders como `{{nome_do_parametro}}` são usados dentro do `JSON` do workflow. A API substitui esses placeholders com os valores fornecidos no campo "parameters" da requisição `/image/generate` ou com valores padrão/randomizados.
* A lógica de preenchimento de placeholders e validação de parâmetros está centralizada em `handler/workflow_handler.py`.
    * Os parâmetros do workflow e do modelo associado (`MODEL_ID`) são processados.
    * Parâmetros podem ser marcados para randomização (`"randomize": true`) e terão valores gerados entre `min_value` e `max_value` se não fornecidos.
    * Parâmetros extras não definidos no workflow ou modelo resultam em erro.
* Os parâmetros de workflow e modelo são definidos usando `ParameterDetail` que especifica nome, tipo, valor padrão, obrigatoriedade, ordem, se é entrada/saída, ID do nó, e opções de randomização.
* Parâmetros de saída (`input_or_output: "OUTPUT"`) são identificados para processar os resultados do workflow.

## 🛠️ Configuração e Inicialização

* **Configuração**:
    * Arquivo `config.ini` para configurações gerais (Redis, Celery, MinIO bucket, ComfyUI server, Fief domain, Logs).
    * Variáveis de ambiente (gerenciadas com `python-dotenv` e definidas em `.env`) para informações sensíveis (Tokens InfluxDB, credenciais Fief, URL PostgreSQL, credenciais MinIO).
* **Inicialização da Aplicação (`main.py`)**:
    * `create_db()`: Criação das tabelas do banco de dados (`PostgreSQL`) usando `SQLModel.metadata.create_all`.
    * `initial_data()`:
        * Semeia modelos, workflows e planos a partir de arquivos JSON (`resources/postgres/`).
        * Sincroniza usuários com o `Fief` (`sync_users_handler`).
    * Limpeza de logs antigos (`cleanup_old_logs`).
    * Inicia subprocessos para `Celery worker` e `Celery beat`.
    * Criação do bucket padrão no `MinIO` (`create_default_bucket`).
    * Configuração de middleware CORS.

## 🏗️ Estrutura do Projeto (Principais Módulos)

* **`api/`**: Contém os módulos que definem os endpoints da API `FastAPI` (roteadores), separados por funcionalidade (ex: `image_api.py`, `user_api.py`, `workflow_api.py`).
* **`core/`**: Módulos centrais do sistema.
    * **`comfy/`**: Lógica de integração com o `ComfyUI`.
        * `__init__.py`: Exporta funcionalidades dos submódulos.
        * `comfy_core.py`: Agregador de funcionalidades (parece ser um ponto de exportação unificado).
        * `config.py`: Configurações específicas do ComfyUI (endereço do servidor, contexto SSL, fila de preview).
        * `connection.py`: Funções para conectar via WebSocket, enfileirar prompts, obter histórico e status da fila.
        * `exceptions.py`: Exceção customizada `ComfyUIError`.
        * `images.py`: Funções para obter imagens geradas e processar saídas de workflows.
        * `preview.py`: Gerenciamento da fila de pré-visualização de imagens (adicionar, obter, limpar, cleanup de previews antigos).
        * `workflow.py`: Execução de workflows e verificação do status da fila para métricas.
    * `celery_core.py`: Configuração da instância do Celery, backend de resultados, e agendamento de tarefas (`beat_schedule` para `check_queue_task` e `preview_queue_cleanup`).
    * `config_core.py`: Carregamento e acesso a configurações do `config.ini`.
    * `db_core.py`: Configuração da engine `asyncpg` para `PostgreSQL` com `SQLModel`, criação de tabelas e gerenciamento de sessões assíncronas.
    * `env_core.py`: Gerenciamento e acesso a variáveis de ambiente.
    * `fief_core.py`: Cliente HTTP (`FiefHttpClient`) para interagir com a API do `Fief` (obter todos os usuários, obter usuário por ID).
    * `logging_core.py`: Configuração do sistema de logging (nível, path, rotação de arquivos) e função para limpar logs antigos.
    * `metric_core.py`: Cliente (`InfluxDBWriter`) para escrita de métricas no `InfluxDB`.
    * `minio_core.py`: Interação com o `MinIO` (criar cliente, criar bucket, listar buckets, upload/download de arquivos e bytes).
* **`handler/`**: Módulos com a lógica de negócio e orquestração das operações solicitadas pelas APIs.
    * `auth_handler.py`: Configuração do cliente `FiefAsync`.
    * `image_handler.py`: Lida com a geração de imagens, incluindo o carregamento e população de workflows, execução no ComfyUI, salvamento da imagem no MinIO e criação do registro no banco de dados.
    * `model_handler.py`: Handlers para operações CRUD de Modelos.
    * `plan_handler.py`: Handlers para operações CRUD de Planos e obtenção de plano por preço.
    * `start_data_handler.py`: Lógica para carregar dados iniciais (modelos, workflows, planos) e sincronizar usuários.
    * `user_folder_handler.py`: Handlers para operações CRUD de Pastas de Usuário.
    * `user_handler.py`: Handlers para obter usuário por ID, atualizar imagem de perfil, criar usuário (incluindo atribuição de plano padrão e pasta padrão), processar webhooks do Fief, listar todos os usuários e sincronizar usuários do Fief.
    * `websocket_handler.py`: Lógica para os updaters de status da fila e preview, e validação de token de acesso para WebSockets.
    * `workflow_handler.py`: Handlers para operações CRUD de Workflows, carregamento e população de workflows com parâmetros (incluindo defaults, randomização e integração de parâmetros de modelo).
* **`model/`**: Define os modelos de dados (`SQLModel`) e enums.
    * **`enum/`**: Contém as enumerações (`FiefTypeWebhook`, `Model` (tipo de modelo), `Sampler`, `WorkflowSegment`, `Workflow` (tipo de workflow)).
    * **`map/`**: Definições para parâmetros.
        * `model_parameter_mapping.py`: Define `ParameterDetail` com atributos como nome, tipo, default, required, order, input/output, node_id, min/max_value, randomize.
        * `segment_parameter_mapping.py`: Mapeamento para permissões de segmentos de workflow em planos.
        * `type_parameter_mapping.py`: Mapeamento para permissões de tipos de workflow em planos.
    * `image_model.py`: Modelo `Image`.
    * `model_model.py`: Modelos `ModelBase`, `Model`, `ModelCreate`, `ModelUpdate`.
    * `plan_model.py`: Modelos `PlanBase`, `PlanParameters`, `Plan`, `PlanCreate`, `PlanUpdate`.
    * `plan_model_model.py`: Tabela associativa `PlanModel`.
    * `plan_workflow_model.py`: Tabela associativa `PlanWorkflow`.
    * `user_folder_model.py`: Modelo `UserFolder`.
    * `user_model.py`: Modelo `User`.
    * `workflow_model.py`: Modelos `WorkflowBase`, `Workflow`, `WorkflowCreate`, `WorkflowUpdate`.
* **`resources/`**: Arquivos de recursos.
    * **`postgres/`**: Arquivos JSON para semear o banco (`models.json`, `plans.json`, `workflows.json`).
    * `openapi_tags_metadata.py`: Metadados para agrupar endpoints na documentação OpenAPI.
* **`service/`**: Camada de serviço que interage diretamente com o banco de dados para operações CRUD e lógicas de dados específicas, usando sessões `AsyncSession`.
* **`tests/`**: Testes unitários para o projeto (ex: `test_celery_core.py`, `test_config_core.py`, `test_workflow_service.py`).
* **`utils/`**: Utilitários gerais.
    * `security_util.py`: Função `safe_urlopen` para chamadas HTTP/HTTPS seguras.
* **`main.py`**: Ponto de entrada da aplicação `FastAPI`.
* **`docker-compose.yaml`**: Define os serviços Docker (db, redis, fief-server, minio, influxdb).
* **`requirements.txt`**: Lista as dependências Python.
* **`config.ini`**: Arquivo de configuração principal.
* **`.github/workflows/`**: Workflows do GitHub Actions para CI (Bandit, Pylint, Ruff).
