FROM node:22-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM alpine:3.20
COPY --from=builder /app/dist /dist
CMD ["sh", "-c", "cp -r /dist/* /app/dist/ && echo 'Frontend dist copied to volume'"]
