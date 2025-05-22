# O-Art 🎨🤖

Bem-vindo ao O-Art, uma API robusta construída com `FastAPI` e projetada para orquestrar a geração de imagens utilizando o `ComfyUI`. Este projeto gerencia usuários, filas de processamento, armazenamento de imagens e muito mais, atuando como um maestro para a criação de arte digital gerada por IA.

[![Python Quality Check Status](https://github.com/pedroluizmossi1/o-art/actions/workflows/pylint.yml/badge.svg)](https://github.com/pedroluizmossi1/o-art/actions/workflows/pylint.yml) [![Bandit Analysis Status](https://github.com/pedroluizmossi1/o-art/actions/workflows/Bandit.yml/badge.svg)](https://github.com/pedroluizmossi1/o-art/actions/workflows/Bandit.yml) [![Ruff Quality Check Status](https://github.com/pedroluizmossi1/o-art/actions/workflows/ruff.yml/badge.svg)](https://github.com/pedroluizmossi1/o-art/actions/workflows/ruff.yml)

## 🔥 Funcionalidades Principais

* **Geração de Imagens Avançada**: Envie o nome de um workflow do `ComfyUI` e seus parâmetros para gerar imagens personalizadas.
* **Workflows Parametrizáveis**: Utilize arquivos `JSON` como templates para workflows, permitindo a inserção dinâmica de valores através de placeholders.
* **Autenticação e Gerenciamento de Usuários**: Integração com `Fief` para autenticação e gerenciamento de usuários, incluindo webhooks para sincronização de dados de usuários (criação, atualização e exclusão).
* **Status da Fila em Tempo Real**: Um endpoint WebSocket (`/websocket/queue-status`) fornece atualizações em tempo real sobre o status da fila de geração do `ComfyUI`.
* **Pré-visualização em Tempo Real**: Um endpoint WebSocket (`/websocket/preview`) permite receber pré-visualizações das imagens durante o processo de geração.
* **Métricas Operacionais**: Envia dados operacionais, como o status da fila, para o `InfluxDB`, permitindo o monitoramento e análise do sistema.
* **Configuração Flexível**: Suporta configuração através de um arquivo `config.ini` e variáveis de ambiente (`.env`).
* **Gerenciamento de Pastas de Usuário**: Permite que os usuários organizem suas imagens em pastas.
* **Gerenciamento de Planos**: Suporta diferentes planos de usuário com parâmetros e permissões variados.
* **Armazenamento de Imagens**: Utiliza o `MinIO` para armazenar as imagens geradas e imagens de perfil dos usuários.
* **Documentação da API Interativa**: Oferece documentação da API através do `Scalar`.

## 💻 Pilha Tecnológica

* **Backend API**: `FastAPI`
* **Banco de Dados**: `PostgreSQL` (com `SQLModel` como ORM)
* **Cache Celery**: `Redis`
* **Autenticação**: `Fief`
* **Geração de Imagem**: `ComfyUI` (rodando separadamente)
* **Armazenamento de Objetos**: `MinIO`
* **Banco de Dados Time-Series (Métricas)**: `InfluxDB`
* **Containerização**: `Docker` & `Docker Compose`

## 🚦 Endpoints Principais da API

A API é organizada em torno de recursos principais, cada um com seus próprios endpoints. A autenticação é gerenciada centralmente e aplicada aos endpoints que a requerem.

### Autenticação (`/auth`)

* `GET /user`: Retorna informações do usuário autenticado.

### Imagens (`/image`)

* `POST /generate`: Envia um job para gerar uma imagem. Requer autenticação e aceita um ID de workflow, um ID de pasta opcional e parâmetros para o workflow.

### Usuários (`/user`)

* `GET /me`: Retorna os detalhes do usuário autenticado.
* `PUT /me/profileImage`: Atualiza a imagem de perfil do usuário.

### Pastas de Usuário (`/user/folder`)

* `GET /`: Lista todas as pastas de um usuário.
* `GET /{folder_id}`: Retorna uma pasta específica pelo ID.
* `GET /name/{folder_name}`: Retorna uma pasta específica pelo nome.
* `POST /`: Cria uma nova pasta para o usuário.
* `DELETE /{folder_id}`: Remove uma pasta pelo ID.

### Imagens do Usuário (`/user/image`)

* `GET /`: Lista todas as imagens de um usuário.
* `GET /{folder_id}`: Lista todas as imagens de um usuário dentro de uma pasta específica.
* `DELETE /{image_id}`: Remove uma imagem pelo ID.

### Modelos (`/model`)

* `GET /`: Lista todos os modelos disponíveis.
* `GET /{model_id}`: Retorna um modelo específico pelo seu ID.
* `POST /`: Cria um novo modelo.
* `PATCH /{model_id}`: Atualiza um modelo específico pelo seu ID.
* `DELETE /{model_id}`: Deleta um modelo específico pelo seu ID.

### Planos (`/plan`)

* `GET /`: Lista todos os planos disponíveis.
* `GET /{plan_id}`: Retorna um plano específico pelo seu ID.
* `POST /`: Cria um novo plano.
* `PATCH /{plan_id}`: Atualiza um plano específico pelo seu ID.
* `DELETE /{plan_id}`: Deleta um plano específico pelo seu ID.

### Webhooks (`/webhook`)

* `POST /user`: Endpoint para receber webhooks do `Fief` relacionados a eventos de usuário (criação, atualização, exclusão). Este endpoint é protegido por verificação de assinatura.

### WebSockets (`/websocket`)

* `WS /queue-status`: Conecta via WebSocket para receber o status da fila do `ComfyUI` em tempo real. Requer token de acesso no header.
* `WS /preview`: Conecta via WebSocket para receber pré-visualizações de imagens durante a geração. Requer token de acesso no header.

### Workflows (`/workflow`)

* `GET /`: Lista todos os workflows disponíveis.
* `GET /simplified`: Lista todos os workflows disponíveis com detalhes simplificados.
* `GET /{workflow_id}`: Retorna um workflow específico pelo seu ID.
* `POST /`: Cria um novo workflow.
* `PATCH /{workflow_id}`: Atualiza um workflow existente pelo ID.
* `DELETE /{workflow_id}`: Remove um workflow pelo ID.

### Documentação (`/docs`)

* `GET /scalar`: Acesso à documentação interativa da API via `Scalar`.

## 🎨 Workflows

* Os workflows do `ComfyUI` são definidos como arquivos `JSON` e armazenados no banco de dados (exemplo em `resources/postgres/workflows.json`).
* Placeholders como `{{nome_do_parametro}}` podem ser usados dentro do `JSON` do workflow.
* A API substitui esses placeholders com os valores fornecidos no campo "parameters" da requisição `/image/generate`.
* O nó de saída principal (geralmente `SaveImage`) pode ser marcado com `{{output_node_id}}` no campo `_meta.title` para identificação. Se não for especificado, o sistema buscará o primeiro nó `SaveImage`.
* Parâmetros podem ser configurados para randomização, onde valores são gerados dentro de um intervalo `min_value` e `max_value` se não fornecidos explicitamente.

## 🛠️ Configuração e Inicialização

* O projeto utiliza um arquivo `config.ini` para configurações gerais (ex: Redis, ComfyUI, Fief, Logs).
* Variáveis de ambiente (gerenciadas com `python-dotenv` e definidas em um arquivo `.env`) são usadas para informações sensíveis e específicas do ambiente (ex: credenciais de banco de dados, MinIO, InfluxDB, Fief).
* A inicialização da aplicação (`main.py`) realiza as seguintes etapas:
    * Criação das tabelas do banco de dados (`PostgreSQL`).
    * Carregamento de dados iniciais (seed) para modelos, workflows e planos a partir de arquivos JSON.
    * Sincronização de usuários com o `Fief`.
    * Criação do bucket padrão no `MinIO`.
    * Inicialização dos processos `Celery` (worker e beat) para lidar com tarefas assíncronas e agendadas.
    * Limpeza de logs antigos com base na configuração.

## 🏗️ Estrutura do Projeto (Principais Módulos)

* **`api/`**: Contém os módulos que definem os endpoints da API `FastAPI`, separados por funcionalidade (ex: `image_api.py`, `user_api.py`, `workflow_api.py`).
* **`core/`**: Módulos centrais do sistema.
    * **`comfy/`**: Lógica de integração com o `ComfyUI` (conexão, execução de workflows, obtenção de imagens e previews). Inclui `comfy_core.py` (agora um agregador de funcionalidades dos submódulos em `core/comfy/`), `config.py`, `connection.py`, `exceptions.py`, `images.py`, `preview.py`, e `workflow.py`.
    * **`celery_core.py`**: Configuração e tarefas do `Celery`.
    * **`config_core.py`**: Carregamento e acesso a configurações do `config.ini`.
    * **`db_core.py`**: Configuração da conexão com o banco de dados (`PostgreSQL` com `SQLModel`) e criação inicial das tabelas.
    * **`env_core.py`**: Gerenciamento de variáveis de ambiente.
    * **`fief_core.py`**: Cliente HTTP para interagir com a API do `Fief`.
    * **`logging_core.py`**: Configuração do sistema de logging e limpeza de logs antigos.
    * **`metric_core.py`**: Cliente para escrita de métricas no `InfluxDB`.
    * **`minio_core.py`**: Interação com o `MinIO` para armazenamento de arquivos.
* **`handler/`**: Módulos com a lógica de negócio e orquestração das operações solicitadas pelas APIs (ex: `image_handler.py`, `user_handler.py`, `workflow_handler.py`).
* **`model/`**: Define os modelos de dados (`SQLModel`) e enums utilizados no projeto.
    * **`enum/`**: Contém as enumerações (ex: `ModelType`, `WorkflowType`, `FiefTypeWebhook`).
    * **`map/`**: Mapeamentos de parâmetros para modelos, segmentos e tipos de workflow (ex: `model_parameter_mapping.py`).
    * Arquivos como `image_model.py`, `user_model.py`, `workflow_model.py`, `plan_model.py` definem as tabelas do banco de dados.
* **`resources/`**: Arquivos de recursos.
    * **`postgres/`**: Dados `JSON` para popular o banco (workflows, planos, modelos).
    * **`openapi_tags_metadata.py`**: Metadados para a documentação OpenAPI.
* **`service/`**: Camada de serviço que interage diretamente com o banco de dados para realizar operações CRUD e outras lógicas de dados (ex: `image_service.py`, `user_service.py`, `workflow_service.py`).
* **`tests/`**: Contém os testes unitários para as diferentes partes do projeto.
* **`utils/`**: Utilitários gerais, como `security_util.py` para `safe_urlopen`.
* **`main.py`**: Ponto de entrada da aplicação `FastAPI`, configuração do ciclo de vida (lifespan), inclusão dos roteadores da API e middlewares.
* **`docker-compose.yaml`**: Define os serviços para rodar a aplicação e suas dependências (`PostgreSQL`, `Redis`, `Fief`, `MinIO`, `InfluxDB`) em containers `Docker`.
* **`requirements.txt`**: Lista as dependências `Python` do projeto.
* **`config.ini`**: Arquivo de configuração para parâmetros não sensíveis.
* **`.github/workflows/`**: Arquivos de configuração para GitHub Actions (Bandit, Pylint, Ruff).
