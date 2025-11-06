"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { api, Order } from "@/utils/api";
import { useDebounce } from "@/hooks/useDebounce";

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
  const [isVisible, setIsVisible] = useState(false);
  
  // Debounce the mobile filter to avoid excessive re-renders
  const debouncedMobile = useDebounce(mobile, 300);

  useEffect(() => {
    // Try to get mobile from localStorage
    const savedMobile = localStorage.getItem("recentMobile");
    if (savedMobile) {
      setMobile(savedMobile);
    }
    setIsVisible(true);
  }, []);

  useEffect(() => {
    loadOrders();
    // Poll every 10 seconds instead of constantly
    const interval = setInterval(loadOrders, 10000);
    return () => clearInterval(interval);
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
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50 py-8 px-4">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className={`flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 gap-4 ${isVisible ? 'animate-fade-in-down' : 'opacity-0'}`}>
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-teal-600 to-blue-600 bg-clip-text text-transparent mb-2">
              My Orders
            </h1>
            <p className="text-gray-600">Track and manage your print orders</p>
          </div>
          <Link
            href="/order/new"
            className="group px-6 py-3 bg-gradient-to-r from-teal-600 to-teal-700 text-white rounded-xl font-semibold hover:shadow-xl hover:scale-105 transition-all duration-300 flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            New Order
          </Link>
        </div>

        {/* Mobile Filter */}
        <div className={`bg-white rounded-2xl shadow-lg p-6 mb-8 hover-lift ${isVisible ? 'animate-fade-in-up animation-delay-100' : 'opacity-0'}`}>
          <label className="block text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
            <svg className="w-5 h-5 text-teal-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            Filter by Mobile Number
          </label>
          <input
            type="tel"
            value={mobile}
            onChange={(e) => setMobile(e.target.value)}
            placeholder="Enter mobile number"
            className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-teal-500 focus:border-teal-500 transition-all"
          />
          {debouncedMobile && (
            <p className="mt-2 text-sm text-gray-600">
              Showing {filteredOrders.length} order{filteredOrders.length !== 1 ? 's' : ''} for {debouncedMobile}
            </p>
          )}
        </div>

        {/* Orders List */}
        {loading ? (
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-white rounded-2xl shadow-lg p-6 animate-pulse">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex-1">
                    <div className="h-6 bg-gray-200 rounded w-3/4 mb-2"></div>
                    <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                  </div>
                  <div className="h-8 bg-gray-200 rounded-full w-24"></div>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                  {[1, 2, 3, 4].map((j) => (
                    <div key={j} className="h-4 bg-gray-200 rounded"></div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : filteredOrders.length === 0 ? (
          <div className={`bg-white rounded-2xl shadow-lg p-12 text-center ${isVisible ? 'animate-scale-in animation-delay-200' : 'opacity-0'}`}>
            <div className="w-24 h-24 bg-gradient-to-br from-gray-100 to-gray-200 rounded-full flex items-center justify-center mx-auto mb-6">
              <svg className="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">No orders found</h3>
            <p className="text-gray-600 mb-6">
              {debouncedMobile ? "No orders found for this mobile number" : "You haven't placed any orders yet"}
            </p>
            <Link
              href="/order/new"
              className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-teal-600 to-teal-700 text-white rounded-xl font-semibold hover:shadow-lg hover:scale-105 transition-all duration-300"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Place your first order
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredOrders.map((order, index) => (
              <Link
                key={order.id}
                href={`/orders/${order.id}`}
                className={`block bg-white rounded-2xl shadow-lg p-6 hover:shadow-2xl transition-all duration-300 hover:scale-[1.02] ${isVisible ? 'animate-fade-in-up' : 'opacity-0'}`}
                style={{ animationDelay: `${200 + index * 50}ms` }}
              >
                <div className="flex flex-col sm:flex-row justify-between items-start mb-4 gap-3">
                  <div className="flex-1">
                    <div className="flex items-start gap-3 mb-2">
                      <div className="w-12 h-12 bg-gradient-to-br from-teal-500 to-teal-600 rounded-xl flex items-center justify-center flex-shrink-0 shadow-md">
                        <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                        </svg>
                      </div>
                      <div className="flex-1">
                        <h3 className="text-lg font-semibold text-gray-900 mb-1">
                          {order.fileName}
                        </h3>
                        <p className="text-sm text-gray-600 flex items-center gap-2">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                          </svg>
                          {order.studentName} • {order.mobile}
                        </p>
                      </div>
                    </div>
                  </div>
                  <div className="flex flex-col gap-2 items-start sm:items-end">
                    <span
                      className={`px-4 py-2 rounded-full text-sm font-semibold ${
                        STATUS_COLORS[order.status]
                      } shadow-sm`}
                    >
                      {order.status}
                    </span>
                    <span className="text-lg font-bold text-teal-600">
                      ₹{order.priceTotal.toFixed(2)}
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
                  <div className="flex items-center gap-2 text-gray-600">
                    <svg className="w-4 h-4 text-teal-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <span><span className="font-semibold">{order.pages}</span> × {order.copies}</span>
                  </div>
                  <div className="flex items-center gap-2 text-gray-600">
                    <div className={`w-3 h-3 rounded-full ${order.color === "bw" ? "bg-gray-800" : "bg-gradient-to-r from-red-500 via-yellow-500 to-blue-500"}`}></div>
                    <span className="font-medium">
                      {order.color === "bw" ? "B&W" : "Color"}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-gray-600">
                    <svg className="w-4 h-4 text-teal-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span className="font-medium capitalize">{order.queueType}</span>
                  </div>
                  <div className="flex items-center gap-2 text-gray-600">
                    <svg className="w-4 h-4 text-teal-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                    </svg>
                    <span className="font-medium">{order.size}</span>
                  </div>
                </div>

                {order.progressPct > 0 && order.status === "Printing" && (
                  <div className="mt-4">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-xs font-medium text-gray-700">Printing Progress</span>
                      <span className="text-xs font-semibold text-teal-600">{order.progressPct}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                      <div
                        className="bg-gradient-to-r from-teal-500 to-teal-600 h-2 rounded-full transition-all duration-500 ease-out"
                        style={{ width: `${order.progressPct}%` }}
                      ></div>
                    </div>
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
