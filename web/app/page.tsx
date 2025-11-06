"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

export default function Home() {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    setIsVisible(true);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-teal-50 via-blue-50 to-purple-50 overflow-hidden">
      {/* Hero Section */}
      <div className="relative min-h-screen flex flex-col items-center justify-center p-4 sm:p-8">
        {/* Animated background elements */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-20 left-10 w-64 h-64 bg-teal-200 rounded-full mix-blend-multiply blur-xl opacity-20 animate-pulse"></div>
          <div className="absolute top-40 right-10 w-64 h-64 bg-purple-200 rounded-full mix-blend-multiply blur-xl opacity-20 animate-pulse animation-delay-200"></div>
          <div className="absolute bottom-20 left-1/2 w-64 h-64 bg-blue-200 rounded-full mix-blend-multiply blur-xl opacity-20 animate-pulse animation-delay-400"></div>
        </div>

        <div className="relative max-w-5xl w-full">
          {/* Main content */}
          <div className={`text-center space-y-8 ${isVisible ? 'opacity-100' : 'opacity-0'} transition-opacity duration-1000`}>
            {/* Logo/Icon */}
            <div className="flex justify-center mb-6 animate-fade-in-down">
              <div className="w-20 h-20 bg-gradient-to-br from-teal-500 to-teal-600 rounded-2xl shadow-lg flex items-center justify-center transform hover:scale-110 transition-transform duration-300">
                <svg className="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
                </svg>
              </div>
            </div>

            {/* Heading */}
            <div className="space-y-4 animate-fade-in-up animation-delay-100">
              <h1 className="text-5xl sm:text-6xl md:text-7xl font-bold bg-gradient-to-r from-teal-600 via-blue-600 to-purple-600 bg-clip-text text-transparent leading-tight">
                PrintHub
              </h1>
              <p className="text-xl sm:text-2xl text-gray-700 max-w-2xl mx-auto font-medium">
                Fast, easy, and reliable print ordering for students
              </p>
              <p className="text-base sm:text-lg text-gray-600 max-w-xl mx-auto">
                Upload your documents, pay instantly via UPI, and track your orders in real-time
              </p>
            </div>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center pt-4 animate-fade-in-up animation-delay-200">
              <Link
                href="/order/new"
                className="group px-8 py-4 bg-gradient-to-r from-teal-600 to-teal-700 text-white rounded-xl font-semibold text-lg shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-300 relative overflow-hidden"
              >
                <span className="relative z-10 flex items-center justify-center gap-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                  New Order
                </span>
                <div className="absolute inset-0 bg-gradient-to-r from-teal-700 to-teal-800 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              </Link>
              <Link
                href="/orders"
                className="group px-8 py-4 bg-white border-2 border-teal-600 text-teal-600 rounded-xl font-semibold text-lg hover:bg-teal-50 hover:border-teal-700 hover:scale-105 transition-all duration-300 shadow-md hover:shadow-lg"
              >
                <span className="flex items-center justify-center gap-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                  </svg>
                  My Orders
                </span>
              </Link>
            </div>
          </div>

          {/* Features */}
          <div className={`grid grid-cols-1 sm:grid-cols-3 gap-6 mt-20 ${isVisible ? 'opacity-100' : 'opacity-0'} transition-opacity duration-1000 delay-500`}>
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-6 shadow-lg hover-lift animate-fade-in-up animation-delay-300">
              <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center mb-4 shadow-md">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Lightning Fast</h3>
              <p className="text-gray-600 text-sm">
                Get your prints ready in minutes with our optimized queue system
              </p>
            </div>

            <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-6 shadow-lg hover-lift animate-fade-in-up animation-delay-400">
              <div className="w-12 h-12 bg-gradient-to-br from-teal-500 to-teal-600 rounded-xl flex items-center justify-center mb-4 shadow-md">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Instant Payment</h3>
              <p className="text-gray-600 text-sm">
                Pay securely via UPI with Google Pay, PhonePe, or Paytm
              </p>
            </div>

            <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-6 shadow-lg hover-lift animate-fade-in-up animation-delay-500">
              <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl flex items-center justify-center mb-4 shadow-md">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Real-time Tracking</h3>
              <p className="text-gray-600 text-sm">
                Monitor your print job status live, from queue to completion
              </p>
            </div>
          </div>

          {/* Stats */}
          <div className="mt-16 text-center animate-fade-in animation-delay-500">
            <p className="text-sm text-gray-500 mb-4">Trusted by students everywhere</p>
            <div className="flex flex-wrap justify-center gap-8 text-center">
              <div className="flex flex-col">
                <span className="text-3xl font-bold bg-gradient-to-r from-teal-600 to-blue-600 bg-clip-text text-transparent">24/7</span>
                <span className="text-sm text-gray-600">Available</span>
              </div>
              <div className="flex flex-col">
                <span className="text-3xl font-bold bg-gradient-to-r from-teal-600 to-blue-600 bg-clip-text text-transparent">5min</span>
                <span className="text-sm text-gray-600">Avg. Time</span>
              </div>
              <div className="flex flex-col">
                <span className="text-3xl font-bold bg-gradient-to-r from-teal-600 to-blue-600 bg-clip-text text-transparent">₹1</span>
                <span className="text-sm text-gray-600">Starting Price</span>
              </div>
            </div>
          </div>
        </div>

        {/* Scroll indicator */}
        <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 animate-bounce">
          <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
          </svg>
        </div>
      </div>
    </div>
  );
}
