# Payment UPI Integration

This document describes the payment integration for PrintHub, ensuring that only paid orders enter the print queue.

## Overview

The payment integration adds a **payment verification step** between order creation and queue entry. This ensures that:
- Orders are created with payment status tracking
- Only paid orders appear in the admin print queue
- Students must complete payment before their orders can be printed

## Payment Flow

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  Create Order   │─────▶│   UPI Payment   │─────▶│ Confirm Payment │─────▶│  Print Queue    │
│   (Pending)     │      │    (QR Code)    │      │   (Queued)      │      │   (Admin App)   │
│  unpaid status  │      │  "I have paid"  │      │  paid status    │      │  Paid orders    │
└─────────────────┘      └─────────────────┘      └─────────────────┘      └─────────────────┘
```

### Step-by-Step Flow

1. **Student creates order** (Web Interface)
   - Order is created with status: `Pending`
   - Payment status: `unpaid`
   - Automatically redirected to UPI payment page

2. **UPI Payment Page**
   - Shows QR code for UPI payment
   - Displays order ID and amount
   - Has "Pay via UPI App" button (opens UPI apps)
   - Has "I have paid" button

3. **Payment Confirmation**
   - Student clicks "I have paid" after completing payment
   - API confirms payment: `POST /orders/{orderId}/confirm-payment`
   - Order status changes: `Pending` → `Queued`
   - Payment status changes: `unpaid` → `paid`
   - Student redirected to order details page

4. **Print Queue (Admin App)**
   - Admin only sees orders with status: `Queued`, `Printing`, or `Ready`
   - All visible orders have `paymentStatus: paid`
   - Admin can print these orders

## API Changes

### New Field: `paymentStatus`

All orders now have a `paymentStatus` field with three possible values:
- `unpaid` - Payment not completed (default for new orders)
- `paid` - Payment confirmed
- `refunded` - Payment was refunded (for future use)

### New Endpoint: Confirm Payment

```http
POST /orders/{orderId}/confirm-payment
```

**Response:**
```json
{
  "id": "order-uuid",
  "status": "Queued",
  "paymentStatus": "paid",
  ...
}
```

**Errors:**
- `404` - Order not found
- `400` - Order is not in Pending status
- `400` - Payment already confirmed

### Updated Order Model

```typescript
interface Order {
  // ... existing fields
  status: "Pending" | "Queued" | "Printing" | "Ready" | "Collected" | "Cancelled";
  paymentStatus: "unpaid" | "paid" | "refunded";
}
```

## Frontend Changes

### Order Creation Flow

**Before:**
```
Create Order → Order Details Page
```

**After:**
```
Create Order → UPI Payment Page → Order Details Page
              (automatic redirect)  (after payment confirmation)
```

### UPI Payment Page

URL: `/upi?amount=100&orderId=abc123&note=Print Order`

Features:
- Dynamic UPI QR code generation
- Order ID and amount display
- "Pay via UPI App" button (opens phone's UPI apps)
- "I have paid" button (confirms payment via API)
- Error handling for payment confirmation

### Order Details Page

New features:
- Payment status badge (Paid/Unpaid/Refunded)
- "Complete Payment" button for unpaid orders
- Links directly to UPI payment page

## Admin App Changes

### Queue Filtering

**Before:**
```python
# Loaded all orders: Pending, Queued, Printing, Ready
GET /orders?status=Pending|Queued|Printing|Ready
```

**After:**
```python
# Only loads paid orders: Queued, Printing, Ready
GET /orders?status=Queued|Printing|Ready
```

### Button States

- **Print button**: Only enabled for `Queued` orders (paid orders)
- **Ready button**: Enabled for `Printing` orders
- **Collected button**: Enabled for `Ready` orders

## Database Migration

For existing databases, run the migration script:

```bash
python migrate_payment_status.py
```

This script:
- Adds `paymentStatus` field to all existing orders
- Sets `paid` for orders with status: Queued, Printing, Ready, Collected
- Sets `unpaid` for orders with status: Pending
- Updates `data/orders.json` in place

## Testing

Run the test suite to verify the integration:

```bash
# Make sure backend is running first
cd backend
uvicorn app.main:app --reload

