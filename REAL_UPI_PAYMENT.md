# Real UPI Payment Integration - PrintHub

## ✅ Implementation Complete

Real UPI payment system integrated with transaction ID tracking and payment verification.

---

## 🎯 Features Implemented

### **1. Real UPI QR Code Generation**
- Dynamic QR codes generated using `qrcode` package
- Contains actual UPI payment link: `upi://pay?pa=UPI_ID&am=AMOUNT&...`
- Works with all UPI apps (GPay, PhonePe, Paytm, etc.)
- QR code updates based on order amount

### **2. Payment Verification**
- Manual verification with optional transaction ID
- Transaction ID stored in database
- Payment timestamp tracking
- Order status automatically updated after payment

### **3. Backend Integration**
- New fields added to Order model:
  - `transactionId` (Optional[str])
  - `paidAt` (Optional[int])
- Enhanced payment confirmation endpoint
- Payment status tracking (unpaid/paid/refunded)

### **4. Frontend Flow**
- Order creation → Redirect to UPI payment page
- Display QR code + UPI deep link
- Transaction ID input (optional)
- Payment confirmation → Order details page

---

## 📋 Payment Flow

### **Step 1: Create Order**
```
Student fills form → Uploads file → Clicks "Place Order"
↓
Order created with status: Pending, paymentStatus: unpaid
↓
Redirects to: /upi?amount=X&orderId=UUID&note=PrintHub Order
```

### **Step 2: UPI Payment Page**
```
┌────────────────────────────────────┐
│       UPI Payment                  │
│   Fast, secure & instant payment   │
│                                    │
│  Order ID: abc123...               │
│                                    │
│  Pay To: Aditya Sonawane           │
│  aditya.sonawane.005@okhdfcbank    │
│                                    │
│  Amount: ₹50.00                    │
│                                    │
│  [QR CODE]                         │
│  Scan to Pay via UPI               │
│                                    │
│  [Pay via UPI App]                 │
│  [I have paid]                     │
│                                    │
│  Supports: GPay / PhonePe / Paytm  │
└────────────────────────────────────┘
```

### **Step 3: User Pays**
1. User scans QR code OR clicks "Pay via UPI App"
2. UPI app opens with pre-filled payment details
3. User completes payment in their UPI app
4. User returns to website

### **Step 4: Confirm Payment**
```
User clicks "I have paid"
↓
Transaction ID input appears (optional)
↓
User enters UPI transaction ID (optional)
↓
Clicks "Confirm Payment"
↓
Backend API called: POST /orders/{id}/confirm-payment
↓
Order updated:
  - paymentStatus: paid
  - status: Queued
  - transactionId: (if provided)
  - paidAt: current timestamp
↓
Redirects to order details page
```

### **Step 5: Order Details**
```
Order page shows:
- Payment Status: Paid ✓
- Transaction ID: 123456789012
- Paid At: 11/6/2025, 2:47:04 AM
- Order Status: Queued (ready for printing)
```

---

## 🔧 Technical Implementation

### **Backend Changes**

#### **1. Models (`backend/app/models.py`)**
```python
class Order(BaseModel):
    # ... existing fields ...
    transactionId: Optional[str] = None  # NEW
    paidAt: Optional[int] = None         # NEW
    
class PaymentConfirmation(BaseModel):  # NEW
    transactionId: Optional[str] = None
    paymentMethod: Optional[str] = "UPI"
    notes: Optional[str] = None
```

#### **2. API Endpoint (`backend/app/routers/orders.py`)**
```python
@router.post("/{order_id}/confirm-payment", response_model=Order)
async def confirm_payment(
    order_id: str, 
    payment_data: Optional[PaymentConfirmation] = None
):
    """
    Confirm payment for an order.
    Accepts optional transaction ID for tracking.
    """
    # Validate order exists and is pending
    # Update payment status to 'paid'
    # Update order status to 'Queued'
    # Store transaction ID if provided
    # Record payment timestamp
```

### **Frontend Changes**

