# Stage 1: Build the React app
FROM node:14-alpine AS build

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

# Run the build command to create the production build
RUN npm run build

ENV PORT=3001

EXPOSE 3001

# Serve the build output with a static file server
# CMD ["npx", "serve", "-s", "build", "-l", "3001"]
CMD [ "npm", "run", "start" ]
