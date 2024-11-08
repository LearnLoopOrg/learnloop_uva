# Gebruik een Node.js image
FROM node:18-alpine

# Maak app directory
WORKDIR /app

# Kopieer package.json en package-lock.json
COPY package*.json ./

# Installeer dependencies
RUN npm install

# Kopieer de rest van de applicatie
COPY . .

# Stel environment variables in
ENV PORT=8080
ENV NODE_ENV=production

# Expose de poort
EXPOSE 8080

# Start de applicatie
CMD ["node", "index.js"]
