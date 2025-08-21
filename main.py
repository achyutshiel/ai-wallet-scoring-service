from fastapi import FastAPI
from app.utils.metrics import Metrics
from app.services.kafka_service import maybe_start_kafka, get_kafka_status

# Initialize FastAPI app
app = FastAPI(title="AI Scoring Service", version="1.0.0")

# Global metrics tracker
metrics = Metrics()


@app.on_event("startup")
async def startup_event():
    """Start Kafka loop if enabled"""
    await maybe_start_kafka(metrics)


@app.get("/")
def root():
    """Root endpoint to verify service is alive"""
    return {
        "service": "ai-scoring",
        "version": "v1",
        "kafka": get_kafka_status(),
    }


@app.get("/api/v1/health")
def health():
    """Health check endpoint"""
    return {"status": "ok"}


@app.get("/api/v1/stats")
def stats():
    """Return basic processing stats"""
    return {
        "processed_wallets": metrics.processed_wallets,
        "avg_processing_ms": metrics.avg_processing_ms,
        "last_errors": list(metrics.last_errors)[-5:],  # convert deque to list
    }
