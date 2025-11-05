# Performance Optimization Guide

## Current Performance Issues

If the application is slow, here are the most common causes and solutions:

## Quick Fixes

### 1. Reduce Polling Frequency

**Web Frontend** - Reduce polling from 3s to 5-10s:

```typescript
// In app/orders/[id]/page.tsx
useEffect(() => {
  loadOrder();
  
  // Change from 3000 to 10000 (10 seconds)
  const interval = setInterval(loadOrder, 10000);
  return () => clearInterval(interval);
}, [orderId]);
```

**Admin App** - Reduce from 2s to 5s:

```python
# In admin-app/main.py
# Change from 2000 to 5000 (5 seconds)
self.poll_timer.start(5000)
```

### 2. Optimize Backend Queries

Add caching to frequently accessed data:

```python
# backend/app/routers/orders.py
from functools import lru_cache
import time

# Cache rates for 60 seconds
@lru_cache(maxsize=1)
def get_cached_rates(timestamp: int):
    return get_single("rates")

@router.post("", response_model=Order)
async def create_order(order_in: OrderIn):
    # Use cached rates
    cache_key = int(time.time() / 60)  # Cache per minute
    rates_data = get_cached_rates(cache_key)
    # ... rest of code
```

### 3. Add Database Indexing

TinyDB is lightweight but can be slow with many records. Consider switching to SQLite for better performance:

```bash
pip install sqlalchemy
```

### 4. Enable Compression

Add gzip compression to FastAPI:

```python
# backend/app/main.py
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

### 5. Optimize Next.js Build

```bash
cd web
npm run build
npm start  # Use production build instead of dev
```

Production build is 10x faster than development mode.

## Detailed Optimizations

### Backend Optimizations

#### 1. Connection Pooling

```python
# backend/app/storage.py
from threading import Lock

_db_cache = {}
_db_lock = Lock()

def get_db(table_name: str) -> TinyDB:
    """Get cached TinyDB instance"""
    with _db_lock:
        if table_name not in _db_cache:
            db_path = DATA_DIR / f"{table_name}.json"
            _db_cache[table_name] = TinyDB(db_path)
        return _db_cache[table_name]
```

#### 2. Batch Operations

```python
def update_multiple(table_name: str, updates: List[Dict]):
    """Batch update multiple documents"""
    db = get_db(table_name)
    Item = Query()
    
    for update in updates:
        doc_id = update.pop("id")
        db.update(update, Item.id == doc_id)
    
    db.close()
```

#### 3. Async Database Operations

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=4)

async def async_find_all(table_name: str):
    """Non-blocking database read"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, find_all, table_name)
```

### Frontend Optimizations

#### 1. Implement Debouncing

```typescript
// lib/hooks/useDebounce.ts
import { useEffect, useState } from 'react';

export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}
```

#### 2. Add Request Caching

```typescript
// lib/api.ts
const cache = new Map<string, { data: any; timestamp: number }>();
const CACHE_TTL = 5000; // 5 seconds

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const cacheKey = `${endpoint}${JSON.stringify(options)}`;
  const cached = cache.get(cacheKey);
  
  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    return cached.data;
  }
  
  const response = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`API Error: ${response.statusText}`);
  }

  const data = await response.json();
  cache.set(cacheKey, { data, timestamp: Date.now() });
  
  return data;
}
```

#### 3. Lazy Load Components

```typescript
// app/orders/page.tsx
import dynamic from 'next/dynamic';

const OrderList = dynamic(() => import('@/components/OrderList'), {
  loading: () => <p>Loading orders...</p>,
  ssr: false
});
```

### Admin App Optimizations

#### 1. Reduce UI Updates

```python
# Only update UI when data actually changes
def poll_data(self):
    try:
        response = requests.get(f"{API_BASE}/orders")
        if response.status_code == 200:
            new_orders = response.json()
            
            # Only update if changed
            if new_orders != self.orders:
                self.orders = new_orders
                self.update_queue_lists()
    except Exception as e:
        print(f"Poll error: {e}")
```

#### 2. Use QTimer Efficiently

```python
# Pause polling when window is minimized
def changeEvent(self, event):
    if event.type() == QEvent.Type.WindowStateChange:
        if self.isMinimized():
            self.poll_timer.stop()
        else:
            self.poll_timer.start(2000)
```

