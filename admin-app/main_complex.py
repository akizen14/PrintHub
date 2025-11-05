import sys
import hashlib
import requests
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QPushButton, QLabel,
    QDialog, QLineEdit, QFormLayout, QMessageBox, QGroupBox
)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont

API_BASE = "http://localhost:8000"

STATUS_COLORS = {
    "Pending": "#9CA3AF",
    "Queued": "#3B82F6", 
    "Printing": "#F59E0B",
    "Ready": "#10B981",
    "Collected": "#6B7280",
}


class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Admin Login")
        self.setFixedSize(300, 120)
        
        layout = QFormLayout()
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addRow("Admin Passcode:", self.password_input)
        
        self.login_btn = QPushButton("Login")
        self.login_btn.clicked.connect(self.verify_login)
        layout.addRow(self.login_btn)
        
        self.setLayout(layout)
        self.password_input.returnPressed.connect(self.verify_login)
    
    def verify_login(self):
        password = self.password_input.text()
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        try:
            response = requests.get(f"{API_BASE}/settings")
            if response.status_code == 200:
                settings = response.json()
                # Check both possible field names
                stored_hash = settings.get("adminPasswordHash") or settings.get("adminPassHash")
                if stored_hash == password_hash:
                    self.accept()
                else:
                    QMessageBox.warning(self, "Error", "Invalid password")
            else:
                QMessageBox.warning(self, "Error", "Cannot connect to backend")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Connection failed: {str(e)}")


