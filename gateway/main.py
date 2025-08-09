from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
import httpx
from loguru import logger
import sys, pika, json, os, uuid

logger.remove()
logger.add(sys.stderr, format="{time} {level} {extra[correlation_id]} {message}", level="INFO")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
app = FastAPI(title="AI Hedge Fund API Gateway", version="1.1.0")
client = httpx.AsyncClient()

def publish_to_rabbitmq(queue_name: str, body: dict):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue=queue_name, durable=True)
    channel.basic_publish(exchange='', routing_key=queue_name, body=json.dumps(body), properties=pika.BasicProperties(delivery_mode=2))
    connection.close()

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def route_request(request: Request, background_tasks: BackgroundTasks, path: str):
    correlation_id = str(uuid.uuid4())
    log = logger.bind(correlation_id=correlation_id)
    if path.startswith("backtest/run"):
        backtest_config = await request.json()
        backtest_config['correlation_id'] = correlation_id
        log.info(f"Received backtest request. Publishing to queue 'backtest_requests'.")
        background_tasks.add_task(publish_to_rabbitmq, "backtest_requests", backtest_config)
        return {"message": "Backtest initiated successfully.", "correlation_id": correlation_id}
    return {"message": "Not a backtest route"}