#### 3. Optimize List Updates

```python
def update_queue_lists(self):
    """Only update changed items"""
    # Store current items
    current_items = {
        'urgent': [self.urgent_list.item(i).data(Qt.ItemDataRole.UserRole) 
                   for i in range(self.urgent_list.count())],
        # ... other queues
    }
    
    # Only clear and rebuild if different
    urgent_orders = [o for o in self.orders if o['queueType'] == 'urgent']
    if urgent_orders != current_items['urgent']:
        self.urgent_list.clear()
        # Rebuild list
```

## Network Optimizations

### 1. Use HTTP/2

```python
# backend/app/main.py
# Run with HTTP/2 support
# uvicorn app.main:app --http h2
```

### 2. Enable Keep-Alive

```python
# admin-app/main.py
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

session = requests.Session()
retry = Retry(total=3, backoff_factor=0.3)
adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
session.mount('http://', adapter)

# Use session instead of requests
response = session.get(f"{API_BASE}/orders")
```

### 3. Compress Responses

```python
# backend/app/main.py
from fastapi.responses import ORJSONResponse

app = FastAPI(default_response_class=ORJSONResponse)
```

## Database Optimization

### Option 1: Switch to SQLite

```python
# backend/app/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///data/printhub.db', echo=False)
SessionLocal = sessionmaker(bind=engine)
```

### Option 2: Optimize TinyDB

```python
# Use in-memory caching
from tinydb.storages import MemoryStorage
from tinydb.middlewares import CachingMiddleware

db = TinyDB('data/orders.json', storage=CachingMiddleware(JSONStorage))
```

## Monitoring Performance

### Add Timing Middleware

```python
# backend/app/main.py
import time
from fastapi import Request

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    print(f"{request.url.path}: {process_time:.3f}s")
    return response
```

### Frontend Performance Monitoring

```typescript
// lib/api.ts
async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const start = performance.now();
  
  const response = await fetch(`${BASE_URL}${endpoint}`, options);
  
  const duration = performance.now() - start;
  if (duration > 1000) {
    console.warn(`Slow request: ${endpoint} took ${duration}ms`);
  }
  
  return response.json();
}
```

## Production Deployment

### 1. Use Production Server

Instead of development server:

```bash
# Backend
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Web
npm run build
npm start
```

### 2. Add Caching Layer

Use Redis for caching:

```bash
pip install redis
```

```python
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def get_cached_orders():
    cached = redis_client.get('orders')
    if cached:
        return json.loads(cached)
    
    orders = find_all("orders")
    redis_client.setex('orders', 10, json.dumps(orders))  # Cache for 10s
    return orders
```

### 3. Load Balancing

Run multiple backend instances:

```bash
# Terminal 1
uvicorn app.main:app --port 8000

# Terminal 2
uvicorn app.main:app --port 8001

# Terminal 3
uvicorn app.main:app --port 8002
```

Use nginx for load balancing.

## Troubleshooting Slow Performance

### Check 1: CPU Usage

```bash
# Windows
tasklist /FI "IMAGENAME eq python.exe"
tasklist /FI "IMAGENAME eq node.exe"
```

### Check 2: Memory Usage

```python
# Add to backend
import psutil

@app.get("/health")
async def health_check():
    return {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage('/').percent
    }
```

### Check 3: Network Latency

```bash
# Test API response time
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/orders
```

### Check 4: Database Size

```bash
# Check JSON file sizes
ls -lh data/
```

If files are >10MB, consider switching to SQLite.

## Quick Performance Checklist

- [ ] Use production build for Next.js (`npm run build`)
- [ ] Reduce polling frequency (5-10s instead of 2-3s)
- [ ] Enable gzip compression
- [ ] Add request caching
- [ ] Use connection pooling
- [ ] Optimize database queries
- [ ] Monitor slow requests
- [ ] Use production server (gunicorn/pm2)
- [ ] Add Redis caching layer
- [ ] Optimize image/asset sizes

## Expected Performance

**Development Mode:**
- API response: 50-200ms
- Page load: 1-3s
- Polling overhead: Minimal

**Production Mode:**
- API response: 10-50ms
- Page load: 0.5-1s
- Polling overhead: Negligible

If you're seeing slower performance, check:
1. Antivirus scanning files
2. Other applications using resources
3. Network connectivity
4. Database file size
