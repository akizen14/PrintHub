# Frontend Dockerfile for PrintHub
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy application code
COPY . .

# Build the application
RUN npm run build

# Expose port
EXPOSE 3000

# Set environment variable
ENV NODE_ENV=production

# Run the application
CMD ["npm", "start"]
