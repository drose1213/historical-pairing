FROM python:3.12-slim

WORKDIR /app

# 安装依赖（利用 Docker 缓存层）
COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY server/app ./app

EXPOSE 8787

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8787"]
