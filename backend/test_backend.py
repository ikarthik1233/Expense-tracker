import sys
import os
import json
from fastapi.testclient import TestClient

# Ensure UTF-8 output encoding for emojis
sys.stdout.reconfigure(encoding='utf-8')

from main import app, models, engine

# Create tables for testing
models.Base.metadata.create_all(bind=engine)

client = TestClient(app)

def run_tests():
    print("--- Starting Backend API Verification ---")

    # 1. Create Friends
    print("1. Testing POST /friends...")
    res1 = client.post("/friends", json={"name": "Rahul"})
    assert res1.status_code == 200, f"Error: {res1.text}"
    friend1 = res1.json()
    print(f"   Created friend: {friend1}")

    res2 = client.post("/friends", json={"name": "Priya"})
    assert res2.status_code == 200
    friend2 = res2.json()
    print(f"   Created friend: {friend2}")

    # 2. Get Friends
    print("2. Testing GET /friends...")
    res_friends = client.get("/friends")
    assert res_friends.status_code == 200
    assert len(res_friends.json()) >= 2
    print(f"   Friends count: {len(res_friends.json())}")

    # 3. Create Receipt
    print("3. Testing POST /receipts...")
    receipt_data = {
        "merchant": "Graveyard Bistro",
        "date": "2026-08-18",
        "total": 600.0,
        "category": "Food",
        "items": [
            {"name": "Phantom Pizza", "price": 450.0},
            {"name": "Potion Punch", "price": 150.0}
        ],
        "image_base64": None
    }
    res_rec = client.post("/receipts", json=receipt_data)
    assert res_rec.status_code == 200, f"Error: {res_rec.text}"
    receipt = res_rec.json()
    print(f"   Created receipt ID: {receipt['id']}, Merchant: {receipt['merchant']}")

    # 4. Get Receipts
    print("4. Testing GET /receipts...")
    res_recs = client.get("/receipts?month=2026-08")
    assert res_recs.status_code == 200
    assert len(res_recs.json()) >= 1
    print(f"   Receipts found: {len(res_recs.json())}")

    # 5. Get Summary
    print("5. Testing GET /receipts/summary...")
    res_sum = client.get("/receipts/summary?month=2026-08")
    assert res_sum.status_code == 200
    summary = res_sum.json()
    print(f"   Summary total: {summary['total_this_month']}, top merchants: {summary['top_merchants']}")

    # 6. Create Splits
    print("6. Testing POST /splits...")
    split_payload = {
        "receipt_id": receipt["id"],
        "split_type": "equal",
        "splits": [
            {"friend_id": friend1["id"], "amount": 200.0, "you_owe": False},
            {"friend_id": friend2["id"], "amount": 200.0, "you_owe": False}
        ]
    }
    res_splits = client.post("/splits", json=split_payload)
    assert res_splits.status_code == 200, f"Error: {res_splits.text}"
    created_splits = res_splits.json()
    print(f"   Created {len(created_splits)} splits.")

    # 7. Get Balances
    print("7. Testing GET /splits/balances...")
    res_bal = client.get("/splits/balances")
    assert res_bal.status_code == 200
    balances = res_bal.json()
    print(f"   Balances: Owed to you: {balances['owed_to_you']}, You owe: {balances['you_owe']}")

    # 8. Toggle Paid Status
    print("8. Testing PATCH /splits/{id}/paid...")
    split_id = created_splits[0]["id"]
    res_toggle = client.patch(f"/splits/{split_id}/paid")
    assert res_toggle.status_code == 200
    print(f"   Toggled split {split_id} paid status to: {res_toggle.json()['paid']}")

    # 9. Test OCR scan
    print("9. Testing POST /receipts/scan...")
    mock_b64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
    res_scan = client.post("/receipts/scan", json={"image_base64": mock_b64})
    assert res_scan.status_code == 200
    scan_res = res_scan.json()
    print(f"   Scan response merchant: {scan_res['merchant']}, total: {scan_res['total']}")

    print("--- ALL BACKEND TESTS PASSED SUCCESSFULLY 🎉 ---")

if __name__ == "__main__":
    run_tests()
