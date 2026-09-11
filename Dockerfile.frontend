# WeatherGPT frontend — Next.js standalone runner (D-02).
# Public base URL is baked via build arg only (never a secret key):
# ARG NEXT_PUBLIC_WEATHERGPT_API is promoted to ENV so Next inlines it
# at build time. Keys are never baked here (D-03).

FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ARG NEXT_PUBLIC_WEATHERGPT_API=http://localhost:8000
ENV NEXT_PUBLIC_WEATHERGPT_API=$NEXT_PUBLIC_WEATHERGPT_API
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
EXPOSE 3000
CMD ["node", "server.js"]
