FROM python:3.12-slim
WORKDIR /app
COPY unidad2/requirements.txt /app/unidad2/requirements.txt
RUN pip install --no-cache-dir -r /app/unidad2/requirements.txt
COPY unidad2 /app/unidad2
EXPOSE 8501
CMD ["streamlit", "run", "unidad2/app.py", "--server.address=0.0.0.0", "--server.port=8501"]
