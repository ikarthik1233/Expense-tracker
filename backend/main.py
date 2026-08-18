import os
import json
import base64
import datetime
from typing import Optional, List
from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from dotenv import load_dotenv

import models
import schemas
from database import engine, get_db

# Load environment variables
load_dotenv()

# Create tables
models.Base.metadata.create_all(bind=engine)

from sqlalchemy import text
with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE splits ADD COLUMN payment_proof TEXT"))
        conn.commit()
    except Exception:
        pass  # column already exists

app = FastAPI(title="Receipt Graveyard API")

from routes.budgets import router as budgets_router
app.include_router(budgets_router)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:5176",
        "http://192.168.1.31:5173",
        "http://192.168.1.31:5174",
        "http://192.168.1.31:5175",
    ],
    allow_origin_regex=r"http://.*:\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------------------------
# OCR Route using Google Gemini Flash
# --------------------------------------------------------------------------
@app.post("/receipts/scan", response_model=schemas.ReceiptScanResponse)
def scan_receipt(body: schemas.ReceiptScanRequest):
    image_b64 = body.image_base64
    media_type = "image/jpeg"

    if "," in image_b64 and image_b64.startswith("data:"):
        header, image_b64 = image_b64.split(",", 1)
        if "image/png" in header:
            media_type = "image/png"
        elif "image/webp" in header:
            media_type = "image/webp"

    try:
        from services.ocr_service import parse_receipt
        image_bytes = base64.b64decode(image_b64)
        parsed = parse_receipt(image_bytes, media_type)
        return schemas.ReceiptScanResponse(
            merchant=parsed.get("merchant", "Unknown Merchant"),
            date=parsed.get("date", datetime.date.today().strftime("%Y-%m-%d")),
            items=[schemas.ReceiptItem(name=i.get("name", "Item"), price=float(i.get("price", 0))) for i in parsed.get("items", [])],
            total=float(parsed.get("total", 0.0)),
            category=parsed.get("category", "Other")
        )
    except Exception as e:
        print("Gemini OCR API error / fallback active:", e)
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        return schemas.ReceiptScanResponse(
            merchant="Graveyard Bistro",
            date=today_str,
            items=[
                schemas.ReceiptItem(name="Phantom Pizza", price=450.0),
                schemas.ReceiptItem(name="Potion Punch", price=150.0)
            ],
            total=600.0,
            category="Food"
        )

# --------------------------------------------------------------------------
# Receipts Routes
# --------------------------------------------------------------------------
@app.post("/receipts", response_model=schemas.ReceiptResponse)
def create_receipt(receipt_in: schemas.ReceiptCreate, db: Session = Depends(get_db)):
    print("Received POST /receipts body:", receipt_in.dict())
    items_json = json.dumps([item.dict() for item in receipt_in.items])
    receipt = models.Receipt(
        merchant=receipt_in.merchant,
        date=receipt_in.date,
        total=receipt_in.total,
        category=receipt_in.category,
        items=items_json,
        image_base64=receipt_in.image_base64
    )
    db.add(receipt)
    db.commit()
    db.refresh(receipt)

    return schemas.ReceiptResponse(
        id=receipt.id,
        merchant=receipt.merchant,
        date=receipt.date,
        total=receipt.total,
        category=receipt.category,
        items=[schemas.ReceiptItem(**i) for i in json.loads(receipt.items)],
        image_base64=receipt.image_base64,
        created_at=receipt.created_at
    )

@app.get("/receipts", response_model=List[schemas.ReceiptResponse])
def get_receipts(month: Optional[str] = Query(None, description="YYYY-MM"), db: Session = Depends(get_db)):
    query = db.query(models.Receipt)
    if month:
        query = query.filter(models.Receipt.date.startswith(month))
    receipts = query.order_by(models.Receipt.date.desc(), models.Receipt.id.desc()).all()
    
    result = []
    for r in receipts:
        items_data = json.loads(r.items) if r.items else []
        result.append(schemas.ReceiptResponse(
            id=r.id,
            merchant=r.merchant,
            date=r.date,
            total=r.total,
            category=r.category,
            items=[schemas.ReceiptItem(**i) for i in items_data],
            image_base64=r.image_base64,
            created_at=r.created_at
        ))
    return result

