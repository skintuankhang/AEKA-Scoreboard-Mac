import json
import os
import sys
import serial
import serial.tools.list_ports
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QPushButton, QLabel, QGroupBox, QMessageBox, QComboBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal



def get_install_dir():
    if getattr(sys, 'frozen', False) or '__compiled__' in globals():
        return os.path.dirname(os.path.abspath(sys.argv[0]))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Gán thẳng biến môi trường cho keymap
KEYMAP_FILE = os.path.join(get_install_dir(), "keymap.json")

# ==========================================
# LUỒNG CHẠY NGẦM: CHUYÊN ĐỌC CỔNG COM
# ==========================================
class SerialReader(QThread):
    # Tín hiệu phát ra khi nhận được chữ (ví dụ: 'A', 'B', 'C')
    data_received = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, port, baud=115200):
        super().__init__()
        self.port = port
        self.baud = baud
        self.running = True
        self.ser = None

    def run(self):
        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=1)
            while self.running:
                if self.ser.in_waiting > 0:
                    # Đọc dòng, giải mã và xóa khoảng trắng/xuống dòng
                    line = self.ser.readline().decode('utf-8').strip()
                    if line:
                        # Bắn chữ nhận được lên cho Giao diện chính
                        self.data_received.emit(line)
        except Exception as e:
            self.error_signal.emit(str(e))

    def stop(self):
        self.running = False
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.quit()
        self.wait()

