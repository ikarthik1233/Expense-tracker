from pydantic import BaseModel
from typing import List, Optional
import datetime

class ReceiptScanRequest(BaseModel):
    image_base64: str

class ReceiptItem(BaseModel):
    name: str
    price: float

class ReceiptScanResponse(BaseModel):
    merchant: str
    date: str
    items: List[ReceiptItem]
    total: float
    category: str

class ReceiptCreate(BaseModel):
    merchant: str
    date: str
    total: float
    category: str
    items: List[ReceiptItem]
    image_base64: Optional[str] = None

class SplitItemCreate(BaseModel):
    friend_id: int
    amount: float
    you_owe: Optional[bool] = False

class SplitCreate(BaseModel):
    receipt_id: int
    split_type: str  # equal, custom, item
    splits: List[SplitItemCreate]

class FriendCreate(BaseModel):
    name: str

class FriendResponse(BaseModel):
    id: int
    name: str
    emoji: str

    class Config:
        from_attributes = True

class SplitPaidRequest(BaseModel):
    payment_proof_base64: Optional[str] = None

class SplitResponse(BaseModel):
    id: int
    receipt_id: int
    friend_id: int
    friend_name: str
    friend_emoji: str
    amount: float
    paid: bool
    split_type: str
    you_owe: bool
    payment_proof: Optional[str] = None

    class Config:
        from_attributes = True

class ReceiptResponse(BaseModel):
    id: int
    merchant: str
    date: str
    total: float
    category: str
    items: List[ReceiptItem]
    image_base64: Optional[str] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class BalanceItem(BaseModel):
    friend_id: int
    friend_name: str
    friend_emoji: str
    amount: float
    split_id: Optional[int] = None

class BalancesResponse(BaseModel):
    owed_to_you: List[BalanceItem]
    you_owe: List[BalanceItem]
    recovered: Optional[float] = 0.0

class MerchantSpend(BaseModel):
    merchant: str
    total: float

class SummaryResponse(BaseModel):
    total_this_month: float
    by_category: dict
    top_merchants: List[MerchantSpend]

class BudgetCreate(BaseModel):
    month: str
    amount: float

class BudgetResponse(BaseModel):
    id: int
    month: str
    amount: float
    created_at: datetime.datetime

    class Config:
        from_attributes = True
