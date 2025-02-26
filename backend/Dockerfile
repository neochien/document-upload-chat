# 使用 Python 作為基礎映像
FROM python:3.10

# 設定工作目錄
WORKDIR /app

# 複製 backend 內的所有檔案
COPY . .

# 複製 requirements.txt 檔案
COPY requirements.txt .

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils

# 安裝依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 暴露 FastAPI 服務的端口
EXPOSE 8000

# 啟動 FastAPI 應用程式
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]