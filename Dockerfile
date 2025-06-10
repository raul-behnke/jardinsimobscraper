# 1. Usa uma imagem base oficial do Node.js. A versão 'alpine' é leve e segura.
FROM node:20-alpine

# 2. Define o diretório de trabalho dentro do container.
WORKDIR /app

# 3. Copia os arquivos de definição de dependências primeiro.
#    Isso aproveita o cache do Docker. Se esses arquivos não mudarem,
#    o Docker não reinstalará as dependências em builds futuros.
COPY package*.json ./

# 4. Instala as dependências do projeto.
RUN npm install

# 5. Copia todo o resto do código do seu projeto para o diretório de trabalho no container.
COPY . .

# 6. Define o comando padrão que será executado quando o container iniciar.
#    Ele irá rodar todo o seu ciclo de atualização.
CMD [ "npm", "run", "generate" ]