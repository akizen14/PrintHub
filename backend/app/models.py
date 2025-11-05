from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class OrderIn(BaseModel):
    studentName: str
    mobile: str
    fileName: str
    pages: int
    copies: int
    color: Literal["bw", "color"]
    sides: Literal["single", "duplex"]
    size: Literal["A4", "A3"]
    pickupTime: Optional[int] = None
    paymentStatus: Optional[Literal["unpaid", "paid", "refunded"]] = "unpaid"


class Order(BaseModel):
    model_config = {"exclude_none": False}
    
    id: str
    studentName: str
    mobile: str
    fileName: str
    filePath: Optional[str] = None
    pages: int
    copies: int
    color: Literal["bw", "color"]
    sides: Literal["single", "duplex"]
    size: Literal["A4", "A3"]
    pickupTime: Optional[int] = None
    status: Literal["Pending", "Queued", "Printing", "Ready", "Collected", "Cancelled", "Error"] = "Pending"
    paymentStatus: Literal["unpaid", "paid", "refunded"] = "unpaid"
    transactionId: Optional[str] = None
    paidAt: Optional[int] = None
    queueType: Literal["urgent", "normal", "bulk"] = "normal"
    priorityIndex: int
    priorityScore: float = 0.0
    assignedPrinterId: Optional[str] = None
    progressPct: int = 0
    estimatedSec: Optional[int] = None
    priceTotal: float
    createdAt: int
    updatedAt: int


class OrderUpdate(BaseModel):
    status: Optional[Literal["Pending", "Queued", "Printing", "Ready", "Collected", "Cancelled", "Error"]] = None
    paymentStatus: Optional[Literal["unpaid", "paid", "refunded"]] = None
    transactionId: Optional[str] = None
    paidAt: Optional[int] = None
    progressPct: Optional[int] = None
    assignedPrinterId: Optional[str] = None
    priorityIndex: Optional[int] = None
    estimatedSec: Optional[int] = None


class PaymentConfirmation(BaseModel):
    transactionId: Optional[str] = None
    paymentMethod: Optional[str] = "UPI"
    notes: Optional[str] = None


class Printer(BaseModel):
    id: str
    name: str
    status: Literal["idle", "printing", "offline", "error"] = "idle"
    ppm: int
    color: bool
    duplex: bool
    a4: bool
    a3: bool
    currentJobId: Optional[str] = None
    progressPct: int = 0
    updatedAt: int


class PrinterUpdate(BaseModel):
    status: Optional[Literal["idle", "printing", "offline", "error"]] = None
    currentJobId: Optional[str] = None
    progressPct: Optional[int] = None


class Rates(BaseModel):
    bwSingleA4: float
    bwDuplexA4: float
    colorSingleA4: float
    colorDuplexA4: float
    minCharge: float
    effectiveDate: int


class Thresholds(BaseModel):
    smallPages: int = 15
    chunkPages: int = 100
    agingMinutes: int = 12


class Settings(BaseModel):
    adminPassHash: str
    thresholds: Thresholds
