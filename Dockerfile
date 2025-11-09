FROM python:3.13.7-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
# Copiar el código del proyecto
COPY . .
# Puerto y comando
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]