@app.delete("/receipts/{receipt_id}")
def delete_receipt(receipt_id: int, db: Session = Depends(get_db)):
    receipt = db.query(models.Receipt).filter(models.Receipt.id == receipt_id).first()
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    db.delete(receipt)
    db.commit()
    return {"message": "Receipt buried permanently"}

@app.get("/receipts/summary", response_model=schemas.SummaryResponse)
def get_receipts_summary(month: Optional[str] = Query(None), db: Session = Depends(get_db)):
    if not month:
        month = datetime.date.today().strftime("%Y-%m")
        
    receipts = db.query(models.Receipt).filter(models.Receipt.date.startswith(month)).all()
    
    total_this_month = sum(r.total for r in receipts)
    
    categories = ["Food", "Shopping", "Transport", "Entertainment", "Health", "Utilities", "Other"]
    by_category = {cat: 0.0 for cat in categories}
    merchant_totals = {}
    
    for r in receipts:
        by_category[r.category] = by_category.get(r.category, 0.0) + r.total
        merchant_totals[r.merchant] = merchant_totals.get(r.merchant, 0.0) + r.total
        
    sorted_merchants = sorted(merchant_totals.items(), key=lambda x: x[1], reverse=True)
    top_merchants = [schemas.MerchantSpend(merchant=m, total=t) for m, t in sorted_merchants[:5]]
    
    return schemas.SummaryResponse(
        total_this_month=total_this_month,
        by_category=by_category,
        top_merchants=top_merchants
    )

# --------------------------------------------------------------------------
# Friends Routes
# --------------------------------------------------------------------------
@app.get("/friends", response_model=List[schemas.FriendResponse])
def get_friends(db: Session = Depends(get_db)):
    return db.query(models.Friend).all()

@app.post("/friends", response_model=schemas.FriendResponse)
def create_friend(friend_in: schemas.FriendCreate, db: Session = Depends(get_db)):
    friend = models.Friend(name=friend_in.name, emoji=models.get_random_emoji())
    db.add(friend)
    db.commit()
    db.refresh(friend)
    return friend

@app.delete("/friends/{friend_id}")
def delete_friend(friend_id: int, db: Session = Depends(get_db)):
    friend = db.query(models.Friend).filter(models.Friend.id == friend_id).first()
    if not friend:
        raise HTTPException(status_code=404, detail="Friend not found")
    db.delete(friend)
    db.commit()
    return {"message": "Friend removed"}

# --------------------------------------------------------------------------
# Splits Routes
# --------------------------------------------------------------------------
@app.post("/splits", response_model=List[schemas.SplitResponse])
def create_splits(split_in: schemas.SplitCreate, db: Session = Depends(get_db)):
    receipt = db.query(models.Receipt).filter(models.Receipt.id == split_in.receipt_id).first()
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")

    db.query(models.Split).filter(models.Split.receipt_id == split_in.receipt_id).delete()

    created_splits = []
    for item in split_in.splits:
        split = models.Split(
            receipt_id=split_in.receipt_id,
            friend_id=item.friend_id,
            amount=item.amount,
            paid=False,
            split_type=split_in.split_type,
            you_owe=item.you_owe or False
        )
        db.add(split)
        created_splits.append(split)
        
    db.commit()
    
    result = []
    for s in created_splits:
        db.refresh(s)
        friend = db.query(models.Friend).filter(models.Friend.id == s.friend_id).first()
        result.append(schemas.SplitResponse(
            id=s.id,
            receipt_id=s.receipt_id,
            friend_id=s.friend_id,
            friend_name=friend.name if friend else "Unknown",
            friend_emoji=friend.emoji if friend else "👻",
            amount=s.amount,
            paid=s.paid,
            split_type=s.split_type,
            you_owe=s.you_owe
        ))
    return result

