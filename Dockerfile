# 基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 将项目代码复制到容器中
COPY . /app

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 暴露端口
EXPOSE 5000

# 启动应用（默认启动 Flask）
CMD ["flask", "run", "--host=0.0.0.0"]

ENV FLASK_APP=app/__init__.py
ENV FLASK_ENV=development