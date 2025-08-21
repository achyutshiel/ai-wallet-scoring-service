import os
import asyncio
import json
from typing import Any
from app.utils.metrics import Metrics
from app.utils.types import WalletMessage
from app.models.dex_model import score_wallet_walletmessage

# For simplicity, use kafka-python if available; else run without Kafka
KAFKA_ENABLED = os.getenv("ENABLE_KAFKA", "false").lower() == "true"

_kafka_status = {"enabled": KAFKA_ENABLED, "running": False, "reason": ""}

def get_kafka_status() -> dict:
    return _kafka_status

async def maybe_start_kafka(metrics: Metrics):
    if not KAFKA_ENABLED:
        _kafka_status.update({"running": False, "reason": "ENABLE_KAFKA=false"})
        return

    try:
        # Lazy import to avoid requirement when disabled
        from kafka import KafkaConsumer, KafkaProducer

        input_topic = os.getenv("KAFKA_INPUT_TOPIC", "wallet-transactions")
        success_topic = os.getenv("KAFKA_SUCCESS_TOPIC", "wallet-scores-success")
        failure_topic = os.getenv("KAFKA_FAILURE_TOPIC", "wallet-scores-failure")
        bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

        consumer = KafkaConsumer(
            input_topic,
            bootstrap_servers=bootstrap,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            enable_auto_commit=True,
            group_id=os.getenv("KAFKA_CONSUMER_GROUP", "ai-scoring-service"),
            auto_offset_reset="earliest",
        )
        producer = KafkaProducer(
            bootstrap_servers=bootstrap,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )

        _kafka_status.update({"running": True, "reason": ""})

        async def _loop():
            loop = asyncio.get_event_loop()
            while True:
                # kafka-python is blocking; run polling in thread
                records = await loop.run_in_executor(None, consumer.poll, 1.0)
                for _tp, messages in (records or {}).items():
                    for m in messages:
                        await handle_message(m.value, producer, success_topic, failure_topic, metrics)
                await asyncio.sleep(0)  # yield

        asyncio.create_task(_loop())

    except Exception as e:
        _kafka_status.update({"running": False, "reason": f"{type(e).__name__}: {e}"})

async def handle_message(raw: Any, producer, success_topic: str, failure_topic: str, metrics: Metrics):
    import time
    start = time.time()
    try:
        msg = WalletMessage(**raw)
        success, _features = score_wallet_walletmessage(msg)
        processing_ms = int((time.time() - start) * 1000)
        success.processing_time_ms = processing_ms
        producer.send(success_topic, json.loads(success.model_dump_json()))
        metrics.record_success(processing_ms)
    except Exception as e:
        processing_ms = int((time.time() - start) * 1000)
        metrics.record_error(str(e))
        failure = {
            "wallet_address": raw.get("wallet_address") if isinstance(raw, dict) else "",
            "error": f"{type(e).__name__}: {e}",
            "timestamp": int(time.time()),
            "processing_time_ms": processing_ms,
            "categories": [
                {
                    "category": "dexes",
                    "error": "processing_failed",
                    "transaction_count": len((raw.get("data", [{}])[0] or {}).get("transactions", []))
                    if isinstance(raw, dict) else 0,
                }
            ],
        }
        producer.send(failure_topic, failure)
