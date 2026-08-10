# TeaMall 前端镜像：Node 20 构建 -> nginx 托管静态资源
FROM node:20-alpine AS build

WORKDIR /app

# npm 镜像源：默认国内镜像（npmmirror），海外环境可用 --build-arg NPM_REGISTRY=... 覆盖
ARG NPM_REGISTRY=https://registry.npmmirror.com
ENV npm_config_registry=$NPM_REGISTRY

# 利用 package-lock.json 保证依赖可复现
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:1.27-alpine

# 构建产物 + nginx 站点配置（含 /api、/uploads 反向代理）
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
