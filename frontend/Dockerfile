# Build stage
FROM node:22-alpine AS build

WORKDIR /app

COPY package.json package-lock.json* ./

RUN npm install

COPY . .

# Build with production API URL
ARG VITE_API_URL=https://api.nuze.dpdns.org
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# Production stage - serve with nginx
FROM nginx:alpine

# Copy built assets
COPY --from=build /app/dist /usr/share/nginx/html

# Copy custom nginx config for SPA routing
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
