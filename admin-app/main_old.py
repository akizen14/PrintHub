import sys
import hashlib
import requests
import math
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QListWidget, QListWidgetItem, QPushButton, QLabel,
    QComboBox, QDialog, QLineEdit, QFormLayout, QMessageBox,
    QProgressBar, QGroupBox, QGridLayout, QSplitter
)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont

API_BASE = "http://localhost:8000"

# Status colors
STATUS_COLORS = {
    "Pending": "#9CA3AF",
    "Queued": "#3B82F6",
    "Printing": "#F59E0B",
    "Ready": "#10B981",
    "Collected": "#6B7280",
    "Cancelled": "#EF4444",
    "Error": "#EF4444",
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
                if settings["adminPassHash"] == password_hash:
                    self.accept()
                else:
                    QMessageBox.warning(self, "Error", "Invalid passcode")
            else:
                QMessageBox.warning(self, "Error", "Failed to verify credentials")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Connection failed: {str(e)}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PrintHub Admin")
        self.setGeometry(100, 100, 1200, 700)
        
        # Data storage
        self.orders = []
        self.printers = []
        self.selected_order = None
        self.printing_jobs = {}  # {order_id: {"timer": QTimer, "start_time": int, "estimated_sec": int}}
        
        # Create UI
        self.init_ui()
        
        # Start polling timer
        self.poll_timer = QTimer()
        self.poll_timer.timeout.connect(self.poll_data)
        self.poll_timer.start(2000)  # Poll every 2 seconds
        
        # Initial load
        self.poll_data()
    
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Tabs
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Queues Tab
        self.queues_tab = self.create_queues_tab()
        self.tabs.addTab(self.queues_tab, "Queues")
        
        # Printers Tab
        self.printers_tab = self.create_printers_tab()
        self.tabs.addTab(self.printers_tab, "Printers")
    
    def create_queues_tab(self):
        widget = QWidget()
        layout = QHBoxLayout()
        widget.setLayout(layout)
        
        # Left side: Queue lists
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)
        
        # Urgent Queue
        urgent_label = QLabel("🔴 Urgent Queue")
        urgent_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        left_layout.addWidget(urgent_label)
        
        self.urgent_list = QListWidget()
        self.urgent_list.itemClicked.connect(self.on_order_selected)
        left_layout.addWidget(self.urgent_list)
        
        # Normal Queue
        normal_label = QLabel("🟢 Normal Queue")
        normal_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        left_layout.addWidget(normal_label)
        
        self.normal_list = QListWidget()
        self.normal_list.itemClicked.connect(self.on_order_selected)
        left_layout.addWidget(self.normal_list)
        
        # Bulk Queue
        bulk_label = QLabel("🟡 Bulk Queue")
        bulk_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        left_layout.addWidget(bulk_label)
        
        self.bulk_list = QListWidget()
        self.bulk_list.itemClicked.connect(self.on_order_selected)
        left_layout.addWidget(self.bulk_list)
        
        # Right side: Actions
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)
        
        actions_label = QLabel("Order Actions")
        actions_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        right_layout.addWidget(actions_label)
        
        self.order_details = QLabel("Select an order to view details")
        self.order_details.setWordWrap(True)
        right_layout.addWidget(self.order_details)
        
        # Printer assignment
        printer_group = QGroupBox("Assign Printer")
        printer_layout = QVBoxLayout()
        printer_group.setLayout(printer_layout)
        
        self.printer_combo = QComboBox()
        printer_layout.addWidget(self.printer_combo)
        
        self.assign_btn = QPushButton("Assign Printer")
        self.assign_btn.clicked.connect(self.assign_printer)
        self.assign_btn.setEnabled(False)
        printer_layout.addWidget(self.assign_btn)
        
        right_layout.addWidget(printer_group)
        
        # Job control
        control_group = QGroupBox("Job Control")
        control_layout = QVBoxLayout()
        control_group.setLayout(control_layout)
        
        self.start_btn = QPushButton("Start Printing")
        self.start_btn.clicked.connect(self.start_printing)
        self.start_btn.setEnabled(False)
        control_layout.addWidget(self.start_btn)
        
        self.complete_btn = QPushButton("Mark Complete")
        self.complete_btn.clicked.connect(self.complete_job)
        self.complete_btn.setEnabled(False)
        control_layout.addWidget(self.complete_btn)
        
        self.cancel_btn = QPushButton("Cancel Order")
        self.cancel_btn.clicked.connect(self.cancel_order)
        self.cancel_btn.setEnabled(False)
        control_layout.addWidget(self.cancel_btn)
        
        right_layout.addWidget(control_group)
        
        # Priority control
        priority_group = QGroupBox("Priority Control")
        priority_layout = QHBoxLayout()
        priority_group.setLayout(priority_layout)
        
        self.priority_up_btn = QPushButton("↑ Move Up")
        self.priority_up_btn.clicked.connect(self.move_priority_up)
        self.priority_up_btn.setEnabled(False)
        priority_layout.addWidget(self.priority_up_btn)
        
        self.priority_down_btn = QPushButton("↓ Move Down")
        self.priority_down_btn.clicked.connect(self.move_priority_down)
        self.priority_down_btn.setEnabled(False)
        priority_layout.addWidget(self.priority_down_btn)
        
        right_layout.addWidget(priority_group)
        
        right_layout.addStretch()
        
        # Add panels to splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        
        layout.addWidget(splitter)
        
        return widget
    
    def create_printers_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        title = QLabel("Printers")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        self.printers_grid = QGridLayout()
        layout.addLayout(self.printers_grid)
        
        layout.addStretch()
        
        return widget
    
    def poll_data(self):
        """Poll backend for orders and printers"""
        try:
            # Get orders
            response = requests.get(f"{API_BASE}/orders", params={"status": "Pending|Queued|Printing"})
            if response.status_code == 200:
                self.orders = response.json()
                self.update_queue_lists()
            
            # Get printers
            response = requests.get(f"{API_BASE}/printers")
            if response.status_code == 200:
                self.printers = response.json()
                self.update_printer_combo()
                self.update_printers_display()
        except Exception as e:
            print(f"Poll error: {e}")
    
    def update_queue_lists(self):
        """Update the three queue lists"""
        self.urgent_list.clear()
        self.normal_list.clear()
        self.bulk_list.clear()
        
        for order in self.orders:
            item_text = f"{order['studentName']} - {order['fileName']}\n{order['pages']}×{order['copies']} | {order['status']}"
            if order.get('assignedPrinterId'):
                printer = next((p for p in self.printers if p['id'] == order['assignedPrinterId']), None)
                if printer:
                    item_text += f" | {printer['name']}"
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, order)
            
            if order['queueType'] == 'urgent':
                self.urgent_list.addItem(item)
            elif order['queueType'] == 'normal':
                self.normal_list.addItem(item)
            else:  # bulk
                self.bulk_list.addItem(item)
    
    def update_printer_combo(self):
        """Update printer dropdown"""
        current = self.printer_combo.currentText()
        self.printer_combo.clear()
        
        online_printers = [p for p in self.printers if p['status'] in ['idle', 'printing']]
        for printer in online_printers:
            self.printer_combo.addItem(f"{printer['name']} ({printer['status']})", printer['id'])
        
        # Restore selection if possible
        index = self.printer_combo.findText(current)
        if index >= 0:
            self.printer_combo.setCurrentIndex(index)
    
    def update_printers_display(self):
        """Update printers grid display"""
        # Clear existing widgets
        while self.printers_grid.count():
            item = self.printers_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add printer cards
        row, col = 0, 0
        for printer in self.printers:
            card = self.create_printer_card(printer)
            self.printers_grid.addWidget(card, row, col)
            col += 1
            if col >= 2:
                col = 0
                row += 1
    
    def create_printer_card(self, printer):
        """Create a printer status card"""
        card = QGroupBox(printer['name'])
        layout = QVBoxLayout()
        card.setLayout(layout)
        
        # Status
        status_label = QLabel(f"Status: {printer['status']}")
        status_label.setStyleSheet(f"color: {STATUS_COLORS.get(printer['status'].capitalize(), '#000')};")
        layout.addWidget(status_label)
        
        # Specs
        specs = QLabel(f"Speed: {printer['ppm']} ppm")
        layout.addWidget(specs)
        
        # Current job
        if printer.get('currentJobId'):
            job_order = next((o for o in self.orders if o['id'] == printer['currentJobId']), None)
            if job_order:
                job_label = QLabel(f"Job: {job_order['fileName']}")
                layout.addWidget(job_label)
                
                progress = QProgressBar()
                progress.setValue(printer.get('progressPct', 0))
                layout.addWidget(progress)
        else:
            idle_label = QLabel("No active job")
            idle_label.setStyleSheet("color: #6B7280;")
            layout.addWidget(idle_label)
        
        # Actions
        actions_layout = QHBoxLayout()
        
        if printer['status'] != 'idle':
            idle_btn = QPushButton("Set Idle")
            idle_btn.clicked.connect(lambda: self.set_printer_idle(printer['id']))
            actions_layout.addWidget(idle_btn)
        
        if printer['status'] != 'offline':
            offline_btn = QPushButton("Set Offline")
            offline_btn.clicked.connect(lambda: self.set_printer_offline(printer['id']))
            actions_layout.addWidget(offline_btn)
        
        layout.addLayout(actions_layout)
        
        return card
    
    def on_order_selected(self, item):
        """Handle order selection"""
        self.selected_order = item.data(Qt.ItemDataRole.UserRole)
        
        # Update details
        order = self.selected_order
        details = f"""
<b>Student:</b> {order['studentName']}<br>
<b>Mobile:</b> {order['mobile']}<br>
<b>File:</b> {order['fileName']}<br>
<b>Pages:</b> {order['pages']} × {order['copies']} copies<br>
<b>Type:</b> {order['color']} / {order['sides']} / {order['size']}<br>
<b>Status:</b> {order['status']}<br>
<b>Price:</b> ₹{order['priceTotal']:.2f}
        """
        self.order_details.setText(details)
        
        # Enable/disable buttons
        self.assign_btn.setEnabled(order['status'] in ['Pending', 'Queued'])
        self.start_btn.setEnabled(order['status'] == 'Queued' and order.get('assignedPrinterId'))
        self.complete_btn.setEnabled(order['status'] == 'Printing')
        self.cancel_btn.setEnabled(order['status'] not in ['Ready', 'Collected', 'Cancelled'])
        self.priority_up_btn.setEnabled(True)
        self.priority_down_btn.setEnabled(True)
    
    def assign_printer(self):
        """Assign selected printer to order"""
        if not self.selected_order:
            return
        
        printer_id = self.printer_combo.currentData()
        if not printer_id:
            QMessageBox.warning(self, "Error", "No printer selected")
            return
        
        try:
            response = requests.patch(
                f"{API_BASE}/orders/{self.selected_order['id']}",
                json={"assignedPrinterId": printer_id, "status": "Queued"}
            )
            if response.status_code == 200:
                QMessageBox.information(self, "Success", "Printer assigned")
                self.poll_data()
            else:
                QMessageBox.warning(self, "Error", "Failed to assign printer")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
    
    def start_printing(self):
        """Start printing job"""
        if not self.selected_order:
            return
        
        order = self.selected_order
        printer = next((p for p in self.printers if p['id'] == order.get('assignedPrinterId')), None)
        
        if not printer:
            QMessageBox.warning(self, "Error", "No printer assigned")
            return
        
        # Calculate estimated time
        total_pages = order['pages'] * order['copies']
        estimated_sec = math.ceil((total_pages / printer['ppm']) * 60)
        
        try:
            # Update order status
            response = requests.patch(
                f"{API_BASE}/orders/{order['id']}",
                json={"status": "Printing", "estimatedSec": estimated_sec, "progressPct": 0}
            )
            
            # Update printer status
            requests.patch(
                f"{API_BASE}/printers/{printer['id']}",
                json={"status": "printing", "currentJobId": order['id'], "progressPct": 0}
            )
            
            if response.status_code == 200:
                # Start progress timer
                self.start_progress_timer(order['id'], estimated_sec)
                QMessageBox.information(self, "Success", "Printing started")
                self.poll_data()
            else:
                QMessageBox.warning(self, "Error", "Failed to start printing")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
    
    def start_progress_timer(self, order_id, estimated_sec):
        """Start a timer to simulate printing progress"""
        if order_id in self.printing_jobs:
            return
        
        timer = QTimer()
        self.printing_jobs[order_id] = {
            "timer": timer,
            "progress": 0,
            "estimated_sec": estimated_sec
        }
        
        def update_progress():
            job = self.printing_jobs.get(order_id)
            if not job:
                timer.stop()
                return
            
            job["progress"] += 1
            progress_pct = min(int((job["progress"] / job["estimated_sec"]) * 100), 100)
            
            try:
                # Update order progress
                requests.patch(
                    f"{API_BASE}/orders/{order_id}",
                    json={"progressPct": progress_pct}
                )
                
                # Update printer progress
                order = next((o for o in self.orders if o['id'] == order_id), None)
                if order and order.get('assignedPrinterId'):
                    requests.patch(
                        f"{API_BASE}/printers/{order['assignedPrinterId']}",
                        json={"progressPct": progress_pct}
                    )
                
                # Auto-complete at 100%
                if progress_pct >= 100:
                    timer.stop()
                    del self.printing_jobs[order_id]
                    self.auto_complete_job(order_id)
            except Exception as e:
                print(f"Progress update error: {e}")
        
        timer.timeout.connect(update_progress)
        timer.start(1000)  # Update every second
    
    def auto_complete_job(self, order_id):
        """Auto-complete job when progress reaches 100%"""
        try:
            order = next((o for o in self.orders if o['id'] == order_id), None)
            if order:
                requests.patch(
                    f"{API_BASE}/orders/{order_id}",
                    json={"status": "Ready", "progressPct": 100}
                )
                
                if order.get('assignedPrinterId'):
                    requests.patch(
                        f"{API_BASE}/printers/{order['assignedPrinterId']}",
                        json={"status": "idle", "currentJobId": None, "progressPct": 0}
                    )
                
                self.poll_data()
        except Exception as e:
            print(f"Auto-complete error: {e}")
    
    def complete_job(self):
        """Manually mark job as complete"""
        if not self.selected_order:
            return
        
        order = self.selected_order
        
        try:
            # Stop progress timer if running
            if order['id'] in self.printing_jobs:
                self.printing_jobs[order['id']]["timer"].stop()
                del self.printing_jobs[order['id']]
            
            # Update order
            requests.patch(
                f"{API_BASE}/orders/{order['id']}",
                json={"status": "Ready", "progressPct": 100}
            )
            
            # Update printer
            if order.get('assignedPrinterId'):
                requests.patch(
                    f"{API_BASE}/printers/{order['assignedPrinterId']}",
                    json={"status": "idle", "currentJobId": None, "progressPct": 0}
                )
            
            QMessageBox.information(self, "Success", "Job marked as complete")
            self.poll_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
    
    def cancel_order(self):
        """Cancel order"""
        if not self.selected_order:
            return
        
        reply = QMessageBox.question(
            self, "Confirm", "Cancel this order?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                order = self.selected_order
                
                # Stop progress timer if running
                if order['id'] in self.printing_jobs:
                    self.printing_jobs[order['id']]["timer"].stop()
                    del self.printing_jobs[order['id']]
                
                requests.patch(
                    f"{API_BASE}/orders/{order['id']}",
                    json={"status": "Cancelled"}
                )
                
                # Free up printer if assigned
                if order.get('assignedPrinterId'):
                    requests.patch(
                        f"{API_BASE}/printers/{order['assignedPrinterId']}",
                        json={"status": "idle", "currentJobId": None, "progressPct": 0}
                    )
                
                QMessageBox.information(self, "Success", "Order cancelled")
                self.poll_data()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
    
    def move_priority_up(self):
        """Move order priority up"""
        if not self.selected_order:
            return
        
        order = self.selected_order
        queue_orders = [o for o in self.orders if o['queueType'] == order['queueType']]
        queue_orders.sort(key=lambda x: x['priorityIndex'])
        
        current_idx = next((i for i, o in enumerate(queue_orders) if o['id'] == order['id']), None)
        if current_idx is None or current_idx == 0:
            return
        
        # Calculate new priority index (midpoint with previous)
        prev_order = queue_orders[current_idx - 1]
        new_priority = (prev_order['priorityIndex'] + order['priorityIndex']) // 2
        
        if new_priority == order['priorityIndex']:
            # Need to reindex
            QMessageBox.information(self, "Info", "Reindexing queue...")
            return
        
        try:
            requests.patch(
                f"{API_BASE}/orders/{order['id']}",
                json={"priorityIndex": new_priority}
            )
            self.poll_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
    
    def move_priority_down(self):
        """Move order priority down"""
        if not self.selected_order:
            return
        
        order = self.selected_order
        queue_orders = [o for o in self.orders if o['queueType'] == order['queueType']]
        queue_orders.sort(key=lambda x: x['priorityIndex'])
        
        current_idx = next((i for i, o in enumerate(queue_orders) if o['id'] == order['id']), None)
        if current_idx is None or current_idx == len(queue_orders) - 1:
            return
        
        # Calculate new priority index (midpoint with next)
        next_order = queue_orders[current_idx + 1]
        new_priority = (order['priorityIndex'] + next_order['priorityIndex']) // 2
        
        if new_priority == order['priorityIndex']:
            # Need to reindex
            QMessageBox.information(self, "Info", "Reindexing queue...")
            return
        
        try:
            requests.patch(
                f"{API_BASE}/orders/{order['id']}",
                json={"priorityIndex": new_priority}
            )
            self.poll_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
    
    def set_printer_idle(self, printer_id):
        """Set printer to idle"""
        try:
            requests.patch(
                f"{API_BASE}/printers/{printer_id}",
                json={"status": "idle", "currentJobId": None, "progressPct": 0}
            )
            self.poll_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
    
    def set_printer_offline(self, printer_id):
        """Set printer to offline"""
        try:
            requests.patch(
                f"{API_BASE}/printers/{printer_id}",
                json={"status": "offline"}
            )
            self.poll_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


def main():
    app = QApplication(sys.argv)
    
    # Show login dialog
    login = LoginDialog()
    if login.exec() != QDialog.DialogCode.Accepted:
        sys.exit(0)
    
    # Show main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
