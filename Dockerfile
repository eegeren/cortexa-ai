FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# Parametrik; varsayılan apps/api
ARG API_DIR=apps/api

# Bağımlılıklar
COPY ${API_DIR}/pyproject.toml /app/
RUN pip install --no-cache-dir \
    fastapi "uvicorn[standard]" "sqlalchemy>=2.0" "psycopg[binary]" \
    "passlib[bcrypt]" pyjwt httpx pydantic python-dotenv email-validator

# Uygulama
COPY ${API_DIR}/app /app/app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]