FROM node:20-alpine AS build

WORKDIR /app

COPY . .

RUN if [ -f pnpm-lock.yaml ]; then \
      corepack enable && corepack prepare pnpm@9.15.4 --activate && \
      pnpm install --frozen-lockfile; \
    elif [ -f yarn.lock ]; then \
      corepack enable && \
      yarn install --frozen-lockfile; \
    elif [ -f package-lock.json ]; then \
      npm ci; \
    else \
      npm install; \
    fi

RUN if [ -f pnpm-lock.yaml ]; then \
      pnpm run build; \
    elif [ -f yarn.lock ]; then \
      yarn build; \
    else \
      npm run build; \
    fi

FROM nginx:alpine AS production

ENV PORT=80

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/templates/default.conf.template

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
