# Usa uma imagem base do Node.js que é baseada em Debian, facilitando a instalação do Python.
FROM node:20-bookworm-slim

# Instala Python, pip e outras utilidades do sistema
RUN apt-get update && apt-get install -y python3 python3-pip && rm -rf /var/lib/apt/lists/*

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia os arquivos de dependência primeiro para aproveitar o cache do Docker
COPY package*.json ./
COPY requirements.txt ./
# A pasta backend precisa ser copiada aqui para o ghl_client.py ser encontrado
COPY backend/ backend/

# Instala as dependências do Node.js
RUN npm install

# Instala as dependências do Python
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

# Copia todo o resto do código do projeto para o diretório de trabalho
COPY . .

# Comando padrão que será executado quando o container iniciar.
# Ele roda o nosso script orquestrador principal.
CMD [ "python3", "-m", "backend.main_runner" ]