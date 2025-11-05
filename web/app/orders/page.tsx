"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { api, Order } from "@/utils/api";
import { useDebounce } from "@/lib/hooks/useDebounce";

const STATUS_COLORS = {
  Pending: "bg-gray-100 text-gray-800",
  Queued: "bg-blue-100 text-blue-800",
  Printing: "bg-amber-100 text-amber-800",
  Ready: "bg-green-100 text-green-800",
  Collected: "bg-gray-100 text-gray-600",
  Cancelled: "bg-red-100 text-red-800",
  Error: "bg-red-100 text-red-800",
};

export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [mobile, setMobile] = useState("");
  
  // Debounce the mobile filter to avoid excessive re-renders
  const debouncedMobile = useDebounce(mobile, 300);

  useEffect(() => {
    // Try to get mobile from localStorage
    const savedMobile = localStorage.getItem("recentMobile");
    if (savedMobile) {
      setMobile(savedMobile);
    }
  }, []);

  useEffect(() => {
    loadOrders();
  }, []);

  const loadOrders = async () => {
    try {
      const allOrders = await api.getOrders();
      setOrders(allOrders);
    } catch (error) {
      console.error("Failed to load orders:", error);
    } finally {
      setLoading(false);
    }
  };

  const filteredOrders = debouncedMobile
    ? orders.filter((o) => o.mobile === debouncedMobile)
    : orders;

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-gray-900">My Orders</h1>
          <Link
            href="/order/new"
            className="px-4 py-2 bg-teal-600 text-white rounded-lg font-semibold hover:bg-teal-700 transition-colors"
          >
            New Order
          </Link>
        </div>

        {/* Mobile Filter */}
        <div className="bg-white rounded-lg shadow-md p-4 mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Filter by Mobile Number
          </label>
          <input
            type="tel"
            value={mobile}
            onChange={(e) => setMobile(e.target.value)}
            placeholder="Enter mobile number"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent"
          />
        </div>

        {loading ? (
          <div className="text-center py-12">
            <p className="text-gray-600">Loading orders...</p>
          </div>
        ) : filteredOrders.length === 0 ? (
          <div className="bg-white rounded-lg shadow-md p-12 text-center">
            <p className="text-gray-600 mb-4">No orders found</p>
            <Link
              href="/order/new"
              className="text-teal-600 hover:text-teal-700 font-semibold"
            >
              Place your first order →
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredOrders.map((order) => (
              <Link
                key={order.id}
                href={`/orders/${order.id}`}
                className="block bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow"
              >
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">
                      {order.fileName}
                    </h3>
                    <p className="text-sm text-gray-600">
                      {order.studentName} • {order.mobile}
                    </p>
                  </div>
                  <span
                    className={`px-3 py-1 rounded-full text-sm font-medium ${
                      STATUS_COLORS[order.status]
                    }`}
                  >
                    {order.status}
                  </span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm text-gray-600">
                  <div>
                    <span className="font-medium">Pages:</span> {order.pages} ×{" "}
                    {order.copies}
                  </div>
                  <div>
                    <span className="font-medium">Type:</span>{" "}
                    {order.color === "bw" ? "B&W" : "Color"}
                  </div>
                  <div>
                    <span className="font-medium">Queue:</span>{" "}
                    {order.queueType.charAt(0).toUpperCase() +
                      order.queueType.slice(1)}
                  </div>
                  <div>
                    <span className="font-medium">Price:</span> ₹
                    {order.priceTotal.toFixed(2)}
                  </div>
                </div>

                {order.progressPct > 0 && order.status === "Printing" && (
                  <div className="mt-4">
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-teal-600 h-2 rounded-full transition-all"
                        style={{ width: `${order.progressPct}%` }}
                      ></div>
                    </div>
                    <p className="text-xs text-gray-600 mt-1">
                      {order.progressPct}% complete
                    </p>
                  </div>
                )}
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
