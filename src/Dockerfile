# 使用 Node.js 作為基礎映像
FROM node:18 AS build-stage

# 設定工作目錄
WORKDIR /app

# 複製 package.json 和 package-lock.json
COPY package*.json ./

# 安裝依賴
RUN npm install

# 安裝 Vue CLI 及依賴
RUN npm install @vue/cli-service --save-dev

# 複製所有程式碼
COPY . .

# 建立 Vue.js 應用程式
RUN npm run build

# 使用 Nginx 作為伺服器
FROM nginx:alpine AS production-stage

# 複製 Vue.js 構建的檔案到 Nginx 伺服器
COPY --from=build-stage /app/dist /usr/share/nginx/html

# 暴露 Nginx 服務的端口
EXPOSE 80

# 啟動 Nginx
CMD ["nginx", "-g", "daemon off;"]