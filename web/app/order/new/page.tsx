"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { api, Rates } from "@/utils/api";
import { computePrice, formatPrice } from "@/utils/price";

export default function NewOrderPage() {
  const router = useRouter();
  const [rates, setRates] = useState<Rates | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState<string>("");
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [detectedPages, setDetectedPages] = useState<number | null>(null);
  const [detectingPages, setDetectingPages] = useState(false);
  const [isVisible, setIsVisible] = useState(false);

  const [formData, setFormData] = useState({
    studentName: "",
    mobile: "",
    copies: 1,
    color: "bw" as "bw" | "color",
    sides: "single" as "single" | "duplex",
    size: "A4" as "A4" | "A3",
    pickupTime: "",
  });

  useEffect(() => {
    api.getRates().then(setRates).catch(console.error);
    setIsVisible(true);
  }, []);

  // File validation
  const validateFile = (file: File): string => {
    const maxSize = 50 * 1024 * 1024; // 50MB
    const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'image/jpeg', 'image/png'];
    
    if (file.size > maxSize) {
      return "File size must be less than 50MB";
    }
    
    if (!allowedTypes.includes(file.type)) {
      return "Only PDF, DOCX, JPG, and PNG files are allowed";
    }
    
    return "";
  };

  // Detect PDF page count
  const detectPdfPages = async (file: File): Promise<number | null> => {
    if (file.type !== 'application/pdf') {
      return null;
    }

    try {
      setDetectingPages(true);
      
      // Dynamically import pdfjs-dist
      const pdfjsLib = await import('pdfjs-dist');
      
      // Set worker path
      pdfjsLib.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`;
      
      // Read file as ArrayBuffer
      const arrayBuffer = await file.arrayBuffer();
      
      // Load PDF
      const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
      
      return pdf.numPages;
    } catch (error) {
      console.error('Failed to detect PDF pages:', error);
      return null;
    } finally {
      setDetectingPages(false);
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const error = validateFile(file);
      if (error) {
        setFileError(error);
        setSelectedFile(null);
        setDetectedPages(null);
      } else {
        setFileError("");
        setSelectedFile(file);
        
        // Detect page count for PDFs
        if (file.type === 'application/pdf') {
          const pages = await detectPdfPages(file);
          setDetectedPages(pages);
        } else {
          setDetectedPages(1); // Images are always 1 page
        }
      }
    }
  };

  // Use detected page count if available, otherwise use estimate
  const pages = detectedPages !== null ? detectedPages : 
    (selectedFile ? (selectedFile.type === 'application/pdf' ? 10 : 1) : 1);

  const price = rates
    ? computePrice(
        {
          pages: pages,
          copies: formData.copies,
          color: formData.color,
          sides: formData.sides,
          size: formData.size,
        },
        rates
      )
    : 0;
  
  const isPriceAccurate = detectedPages !== null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedFile) {
      setFileError("Please select a file to upload");
      return;
    }
    
    setLoading(true);
    setUploadProgress(0);

    try {
      const orderData = {
        ...formData,
        pickupTime: formData.pickupTime
          ? Math.floor(new Date(formData.pickupTime).getTime() / 1000)
          : undefined,
      };

      // Upload file and create order
      const order = await api.createOrderWithFile(selectedFile, orderData);
      
      // Store mobile in localStorage for "My Orders"
      localStorage.setItem("recentMobile", formData.mobile);
      
      // Redirect to UPI payment page with order details
      router.push(`/upi?amount=${order.priceTotal}&orderId=${order.id}&note=Print Order`);
    } catch (error) {
      console.error("Failed to create order:", error);
      const errorMessage = error instanceof Error ? error.message : "Failed to create order";
      alert(`Upload failed: ${errorMessage}`);
    } finally {
      setLoading(false);
      setUploadProgress(0);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50 py-8 px-4">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className={`mb-8 text-center ${isVisible ? 'animate-fade-in-down' : 'opacity-0'}`}>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-teal-600 to-blue-600 bg-clip-text text-transparent mb-2">
            New Print Order
          </h1>
          <p className="text-gray-600">Fill in the details to place your order</p>
        </div>

        <div className={`bg-white rounded-2xl shadow-xl p-6 sm:p-8 ${isVisible ? 'animate-fade-in-up animation-delay-100' : 'opacity-0'}`}>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Student Info Section */}
            <div className="space-y-4 pb-6 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <svg className="w-5 h-5 text-teal-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                Student Information
              </h2>
              
              <div className="grid sm:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="block text-sm font-semibold text-gray-700">
                    Student Name *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.studentName}
                    onChange={(e) =>
                      setFormData({ ...formData, studentName: e.target.value })
                    }
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-teal-500 focus:border-teal-500 transition-all"
                    placeholder="Enter your name"
                  />
                </div>

                <div className="space-y-2">
                  <label className="block text-sm font-semibold text-gray-700">
                    Mobile Number *
                  </label>
                  <input
                    type="tel"
                    required
                    pattern="[0-9]{10}"
                    value={formData.mobile}
                    onChange={(e) =>
                      setFormData({ ...formData, mobile: e.target.value })
                    }
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-teal-500 focus:border-teal-500 transition-all"
                    placeholder="10-digit mobile"
                  />
                </div>
              </div>
            </div>

            {/* File Upload Section */}
            <div className="space-y-4 pb-6 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <svg className="w-5 h-5 text-teal-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                Upload Document
              </h2>
              
              <div className="space-y-2">
                <label className="block">
                  <input
                    type="file"
                    required
                    accept=".pdf,.docx,.jpg,.jpeg,.png"
                    onChange={handleFileChange}
                    className="w-full px-4 py-3 border-2 border-dashed border-gray-300 rounded-xl focus:ring-2 focus:ring-teal-500 focus:border-teal-500 transition-all file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-sm file:font-semibold file:bg-gradient-to-r file:from-teal-500 file:to-teal-600 file:text-white hover:file:from-teal-600 hover:file:to-teal-700 cursor-pointer"
                  />
                </label>
                
                {fileError && (
                  <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-xl">
                    <svg className="w-5 h-5 text-red-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <p className="text-sm font-medium text-red-800">{fileError}</p>
                  </div>
                )}
                
                {selectedFile && (
                  <div className="p-4 bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-200 rounded-xl animate-scale-in">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl flex items-center justify-center flex-shrink-0 shadow-md">
                          <svg className="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                        </div>
                        <div>
                          <p className="text-sm font-semibold text-green-900">
                            {selectedFile.name}
                          </p>
                          <p className="text-xs text-green-700">
                            {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                          </p>
                        </div>
                      </div>
                      {detectingPages && (
                        <div className="flex items-center gap-2 text-sm text-green-700">
                          <div className="w-4 h-4 border-2 border-green-600 border-t-transparent rounded-full animate-spin"></div>
                          Detecting...
                        </div>
                      )}
                      {detectedPages !== null && !detectingPages && (
                        <div className="px-3 py-1 bg-white rounded-lg shadow-sm">
                          <span className="text-sm font-bold text-green-700">
                            📄 {detectedPages} {detectedPages === 1 ? 'page' : 'pages'}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                )}
                
                <p className="text-xs text-gray-500 flex items-center gap-1">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Supported: PDF, DOCX, JPG, PNG (max 50MB)
                </p>
              </div>
            </div>

            {/* Print Options Section */}
            <div className="space-y-4 pb-6 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <svg className="w-5 h-5 text-teal-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
                </svg>
                Print Options
              </h2>
              
              <div className="grid sm:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="block text-sm font-semibold text-gray-700">
                    Number of Copies *
                  </label>
                  <input
                    type="number"
                    required
                    min="1"
                    value={formData.copies}
                    onChange={(e) =>
                      setFormData({ ...formData, copies: parseInt(e.target.value) || 1 })
                    }
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-teal-500 focus:border-teal-500 transition-all"
                  />
                </div>

                <div className="space-y-2">
                  <label className="block text-sm font-semibold text-gray-700">
                    Color Mode
                  </label>
                  <select
                    value={formData.color}
                    onChange={(e) =>
                      setFormData({ ...formData, color: e.target.value as "bw" | "color" })
                    }
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-teal-500 focus:border-teal-500 transition-all bg-white"
                  >
                    <option value="bw">⚫ Black & White</option>
                    <option value="color">🌈 Color</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <label className="block text-sm font-semibold text-gray-700">
                    Print Sides
                  </label>
                  <select
                    value={formData.sides}
                    onChange={(e) =>
                      setFormData({ ...formData, sides: e.target.value as "single" | "duplex" })
                    }
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-teal-500 focus:border-teal-500 transition-all bg-white"
                  >
                    <option value="single">📄 Single-sided</option>
                    <option value="duplex">📑 Double-sided</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <label className="block text-sm font-semibold text-gray-700">
                    Paper Size
                  </label>
                  <select
                    value={formData.size}
                    onChange={(e) =>
                      setFormData({ ...formData, size: e.target.value as "A4" | "A3" })
                    }
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-teal-500 focus:border-teal-500 transition-all bg-white"
                  >
                    <option value="A4">📃 A4</option>
                    <option value="A3">📰 A3</option>
                  </select>
                </div>
              </div>

              <div className="space-y-2">
                <label className="block text-sm font-semibold text-gray-700 flex items-center gap-2">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Pickup Time (Optional)
                </label>
                <input
                  type="datetime-local"
                  value={formData.pickupTime}
                  onChange={(e) =>
                    setFormData({ ...formData, pickupTime: e.target.value })
                  }
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-teal-500 focus:border-teal-500 transition-all"
                />
              </div>
            </div>

            {/* Price Preview */}
            <div className={`${isPriceAccurate ? 'bg-gradient-to-r from-green-50 to-emerald-50 border-green-300' : 'bg-gradient-to-r from-amber-50 to-orange-50 border-amber-300'} border-2 rounded-xl p-6 shadow-inner`}>
              <div className="flex justify-between items-center mb-3">
                <span className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                  {isPriceAccurate ? (
                    <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  ) : (
                    <svg className="w-5 h-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                  )}
                  {isPriceAccurate ? 'Total Price' : 'Estimated Price'}
                </span>
                <span className={`text-3xl font-bold ${isPriceAccurate ? 'text-green-600' : 'text-amber-600'}`}>
                  {formatPrice(price)}
                </span>
              </div>
              <p className={`text-sm font-medium ${isPriceAccurate ? 'text-green-700' : 'text-amber-700'}`}>
                {isPriceAccurate ? (
                  <>✅ Accurate price based on {pages} {pages === 1 ? 'page' : 'pages'} detected</>
                ) : (
                  <>⚠️ This is an estimate. Upload a PDF to see the exact price.</>
                )}
              </p>
            </div>

            {/* Submit Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 pt-4">
              <button
                type="button"
                onClick={() => router.back()}
                className="flex-1 px-6 py-4 border-2 border-gray-300 text-gray-700 rounded-xl font-semibold hover:bg-gray-50 hover:border-gray-400 transition-all"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="flex-1 px-6 py-4 bg-gradient-to-r from-teal-600 to-teal-700 text-white rounded-xl font-semibold hover:shadow-xl hover:scale-105 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    Submitting...
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Place Order
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
