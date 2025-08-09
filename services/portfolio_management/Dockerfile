FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry config virtualenvs.create false && poetry install --no-root --no-dev
COPY . .
CMD ["uvicorn", "services.portfolio_management.main:app", "--host", "0.0.0.0", "--port", "8002"]
