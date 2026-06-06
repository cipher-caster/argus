FROM node:20-alpine AS base
WORKDIR /app

# Dependencies stage - cached unless package*.json changes
FROM base AS deps
COPY package.json package-lock.json* ./
RUN npm ci --prefer-offline

# Final stage
FROM base AS final

# Copy node_modules from deps stage
COPY --from=deps /app/node_modules ./node_modules

# Copy source
COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]
