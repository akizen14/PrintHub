"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { api, Rates } from "@/utils/api";
import { computePrice, formatPrice } from "@/lib/price";

export default function NewOrderPage() {
  const router = useRouter();
  const [rates, setRates] = useState<Rates | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState<string>("");
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [detectedPages, setDetectedPages] = useState<number | null>(null);
  const [detectingPages, setDetectingPages] = useState(false);

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
      
      router.push(`/orders/${order.id}`);
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
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-lg shadow-md p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-6">
            New Print Order
          </h1>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Student Info */}
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Student Name *
                </label>
                <input
                  type="text"
                  required
                  value={formData.studentName}
                  onChange={(e) =>
                    setFormData({ ...formData, studentName: e.target.value })
                  }
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
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
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                  placeholder="10-digit mobile number"
                />
              </div>

              {/* File Upload */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Upload File *
                </label>
                <input
                  type="file"
                  required
                  accept=".pdf,.docx,.jpg,.jpeg,.png"
                  onChange={handleFileChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-teal-50 file:text-teal-700 hover:file:bg-teal-100"
                />
                {fileError && (
                  <p className="mt-1 text-sm text-red-600">{fileError}</p>
                )}
                {selectedFile && (
                  <div className="mt-2 p-3 bg-green-50 border border-green-200 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center">
                        <div className="flex-shrink-0">
                          <svg className="h-5 w-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                        </div>
                        <div className="ml-3">
                          <p className="text-sm font-medium text-green-800">
                            {selectedFile.name}
                          </p>
                          <p className="text-sm text-green-600">
                            {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                          </p>
                        </div>
                      </div>
                      {detectingPages && (
                        <div className="text-sm text-green-600">
                          Detecting pages...
                        </div>
                      )}
                      {detectedPages !== null && !detectingPages && (
                        <div className="text-sm font-semibold text-green-700">
                          📄 {detectedPages} {detectedPages === 1 ? 'page' : 'pages'}
                        </div>
                      )}
                    </div>
                  </div>
                )}
                <p className="mt-1 text-sm text-gray-500">
                  Supported: PDF, DOCX, JPG, PNG (max 50MB)
                </p>
              </div>
            </div>

            {/* Print Options */}
            <div className="grid grid-cols-2 gap-4">

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Copies *
                </label>
                <input
                  type="number"
                  required
                  min="1"
                  value={formData.copies}
                  onChange={(e) =>
                    setFormData({ ...formData, copies: parseInt(e.target.value) || 1 })
                  }
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Color
                </label>
                <select
                  value={formData.color}
                  onChange={(e) =>
                    setFormData({ ...formData, color: e.target.value as "bw" | "color" })
                  }
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                >
                  <option value="bw">Black & White</option>
                  <option value="color">Color</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Sides
                </label>
                <select
                  value={formData.sides}
                  onChange={(e) =>
                    setFormData({ ...formData, sides: e.target.value as "single" | "duplex" })
                  }
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                >
                  <option value="single">Single-sided</option>
                  <option value="duplex">Double-sided</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Paper Size
              </label>
              <select
                value={formData.size}
                onChange={(e) =>
                  setFormData({ ...formData, size: e.target.value as "A4" | "A3" })
                }
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent"
              >
                <option value="A4">A4</option>
                <option value="A3">A3</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Pickup Time (Optional)
              </label>
              <input
                type="datetime-local"
                value={formData.pickupTime}
                onChange={(e) =>
                  setFormData({ ...formData, pickupTime: e.target.value })
                }
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent"
              />
            </div>

            {/* Price Preview */}
            <div className={`${isPriceAccurate ? 'bg-green-50 border-green-300' : 'bg-amber-50 border-amber-300'} border rounded-lg p-4`}>
              <div className="flex justify-between items-center mb-2">
                <span className="text-lg font-medium text-gray-700">
                  {isPriceAccurate ? 'Total Price:' : 'Estimated Price:'}
                </span>
                <span className={`text-2xl font-bold ${isPriceAccurate ? 'text-green-600' : 'text-amber-600'}`}>
                  {formatPrice(price)}
                </span>
              </div>
              {isPriceAccurate ? (
                <p className="text-sm text-green-700">
                  ✅ Actual price based on {pages} {pages === 1 ? 'page' : 'pages'} detected
                </p>
              ) : (
                <p className="text-sm text-amber-700">
                  ⚠️ This is an estimate. Upload a PDF to see the actual price.
                </p>
              )}
            </div>

            {/* Submit */}
            <div className="flex gap-4">
              <button
                type="button"
                onClick={() => router.back()}
                className="flex-1 px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-semibold hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="flex-1 px-6 py-3 bg-teal-600 text-white rounded-lg font-semibold hover:bg-teal-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? "Submitting..." : "Place Order"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
