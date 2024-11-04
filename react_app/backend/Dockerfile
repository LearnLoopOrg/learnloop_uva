
FROM node:14-alpine

WORKDIR /backend

COPY package*.json ./

RUN npm install

COPY . .

ENV PORT=5001

EXPOSE 5001

CMD ["node", "index.js"]