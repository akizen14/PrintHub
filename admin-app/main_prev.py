import sys
import hashlib
import requests
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel,
    QDialog, QLineEdit, QFormLayout, QMessageBox, QHeaderView
)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont, QColor

API_BASE = "http://localhost:8000"


class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PrintHub Admin Login")
        self.setFixedSize(350, 150)
        
        layout = QVBoxLayout()
        
        title = QLabel("PrintHub Admin")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        form = QFormLayout()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Enter admin password")
        form.addRow("Password:", self.password_input)
        layout.addLayout(form)
        
        self.login_btn = QPushButton("Login")
        self.login_btn.setStyleSheet("padding: 8px; font-size: 14px;")
        self.login_btn.clicked.connect(self.verify_login)
        layout.addWidget(self.login_btn)
        
        self.setLayout(layout)
        self.password_input.returnPressed.connect(self.verify_login)
    
    def verify_login(self):
        password = self.password_input.text()
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        try:
            response = requests.get(f"{API_BASE}/settings")
            if response.status_code == 200:
                settings = response.json()
                stored_hash = settings.get("adminPasswordHash") or settings.get("adminPassHash")
                if stored_hash == password_hash:
                    self.accept()
                else:
                    QMessageBox.warning(self, "Error", "Invalid password")
                    self.password_input.clear()
            else:
                QMessageBox.warning(self, "Error", "Cannot connect to backend")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Connection failed: {str(e)}")


