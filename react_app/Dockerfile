# Stage 1: Build the React app
FROM node:14-alpine AS build

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
