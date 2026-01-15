# Frontend Dockerfile (Vite build → Nginx serve)
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
# In case package-lock.json is not present, fallback to npm install
RUN npm ci || npm install
COPY . .
# Build with API base routed through Nginx proxy
ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

FROM nginx:alpine
RUN apk add --no-cache curl
# Nginx config for SPA + API proxy
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/build /usr/share/nginx/html
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=5s CMD curl -fsS http://localhost/ >/dev/null || exit 1
CMD ["nginx", "-g", "daemon off;"]
