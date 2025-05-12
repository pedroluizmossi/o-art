# O-Art 🎨🤖

Bem-vindo ao O-Art, uma API robusta construída com `FastAPI`, projetada para orquestrar a geração de imagens usando o poderoso `ComfyUI`. Este projeto gerencia usuários, filas, armazenamento e muito mais, atuando como o maestro de uma orquestra de arte digital gerada por IA.

## 🔥 Funcionalidades Principais

* **Geração de Imagens Mágicas**: Envie o nome de um workflow do `ComfyUI` e seus parâmetros para gerar imagens.
* **Workflows Parametrizáveis**: Utilize arquivos `JSON` como templates para workflows, permitindo a inserção dinâmica de valores através de placeholders.
* **Autenticação e Gerenciamento de Usuários**: Integração com `Fief` para autenticação e gerenciamento de usuários, incluindo webhooks para criação, atualização e exclusão de usuários.
* **Processamento Assíncrono de Jobs**: Emprega `Celery` com `Redis` para enfileirar as solicitações de geração de imagem, otimizando o desempenho e a experiência do usuário.
* **Status da Fila em Tempo Real**: Um endpoint WebSocket (`/websocket/queue-status`) fornece atualizações em tempo real sobre o status da fila de geração.
* **Métricas Operacionais**: Envia dados operacionais, como o status da fila, para o `InfluxDB`, permitindo o monitoramento e análise do sistema.
* **Configuração Flexível**: Suporta configuração através de um arquivo `config.ini` e variáveis de ambiente (`.env`).
* **Gerenciamento de Pastas de Usuário**: Permite que os usuários organizem suas imagens em pastas.
* **Gerenciamento de Planos**: Suporta diferentes planos de usuário com parâmetros e permissões variados.
* **Armazenamento de Imagens**: Utiliza o `MinIO` para armazenar as imagens geradas.
* **Documentação da API**: Oferece documentação interativa da API através do `Scalar`.

## 💻 Pilha Tecnológica

* **Backend API**: `FastAPI`
* **Tarefas Assíncronas**: `Celery`
* **Banco de Dados**: `PostgreSQL` (com `SQLModel` como ORM)
* **Broker/Cache Celery**: `Redis`
* **Autenticação**: `Fief`
* **Geração de Imagem**: `ComfyUI` (rodando separadamente)
* **Armazenamento de Objetos**: `MinIO`
* **Banco de Dados Time-Series (Métricas)**: `InfluxDB`
* **Containerização**: `Docker` & `Docker Compose`

## 🚦 Endpoints Principais da API

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
* Endpoints para gerenciar modelos de IA (CRUD).

### Planos (`/plan`)
* Endpoints para gerenciar planos de assinatura (CRUD).

### Webhooks (`/webhook`)
* `POST /user`: Endpoint para receber webhooks do `Fief` relacionados a eventos de usuário (criação, atualização, exclusão). Não deve ser chamado diretamente.

### WebSockets (`/websocket`)
* `WS /queue-status`: Conecta via WebSocket para receber o status da fila do `ComfyUI` em tempo real.
* `WS /preview`: Conecta via WebSocket para receber pré-visualizações de imagens durante a geração.

### Workflows (`/workflow`)
* Endpoints para gerenciar workflows do `ComfyUI` (CRUD).

### Documentação (`/docs`)
* `GET /scalar`: Acesso à documentação da API via `Scalar`.

## 🎨 Workflows

* Os workflows do `ComfyUI` residem como arquivos `JSON` (por exemplo, em `resources/postgres/workflows.json`).
* Placeholders como `{{nome_do_parametro}}` podem ser usados dentro do `JSON` do workflow.
* A API substitui esses placeholders com os valores fornecidos no campo "parameters" da requisição `/image/generate`.
* É recomendado marcar o nó de saída principal (geralmente `SaveImage`) com `{{output_node_id}}` no campo `_meta.title` para fácil identificação, embora exista um fallback para o primeiro nó `SaveImage` encontrado.

