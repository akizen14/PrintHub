const BASE_URL = "http://localhost:8000";

// Simple in-memory cache with TTL
interface CacheEntry<T> {
  data: T;
  timestamp: number;
}

const cache = new Map<string, CacheEntry<unknown>>();
const CACHE_TTL = 5000; // 5 seconds

function getCacheKey(endpoint: string, options?: RequestInit): string {
  return `${endpoint}${JSON.stringify(options || {})}`;
}

function getFromCache<T>(cacheKey: string): T | null {
  const cached = cache.get(cacheKey);
  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    // Type assertion is safe here because we control what goes into the cache
    return cached.data as T;
  }
  return null;
}

function setCache<T>(cacheKey: string, data: T): void {
  cache.set(cacheKey, { data, timestamp: Date.now() });
}

export interface Order {
  id: string;
  studentName: string;
  mobile: string;
  fileName: string;
  filePath?: string;
  pages: number;
  copies: number;
  color: "bw" | "color";
  sides: "single" | "duplex";
  size: "A4" | "A3";
  pickupTime?: number;
  status: "Pending" | "Queued" | "Printing" | "Ready" | "Collected" | "Cancelled";
  paymentStatus: "unpaid" | "paid" | "refunded";
  transactionId?: string;
  paidAt?: number;
  queueType: "urgent" | "normal" | "bulk";
  priorityIndex: number;
  priceTotal: number;
  assignedPrinterId?: string;
  progressPct: number;
  estimatedSec: number;
  createdAt: number;
  updatedAt: number;
}

export interface Printer {
  id: string;
  name: string;
  status: "idle" | "printing" | "offline" | "error";
  ppm: number;
  color: boolean;
  duplex: boolean;
  a4: boolean;
  a3: boolean;
  currentJobId?: string;
  progressPct: number;
  updatedAt: number;
}

export interface Rates {
  bwSingleA4: number;
  bwDuplexA4: number;
  colorSingleA4: number;
  colorDuplexA4: number;
  minCharge: number;
  effectiveDate: number;
}

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  // Check cache for GET requests
  const cacheKey = getCacheKey(endpoint, options);
  if (!options || !options.method || options.method === "GET") {
    const cachedData = getFromCache<T>(cacheKey);
    if (cachedData) {
      return cachedData;
    }
  }

  const response = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`API Error: ${response.statusText}`);
  }

  const data = await response.json();
  
  // Cache GET requests
  if (!options || !options.method || options.method === "GET") {
    setCache(cacheKey, data);
  }
  
  return data;
}

// File upload function (no JSON content-type for FormData)
async function uploadFile<T>(endpoint: string, formData: FormData): Promise<T> {
  const response = await fetch(`${BASE_URL}${endpoint}`, {
    method: "POST",
    body: formData,
    // Don't set Content-Type header - let browser set it with boundary for FormData
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Upload Error: ${response.statusText} - ${errorText}`);
  }

  return response.json();
}

export const api = {
  // Orders
  async createOrderWithFile(
    file: File,
    orderData: {
      studentName: string;
      mobile: string;
      copies: number;
      color: "bw" | "color";
      sides: "single" | "duplex";
      size: "A4" | "A3";
      pickupTime?: number;
    }
  ): Promise<Order> {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("studentName", orderData.studentName);
    formData.append("mobile", orderData.mobile);
    formData.append("copies", orderData.copies.toString());
    formData.append("color", orderData.color);
    formData.append("sides", orderData.sides);
    formData.append("size", orderData.size);
    
    if (orderData.pickupTime) {
      formData.append("pickupTime", orderData.pickupTime.toString());
    }

    return uploadFile<Order>("/orders/upload", formData);
  },

  async createOrder(order: Omit<Order, "id" | "status" | "queueType" | "priorityIndex" | "priceTotal" | "assignedPrinterId" | "progressPct" | "estimatedSec" | "createdAt" | "updatedAt">): Promise<Order> {
    return fetchAPI<Order>("/orders", {
      method: "POST",
      body: JSON.stringify(order),
    });
  },

  async getOrders(filters?: { status?: string; queueType?: string }): Promise<Order[]> {
    const params = new URLSearchParams();
    if (filters?.status) params.append("status", filters.status);
    if (filters?.queueType) params.append("queueType", filters.queueType);
    
    const query = params.toString() ? `?${params.toString()}` : "";
    return fetchAPI<Order[]>(`/orders${query}`);
  },

  async getOrder(id: string): Promise<Order> {
    return fetchAPI<Order>(`/orders/${id}`);
  },

  async updateOrder(id: string, updates: Partial<Order>): Promise<Order> {
    return fetchAPI<Order>(`/orders/${id}`, {
      method: "PATCH",
      body: JSON.stringify(updates),
    });
  },

  async confirmPayment(orderId: string, paymentData?: { transactionId?: string }): Promise<Order> {
    return fetchAPI<Order>(`/orders/${orderId}/confirm-payment`, {
      method: "POST",
      body: paymentData ? JSON.stringify(paymentData) : undefined,
    });
  },

  // Printers
  async getPrinters(): Promise<Printer[]> {
    return fetchAPI<Printer[]>("/printers");
  },

  async getPrinter(id: string): Promise<Printer> {
    return fetchAPI<Printer>(`/printers/${id}`);
  },

  async discoverPrinters(): Promise<{
    discovered: number;
    updated: number;
    total: number;
    printers: any[];
  }> {
    return fetchAPI("/printers/discover/system", {
      method: "GET",
    });
  },

  async autoAssignPrinter(orderId: string): Promise<{
    success: boolean;
    printer: string;
    printer_id: string;
    reason: string;
  }> {
    return fetchAPI(`/printers/auto-assign/${orderId}`, {
      method: "POST",
    });
  },

  async sendToPrinter(printerId: string, orderId: string): Promise<{
    success: boolean;
    message: string;
    printer: string;
    order_id: string;
  }> {
    return fetchAPI(`/printers/${printerId}/print`, {
      method: "POST",
      body: JSON.stringify({ order_id: orderId }),
    });
  },

  async getPrinterStatus(printerId: string): Promise<{
    status: string;
    jobs_in_queue: number;
    current_job?: any;
  }> {
    return fetchAPI(`/printers/${printerId}/status`);
  },

  // Rates
  async getRates(): Promise<Rates> {
    return fetchAPI<Rates>("/rates");
  },

  async updateRates(rates: Rates): Promise<Rates> {
    return fetchAPI<Rates>("/rates", {
      method: "PUT",
      body: JSON.stringify(rates),
    });
  },
};