# In another terminal
python test_payment_integration.py
```

Tests cover:
1. Order creation with unpaid status
2. Payment confirmation moving order to queue
3. Admin queue showing only paid orders
4. Preventing double payment confirmation

## Development Setup

### Seed Data

The seed endpoint creates orders with mixed payment statuses:

```bash
curl -X POST http://localhost:8000/seed
```

Creates:
- 3 paid orders (Alice, Bob, Diana) - Status: `Queued`
- 1 unpaid order (Charlie) - Status: `Pending`

This allows testing both paid and unpaid order scenarios.

### Manual Testing

1. **Create an order:**
   ```
   http://localhost:3000/order/new
   ```
   - Fill in details and submit
   - Should redirect to UPI payment page

2. **Complete payment:**
   - On UPI page, click "I have paid"
   - Should redirect to order details
   - Payment status should show as "Paid"

3. **Check admin app:**
   - Open admin app: `python admin-app/main.py`
   - Login with password: `printhub2025`
   - Verify order appears in queue with Queued status

## Configuration

### UPI Settings

UPI payment details are configured via environment variables:

```env
NEXT_PUBLIC_UPI_ID=aditya.sonawane.005@okhdfcbank
NEXT_PUBLIC_MERCHANT_NAME=Aditya Sonawane
```

Or can be overridden via URL parameters:
```
/upi?upiId=merchant@bank&merchantName=My%20Store&amount=100
```

## Security Considerations

⚠️ **Important:** This is a manual confirmation system. For production use:

1. **Integrate real payment gateway** (Razorpay, PayU, etc.)
2. **Verify payments server-side** using payment gateway webhooks
3. **Add transaction IDs** to track actual payments
4. **Implement refund workflow** for cancelled orders
5. **Add payment logs** for audit trail

Current implementation is suitable for:
- Development/testing
- Manual payment verification scenarios
- Small-scale operations with manual oversight

## Troubleshooting

### Orders not appearing in admin queue

**Problem:** Created an order but it doesn't show in admin app

**Solution:** 
- Check if payment was confirmed
- Verify order status is `Queued` (not `Pending`)
- Check payment status is `paid`
- Admin app filters out unpaid orders

### Payment confirmation fails

**Problem:** "I have paid" button shows error

**Possible causes:**
1. Order is not in `Pending` status
2. Payment already confirmed
3. Invalid order ID
4. Backend not running

**Solution:** Check browser console and backend logs

### Migration issues

**Problem:** Old orders don't have payment status

**Solution:** Run migration script:
```bash
python migrate_payment_status.py
```

## Future Enhancements

- [ ] Real payment gateway integration (Razorpay/PayU)
- [ ] Webhook verification for automatic confirmation
- [ ] Payment transaction logs
- [ ] Refund workflow
- [ ] Multiple payment methods (UPI, Card, Wallet)
- [ ] Payment reminders
- [ ] Automated payment verification
- [ ] Receipt generation

## Related Files

- Backend:
  - `backend/app/models.py` - Order models with paymentStatus
  - `backend/app/routers/orders.py` - Payment confirmation endpoint
  - `backend/app/main.py` - Seed data with payment statuses

- Frontend:
  - `web/utils/api.ts` - API client with confirmPayment()
  - `web/app/upi/page.tsx` - UPI payment page
  - `web/app/order/new/page.tsx` - Order creation with redirect
  - `web/app/orders/[id]/page.tsx` - Order details with payment status

- Admin:
  - `admin-app/main.py` - Queue filtering for paid orders

- Scripts:
  - `migrate_payment_status.py` - Database migration
  - `test_payment_integration.py` - Integration tests
