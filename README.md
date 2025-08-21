# AI Scoring Server (Scaffold)

## What this provides
- FastAPI app with `/`, `/api/v1/health`, `/api/v1/stats`
- Minimal DEX features & scoring (replace with your notebook logic later)
- Kafka consumer/producer **optional** (toggle `ENABLE_KAFKA=true`)

## Place these files at repo root
- `AI_ENGINEER_CHALLENGE.md`  (given)
- `dex_scoring_model.ipynb`   (given — convert to `app/models/dex_model.py` later)
- `test_challenge.py`         (given — run it locally)

## Setup
```bash
python3.11 -m venv venv
source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
