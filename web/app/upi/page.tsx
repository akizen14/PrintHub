"use client";
import { useState, useEffect } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import QRCode from "qrcode";
import { api } from "@/utils/api";

/**
 * UPI Intent Payment Page - Dynamic
 * 
 * Accepts payment details via URL params or can be integrated with other components
 * 
 * URL Parameters:
 * - amount: Payment amount (required)
 * - orderId: Order/Transaction ID (optional)
 * - upiId: Receiver UPI ID (optional, uses default if not provided)
 * - merchantName: Merchant/Business name (optional)
 * - note: Payment note/description (optional)
 * 
 * Example: /upi?amount=100&orderId=ORDER123&note=Product%20Payment
 */

export default function UPIIntentPage() {
  const searchParams = useSearchParams();
  const router = useRouter();

  // Get dynamic values from URL params or use defaults
  const upiId = searchParams.get("upiId") || process.env.NEXT_PUBLIC_UPI_ID || "aditya.sonawane.005@okhdfcbank";
  const amount = searchParams.get("amount") || "50";
  const merchantName = searchParams.get("merchantName") || process.env.NEXT_PUBLIC_MERCHANT_NAME || "Aditya Sonawane";
  const orderId = searchParams.get("orderId") || `ORDER_${Date.now()}`;
  const note = searchParams.get("note") || "Payment";

  // State for UPI link and QR code
  const [upiLink, setUpiLink] = useState("");
  const [qrCode, setQrCode] = useState("");
  const [loading, setLoading] = useState(true);
  const [confirming, setConfirming] = useState(false);
  const [transactionId, setTransactionId] = useState("");
  const [showTransactionInput, setShowTransactionInput] = useState(false);

  // Generate UPI deep link and QR code when params change
  useEffect(() => {
    setLoading(true);
    
    // Create transaction note with order ID
    const transactionNote = `${note} - ${orderId}`;
    
    // Generate UPI deep link
    const link = `upi://pay?pa=${upiId}&pn=${encodeURIComponent(merchantName)}&am=${amount}&cu=INR&tn=${encodeURIComponent(transactionNote)}`;
    setUpiLink(link);

    // Generate QR code locally
    QRCode.toDataURL(link, {
      width: 200,
      margin: 2,
      color: {
        dark: "#000000",
        light: "#FFFFFF",
      },
    })
      .then((dataUrl) => {
        setQrCode(dataUrl);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error generating QR code:", err);
        setLoading(false);
      });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Handle pay button click
  const handlePayClick = () => {
    if (upiLink) {
      window.location.href = upiLink;
    }
  };

  // Handle manual confirmation
  const handleConfirmPayment = async () => {
    // Validate order ID (should be a UUID, not the default placeholder)
    if (!orderId || !orderId.includes('-')) {
      alert("Invalid order ID. Please create an order first.");
      return;
    }

    setConfirming(true);
    try {
      // Call the payment confirmation API with optional transaction ID
      const payload = transactionId.trim() ? { transactionId: transactionId.trim() } : undefined;
      await api.confirmPayment(orderId, payload);
      
      // Redirect to order details page
      router.push(`/orders/${orderId}`);
    } catch (error) {
      console.error("Failed to confirm payment:", error);
      const errorMessage = error instanceof Error ? error.message : "Failed to confirm payment";
      alert(`Payment confirmation failed: ${errorMessage}`);
    } finally {
      setConfirming(false);
    }
  };

  const handleIHavePaid = () => {
    setShowTransactionInput(true);
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-purple-50 to-indigo-100 flex items-center justify-center p-6">
      <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full mx-auto">
        {/* Heading */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            UPI Payment
          </h1>
          <p className="text-gray-500">Fast, secure & instant payment</p>
        </div>

        {/* Payment Details */}
        <div className="space-y-3 mb-6">
          {orderId && (
            <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
              <p className="text-xs text-blue-600 mb-1 uppercase tracking-wide">Order ID</p>
              <p className="text-sm font-mono text-blue-900">{orderId}</p>
            </div>
          )}
          
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-xs text-gray-500 mb-1 uppercase tracking-wide">Pay To</p>
            <p className="text-sm font-semibold text-gray-900">{merchantName}</p>
            <p className="text-xs text-gray-500 mt-1">{upiId}</p>
          </div>

          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-xs text-gray-500 mb-1 uppercase tracking-wide">Amount</p>
            <p className="text-3xl font-bold text-purple-600">₹{amount}</p>
          </div>
        </div>

        {/* QR Code */}
        <div className="bg-gray-100 rounded-lg p-6 mb-6 flex flex-col items-center justify-center">
          {loading ? (
            <div className="text-center">
              <div className="w-[200px] h-[200px] bg-gray-200 rounded-lg flex items-center justify-center mb-3">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
              </div>
              <p className="text-xs text-gray-500">Generating QR code...</p>
            </div>
          ) : qrCode ? (
            <>
              <img 
                src={qrCode} 
                alt="UPI QR Code" 
                className="w-[200px] h-[200px] mb-3"
              />
              <p className="text-sm font-medium text-gray-700">Scan to Pay via UPI</p>
            </>
          ) : (
            <div className="text-center">
              <div className="w-[200px] h-[200px] bg-red-100 rounded-lg flex items-center justify-center mb-3">
                <p className="text-red-500 text-sm">Failed to generate QR</p>
              </div>
              <p className="text-xs text-red-500">Please try again</p>
            </div>
          )}
        </div>

        {/* Pay Button */}
        <button 
          onClick={handlePayClick}
          className="w-full bg-purple-600 text-white py-4 px-6 rounded-lg font-semibold hover:bg-purple-700 active:scale-98 transition-all shadow-md hover:shadow-lg"
        >
          Pay via UPI App
        </button>

        {/* Transaction ID Input (shown after clicking I have paid) */}
        {showTransactionInput ? (
          <div className="mt-4 space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                UPI Transaction ID (Optional)
              </label>
              <input
                type="text"
                value={transactionId}
                onChange={(e) => setTransactionId(e.target.value)}
                placeholder="e.g., 123456789012"
                className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-purple-500 focus:outline-none"
              />
              <p className="text-xs text-gray-500 mt-1">
                Enter your UPI transaction/reference ID for verification (optional)
              </p>
            </div>
            <button 
              onClick={handleConfirmPayment}
              disabled={confirming}
              className="w-full bg-green-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-green-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {confirming ? "Confirming Payment..." : "Confirm Payment"}
            </button>
            <button 
              onClick={() => setShowTransactionInput(false)}
              disabled={confirming}
              className="w-full border-2 border-gray-300 text-gray-700 py-2 px-6 rounded-lg font-medium hover:bg-gray-50 transition-all"
            >
              Back
            </button>
          </div>
        ) : (
          <button 
            onClick={handleIHavePaid}
            className="w-full mt-3 border-2 border-purple-600 text-purple-600 py-3 px-6 rounded-lg font-semibold hover:bg-purple-50 transition-all"
          >
            I have paid
          </button>
        )}

        {/* Supported Apps Note */}
        <div className="mt-6 text-center">
          <p className="text-xs text-gray-400 mb-1">Supports</p>
          <p className="text-sm text-gray-500">Google Pay / PhonePe / Paytm</p>
        </div>
      </div>
    </main>
  );
}