class PrintHubAdmin(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PrintHub Admin")
        self.setGeometry(100, 100, 1000, 700)
        
        # Main widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Header
        header = QLabel("PrintHub Admin Dashboard")
        header.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # Orders section
        orders_group = QGroupBox("Active Orders")
        orders_layout = QVBoxLayout()
        
        # Order list
        self.order_list = QListWidget()
        self.order_list.itemClicked.connect(self.on_order_selected)
        orders_layout.addWidget(self.order_list)
        
        # Action buttons
        btn_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.load_orders)
        btn_layout.addWidget(self.refresh_btn)
        
        self.assign_btn = QPushButton("🖨️ Auto-Assign Printer")
        self.assign_btn.clicked.connect(self.auto_assign_printer)
        self.assign_btn.setEnabled(False)
        btn_layout.addWidget(self.assign_btn)
        
        self.print_btn = QPushButton("✅ Send to Printer")
        self.print_btn.clicked.connect(self.send_to_printer)
        self.print_btn.setEnabled(False)
        btn_layout.addWidget(self.print_btn)
        
        self.ready_btn = QPushButton("✓ Mark Ready")
        self.ready_btn.clicked.connect(self.mark_ready)
        self.ready_btn.setEnabled(False)
        btn_layout.addWidget(self.ready_btn)
        
        orders_layout.addLayout(btn_layout)
        orders_group.setLayout(orders_layout)
        layout.addWidget(orders_group)
        
        # Printers section
        printers_group = QGroupBox("Available Printers")
        printers_layout = QVBoxLayout()
        
        self.printer_list = QListWidget()
        printers_layout.addWidget(self.printer_list)
        
        discover_btn = QPushButton("🔍 Discover Printers")
        discover_btn.clicked.connect(self.discover_printers)
        printers_layout.addWidget(discover_btn)
        
        printers_group.setLayout(printers_layout)
        layout.addWidget(printers_group)
        
        # Status bar
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
        # Selected order tracking
        self.selected_order = None
        
        # Auto-refresh timer (every 5 seconds - less frequent for better performance)
        self.timer = QTimer()
        self.timer.timeout.connect(self.load_orders)
        self.timer.start(5000)
        
        # Initial load
        self.load_orders()
        self.load_printers()
    
    def load_orders(self):
        """Load active orders from backend"""
        try:
            response = requests.get(f"{API_BASE}/orders?status=Pending|Queued|Printing")
            if response.status_code == 200:
                orders = response.json()
                self.order_list.clear()
                
                for order in orders:
                    status = order.get("status", "Unknown")
                    student = order.get("studentName", "N/A")
                    pages = order.get("pages", 0)
                    copies = order.get("copies", 1)
                    color = "Color" if order.get("color") == "color" else "B&W"
                    
                    item_text = f"[{status}] {student} - {pages}p × {copies} ({color})"
                    item = QListWidgetItem(item_text)
                    
                    # Color code by status
                    color_code = STATUS_COLORS.get(status, "#000000")
                    item.setForeground(Qt.GlobalColor.white if status == "Printing" else Qt.GlobalColor.black)
                    item.setBackground(Qt.GlobalColor.transparent)
                    
                    item.setData(Qt.ItemDataRole.UserRole, order)
                    self.order_list.addItem(item)
                
                self.status_label.setText(f"Loaded {len(orders)} active orders")
        except Exception as e:
            self.status_label.setText(f"Error loading orders: {str(e)}")
    
    def load_printers(self):
        """Load printers from backend"""
        try:
            response = requests.get(f"{API_BASE}/printers")
            if response.status_code == 200:
                printers = response.json()
                self.printer_list.clear()
                
                for printer in printers:
                    name = printer.get("name", "Unknown")
                    status = printer.get("status", "unknown")
                    color = "Color" if printer.get("color") else "B&W"
                    
                    item_text = f"{name} - {status} ({color})"
                    item = QListWidgetItem(item_text)
                    item.setData(Qt.ItemDataRole.UserRole, printer)
                    self.printer_list.addItem(item)
        except Exception as e:
            self.status_label.setText(f"Error loading printers: {str(e)}")
    
    def on_order_selected(self, item):
        """Handle order selection"""
        self.selected_order = item.data(Qt.ItemDataRole.UserRole)
        
        if self.selected_order:
            status = self.selected_order.get("status")
            has_printer = self.selected_order.get("assignedPrinterId") is not None
            
            # Enable/disable buttons based on status
            self.assign_btn.setEnabled(status == "Pending")
            self.print_btn.setEnabled(status == "Queued" and has_printer)
            self.ready_btn.setEnabled(status == "Printing")
    
    def auto_assign_printer(self):
        """Auto-assign printer to selected order"""
        if not self.selected_order:
            return
        
        order_id = self.selected_order.get("id")
        
        try:
            response = requests.post(f"{API_BASE}/printers/auto-assign/{order_id}")
            if response.status_code == 200:
                result = response.json()
                QMessageBox.information(self, "Success", 
                    f"Assigned to: {result['printer']}\n{result['reason']}")
                self.load_orders()
            else:
                QMessageBox.warning(self, "Error", "Failed to assign printer")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed: {str(e)}")
    
    def send_to_printer(self):
        """Send order to actual printer"""
        if not self.selected_order:
            return
        
        order_id = self.selected_order.get("id")
        printer_id = self.selected_order.get("assignedPrinterId")
        
        if not printer_id:
            QMessageBox.warning(self, "Error", "No printer assigned")
            return
        
        try:
            response = requests.post(f"{API_BASE}/printers/{printer_id}/print?order_id={order_id}")
            if response.status_code == 200:
                QMessageBox.information(self, "Success", "Print job sent!")
                self.load_orders()
            else:
                error_msg = response.text if response.text else "Failed to send print job"
                QMessageBox.warning(self, "Error", f"Failed: {error_msg}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed: {str(e)}")
    
    def mark_ready(self):
        """Mark order as ready for pickup"""
        if not self.selected_order:
            return
        
        order_id = self.selected_order.get("id")
        
        try:
            response = requests.patch(f"{API_BASE}/orders/{order_id}",
                                    json={"status": "Ready", "progressPct": 100})
            if response.status_code == 200:
                QMessageBox.information(self, "Success", "Order marked as Ready!")
                self.load_orders()
            else:
                QMessageBox.warning(self, "Error", "Failed to update order")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed: {str(e)}")
    
    def discover_printers(self):
        """Discover system printers"""
        try:
            response = requests.get(f"{API_BASE}/printers/discover/system")
            if response.status_code == 200:
                result = response.json()
                QMessageBox.information(self, "Success",
                    f"Discovered: {result['discovered']}\n"
                    f"Updated: {result['updated']}\n"
                    f"Total: {result['total']}")
                self.load_printers()
            else:
                QMessageBox.warning(self, "Error", "Failed to discover printers")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed: {str(e)}")


def main():
    app = QApplication(sys.argv)
    
    # Show login dialog
    login = LoginDialog()
    if login.exec() == QDialog.DialogCode.Accepted:
        window = PrintHubAdmin()
        window.show()
        sys.exit(app.exec())
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
