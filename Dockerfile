FROM python:3.11-slim

WORKDIR /app

# 安装依赖
RUN pip install flask requests -i https://pypi.tsinghua.edu.cn/simple

# 复制应用代码
COPY faka_app.py .

# 暴露端口
EXPOSE 3001

# 启动应用
CMD ["python", "faka_app.py"]
