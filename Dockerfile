# art/Dockerfile

# ---- Estágio de Build (Builder) ----
# Usamos uma imagem slim do Python como base
FROM python:3.10-slim as builder

# Variáveis de ambiente para Python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Diretório de trabalho dentro do container
WORKDIR /app

# Instala dependências do sistema necessárias para compilar algumas libs Python
# psycopg2-binary evita a necessidade de libpq-dev, mas outras como cryptography/cffi podem precisar
# Verifique se outras libs em requirements.txt precisam de mais algo.
# Usamos --no-install-recommends para manter a imagem menor.
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    # Limpa o cache do apt para reduzir o tamanho da imagem
    rm -rf /var/lib/apt/lists/*

# Atualiza o pip para a versão mais recente
RUN pip install --upgrade pip

# Copia o arquivo de dependências PRIMEIRO para aproveitar o cache do Docker
COPY requirements.txt .

# Cria wheels (pacotes pré-compilados) para todas as dependências.
# Isso pode acelerar a instalação no estágio final e ajuda com dependências complexas.
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt


# ---- Estágio Final (Produção) ----
# Começamos novamente com a imagem base slim limpa
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Cria um usuário e grupo não-root 'app' para rodar a aplicação (mais seguro)
RUN addgroup --system app && adduser --system --ingroup app app

# Cria os diretórios necessários e define permissões
# /app para o código, /schedule para o arquivo de estado do celery beat
RUN mkdir -p /app /schedule && chown -R app:app /app /schedule

# Define o diretório de trabalho
WORKDIR /app

# Copia os wheels criados no estágio builder
COPY --from=builder /wheels /wheels

# Instala as dependências Python usando os wheels (mais rápido)
# --no-cache evita manter o cache do pip, rm -rf /wheels remove os arquivos após instalação
RUN pip install --no-cache /wheels/* && rm -rf /wheels

# Copia o código da aplicação para o container DEPOIS de instalar dependências
# Usa --chown para garantir que o usuário 'app' seja dono dos arquivos
COPY --chown=app:app . .

# Expõe a porta que a API FastAPI usará (documentação, mapeamento é no docker-compose)
EXPOSE 8000

# Muda para o usuário não-root 'app'
USER app

# Define o comando padrão para iniciar a aplicação (API FastAPI com Uvicorn)
# Este comando será usado pelo serviço 'app' no docker-compose.
# Os serviços 'celery-worker' e 'celery-beat' sobrescreverão este comando.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]