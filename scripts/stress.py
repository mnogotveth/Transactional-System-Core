import threading, requests

URL = "http://localhost:8000/api/transfer"
PAYLOAD = {"source_wallet_id": 2, "destination_wallet_id": 3, "amount": "200.00"}

def fire():
    resp = requests.post(URL, json=PAYLOAD)
    print(resp.status_code, resp.text)

threads = [threading.Thread(target=fire) for _ in range(10)]
[t.start() for t in threads]
[t.join() for t in threads]
