import sys
import hashlib
import requests
import os
import shutil
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel,
    QDialog, QLineEdit, QFormLayout, QMessageBox, QHeaderView
)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont, QColor

API_BASE = "http://localhost:8000"

# Temp print directory
TEMP_PRINT_DIR = r"C:\PrintHub\TempPrint"
os.makedirs(TEMP_PRINT_DIR, exist_ok=True)


def system_print(pdf_path, printer_name):
    """
    Print PDF using Windows PrintTo verb for proper rendering
    """
    subprocess.run([
        "powershell",
        "-Command",
        f"Start-Process -FilePath '{pdf_path}' -Verb PrintTo -ArgumentList '{printer_name}' -WindowStyle Hidden"
    ])


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
        self.setWindowTitle("PrintHub Admin")
        self.setGeometry(100, 100, 1400, 700)
        
        # Main widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header with refresh
        header_layout = QHBoxLayout()
        header = QLabel("Print Orders")
        header.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        header_layout.addWidget(header)
        
        header_layout.addStretch()
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setStyleSheet("padding: 8px 15px; font-size: 13px;")
        self.refresh_btn.clicked.connect(self.load_orders)
        header_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Orders table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Student", "Mobile", "File Name", "Pages", "Copies", "Type", "Status"
        ])
        
        # Table styling - Professional theme
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setStyleSheet("""
            QTableWidget {
                font-size: 14px;
                gridline-color: #d1d5db;
                background-color: white;
                alternate-background-color: #f9fafb;
                selection-background-color: #dbeafe;
                selection-color: #1e3a8a;
                color: #1f2937;
            }
            QTableWidget::item {
                padding: 8px;
                color: #1f2937;
            }
            QHeaderView::section {
                background-color: #1e293b;
                color: white;
                padding: 12px 8px;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-right: 1px solid #334155;
            }
            QHeaderView::section:last {
                border-right: none;
            }
        """)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Student
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Mobile
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # File Name
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Pages
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Copies
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Type
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Status
        
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        layout.addWidget(self.table)
        
        # Action buttons - EXTRA LARGE and SIMPLE
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        
        self.print_btn = QPushButton("🖨️\nPRINT")
        self.print_btn.setStyleSheet("""
            QPushButton {
                padding: 25px 40px;
                font-size: 18px;
                font-weight: bold;
                background-color: #2563eb;
                color: white;
                border: none;
                border-radius: 8px;
                min-height: 80px;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
            QPushButton:disabled {
                background-color: #cbd5e1;
                color: #94a3b8;
            }
        """)
        self.print_btn.clicked.connect(self.send_to_printer)
        self.print_btn.setEnabled(False)
        btn_layout.addWidget(self.print_btn)
        
        self.ready_btn = QPushButton("✅\nREADY")
        self.ready_btn.setStyleSheet("""
            QPushButton {
                padding: 25px 40px;
                font-size: 18px;
                font-weight: bold;
                background-color: #16a34a;
                color: white;
                border: none;
                border-radius: 8px;
                min-height: 80px;
            }
            QPushButton:hover {
                background-color: #15803d;
            }
            QPushButton:disabled {
                background-color: #cbd5e1;
                color: #94a3b8;
            }
        """)
        self.ready_btn.clicked.connect(self.mark_ready)
        self.ready_btn.setEnabled(False)
        btn_layout.addWidget(self.ready_btn)
        
        self.collected_btn = QPushButton("📦\nCOLLECTED")
        self.collected_btn.setStyleSheet("""
            QPushButton {
                padding: 25px 40px;
                font-size: 18px;
                font-weight: bold;
                background-color: #64748b;
                color: white;
                border: none;
                border-radius: 8px;
                min-height: 80px;
            }
            QPushButton:hover {
                background-color: #475569;
            }
            QPushButton:disabled {
                background-color: #cbd5e1;
                color: #94a3b8;
            }
        """)
        self.collected_btn.clicked.connect(self.mark_collected)
        self.collected_btn.setEnabled(False)
        btn_layout.addWidget(self.collected_btn)
        
        self.cancel_btn = QPushButton("❌\nCANCEL")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                padding: 25px 40px;
                font-size: 18px;
                font-weight: bold;
                background-color: #dc2626;
                color: white;
                border: none;
                border-radius: 8px;
                min-height: 80px;
            }
            QPushButton:hover {
                background-color: #b91c1c;
            }
            QPushButton:disabled {
                background-color: #cbd5e1;
                color: #94a3b8;
            }
        """)
        self.cancel_btn.clicked.connect(self.cancel_order)
        self.cancel_btn.setEnabled(False)
        btn_layout.addWidget(self.cancel_btn)
        
        self.view_file_btn = QPushButton("📄\nVIEW FILE")
        self.view_file_btn.setStyleSheet("""
            QPushButton {
                padding: 25px 40px;
                font-size: 18px;
                font-weight: bold;
                background-color: #7c3aed;
                color: white;
                border: none;
                border-radius: 8px;
                min-height: 80px;
            }
            QPushButton:hover {
                background-color: #6d28d9;
            }
            QPushButton:disabled {
                background-color: #cbd5e1;
                color: #94a3b8;
            }
        """)
        self.view_file_btn.clicked.connect(self.view_file)
        self.view_file_btn.setEnabled(False)
        btn_layout.addWidget(self.view_file_btn)
        
        layout.addLayout(btn_layout)
        
        # Status bar
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #16a34a; font-size: 13px; padding: 5px;")
        layout.addWidget(self.status_label)
        
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
                self.status_label.setStyleSheet("color: #16a34a; font-size: 13px; padding: 5px;")
        except Exception as e:
            self.status_label.setText(f"❌ Error: {str(e)}")
            self.status_label.setStyleSheet("color: #dc2626; font-size: 13px; padding: 5px;")
    
    def update_table(self):
        """Update the table with orders data"""
        self.table.setRowCount(len(self.orders_data))
        
        for row, order in enumerate(self.orders_data):
            # Student name
            name_item = QTableWidgetItem(order.get("studentName", "N/A"))
            name_item.setFont(QFont("Arial", 13, QFont.Weight.Bold))
            self.table.setItem(row, 0, name_item)
            
            # Mobile
            mobile_item = QTableWidgetItem(order.get("mobile", "N/A"))
            mobile_item.setFont(QFont("Arial", 12))
            mobile_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 1, mobile_item)
            
            # File name
            file_item = QTableWidgetItem(order.get("fileName", "N/A"))
            file_item.setFont(QFont("Arial", 12))
            self.table.setItem(row, 2, file_item)
            
            # Pages
            pages_item = QTableWidgetItem(str(order.get("pages", 0)))
            pages_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            pages_item.setFont(QFont("Arial", 12))
            self.table.setItem(row, 3, pages_item)
            
            # Copies
            copies_item = QTableWidgetItem(str(order.get("copies", 1)))
            copies_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            copies_item.setFont(QFont("Arial", 12))
            self.table.setItem(row, 4, copies_item)
            
            # Type
            color = "Color" if order.get("color") == "color" else "B&W"
            type_item = QTableWidgetItem(color)
            type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            type_item.setFont(QFont("Arial", 12))
            self.table.setItem(row, 5, type_item)
            
            # Status
            status = order.get("status", "Unknown")
            status_item = QTableWidgetItem(status)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            status_item.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            
            # Color code status
            if status == "Pending":
                status_item.setBackground(QColor("#fef3c7"))
                status_item.setForeground(QColor("#92400e"))
            elif status == "Queued":
                status_item.setBackground(QColor("#dbeafe"))
                status_item.setForeground(QColor("#1e40af"))
            elif status == "Printing":
                status_item.setBackground(QColor("#fed7aa"))
                status_item.setForeground(QColor("#9a3412"))
            elif status == "Ready":
                status_item.setBackground(QColor("#d1fae5"))
                status_item.setForeground(QColor("#065f46"))
            
            self.table.setItem(row, 6, status_item)
            
            # Set row height
            self.table.setRowHeight(row, 50)
    
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
            self.cancel_btn.setEnabled(status in ["Pending", "Queued", "Printing"])
            self.view_file_btn.setEnabled(True)  # Always enabled if order is selected
        else:
            self.selected_order = None
            self.print_btn.setEnabled(False)
            self.ready_btn.setEnabled(False)
            self.collected_btn.setEnabled(False)
            self.cancel_btn.setEnabled(False)
            self.view_file_btn.setEnabled(False)
    
    def send_to_printer(self):
        """Send order to printer using Windows PrintTo verb"""
        if not self.selected_order:
            return
        
        order_id = self.selected_order.get("id")
        file_path = self.selected_order.get("filePath")
        
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self, "Error", "File not found for this order")
            return
        
        try:
            printers_response = requests.get(f"{API_BASE}/printers")
            if printers_response.status_code != 200:
                QMessageBox.warning(self, "Error", "Cannot load printers")
                return
            
            printers = printers_response.json()
            if not printers:
                discover_response = requests.get(f"{API_BASE}/printers/discover/system")
                if discover_response.status_code == 200:
                    printers_response = requests.get(f"{API_BASE}/printers")
                    printers = printers_response.json()
                
                if not printers:
                    QMessageBox.warning(self, "Error", "No printers available")
                    return
            
            # Show printer selection
            from PyQt6.QtWidgets import QInputDialog
            printer_names = [p.get('name') for p in printers]
            
            selected_printer_name, ok = QInputDialog.getItem(
                self, 
                "Select Printer",
                "Choose printer:",
                printer_names,
                0,
                False
            )
            
            if not ok:
                return
            
            # Copy file to temp location
            temp_path = os.path.join(TEMP_PRINT_DIR, f"{order_id}.pdf")
            shutil.copy(file_path, temp_path)
            
            # Print using Windows PrintTo verb
            system_print(temp_path, selected_printer_name)
            
            # Update order status to Printing
            response = requests.patch(f"{API_BASE}/orders/{order_id}",
                                    json={"status": "Printing", "progressPct": 50})
            
            if response.status_code == 200:
                QMessageBox.information(self, "Success", 
                    f"Printing on: {selected_printer_name}\n\nDocument is being printed...")
                self.load_orders()
            else:
                QMessageBox.warning(self, "Warning", "Print sent but status update failed")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Print failed: {str(e)}")
    
    def mark_ready(self):
        """Mark order as ready and clean up temp files"""
        if not self.selected_order:
            return
        
        order_id = self.selected_order.get("id")
        
        try:
            # Clean up temp print file
            temp_path = os.path.join(TEMP_PRINT_DIR, f"{order_id}.pdf")
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass  # Ignore if file is locked or already deleted
            
            response = requests.patch(f"{API_BASE}/orders/{order_id}",
                                    json={"status": "Ready", "progressPct": 100})
            if response.status_code == 200:
                QMessageBox.information(self, "Success", "Order is ready for pickup!")
                self.load_orders()
            else:
                QMessageBox.warning(self, "Error", "Failed to update")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
    
    def mark_collected(self):
        """Mark order as collected"""
        if not self.selected_order:
            return
        
        order_id = self.selected_order.get("id")
        
        try:
            response = requests.patch(f"{API_BASE}/orders/{order_id}",
                                    json={"status": "Collected"})
            if response.status_code == 200:
                QMessageBox.information(self, "Success", "Order collected!")
                self.load_orders()
            else:
                QMessageBox.warning(self, "Error", "Failed to update")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
    
    def cancel_order(self):
        """Cancel order"""
        if not self.selected_order:
            return
        
        order_id = self.selected_order.get("id")
        student = self.selected_order.get("studentName", "Student")
        
        # Confirm cancellation
        reply = QMessageBox.question(
            self,
            "Cancel Order",
            f"Cancel order for {student}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                response = requests.patch(f"{API_BASE}/orders/{order_id}",
                                        json={"status": "Cancelled"})
                if response.status_code == 200:
                    QMessageBox.information(self, "Success", "Order cancelled")
                    self.load_orders()
                else:
                    QMessageBox.warning(self, "Error", "Failed to cancel")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
    
    def view_file(self):
        """Open the uploaded file"""
        if not self.selected_order:
            return
        
        file_path = self.selected_order.get("filePath")
        
        if not file_path:
            QMessageBox.warning(self, "Error", "No file attached to this order")
            return
        
        import os
        import subprocess
        
        # Check if file exists
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "Error", f"File not found:\n{file_path}")
            return
        
        try:
            # Open file with default application
            os.startfile(file_path)
            self.status_label.setText(f"✅ Opened: {os.path.basename(file_path)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open file:\n{str(e)}")


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