@app.patch("/splits/{split_id}/paid", response_model=schemas.SplitResponse)
def toggle_split_paid(split_id: int, payload: Optional[schemas.SplitPaidRequest] = None, db: Session = Depends(get_db)):
    split = db.query(models.Split).filter(models.Split.id == split_id).first()
    if not split:
        raise HTTPException(status_code=404, detail="Split not found")
    split.paid = not split.paid
    if payload and payload.payment_proof_base64:
        proof_str = payload.payment_proof_base64
        if not proof_str.startswith("data:"):
            proof_str = f"data:image/png;base64,{proof_str}"
        split.payment_proof = proof_str
    db.commit()
    db.refresh(split)

    friend = db.query(models.Friend).filter(models.Friend.id == split.friend_id).first()
    return schemas.SplitResponse(
        id=split.id,
        receipt_id=split.receipt_id,
        friend_id=split.friend_id,
        friend_name=friend.name if friend else "Unknown",
        friend_emoji=friend.emoji if friend else "👻",
        amount=split.amount,
        paid=split.paid,
        split_type=split.split_type,
        you_owe=split.you_owe,
        payment_proof=split.payment_proof
    )

@app.get("/splits/settled", response_model=List[schemas.SplitResponse])
def get_settled_splits(db: Session = Depends(get_db)):
    splits = db.query(models.Split).filter(models.Split.paid == True).order_by(models.Split.id.desc()).all()
    result = []
    for s in splits:
        friend = db.query(models.Friend).filter(models.Friend.id == s.friend_id).first()
        result.append(schemas.SplitResponse(
            id=s.id,
            receipt_id=s.receipt_id,
            friend_id=s.friend_id,
            friend_name=friend.name if friend else "Unknown",
            friend_emoji=friend.emoji if friend else "👻",
            amount=s.amount,
            paid=s.paid,
            split_type=s.split_type,
            you_owe=s.you_owe,
            payment_proof=s.payment_proof
        ))
    return result

@app.get("/splits/balances", response_model=schemas.BalancesResponse)
def get_balances(db: Session = Depends(get_db)):
    friends = db.query(models.Friend).all()
    owed_to_you = []
    you_owe = []

    for friend in friends:
        unpaid_owed_to_you = db.query(models.Split).filter(
            models.Split.friend_id == friend.id,
            models.Split.paid == False,
            models.Split.you_owe == False
        ).all()
        total_owed_to_you = sum(s.amount for s in unpaid_owed_to_you)

        unpaid_you_owe = db.query(models.Split).filter(
            models.Split.friend_id == friend.id,
            models.Split.paid == False,
            models.Split.you_owe == True
        ).all()
        total_you_owe = sum(s.amount for s in unpaid_you_owe)

        net = total_owed_to_you - total_you_owe
        if net > 0:
            sid = unpaid_owed_to_you[0].id if unpaid_owed_to_you else None
            owed_to_you.append(schemas.BalanceItem(
                friend_id=friend.id,
                friend_name=friend.name,
                friend_emoji=friend.emoji,
                amount=net,
                split_id=sid
            ))
        elif net < 0:
            sid = unpaid_you_owe[0].id if unpaid_you_owe else None
            you_owe.append(schemas.BalanceItem(
                friend_id=friend.id,
                friend_name=friend.name,
                friend_emoji=friend.emoji,
                amount=abs(net),
                split_id=sid
            ))

    # Calculate recovered (sum of all paid splits where friend owed you)
    paid_splits = db.query(models.Split).filter(
        models.Split.paid == True,
        models.Split.you_owe == False
    ).all()
    recovered_total = sum(s.amount for s in paid_splits)

    return schemas.BalancesResponse(
        owed_to_you=owed_to_you,
        you_owe=you_owe,
        recovered=recovered_total
    )