#### **1. UPI Payment Page (`web/app/upi/page.tsx`)**
```typescript
// Real UPI ID from environment or hardcoded
const upiId = "aditya.sonawane.005@okhdfcbank";

// Generate UPI deep link
const link = `upi://pay?pa=${upiId}&pn=${merchantName}&am=${amount}&cu=INR&tn=${note}`;

// Generate QR code using qrcode package
QRCode.toDataURL(link, options).then(setQrCode);

// Transaction ID input (shown after "I have paid")
<input
  type="text"
  value={transactionId}
  onChange={(e) => setTransactionId(e.target.value)}
  placeholder="e.g., 123456789012"
/>

// Confirm payment with optional transaction ID
await api.confirmPayment(orderId, { 
  transactionId: transactionId.trim() || undefined 
});
```

#### **2. Order Creation (`web/app/order/new/page.tsx`)**
```typescript
// After order creation, redirect to UPI payment
const order = await api.createOrderWithFile(selectedFile, orderData);
router.push(`/upi?amount=${order.priceTotal}&orderId=${order.id}&note=PrintHub Order`);
```

#### **3. Order Details (`web/app/orders/[id]/page.tsx`)**
```typescript
// Display payment information if transaction ID exists
{order.transactionId && (
  <div className="bg-green-50 border border-green-200">
    <p>Transaction ID: {order.transactionId}</p>
    <p>Paid At: {new Date(order.paidAt * 1000).toLocaleString()}</p>
  </div>
)}

// Show "Complete Payment" button if unpaid
{order.paymentStatus === "unpaid" && (
  <a href={`/upi?amount=${order.priceTotal}&orderId=${order.id}`}>
    Complete Payment
  </a>
)}
```

---

## 🔑 Configuration

### **UPI ID Setup**

**Option 1: Environment Variable (Recommended)**
```bash
# .env.local
NEXT_PUBLIC_UPI_ID=your-upi-id@bank
NEXT_PUBLIC_MERCHANT_NAME=Your Name
```

**Option 2: Hardcoded (Current)**
```typescript
// web/app/upi/page.tsx
const upiId = "aditya.sonawane.005@okhdfcbank";
const merchantName = "Aditya Sonawane";
```

### **Change UPI Details**
Edit `web/app/upi/page.tsx`:
```typescript
const upiId = searchParams.get("upiId") || 
              process.env.NEXT_PUBLIC_UPI_ID || 
              "your-upi-id@bank";  // ← Change this

const merchantName = searchParams.get("merchantName") || 
                     process.env.NEXT_PUBLIC_MERCHANT_NAME || 
                     "Your Name";  // ← Change this
