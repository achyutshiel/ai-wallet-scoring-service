from typing import Dict, List, Tuple
from decimal import Decimal, ROUND_HALF_UP
from app.utils.types import WalletMessage, Transaction, SuccessMessage, CategorySuccess

def _sum_safe(x):
    return float(sum(v for v in x if isinstance(v, (int, float))))

def _format_z(z: float) -> str:
    # Return as high-precision string (18 decimals allowed by test)
    return str(Decimal(z).quantize(Decimal("0.000000000000000001"), rounding=ROUND_HALF_UP))

def extract_dex_features(transactions: List[Transaction]) -> Dict[str, float]:
    total_deposit_usd = 0.0
    total_withdraw_usd = 0.0
    total_swap_volume = 0.0
    num_deposits = 0
    num_withdraws = 0
    num_swaps = 0
    pools = set()

    for tx in transactions:
        if tx.poolId:
            pools.add(tx.poolId)

        action = tx.action.lower()
        if action == "deposit":
            usd0 = tx.token0.amountUSD if tx.token0 and tx.token0.amountUSD else 0.0
            usd1 = tx.token1.amountUSD if tx.token1 and tx.token1.amountUSD else 0.0
            total_deposit_usd += (usd0 + usd1)
            num_deposits += 1

        elif action == "withdraw":
            usd0 = tx.token0.amountUSD if tx.token0 and tx.token0.amountUSD else 0.0
            usd1 = tx.token1.amountUSD if tx.token1 and tx.token1.amountUSD else 0.0
            total_withdraw_usd += (usd0 + usd1)
            num_withdraws += 1

        elif action == "swap":
            # Count swap volume in USD from tokenIn or tokenOut (prefer tokenIn)
            if tx.tokenIn and tx.tokenIn.amountUSD:
                total_swap_volume += tx.tokenIn.amountUSD
            elif tx.tokenOut and tx.tokenOut.amountUSD:
                total_swap_volume += tx.tokenOut.amountUSD
            num_swaps += 1

    features = {
        "total_deposit_usd": round(total_deposit_usd, 6),
        "total_withdraw_usd": round(total_withdraw_usd, 6),
        "num_deposits": float(num_deposits),
        "num_withdraws": float(num_withdraws),
        "total_swap_volume": round(total_swap_volume, 6),
        "num_swaps": float(num_swaps),
        "unique_pools": float(len(pools)),
    }
    return features

def simple_dex_score(features: Dict[str, float]) -> float:
    """
    Normalize a simple score into ~0–1000 range.
    This is a placeholder; replace with notebook logic later.
    """
    base = 0.0
    base += min(features.get("total_deposit_usd", 0.0) / 1.0, 500)   # scale deposits
    base += min(features.get("total_swap_volume", 0.0) / 2.0, 400)  # scale swaps
    base += 50 * features.get("unique_pools", 0.0)                  # pool diversity
    return float(max(0.0, min(base, 1000.0)))

def score_wallet_walletmessage(msg: WalletMessage) -> Tuple[SuccessMessage, Dict[str, float]]:
    """
    Build a SuccessMessage for a single-wallet DEX category.
    Returns (success_message, features)
    """
    # Find DEX data
    dex = next((b for b in msg.data if b.protocolType.lower() == "dexes"), None)
    txs = dex.transactions if dex else []

    features = extract_dex_features(txs)
    score = simple_dex_score(features)
    zscore = _format_z(score)  # keep as string

    tx_count = len(txs)
    ts = txs[0].timestamp if txs else 0  # simplistic; adjust as needed

    cat = CategorySuccess(
        category="dexes",
        score=round(score, 2),
        transaction_count=tx_count,
        features=features,
    )

    success = SuccessMessage(
        wallet_address=msg.wallet_address,
        zscore=zscore,
        timestamp=ts,
        processing_time_ms=1,  # placeholder; set real timing in pipeline
        categories=[cat],
    )
    return success, features
