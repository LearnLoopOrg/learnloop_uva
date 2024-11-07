# Stage 1: Build the React app
FROM node:18 AS build

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

ENV NODE_ENV=production
# Run the build command to create the production build
RUN npm run build

FROM nginx:alpine

# Copy the custom Nginx configuration to set port 3001
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy the built React app to Nginx's web server directory
COPY --from=build /app/build /usr/share/nginx/html

# ENV PORT=3001

EXPOSE 3001

# Serve the build output with a static file server
# CMD ["npx", "serve", "-s", "build", "-l", "3001"]
# CMD [ "npm", "run", "start" ]

# Start Nginx when the container runs
CMD ["nginx", "-g", "daemon off;"]
