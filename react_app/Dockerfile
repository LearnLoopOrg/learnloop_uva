FROM node:18

WORKDIR /app

COPY package*.json ./

ENV NODE_ENV=production

RUN npm install
RUN npm install -g serve

COPY . .

RUN npm run build

EXPOSE 3001

CMD ["serve", "-s", "build"]