## 🛠️ Configuração e Inicialização

* O projeto utiliza um arquivo `config.ini` para configurações gerais e variáveis de ambiente (gerenciadas com `python-dotenv`) para informações sensíveis e específicas do ambiente.
* A inicialização da aplicação (`main.py`) envolve:
    * Criação das tabelas do banco de dados.
    * Carregamento de dados iniciais (seed) para modelos, workflows e planos.
    * Sincronização de usuários com o `Fief`.
    * Criação do bucket padrão no `MinIO`.
    * Inicialização dos processos `Celery` (worker e beat) para lidar com tarefas assíncronas e agendadas.
    * Limpeza de logs antigos.

## 🏗️ Estrutura do Projeto (Principais Módulos)

* **`api/`**: Contém os módulos que definem os endpoints da API `FastAPI`, separados por funcionalidade (ex: `image_api.py`, `user_api.py`).
* **`core/`**: Módulos centrais do sistema.
    * **`comfy/`**: Lógica de integração com o `ComfyUI` (conexão, execução de workflows, obtenção de imagens e previews).
    * **`celery_core.py`**: Configuração e tarefas do `Celery`.
    * **`config_core.py`**: Carregamento e acesso a configurações do `config.ini`.
    * **`db_core.py`**: Configuração da conexão com o banco de dados (`PostgreSQL` com `SQLModel`) e criação inicial das tabelas.
    * **`env_core.py`**: Gerenciamento de variáveis de ambiente.
    * **`fief_core.py`**: Cliente HTTP para interagir com a API do `Fief`.
    * **`logging_core.py`**: Configuração do sistema de logging.
    * **`metric_core.py`**: Cliente para escrita de métricas no `InfluxDB`.
    * **`minio_core.py`**: Interação com o `MinIO` para armazenamento de arquivos.
* **`handler/`**: Módulos com a lógica de negócio e orquestração das operações solicitadas pelas APIs.
* **`model/`**: Define os modelos de dados (`SQLModel`) e enums utilizados no projeto.
    * **`enum/`**: Contém as enumerações (ex: `ModelType`, `WorkflowType`).
    * **`map/`**: Mapeamentos de parâmetros para modelos, segmentos e tipos de workflow.
    * Arquivos como `image_model.py`, `user_model.py`, `workflow_model.py` definem as tabelas do banco de dados.
* **`resources/`**: Arquivos de recursos, como dados `JSON` para popular o banco (workflows, planos, modelos) e metadados para a documentação OpenAPI.
* **`service/`**: Camada de serviço que interage diretamente com o banco de dados para realizar operações CRUD e outras lógicas de dados.
* **`tests/`**: Contém os testes unitários para as diferentes partes do projeto.
* **`utils/`**: Utilitários gerais, como `security_util.py`.
* **`main.py`**: Ponto de entrada da aplicação `FastAPI`, configuração do ciclo de vida e inclusão dos roteadores.
* **`docker-compose.yaml`**: Define os serviços para rodar a aplicação e suas dependências (`PostgreSQL`, `Redis`, `Fief`, `MinIO`, `InfluxDB`) em containers `Docker`.
* **`requirements.txt`**: Lista as dependências `Python` do projeto.
* **`config.ini`**: Arquivo de configuração para parâmetros não sensíveis.

[![Python Quality Check Status](https://github.com/pedroluizmossi1/o-art/actions/workflows/pylint.yml/badge.svg)](https://github.com/pedroluizmossi1/o-art/actions/workflows/pylint.yml) [![Bandit Analysis Status](https://github.com/pedroluizmossi1/o-art/actions/workflows/Bandit.yml/badge.svg)](https://github.com/pedroluizmossi1/o-art/actions/workflows/Bandit.yml) [![Ruff Quality Check Status](https://github.com/pedroluizmossi1/o-art/actions/workflows/ruff.yml/badge.svg)](https://github.com/pedroluizmossi1/o-art/actions/workflows/ruff.yml)
