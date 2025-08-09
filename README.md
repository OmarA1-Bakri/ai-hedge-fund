# AI Hedge Fund (v1.0)

An agent-centric, microservice-based platform for developing and backtesting quantitative trading strategies using Large Language Models and LangGraph. This version has been refactored for security, scalability, and resilience based on the "Blueprint for Improvement."

## Architecture Overview (v1.0)

The platform is a distributed system composed of several independent services that communicate asynchronously via a **RabbitMQ** message queue, orchestrated by a central **API Gateway**.

-   **API Gateway**: The single, secure entry point for all client requests (port `8080`). It routes synchronous traffic and publishes asynchronous job requests (like backtests) to the message queue.
-   **RabbitMQ**: The message broker (port `5672`) that decouples services, ensuring that tasks like backtesting are handled asynchronously and reliably.
-   **Data Ingestion Service**: A dedicated service for all external financial data fetching with built-in caching (port `8001`).
-   **Portfolio & Risk Management Service**: Manages the state of all portfolios, including cash, positions, and pre-trade compliance and risk checks (port `8002`).
-   **Strategy Service**: Contains the core AI agent and LangGraph logic for generating trade recommendations (port `8003`).
-   **Backtest Orchestrator**: A worker service that listens to the `backtest_requests` queue on RabbitMQ and executes the end-to-end simulation logic.
-   **Frontend**: The React-based user interface for interacting with the platform (port `5173`).
-   **Database**: A PostgreSQL database for persistent storage.

---

## Getting Started

### Prerequisites

-   Docker and Docker Compose
-   A `.env` file configured with the necessary API keys.

### 1. Configuration

Create a `.env` file in the root directory by copying the example:

`cp .env.example .env`

Now, edit the `.env` file with your credentials:

-   `OPENAI_API_KEY`, `TAVILY_API_KEY`, etc.
-   `DATABASE_URL`: Pre-configured for Docker. No changes are needed for local setup.
-   `RABBITMQ_HOST`: Pre-configured for Docker. No changes are needed.
-   `ENCRYPTION_KEY`: **CRITICAL**. Generate a secret key for encrypting API keys in the database. You can generate one with the following Python command and paste the output into the `.env` file:
    `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`

### 2. Build and Run the System

The entire multi-container application can be built and started with a single command from the project's root directory:

`docker-compose up --build -d`
*The `-d` flag runs the containers in detached mode.*

### 3. Using the Platform

-   **Frontend UI**: `http://localhost:5173`
-   **API Gateway**: `http://localhost:8080`
-   **RabbitMQ Management UI**: `http://localhost:15672` (user: `user`, pass: `password`)

To run a backtest, use the frontend UI or send a POST request to the gateway:
`POST http://localhost:8080/backtest/run`

Monitor logs: `docker logs -f backtest_orchestrator`
