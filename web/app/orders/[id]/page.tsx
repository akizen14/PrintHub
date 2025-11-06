"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api, Order, Printer } from "@/utils/api";
import { formatPrice } from "@/utils/price";

const STATUS_COLORS = {
  Pending: "bg-gray-100 text-gray-800",
  Queued: "bg-blue-100 text-blue-800",
  Printing: "bg-amber-100 text-amber-800",
  Ready: "bg-green-100 text-green-800",
  Collected: "bg-gray-100 text-gray-600",
  Cancelled: "bg-red-100 text-red-800",
  Error: "bg-red-100 text-red-800",
};

export default function OrderDetailPage() {
  const params = useParams();
  const router = useRouter();
  const orderId = params.id as string;

  const [order, setOrder] = useState<Order | null>(null);
  const [printer, setPrinter] = useState<Printer | null>(null);
  const [loading, setLoading] = useState(true);
  const [isVisible, setIsVisible] = useState(false);

  const loadOrder = useCallback(async () => {
    try {
      const orderData = await api.getOrder(orderId);
      setOrder(orderData);

      // Load printer if assigned
      if (orderData.assignedPrinterId) {
        const printerData = await api.getPrinter(orderData.assignedPrinterId);
        setPrinter(printerData);
      }
    } catch (error) {
      console.error("Failed to load order:", error);
    } finally {
      setLoading(false);
      setIsVisible(true);
    }
  }, [orderId]);

  useEffect(() => {
    loadOrder();
    
    // Poll every 10 seconds (optimized from 5 seconds)
    const interval = setInterval(loadOrder, 10000);
    return () => clearInterval(interval);
  }, [loadOrder]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50 flex items-center justify-center p-4">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-teal-200 border-t-teal-600 rounded-full animate-spin mb-4 mx-auto"></div>
          <p className="text-gray-600 font-medium">Loading order details...</p>
        </div>
      </div>
    );
  }

  if (!order) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50 flex items-center justify-center p-4">
        <div className="text-center bg-white rounded-2xl shadow-lg p-12 max-w-md animate-scale-in">
          <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg className="w-10 h-10 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Order Not Found</h2>
          <p className="text-gray-600 mb-6">The order you&apos;re looking for doesn&apos;t exist</p>
          <Link
            href="/orders"
            className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-teal-600 to-teal-700 text-white rounded-xl font-semibold hover:shadow-lg hover:scale-105 transition-all duration-300"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Back to Orders
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Back Button */}
        <div className={`mb-6 ${isVisible ? 'animate-fade-in-down' : 'opacity-0'}`}>
          <Link
            href="/orders"
            className="inline-flex items-center gap-2 text-teal-600 hover:text-teal-700 font-semibold group"
          >
            <svg className="w-5 h-5 group-hover:-translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Back to Orders
          </Link>
        </div>

        <div className={`bg-white rounded-2xl shadow-xl p-6 sm:p-8 ${isVisible ? 'animate-fade-in-up animation-delay-100' : 'opacity-0'}`}>
          {/* Header */}
          <div className="flex flex-col sm:flex-row justify-between items-start mb-8 gap-4">
            <div className="flex items-start gap-4">
              <div className="w-16 h-16 bg-gradient-to-br from-teal-500 to-teal-600 rounded-2xl flex items-center justify-center flex-shrink-0 shadow-lg">
                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                </svg>
              </div>
              <div>
                <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2">
                  {order.fileName}
                </h1>
                <p className="text-sm text-gray-600 font-mono">Order #{order.id.slice(0, 8)}</p>
              </div>
            </div>
            <div className="flex flex-col gap-2 items-start sm:items-end">
              <span
                className={`px-4 py-2 rounded-xl text-sm font-semibold ${
                  STATUS_COLORS[order.status]
                } shadow-md`}
              >
                {order.status}
              </span>
              {order.paymentStatus && (
                <span
                  className={`px-4 py-2 rounded-xl text-sm font-semibold shadow-md ${
                    order.paymentStatus === "paid"
                      ? "bg-green-100 text-green-800"
                      : order.paymentStatus === "unpaid"
                      ? "bg-yellow-100 text-yellow-800"
                      : "bg-red-100 text-red-800"
                  }`}
                >
                  Payment: {order.paymentStatus.charAt(0).toUpperCase() + order.paymentStatus.slice(1).toLowerCase()}
                </span>
              )}
            </div>
          </div>

          {/* Progress Bar */}
          {order.status === "Printing" && (
            <div className="mb-8 bg-gradient-to-r from-amber-50 to-orange-50 rounded-xl p-6 shadow-inner">
              <div className="flex justify-between items-center mb-3">
                <span className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                  <svg className="w-5 h-5 text-amber-600 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  Printing in Progress
                </span>
                <span className="text-lg font-bold text-amber-600">{order.progressPct}%</span>
              </div>
              <div className="w-full bg-white rounded-full h-4 overflow-hidden shadow-inner">
                <div
                  className="bg-gradient-to-r from-amber-500 to-orange-500 h-4 rounded-full transition-all duration-1000 ease-out relative"
                  style={{ width: `${order.progressPct}%` }}
                >
                  <div className="absolute inset-0 bg-white/30 animate-pulse"></div>
                </div>
              </div>
            </div>
          )}

          {/* Student Info */}
          <div className="mb-6 bg-gradient-to-br from-blue-50 to-teal-50 rounded-xl p-6">
            <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
              <svg className="w-5 h-5 text-teal-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
              Student Information
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <span className="text-sm text-gray-600">Name</span>
                <p className="font-semibold text-gray-900 text-lg">{order.studentName}</p>
              </div>
              <div>
                <span className="text-sm text-gray-600">Mobile</span>
                <p className="font-semibold text-gray-900 text-lg">{order.mobile}</p>
              </div>
            </div>
          </div>

          {/* Print Details */}
          <div className="mb-6 bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl p-6">
            <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
              <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Print Details
            </h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              <div>
                <span className="text-sm text-gray-600">Pages</span>
                <p className="font-semibold text-gray-900 text-lg">
                  {order.pages} × {order.copies}
                </p>
              </div>
              <div>
                <span className="text-sm text-gray-600">Color</span>
                <p className="font-semibold text-gray-900 text-lg">
                  {order.color === "bw" ? "Black & White" : "Color"}
                </p>
              </div>
              <div>
                <span className="text-sm text-gray-600">Sides</span>
                <p className="font-semibold text-gray-900 text-lg">
                  {order.sides === "single" ? "Single" : "Double"}
                </p>
              </div>
              <div>
                <span className="text-sm text-gray-600">Size</span>
                <p className="font-semibold text-gray-900 text-lg">{order.size}</p>
              </div>
              <div>
                <span className="text-sm text-gray-600">Queue</span>
                <p className="font-semibold text-gray-900 text-lg capitalize">
                  {order.queueType}
                </p>
              </div>
              {order.pickupTime && (
                <div className="sm:col-span-1">
                  <span className="text-sm text-gray-600">Pickup Time</span>
                  <p className="font-semibold text-gray-900 text-sm">
                    {new Date(order.pickupTime * 1000).toLocaleString()}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Printer Info */}
          {printer && (
            <div className="mb-6 bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl p-6">
              <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
                </svg>
                Assigned Printer
              </h2>
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-semibold text-gray-900 text-lg">{printer.name}</p>
                  <p className="text-sm text-gray-600">
                    Status: <span className="font-medium capitalize">{printer.status}</span> • {printer.ppm} pages/min
                  </p>
                </div>
                <div className={`w-3 h-3 rounded-full ${printer.status === 'idle' ? 'bg-green-500' : printer.status === 'printing' ? 'bg-amber-500 animate-pulse' : 'bg-red-500'}`}></div>
              </div>
            </div>
          )}

          {/* Payment Info */}
          {order.transactionId && (
            <div className="mb-6 bg-gradient-to-br from-green-50 to-emerald-50 border-2 border-green-200 rounded-xl p-6">
              <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Payment Information
              </h2>
              <div className="space-y-3">
                <div>
                  <span className="text-sm text-gray-600">Transaction ID</span>
                  <p className="font-mono font-medium text-gray-900 mt-1 bg-white px-3 py-2 rounded-lg">{order.transactionId}</p>
                </div>
                {order.paidAt && (
                  <div>
                    <span className="text-sm text-gray-600">Paid At</span>
                    <p className="font-medium text-gray-900 mt-1">
                      {new Date(order.paidAt * 1000).toLocaleString()}
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Price */}
          <div className="border-t-2 border-gray-200 pt-6">
            <div className="flex justify-between items-center mb-4">
              <span className="text-xl font-bold text-gray-900">
                Total Price
              </span>
              <span className="text-3xl font-bold bg-gradient-to-r from-teal-600 to-blue-600 bg-clip-text text-transparent">
                {formatPrice(order.priceTotal)}
              </span>
            </div>
            {order.paymentStatus === "unpaid" && order.status === "Pending" && (
              <div className="mt-4">
                <a
                  href={`/upi?amount=${order.priceTotal}&orderId=${order.id}&note=Print Order`}
                  className="block w-full text-center bg-gradient-to-r from-purple-600 to-purple-700 text-white py-4 px-6 rounded-xl font-semibold hover:shadow-xl hover:scale-105 transition-all duration-300 flex items-center justify-center gap-2"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                  Complete Payment
                </a>
              </div>
            )}
          </div>

          {/* Timestamps */}
          <div className="mt-6 pt-6 border-t border-gray-200 text-xs text-gray-500 space-y-1">
            <p className="flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Created: {new Date(order.createdAt * 1000).toLocaleString()}
            </p>
            <p className="flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Last Updated: {new Date(order.updatedAt * 1000).toLocaleString()}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