# ==========================================
# GIAO DIỆN CHÍNH
# ==========================================
class KeymapDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("DEV TOOL - GÁN MÃ PHÍM TAY CẦM & HỆ THỐNG")
        self.resize(900, 750) 
        self.setStyleSheet("""
            QDialog { background-color: #1E1E24; color: white; font-family: Arial; }
            QGroupBox { font-weight: bold; border: 2px solid #555; border-radius: 8px; margin-top: 15px; padding-top: 15px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; color: #00FFB2; }
            QPushButton { background-color: #2D2D3B; border: 1px solid #444; border-radius: 4px; padding: 10px; color: white; font-weight: bold; }
            QPushButton:hover { border: 1px solid #00FFB2; }
            QPushButton.listening { background-color: #A03333; border: 2px solid #FF3333; color: yellow; }
            QComboBox { background-color: #2D2D3B; color: white; padding: 5px; border: 1px solid #444; }
        """)

        self.key_dict = {}
        self.listening_btn = None 
        self.listening_data = None 
        self.btn_map = {} 
        self.serial_thread = None # Chứa luồng đọc COM

        self.setup_ui()
        self.load_current_keymap()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        lbl_info = QLabel("AEKA KEYMAP CONFIG - KẾT NỐI BÀN PHÍM RỜI")
        lbl_info.setStyleSheet("color: #FFD700; font-size: 14px; font-weight: bold;")
        lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(lbl_info)

        # ==========================================
        # 0. KHU VỰC KẾT NỐI CỔNG COM
        # ==========================================
        com_layout = QHBoxLayout()
        com_layout.addWidget(QLabel("Chọn cổng (Cục Thu):"))
        
        self.com_combo = QComboBox()
        # Lấy danh sách các cổng COM đang cắm vào máy
        ports = serial.tools.list_ports.comports()
        for port, desc, hwid in sorted(ports):
            self.com_combo.addItem(f"{port} - {desc}", port)
            
        com_layout.addWidget(self.com_combo)

        self.btn_connect = QPushButton("KẾT NỐI TAY CẦM")
        self.btn_connect.setStyleSheet("background-color: #006699;")
        self.btn_connect.clicked.connect(self.toggle_serial)
        com_layout.addWidget(self.btn_connect)
        
        main_layout.addLayout(com_layout)

        # ==========================================
        # 1. KHU VỰC PHÍM TAY CẦM TRỌNG TÀI
        # ==========================================
        group_judges = QGroupBox("PHÍM TAY CẦM (3 TRỌNG TÀI)")
        grid = QGridLayout(group_judges)
        
        # --- Sửa khu vực tạo bảng gán phím trong ui/keymap_window.py ---
        grid.addWidget(QLabel("LOẠI ĐÒN"), 0, 1, alignment=Qt.AlignmentFlag.AlignCenter)
        grid.addWidget(QLabel("TRỌNG TÀI 1"), 0, 2, alignment=Qt.AlignmentFlag.AlignCenter)
        grid.addWidget(QLabel("TRỌNG TÀI 2"), 0, 3, alignment=Qt.AlignmentFlag.AlignCenter)
        grid.addWidget(QLabel("TRỌNG TÀI 3"), 0, 4, alignment=Qt.AlignmentFlag.AlignCenter)
        # 🔥 Thêm tiêu đề cột 4
        lbl_t4 = QLabel("TAY 4 (DỰ PHÒNG)")
        lbl_t4.setStyleSheet("color: #FFD700;")
        grid.addWidget(lbl_t4, 0, 5, alignment=Qt.AlignmentFlag.AlignCenter)

        actions = [
            ("XANH ĐẤM", "B1"), ("XANH BỤNG", "B2"), ("XANH ĐẦU", "B3"), ("XANH XOAY", "BT"),
            ("ĐỎ ĐẤM", "R1"), ("ĐỎ BỤNG", "R2"), ("ĐỎ ĐẦU", "R3"), ("ĐỎ XOAY", "RT")
        ]

        for row, (label, act_code) in enumerate(actions, start=1):
            lbl = QLabel(label)
            lbl.setStyleSheet("color: #6699FF;" if "XANH" in label else "color: #FF6666;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            grid.addWidget(lbl, row, 1)

            # 🔥 Đổi list [1, 2, 3] thành [1, 2, 3, 4] để nó vẽ thêm nút
            for judge in [1, 2, 3, 4]:
                btn = QPushButton("Chưa gán")
                btn.clicked.connect(lambda checked, b=btn, j=judge, a=act_code: self.start_listening(b, j, a))
                grid.addWidget(btn, row, judge + 1)
                self.btn_map[(judge, act_code)] = btn

        main_layout.addWidget(group_judges)

        # ==========================================
        # 2. KHU VỰC PHÍM HỆ THỐNG
        # ==========================================
        sys_group = QGroupBox("PHÍM HỆ THỐNG (DÙNG CHO BÀN PHÍM RỜI LÀ CHÍNH)")
        sys_group.setStyleSheet("QGroupBox { border: 2px solid #A03333; } QGroupBox::title { color: #FF9999; }")
        sys_layout = QGridLayout(sys_group)
        
        sys_actions = [
            ("TẠM DỪNG TIME", "SYS_PAUSE"),
            ("ĐỎ +1 LỖI", "R_GJ_PLUS"), ("ĐỎ -1 LỖI", "R_GJ_MINUS"),
            ("XANH +1 LỖI", "B_GJ_PLUS"), ("XANH -1 LỖI", "B_GJ_MINUS"),
            ("ĐỎ ĐỔI NGƯỜI", "R_SUB"), ("XANH ĐỔI NGƯỜI", "B_SUB")
        ]
        
        for i, (label, act_code) in enumerate(sys_actions):
            row = i // 2
            col = (i % 2) * 2
            
            lbl = QLabel(label)
            if "ĐỎ" in label: lbl.setStyleSheet("color: #FF6666; font-weight: bold;")
            elif "XANH" in label: lbl.setStyleSheet("color: #6699FF; font-weight: bold;")
            else: lbl.setStyleSheet("color: #FFD700; font-weight: bold;")
            
            btn = QPushButton("Chưa gán")
            btn.clicked.connect(lambda checked, b=btn, a=act_code: self.start_listening(b, "SYS", a))
            
            sys_layout.addWidget(lbl, row, col, alignment=Qt.AlignmentFlag.AlignRight)
            sys_layout.addWidget(btn, row, col+1)
            self.btn_map[("SYS", act_code)] = btn
            
        main_layout.addWidget(sys_group)

        # Nút lưu
        btn_save = QPushButton("💾 LƯU KEYMAP (JSON)")
        btn_save.setStyleSheet("background-color: #008855; font-size: 16px; padding: 15px; margin-top: 10px;")
        btn_save.clicked.connect(self.save_keymap)
        main_layout.addWidget(btn_save)

    # ==========================================
    # CÁC HÀM XỬ LÝ LOGIC
    # ==========================================
    def toggle_serial(self):
        """Bật/Tắt kết nối với cổng COM"""
        if self.serial_thread and self.serial_thread.running:
            self.serial_thread.stop()
            self.serial_thread = None
            self.btn_connect.setText("KẾT NỐI TAY CẦM")
            self.btn_connect.setStyleSheet("background-color: #006699;")
            self.com_combo.setEnabled(True)
        else:
            port = self.com_combo.currentData()
            if not port:
                QMessageBox.warning(self, "Lỗi", "Chưa có cổng nào được chọn!")
                return
                
            self.serial_thread = SerialReader(port, 115200)
            self.serial_thread.data_received.connect(self.handle_incoming_key)
            self.serial_thread.error_signal.connect(self.handle_serial_error)
            self.serial_thread.start()
            
            self.btn_connect.setText("🛑 NGẮT KẾT NỐI")
            self.btn_connect.setStyleSheet("background-color: #A03333;")
            self.com_combo.setEnabled(False)

    def handle_serial_error(self, err_msg):
        QMessageBox.critical(self, "Lỗi Serial", f"Mất kết nối cổng:\n{err_msg}")
        self.toggle_serial() # Tự động tắt nút nếu lỗi

    def load_current_keymap(self):
        if os.path.exists(KEYMAP_FILE):
            with open(KEYMAP_FILE, 'r') as f:
                data = json.load(f)
                for keycode_str, val in data.items():
                    judge, act = val
                    parsed_judge = judge if judge == "SYS" else int(judge)
                    
                    # Giữ nguyên kiểu chuỗi (String) cho keycode_str 
                    # vì cổng COM sẽ gửi 'A', 'B', 'C' chứ không gửi số nguyên
                    self.key_dict[keycode_str] = (parsed_judge, act)
                    
                    if (parsed_judge, act) in self.btn_map:
                        self.btn_map[(parsed_judge, act)].setText(f"Key: {keycode_str}")

    def start_listening(self, btn, judge, action):
        if self.listening_btn:
            self.listening_btn.setProperty("listening", False)
            self.listening_btn.style().unpolish(self.listening_btn)
            self.listening_btn.style().polish(self.listening_btn)

        self.listening_btn = btn
        self.listening_data = (judge, action)
        
        btn.setProperty("listening", True)
        btn.style().unpolish(btn)
        btn.style().polish(btn)
        btn.setText("Đang chờ phím...")

    def handle_incoming_key(self, keycode):
        """Hàm dùng chung để lưu phím: Xử lý cả Bàn phím (số) và Cổng COM (chữ)"""
        if self.listening_btn:
            # Ép về String để lưu đồng nhất vào JSON
            keycode_str = str(keycode) 
            
            keys_to_delete = [k for k, v in self.key_dict.items() if v == self.listening_data]
            for k in keys_to_delete: del self.key_dict[k]
            
            self.key_dict[keycode_str] = self.listening_data
            self.listening_btn.setText(f"Key: {keycode_str}")
            
            self.listening_btn.setProperty("listening", False)
            self.listening_btn.style().unpolish(self.listening_btn)
            self.listening_btn.style().polish(self.listening_btn)
            self.listening_btn = None
            self.listening_data = None

    def keyPressEvent(self, event):
        """Vẫn bắt phím từ bàn phím vật lý để gán cho các phím Hệ Thống"""
        if self.listening_btn:
            # Lấy mã ASCII của bàn phím và đẩy chung vào hàm xử lý
            self.handle_incoming_key(event.key())
        else:
            super().keyPressEvent(event)

    def save_keymap(self):
        with open(KEYMAP_FILE, 'w') as f:
            json.dump(self.key_dict, f, indent=4)
        QMessageBox.information(self, "Thành công", "Đã lưu mã phím thành công vào keymap.json!")
        self.accept()
        
    def closeEvent(self, event):
        """Đảm bảo tắt luồng COM an toàn khi tắt cửa sổ"""
        if self.serial_thread:
            self.serial_thread.stop()
        super().closeEvent(event)