class PrintHubAdmin(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PrintHub Admin Dashboard")
        self.setGeometry(100, 100, 1200, 600)
        
        # Main widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Header
        header_layout = QHBoxLayout()
        header = QLabel("📋 Active Print Orders")
        header.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        header_layout.addWidget(header)
        
        header_layout.addStretch()
        
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #10B981; font-size: 14px;")
        header_layout.addWidget(self.status_label)
        
        layout.addLayout(header_layout)
        
        # Orders table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Student Name", "Mobile", "Pages", "Copies", "Type", "Status"
        ])
        
        # Make table look better
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        layout.addWidget(self.table)
        
        # Action buttons
        btn_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setStyleSheet("padding: 10px; font-size: 14px;")
        self.refresh_btn.clicked.connect(self.load_orders)
        btn_layout.addWidget(self.refresh_btn)
        
        btn_layout.addStretch()
        
        self.print_btn = QPushButton("🖨️ Send to Printer")
        self.print_btn.setStyleSheet("padding: 10px; font-size: 14px; background-color: #3B82F6; color: white;")
        self.print_btn.clicked.connect(self.send_to_printer)
        self.print_btn.setEnabled(False)
        btn_layout.addWidget(self.print_btn)
        
        self.ready_btn = QPushButton("✅ Mark as Ready")
        self.ready_btn.setStyleSheet("padding: 10px; font-size: 14px; background-color: #10B981; color: white;")
        self.ready_btn.clicked.connect(self.mark_ready)
        self.ready_btn.setEnabled(False)
        btn_layout.addWidget(self.ready_btn)
        
        self.collected_btn = QPushButton("📦 Mark as Collected")
        self.collected_btn.setStyleSheet("padding: 10px; font-size: 14px; background-color: #6B7280; color: white;")
        self.collected_btn.clicked.connect(self.mark_collected)
        self.collected_btn.setEnabled(False)
        btn_layout.addWidget(self.collected_btn)
        
        layout.addLayout(btn_layout)
        
        # Instructions
        instructions = QLabel("💡 Select an order → Send to Printer → Mark as Ready → Mark as Collected")
        instructions.setStyleSheet("color: #6B7280; font-size: 12px; padding: 10px;")
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(instructions)
        
        # Selected order tracking
        self.selected_order = None
        self.orders_data = []
        
        # Auto-refresh timer (every 5 seconds)
        self.timer = QTimer()
        self.timer.timeout.connect(self.load_orders)
        self.timer.start(5000)
        
        # Initial load
        self.load_orders()
    
    def load_orders(self):
        """Load active orders from backend"""
        try:
            response = requests.get(f"{API_BASE}/orders?status=Pending|Queued|Printing|Ready")
            if response.status_code == 200:
                self.orders_data = response.json()
                self.update_table()
                self.status_label.setText(f"✅ {len(self.orders_data)} active orders")
                self.status_label.setStyleSheet("color: #10B981; font-size: 14px;")
        except Exception as e:
            self.status_label.setText(f"❌ Error: {str(e)}")
            self.status_label.setStyleSheet("color: #EF4444; font-size: 14px;")
    
    def update_table(self):
        """Update the table with orders data"""
        self.table.setRowCount(len(self.orders_data))
        
        for row, order in enumerate(self.orders_data):
            # Student name
            self.table.setItem(row, 0, QTableWidgetItem(order.get("studentName", "N/A")))
            
            # Mobile
            self.table.setItem(row, 1, QTableWidgetItem(order.get("mobile", "N/A")))
            
            # Pages
            pages = str(order.get("pages", 0))
            self.table.setItem(row, 2, QTableWidgetItem(pages))
            
            # Copies
            copies = str(order.get("copies", 1))
            self.table.setItem(row, 3, QTableWidgetItem(copies))
            
            # Type (Color/B&W, Single/Duplex)
            color = "Color" if order.get("color") == "color" else "B&W"
            sides = "Duplex" if order.get("sides") == "duplex" else "Single"
            type_str = f"{color}, {sides}"
            self.table.setItem(row, 4, QTableWidgetItem(type_str))
            
            # Status
            status = order.get("status", "Unknown")
            status_item = QTableWidgetItem(status)
            
            # Color code status
            if status == "Pending":
                status_item.setBackground(QColor("#FEF3C7"))
                status_item.setForeground(QColor("#92400E"))
            elif status == "Queued":
                status_item.setBackground(QColor("#DBEAFE"))
                status_item.setForeground(QColor("#1E40AF"))
            elif status == "Printing":
                status_item.setBackground(QColor("#FED7AA"))
                status_item.setForeground(QColor("#9A3412"))
            elif status == "Ready":
                status_item.setBackground(QColor("#D1FAE5"))
                status_item.setForeground(QColor("#065F46"))
            
            self.table.setItem(row, 5, status_item)
    
    def on_selection_changed(self):
        """Handle row selection"""
        selected_rows = self.table.selectedIndexes()
        if selected_rows:
            row = selected_rows[0].row()
            self.selected_order = self.orders_data[row]
            
            status = self.selected_order.get("status")
            
            # Enable/disable buttons based on status
            self.print_btn.setEnabled(status in ["Pending", "Queued"])
            self.ready_btn.setEnabled(status == "Printing")
            self.collected_btn.setEnabled(status == "Ready")
        else:
            self.selected_order = None
            self.print_btn.setEnabled(False)
            self.ready_btn.setEnabled(False)
            self.collected_btn.setEnabled(False)
    
    def send_to_printer(self):
        """Send order to printer"""
        if not self.selected_order:
            return
        
        order_id = self.selected_order.get("id")
        
        # First, get available printers
        try:
            printers_response = requests.get(f"{API_BASE}/printers")
            if printers_response.status_code != 200:
                QMessageBox.warning(self, "Error", "Cannot load printers")
                return
            
            printers = printers_response.json()
            if not printers:
                # Try to discover printers first
                discover_response = requests.get(f"{API_BASE}/printers/discover/system")
                if discover_response.status_code == 200:
                    printers_response = requests.get(f"{API_BASE}/printers")
                    printers = printers_response.json()
                
                if not printers:
                    QMessageBox.warning(self, "Error", "No printers available. Please check if printers are installed on your system.")
                    return
            
            # Show printer selection dialog
            from PyQt6.QtWidgets import QInputDialog
            printer_names = [f"{p.get('name')} ({p.get('status', 'unknown')})" for p in printers]
            
            selected_printer_name, ok = QInputDialog.getItem(
                self, 
                "Select Printer",
                "Choose a printer for this job:",
                printer_names,
                0,
                False
            )
            
            if not ok:
                return
            
            # Get the selected printer
            selected_index = printer_names.index(selected_printer_name)
            printer = printers[selected_index]
            printer_id = printer.get("id")
            
            # Send print job
            response = requests.post(f"{API_BASE}/printers/{printer_id}/print?order_id={order_id}")
            if response.status_code == 200:
                QMessageBox.information(self, "Success", 
                    f"Print job sent to: {printer.get('name')}\n\nOrder status updated to 'Printing'")
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
        student_name = self.selected_order.get("studentName", "Student")
        
        try:
            response = requests.patch(f"{API_BASE}/orders/{order_id}",
                                    json={"status": "Ready", "progressPct": 100})
            if response.status_code == 200:
                QMessageBox.information(self, "Success", 
                    f"Order for {student_name} is now ready for pickup!")
                self.load_orders()
            else:
                QMessageBox.warning(self, "Error", "Failed to update order")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed: {str(e)}")
    
    def mark_collected(self):
        """Mark order as collected"""
        if not self.selected_order:
            return
        
        order_id = self.selected_order.get("id")
        student_name = self.selected_order.get("studentName", "Student")
        
        try:
            response = requests.patch(f"{API_BASE}/orders/{order_id}",
                                    json={"status": "Collected"})
            if response.status_code == 200:
                QMessageBox.information(self, "Success", 
                    f"Order collected by {student_name}!")
                self.load_orders()
            else:
                QMessageBox.warning(self, "Error", "Failed to update order")
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