```

---

## 🧪 Testing

### **Test Complete Flow**

1. **Create Order:**
   ```
   - Go to http://localhost:3000
   - Click "New Order"
   - Fill form and upload file
   - Click "Place Order"
   ```

2. **Payment Page:**
   ```
   - Verify QR code displays
   - Verify UPI ID shows: aditya.sonawane.005@okhdfcbank
   - Verify amount matches order total
   ```

3. **Make Payment:**
   ```
   - Scan QR code with UPI app
   - OR click "Pay via UPI App" (mobile only)
   - Complete payment in UPI app
   ```

4. **Confirm Payment:**
   ```
   - Click "I have paid"
   - Enter transaction ID (optional): 123456789012
   - Click "Confirm Payment"
   ```

5. **Verify Order:**
   ```
   - Redirects to order details
   - Status shows: Queued
   - Payment Status: Paid
   - Transaction ID displayed
   - Paid timestamp shown
   ```

### **Test Without Transaction ID**
```
- Follow same steps
- Click "I have paid"
- Leave transaction ID blank
- Click "Confirm Payment"
- Payment still confirmed (transaction ID optional)
```

---

## 📊 Database Schema

### **Order Document**
```json
{
  "id": "abc-123-def-456",
  "studentName": "John Doe",
  "mobile": "9876543210",
  "fileName": "document.pdf",
  "pages": 10,
  "copies": 1,
  "color": "bw",
  "sides": "single",
  "size": "A4",
  "priceTotal": 50.00,
  "status": "Queued",
  "paymentStatus": "paid",
  "transactionId": "123456789012",  // NEW - Optional
  "paidAt": 1730000000,             // NEW - Unix timestamp
  "queueType": "normal",
  "priorityIndex": 1000,
  "createdAt": 1729999000,
  "updatedAt": 1730000000
}
```

---

## 🔐 Security Considerations

### **Current Implementation (Manual Verification)**
- ✅ Transaction ID stored for reference
- ✅ Payment timestamp recorded
- ⚠️ No automatic verification (manual trust-based)
- ⚠️ Admin should verify transaction ID in UPI app

### **Production Recommendations**

**Option 1: Payment Gateway Integration**
- Integrate Razorpay/Cashfree/PhonePe Business
- Automatic payment verification via webhooks
- Real-time payment status updates
- Refund support

**Option 2: Bank API Integration**
- Direct integration with bank's UPI API
- Verify transaction ID against bank records
- Automated reconciliation

**Option 3: Enhanced Manual Verification**
- Admin panel to verify transaction IDs
- Mark payments as verified/unverified
- Require admin approval before printing

---

## 🚀 Future Enhancements

### **Immediate Improvements**
1. **Admin Verification Dashboard**
   - List all pending payments
   - Verify transaction IDs manually
   - Approve/reject payments

2. **Payment Receipts**
   - Generate PDF receipts
   - Email receipts to students
   - Download receipt from order page

3. **Payment History**
   - View all payments
   - Filter by date/status
   - Export payment reports

### **Advanced Features**
1. **Automated Verification**
   - Integrate with payment gateway
   - Webhook for real-time updates
   - Automatic order processing

2. **Multiple Payment Methods**
   - Credit/Debit cards
   - Net banking
   - Wallets (Paytm, PhonePe)

3. **Refund System**
   - Initiate refunds from admin
   - Track refund status
   - Automatic refund processing

---

## 📝 API Documentation

### **Confirm Payment Endpoint**

**POST** `/orders/{order_id}/confirm-payment`

**Request Body (Optional):**
```json
{
  "transactionId": "123456789012",
  "paymentMethod": "UPI",
  "notes": "Payment via GPay"
}
```

**Response:**
```json
{
  "id": "abc-123",
  "status": "Queued",
  "paymentStatus": "paid",
  "transactionId": "123456789012",
  "paidAt": 1730000000,
  ...
}
```

**Error Responses:**
- `404`: Order not found
- `400`: Order not in Pending status
- `400`: Payment already confirmed

---

## ✅ Verification Checklist

- [x] UPI QR code generates correctly
- [x] QR code contains real UPI payment link
- [x] Payment link works with UPI apps
- [x] Transaction ID can be entered (optional)
- [x] Payment confirmation updates order status
- [x] Transaction ID stored in database
- [x] Payment timestamp recorded
- [x] Order details show payment info
- [x] "Complete Payment" button for unpaid orders
- [x] Backend validates payment status
- [x] API accepts optional transaction ID

---

## 🎯 Summary

**What Works:**
- ✅ Real UPI QR codes with actual payment links
- ✅ Dynamic amount based on order total
- ✅ Transaction ID tracking (optional)
- ✅ Payment timestamp recording
- ✅ Order status updates after payment
- ✅ Complete payment flow from order to confirmation

**What's Manual:**
- ⚠️ Payment verification (trust-based)
- ⚠️ Transaction ID validation (not verified against bank)
- ⚠️ Admin should manually verify payments

**For Production:**
- 🔄 Integrate payment gateway for automatic verification
- 🔄 Add admin verification dashboard
- 🔄 Implement refund system
- 🔄 Add payment receipts

---

**Status:** ✅ Real UPI Payment System Implemented  
**Version:** 1.0.0  
**Date:** November 6, 2025  
**UPI ID:** aditya.sonawane.005@okhdfcbank
