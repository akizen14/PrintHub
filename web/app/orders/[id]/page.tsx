"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api, Order, Printer } from "@/utils/api";
import { formatPrice } from "@/lib/price";

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

  useEffect(() => {
    loadOrder();
    
    // Poll every 5 seconds (reduced from 3 seconds for better performance)
    const interval = setInterval(loadOrder, 5000);
    return () => clearInterval(interval);
  }, [orderId]);

  const loadOrder = async () => {
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
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <p className="text-gray-600">Loading order...</p>
      </div>
    );
  }

  if (!order) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600 mb-4">Order not found</p>
          <Link
            href="/orders"
            className="text-teal-600 hover:text-teal-700 font-semibold"
          >
            ← Back to Orders
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-3xl mx-auto">
        <div className="mb-6">
          <Link
            href="/orders"
            className="text-teal-600 hover:text-teal-700 font-semibold"
          >
            ← Back to Orders
          </Link>
        </div>

        <div className="bg-white rounded-lg shadow-md p-8">
          {/* Header */}
          <div className="flex justify-between items-start mb-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                {order.fileName}
              </h1>
              <p className="text-gray-600">Order #{order.id.slice(0, 8)}</p>
            </div>
            <span
              className={`px-4 py-2 rounded-full text-sm font-medium ${
                STATUS_COLORS[order.status]
              }`}
            >
              {order.status}
            </span>
          </div>

          {/* Progress Bar */}
          {order.status === "Printing" && (
            <div className="mb-6">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-700">
                  Printing Progress
                </span>
                <span className="text-sm font-medium text-teal-600">
                  {order.progressPct}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-4">
                <div
                  className="bg-teal-600 h-4 rounded-full transition-all duration-500"
                  style={{ width: `${order.progressPct}%` }}
                ></div>
              </div>
            </div>
          )}

          {/* Student Info */}
          <div className="mb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-3">
              Student Information
            </h2>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Name:</span>
                <p className="font-medium text-gray-900">{order.studentName}</p>
              </div>
              <div>
                <span className="text-gray-600">Mobile:</span>
                <p className="font-medium text-gray-900">{order.mobile}</p>
              </div>
            </div>
          </div>

          {/* Print Details */}
          <div className="mb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-3">
              Print Details
            </h2>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Pages:</span>
                <p className="font-medium text-gray-900">
                  {order.pages} × {order.copies} copies
                </p>
              </div>
              <div>
                <span className="text-gray-600">Color:</span>
                <p className="font-medium text-gray-900">
                  {order.color === "bw" ? "Black & White" : "Color"}
                </p>
              </div>
              <div>
                <span className="text-gray-600">Sides:</span>
                <p className="font-medium text-gray-900">
                  {order.sides === "single" ? "Single-sided" : "Double-sided"}
                </p>
              </div>
              <div>
                <span className="text-gray-600">Size:</span>
                <p className="font-medium text-gray-900">{order.size}</p>
              </div>
              <div>
                <span className="text-gray-600">Queue:</span>
                <p className="font-medium text-gray-900">
                  {order.queueType.charAt(0).toUpperCase() +
                    order.queueType.slice(1)}
                </p>
              </div>
              {order.pickupTime && (
                <div>
                  <span className="text-gray-600">Pickup Time:</span>
                  <p className="font-medium text-gray-900">
                    {new Date(order.pickupTime * 1000).toLocaleString()}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Printer Info */}
          {printer && (
            <div className="mb-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-3">
                Assigned Printer
              </h2>
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="font-medium text-gray-900">{printer.name}</p>
                <p className="text-sm text-gray-600">
                  Status: {printer.status} • {printer.ppm} pages/min
                </p>
              </div>
            </div>
          )}

          {/* Price */}
          <div className="border-t pt-6">
            <div className="flex justify-between items-center">
              <span className="text-lg font-semibold text-gray-900">
                Total Price
              </span>
              <span className="text-2xl font-bold text-teal-600">
                {formatPrice(order.priceTotal)}
              </span>
            </div>
          </div>

          {/* Timestamps */}
          <div className="mt-6 pt-6 border-t text-xs text-gray-500">
            <p>Created: {new Date(order.createdAt * 1000).toLocaleString()}</p>
            <p>
              Last Updated: {new Date(order.updatedAt * 1000).toLocaleString()}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
