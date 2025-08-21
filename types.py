from typing import List, Dict, Optional
from pydantic import BaseModel

# ---- Input types ----
class TokenAmount(BaseModel):
    amount: Optional[float] = None
    amountUSD: Optional[float] = None
    address: Optional[str] = None
    symbol: Optional[str] = None

class Transaction(BaseModel):
    document_id: Optional[str]
    action: str
    timestamp: int
    caller: Optional[str]
    protocol: Optional[str]
    poolId: Optional[str]
    poolName: Optional[str]

    # Swap
    tokenIn: Optional[TokenAmount] = None
    tokenOut: Optional[TokenAmount] = None

    # LP deposit/withdraw
    token0: Optional[TokenAmount] = None
    token1: Optional[TokenAmount] = None

class ProtocolData(BaseModel):
    protocolType: str
    transactions: List[Transaction]

class WalletMessage(BaseModel):
    wallet_address: str
    data: List[ProtocolData]

# ---- Output types ----
class CategorySuccess(BaseModel):
    category: str
    score: float
    transaction_count: int
    features: Dict[str, float]

class SuccessMessage(BaseModel):
    wallet_address: str
    zscore: str  # keep as string to satisfy validator
    timestamp: int
    processing_time_ms: int
    categories: List[CategorySuccess]

class CategoryFailure(BaseModel):
    category: str
    error: str
    transaction_count: int

class FailureMessage(BaseModel):
    wallet_address: str
    error: str
    timestamp: int
    processing_time_ms: int
    categories: List[CategoryFailure]
