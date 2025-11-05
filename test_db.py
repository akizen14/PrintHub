from tinydb import TinyDB, Query

db = TinyDB('data/orders.json')
orders = db.all()

print(f"Total orders: {len(orders)}")
if orders:
    first = orders[0]
    print(f"\nFirst order keys: {list(first.keys())}")
    print(f"ID: {first.get('id')}")
    print(f"fileName: {first.get('fileName')}")
    print(f"filePath: {first.get('filePath')}")
    print(f"\nFull order:")
    for key, value in first.items():
        print(f"  {key}: {value}")
