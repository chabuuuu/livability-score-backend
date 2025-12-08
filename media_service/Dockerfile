FROM node:21-alpine3.19

RUN mkdir -p /opt/app

WORKDIR /opt/app

RUN npm i npm@10 -g

COPY package.json package-lock.json ./

RUN npm install

COPY . .

# Build the application
RUN npm run build

EXPOSE 8080

CMD ["sh", "-c", "npm run start:prod"]
