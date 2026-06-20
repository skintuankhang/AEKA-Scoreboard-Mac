import os
import serial.tools.list_ports
from ui.keymap_window import KeymapDialog, SerialReader
import sys
import json
import time
import math
import csv
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QGroupBox, QPushButton, QLabel, QLineEdit, QCheckBox,
                             QComboBox, QTableWidget, QHeaderView, QMessageBox, QFrame, 
                             QMenu, QFileDialog, QTextEdit, QTableWidgetItem, QDialog, 
                             QRadioButton, QSizePolicy, QSplitter)
from PyQt6.QtGui import QPixmap, QPainter, QPen, QColor, QIntValidator
from PyQt6.QtCore import Qt, QTimer, QEvent
from core.engine import ScoreEngine
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QUrl


# Centralized UI strings to simplify translations and switching languages.
TEXTS = {
    'VI': {
        'btn_lang_toggle': "🌐 Đổi Ngôn Ngữ (EN)",
        'window_title': "AEKA Control Panel - Bàn Thư Ký",
        'btn_dev_keymap': "⚙️ CÀI ĐẶT MÃ PHÍM TAY CẦM (DEV)",
        'btn_connect_com_default': "KẾT NỐI TAY CẦM",
        'group_hotswap_title': "QUẢN LÝ TAY CẦM THAY THẾ",
        'lbl_hw_status': "Trạng thái: Đang dùng Tay 1, 2, 3 chuẩn.",
        'btn_hotswap': "KÍCH HOẠT TAY CẦM DỰ PHÒNG",
        'lbl_live_preview': "Đang tải tín hiệu Tivi...",
        'group_info_title': "THÔNG TIN TRẬN ĐẤU",
        'lbl_red_name_title': "Tên Đỏ:",
        'lbl_blue_name_title': "Tên Xanh:",
        'lbl_match_category_title': "Loại trận:",
        'lbl_match_num_title': "Trận số:",
        'lbl_gender_title': "Giới tính:",
        'lbl_weight_title': "Hạng cân:",
        'radio_bo3': "BO3",
        'radio_team': "Team (150 HP)",
        'btn_update_display': "CẬP NHẬT LÊN MÀN HÌNH TIVI",
        'group_data_title': "DANH SÁCH TRẬN (IMPORT)",
        'btn_import': "Nhập File CSV",
        'table_schedule_headers': ["Trận", "Hạng cân", "Đỏ", "Xanh"],
        'group_preview_title': "MINI PREVIEW (CLONE TIVI)",
        'group_timer_title': "ĐIỀU KHIỂN THỜI GIAN & HIỆP",
        'btn_start_pause': "BẮT ĐẦU / TẠM DỪNG (SPACE)",
        'btn_pause_menu': "TẠM DỪNG CÓ CHỦ ĐÍCH ▾",
        'action_kyeshi': "Dừng Săn Sóc Y Tế (KYESHI - 1 Phút)",
        'action_shigan': "Dừng Xem Xét Video (SHI-GAN)",
        'lbl_round_time_title': "T.Gian 1 Hiệp:",
        'lbl_break_time_title': "Nghỉ Giữa Hiệp:",
        'chk_ptg': "Áp dụng Cách biệt 12đ",
        'chk_pun': "Áp dụng 5 Lỗi Gam-Jeom",
        'btn_reset_timer': "ĐẶT LẠI ĐỒNG HỒ",
        'group_manual_title': "CHỈNH SỬA THỦ CÔNG (VIDEO REPLAY)",
        'lbl_red_title': "BÊN ĐỎ",
        'lbl_blue_title': "BÊN XANH",
        'lbl_action_title': "LOẠI ĐÒN",
        'group_log_title': "LỊCH SỬ THAO TÁC (MATCH LOG)",
        'btn_clear_log': "XÓA LỊCH SỬ LOG",
        'btn_export_log': "XUẤT KẾT QUẢ & LOG (CSV)",
        'actions': ["ĐẤM (Punch)", "BỤNG (Body)", "ĐẦU (Head)", "K.THUẬT BỤNG", "K.THUẬT ĐẦU", "LỖI (Gam-Jeom)"],
        'btn_reset_match': "XÓA ĐIỂM / RESET TRẬN ĐẤU",
        'btn_ivr_red_valid': "IVR ĐỎ:CÒN",
        'btn_ivr_red_rejected': "IVR ĐỎ:HẾT",
        'btn_ivr_blue_valid': "IVR XANH:CÒN",
        'btn_ivr_blue_rejected': "IVR XANH:HẾT",
        'btn_sub_red': "ĐỔI NGƯỜI(+15s)",
        'btn_sub_blue': "ĐỔI NGƯỜI(+15s)",
        'combo_match_category_items': ["VÒNG LOẠI", "TỨ KẾT", "BÁN KẾT", "CHUNG KẾT"],
        'combo_gender_items': ["NAM", "NỮ"]
    },
    'EN': {
        'btn_lang_toggle': "🌐 Switch Language (VI)",
        'window_title': "AEKA Control Panel - Control Desk",
        'btn_dev_keymap': "⚙️ DEV Keymap Tool",
        'btn_connect_com_default': "CONNECT GAMEPAD",
        'group_hotswap_title': "HOTSWAP CONTROLLER",
        'lbl_hw_status': "Status: Using default pads 1,2,3.",
        'btn_hotswap': "ACTIVATE HOTSWAP",
        'lbl_live_preview': "Loading TV signal...",
        'group_info_title': "MATCH INFORMATION",
        'lbl_red_name_title': "Red Name:",
        'lbl_blue_name_title': "Blue Name:",
        'lbl_match_category_title': "Category:",
        'lbl_match_num_title': "Match No:",
        'lbl_gender_title': "Gender:",
        'lbl_weight_title': "Weight:",
        'radio_bo3': "Classic BO3",
        'radio_team': "Team (150 HP)",
        'btn_update_display': "UPDATE TV DISPLAY",
        'group_data_title': "MATCH SCHEDULE (IMPORT)",
        'btn_import': "Import CSV",
        'table_schedule_headers': ["Match", "Weight", "Red", "Blue"],
        'group_preview_title': "MINI PREVIEW (TV CLONE)",
        'group_timer_title': "TIME & ROUND CONTROL",
        'btn_start_pause': "START / STOP MATCH (SPACE)",
        'btn_pause_menu': "OFFICIAL PAUSE ▾",
        'action_kyeshi': "Medical Time-out (KYESHI - 1 Min)",
        'action_shigan': "Video Replay Request (SHI-GAN)",
        'lbl_round_time_title': "Round Duration:",
        'lbl_break_time_title': "Break Duration:",
        'chk_ptg': "Apply 12pt Gap",
        'chk_pun': "Apply 5 Gam-Jeom",
        'btn_reset_timer': "RESET TIMER",
        'group_manual_title': "MANUAL OVERRIDE (VIDEO REPLAY)",
        'lbl_red_title': "RED SIDE",
        'lbl_blue_title': "BLUE SIDE",
        'lbl_action_title': "ACTION",
        'group_log_title': "MATCH LOG",
        'btn_clear_log': "CLEAR MATCH LOG",
        'btn_export_log': "EXPORT RESULT & LOG (CSV)",
        'actions': ["Punch", "Body Kick", "Head Kick", "Tech Body", "Tech Head", "Penalty (Gam-Jeom)"],
        'btn_reset_match': "CLEAR SCORE / RESET MATCH",
        'btn_ivr_red_valid': "RED IVR: VALID",
        'btn_ivr_red_rejected': "RED IVR: REJECTED",
        'btn_ivr_blue_valid': "BLUE IVR: VALID",
        'btn_ivr_blue_rejected': "BLUE IVR: REJECTED",
        'btn_sub_red': "SUBSTITUTE(+15s)",
        'btn_sub_blue': "SUBSTITUTE(+15s)",
        'combo_match_category_items': ["PRELIMINARY", "QUARTER-FINAL", "SEMI-FINAL", "FINAL"],
        'combo_gender_items': ["MALE", "FEMALE"]
    }
}


def get_install_dir():
    if getattr(sys, 'frozen', False) or '__compiled__' in globals():
        return os.path.dirname(os.path.abspath(sys.argv[0]))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_path(relative_path):
    if '__compiled__' in globals():
        base_path = os.path.dirname(__file__)
    elif getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        import __main__
        base_path = os.path.dirname(os.path.abspath(__main__.__file__))
    
    full_path = os.path.join(base_path, relative_path)
    return full_path if os.path.exists(full_path) else relative_path

class RoundEndDialog(QDialog):
    def __init__(self, red_name, blue_name, auto_winner, auto_method, is_vi=True, parent=None):
        super().__init__(parent)
        self.setWindowTitle("KẾT THÚC HIỆP - XÁC NHẬN KẾT QUẢ" if is_vi else "END OF ROUND - CONFIRM RESULT")
        self.setFixedSize(450, 300) 
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        self.setStyleSheet("""
            QDialog { background-color: #1E1E24; color: white; font-family: Arial; border: 2px solid #00FFB2; }
            QLabel { font-size: 16px; font-weight: bold; }
            QComboBox { background-color: #2D2D3B; border: 2px solid #555; padding: 8px; font-size: 16px; font-weight: bold; }
            QPushButton { background-color: #008855; color: white; font-size: 16px; font-weight: bold; padding: 12px; border-radius: 5px; }
            QPushButton:hover { background-color: #00FFB2; color: black; }
        """)

        layout = QVBoxLayout(self)
        lbl_title = QLabel("KẾT THÚC HIỆP! HỆ THỐNG ĐỀ XUẤT:" if is_vi else "END OF ROUND! SYSTEM PROPOSES:")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_title.setStyleSheet("color: #00FFB2;")
        layout.addWidget(lbl_title)

        self.combo_winner = QComboBox()
        self.combo_winner.addItem(f" ĐỎ ({red_name}) THẮNG" if is_vi else f" RED ({red_name}) WINS", "RED")
        self.combo_winner.addItem(f" XANH ({blue_name}) THẮNG" if is_vi else f" BLUE ({blue_name}) WINS", "BLUE")
        self.combo_winner.addItem(" HÒA (CHƯA RÕ)" if is_vi else " TIE (UNDECIDED)", "TIE")
        layout.addWidget(self.combo_winner)
        
        self.combo_method = QComboBox()
        self.combo_method.addItem("PTF - Điểm Tổng (Point Final)", "PTF")
        self.combo_method.addItem("SUP - Ưu Thế (Superiority)", "SUP")
        self.combo_method.addItem("PTG - Cách Biệt 12đ (Point Gap)", "PTG")
        self.combo_method.addItem("PUN - 5 Lỗi (Punitive)", "PUN")
        self.combo_method.addItem("KO - Knockout (Hết HP)", "KO")
        self.combo_method.addItem("HP - Nhiều máu hơn", "HP")
        layout.addWidget(self.combo_method)
        
        self.update_winner(auto_winner, auto_method)

        layout.addSpacing(20)
        btn_confirm = QPushButton("CHỐT KẾT QUẢ HIỆP NÀY" if is_vi else "CONFIRM ROUND RESULT")
        btn_confirm.clicked.connect(self.accept)
        layout.addWidget(btn_confirm)

    def update_winner(self, auto_winner, auto_method):
        if auto_winner == "RED":
            self.combo_winner.setCurrentIndex(0)
            self.combo_winner.setStyleSheet("background-color: #4A1515; color: #FF6666; border: 2px solid #FF3333;")
        elif auto_winner == "BLUE":
            self.combo_winner.setCurrentIndex(1)
            self.combo_winner.setStyleSheet("background-color: #15224A; color: #6699FF; border: 2px solid #3366FF;")
        else:
            self.combo_winner.setCurrentIndex(2)
            self.combo_winner.setStyleSheet("background-color: #2D2D3B; color: white; border: 2px solid #555;")
            
        index = self.combo_method.findData(auto_method)
        if index >= 0:
            self.combo_method.setCurrentIndex(index)

    def get_winner(self): return self.combo_winner.currentData()
    def get_method(self): return self.combo_method.currentData()


class MatchEndDialog(QDialog):
    def __init__(self, red_name, blue_name, auto_winner, is_vi=True, parent=None):
        super().__init__(parent)
        self.setWindowTitle("KẾT THÚC TRẬN ĐẤU - XÁC NHẬN CHUNG CUỘC" if is_vi else "END OF MATCH - CONFIRM RESULT")
        self.setFixedSize(450, 250)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        self.setStyleSheet("""
            QDialog { background-color: #1E1E24; color: white; font-family: Arial; border: 3px solid #FFD700; }
            QLabel { font-size: 16px; font-weight: bold; }
            QComboBox { background-color: #2D2D3B; border: 2px solid #555; padding: 10px; font-size: 18px; font-weight: bold; }
            QPushButton { background-color: #CC9900; color: white; font-size: 16px; font-weight: bold; padding: 12px; border-radius: 5px; }
            QPushButton:hover { background-color: #FFD700; color: black; }
        """)

        layout = QVBoxLayout(self)
        lbl_title = QLabel("🏆 ĐÃ CÓ VĐV ĐẠT 2 HIỆP THẮNG. CHỐT KẾT QUẢ TRẬN:" if is_vi else "🏆 2 ROUNDS WON REACHED. CONFIRM MATCH RESULT:")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_title.setStyleSheet("color: #FFD700;")
        layout.addWidget(lbl_title)

        self.combo_winner = QComboBox()
        self.combo_winner.addItem(f"🔴 ĐỎ ({red_name}) THẮNG TRẬN" if is_vi else f"🔴 RED ({red_name}) WINS MATCH", "RED")
        self.combo_winner.addItem(f"🔵 XANH ({blue_name}) THẮNG TRẬN" if is_vi else f"🔵 BLUE ({blue_name}) WINS MATCH", "BLUE")

        if auto_winner == "RED":
            self.combo_winner.setCurrentIndex(0)
            self.combo_winner.setStyleSheet("background-color: #4A1515; color: #FFD700; border: 2px solid #FFD700;")
        else:
            self.combo_winner.setCurrentIndex(1)
            self.combo_winner.setStyleSheet("background-color: #15224A; color: #FFD700; border: 2px solid #FFD700;")

        layout.addWidget(self.combo_winner)
        layout.addSpacing(20)
        btn_confirm = QPushButton("CHỐT TRẬN & PHÁT HIỆU ỨNG TIVI" if is_vi else "CONFIRM MATCH & PLAY TV ANIMATION")
        btn_confirm.clicked.connect(self.accept)
        layout.addWidget(btn_confirm)

    def get_winner(self): return self.combo_winner.currentData()
        
class BreakEndDialog(QDialog):
    def __init__(self, next_round, is_vi, parent=None):
        super().__init__(parent)
        title = "HẾT GIỜ NGHỈ" if is_vi else "BREAK OVER"
        self.setWindowTitle(title)
        self.setFixedSize(400, 200)
        self.setStyleSheet("""
            QDialog { background-color: #1E1E24; color: white; font-family: Arial; border: 2px solid #FFD700; }
            QLabel { font-size: 18px; font-weight: bold; color: #FFD700; }
            QPushButton { background-color: #CC9900; color: white; font-size: 16px; font-weight: bold; padding: 15px; border-radius: 5px; }
            QPushButton:hover { background-color: #FFD700; color: black; }
        """)
        layout = QVBoxLayout(self)
        msg = f"Đã hết thời gian nghỉ!\nChuẩn bị bắt đầu HIỆP {next_round}" if is_vi else f"Break time is over!\nReady to start ROUND {next_round}"
        lbl_msg = QLabel(msg)
        lbl_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_msg)
        layout.addSpacing(20)
        btn_text = "BẮT ĐẦU HIỆP MỚI NGAY" if is_vi else "START NEW ROUND NOW"
        btn_start = QPushButton(btn_text)
        btn_start.clicked.connect(self.accept)
        layout.addWidget(btn_start)

class HotSwapDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("KÍCH HOẠT TAY CẦM SỐ 4 (DỰ PHÒNG)")
        self.setFixedSize(400, 200)
        self.setStyleSheet("""
            QDialog { background-color: #1E1E24; color: white; border: 2px solid #FFD700; }
            QLabel { font-size: 14px; font-weight: bold; }
            QPushButton { background-color: #2D2D3B; color: white; font-size: 14px; font-weight: bold; padding: 15px; border-radius: 5px; }
            QPushButton:hover { background-color: #FFD700; color: black; }
        """)
        
        layout = QVBoxLayout(self)
        lbl = QLabel("Tay bấm nào đang bị hỏng cần thay thế?")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("color: #FFD700; font-size: 16px;")
        layout.addWidget(lbl)
        
        btn_layout = QHBoxLayout()
        self.selected_target = None
        
        for i in [1, 2, 3]:
            btn = QPushButton(f"Thay cho TT{i}")
            btn.clicked.connect(lambda checked, val=i: self.make_selection(val))
            btn_layout.addWidget(btn)
            
        layout.addLayout(btn_layout)
        
    def make_selection(self, val):
        self.selected_target = val
        self.accept()

class ControlPanelWindow(QWidget):
    def load_keymap_file(self):
        self.hardware_keymap.clear()
        keymap_path = get_path("keymap.json") 
        if os.path.exists(keymap_path):
            with open(keymap_path, 'r') as f:
                data = json.load(f)
                for k, v in data.items(): self.hardware_keymap[str(k)] = v
        else: self.log_action("SYSTEM", "⚠️ CẢNH BÁO: Chưa có file keymap.json.", "⚠️ WARNING: keymap.json not found.")

    def __init__(self, state, scoreboard):
        super().__init__()
        self.state = state
        self.scoreboard = scoreboard 
        self.state.red_x2_timer = 0.0
        self.state.blue_x2_timer = 0.0
        self.current_lang = "VI" 
        self.DEV_MODE = False
        try:
            ver_file = os.path.join(get_install_dir(), "version.txt")
            if os.path.exists(ver_file):
                with open(ver_file, 'r') as f:
                    ver_text = f.read().strip()
                    if ver_text.startswith("9."):
                        self.DEV_MODE = True
        except Exception:
            pass
        self.hardware_keymap = {}
        self.gamepad_routing = {1: 1, 2: 2, 3: 3, 4: None}
        self.log_history = []
        self.round_dialog = None
        self.match_dialog = None

        self.audio_out_5s = QAudioOutput()
        self.player_5s = QMediaPlayer()
        self.player_5s.setAudioOutput(self.audio_out_5s)
        self.player_5s.setSource(QUrl.fromLocalFile(get_path("assets/sounds/5giay.wav")))

        self.audio_out_bell = QAudioOutput()
        self.player_bell = QMediaPlayer()
        self.player_bell.setAudioOutput(self.audio_out_bell)
        self.player_bell.setSource(QUrl.fromLocalFile(get_path("assets/sounds/bell.wav")))

        if not hasattr(self.state.red, 'ivr_quota'): self.state.red.ivr_quota = True
        if not hasattr(self.state.blue, 'ivr_quota'): self.state.blue.ivr_quota = True
        if not hasattr(self.state, 'round_results'): self.state.round_results = {1: None, 2: None, 3: None}
        
        self.setWindowTitle("AEKA Control Panel - Bàn Thư Ký")
        self.resize(1300, 800)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setStyleSheet("""
            QWidget { background-color: #1E1E24; color: #E0E0E0; font-family: 'Segoe UI', Arial; font-size: 14px; }
            QGroupBox { font-weight: bold; border: 2px solid #3A3A4A; border-radius: 8px; margin-top: 10px; padding-top: 15px; }
            QGroupBox::title { subcontrol-origin: margin; left: 15px; padding: 0 5px; color: #00FFB2; }
            QPushButton { background-color: #2D2D3B; border: 1px solid #444; border-radius: 5px; padding: 8px; font-weight: bold; }
            QPushButton:hover { background-color: #3D3D4B; border: 1px solid #00FFB2; }
            QLineEdit, QComboBox { background-color: #15151A; border: 1px solid #555; padding: 5px; border-radius: 4px; }
            QCheckBox, QRadioButton { color: #00FFB2; font-weight: bold; }
            QTableWidget { background-color: #15151A; gridline-color: #333; color: white; }
            QHeaderView::section { background-color: #2D2D3B; padding: 4px; border: 1px solid #333; color: white; }
            QTextEdit { background-color: #0F0F13; border: 1px solid #555; color: #00FFB2; font-family: 'Consolas'; font-size: 12px; }
            QSplitter::handle { background-color: #3A3A4A; width: 4px; border-radius: 2px; }
            QSplitter::handle:hover { background-color: #00FFB2; }
        """)
        
        self.kyeshi_timer = 60.0
        self.last_timer_color = ""
        
        self.setup_ui()
        self.update_texts() 
        self.update_match_info()
        self.engine = ScoreEngine(self.state)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_tick)
        self.timer.start(100)
        self.last_timer_text = ""
        self.preview_interval = 0.3
        self.reset_timer_to_combo()
        self.log_action("SYSTEM", "Hệ thống khởi động thành công.", "System booted successfully.")
        self.load_keymap_file()
        
        self.last_grab_time = 0.0
        self.played_3s_warning = False

    def t(self, key):
        lang = getattr(self, 'current_lang', 'VI')
        return TEXTS.get(lang, {}).get(key, TEXTS.get('VI', {}).get(key, key))

    def setup_ui(self):
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.setSpacing(5)
        
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        
        self.w_col1 = QWidget()
        self.w_col1.setMinimumWidth(250)
        col1_layout = QVBoxLayout(self.w_col1)
        col1_layout.setContentsMargins(0, 0, 5, 0)
        
        self.btn_lang_toggle = QPushButton()
        self.btn_lang_toggle.setStyleSheet("background-color: #3355A0; color: white; padding: 10px; font-weight: bold;")
        self.btn_lang_toggle.clicked.connect(self.toggle_language)
        col1_layout.addWidget(self.btn_lang_toggle)

        if self.DEV_MODE:
            self.btn_dev_keymap = QPushButton("⚙️ CÀI ĐẶT MÃ PHÍM TAY CẦM (DEV)")
            self.btn_dev_keymap.setStyleSheet("background-color: #663399; color: white; padding: 10px; font-weight: bold; border-radius: 4px;")
            self.btn_dev_keymap.clicked.connect(self.open_keymap_tool)
            col1_layout.addWidget(self.btn_dev_keymap)
            
        self.com_layout = QHBoxLayout()
        self.com_combo = QComboBox()
        self.com_combo.setStyleSheet("background-color: #2D2D3B; padding: 5px;")
        for port, desc, hwid in sorted(serial.tools.list_ports.comports()):
            self.com_combo.addItem(f"{port} - {desc}", port)
            
        self.btn_connect_com = QPushButton(" KẾT NỐI TAY CẦM")
        self.btn_connect_com.setStyleSheet("background-color: #006699; font-weight: bold; padding: 10px;")
        self.btn_connect_com.clicked.connect(self.toggle_serial)
        
        self.com_layout.addWidget(self.com_combo, stretch=2)
        self.com_layout.addWidget(self.btn_connect_com, stretch=1)
        col1_layout.addLayout(self.com_layout)
        
        self.serial_thread = None
        
        self.group_hotswap = QGroupBox("QUẢN LÝ TAY CẦM THAY THẾ")
        self.group_hotswap.setStyleSheet("QGroupBox { border: 2px solid #FFD700; } QGroupBox::title { color: #FFD700; }")
        hw_layout = QVBoxLayout(self.group_hotswap)
        
        self.lbl_hw_status = QLabel("Trạng thái: Đang dùng Tay 1, 2, 3 chuẩn.")
        self.lbl_hw_status.setStyleSheet("color: #00FFB2; font-weight: bold;")
        self.lbl_hw_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hw_layout.addWidget(self.lbl_hw_status)
        
        self.btn_hotswap = QPushButton("KÍCH HOẠT TAY CẦM DỰ PHÒNG)")
        self.btn_hotswap.setStyleSheet("background-color: #552222; color: #FF9999; font-weight: bold; padding: 10px;")
        self.btn_hotswap.clicked.connect(self.trigger_hotswap)
        hw_layout.addWidget(self.btn_hotswap)
        
        col1_layout.addWidget(self.group_hotswap)
        
        self.group_info = QGroupBox()
        self.group_info.setMinimumWidth(100)
        info_layout = QGridLayout(self.group_info)
        
        self.input_red_name = QLineEdit("VĐV ĐỎ")
        self.input_red_name.setStyleSheet("color: #FF6666; font-weight: bold;")
        self.combo_red_flag = QComboBox(); self.combo_red_flag.setEditable(True)
        self.combo_red_flag.addItems(["vietnam", "korea", "thailand", "japan", "usa", "china"])
        self.combo_red_flag.setCurrentText("vietnam")

        self.input_blue_name = QLineEdit("VĐV XANH")
        self.input_blue_name.setStyleSheet("color: #6699FF; font-weight: bold;")
        self.combo_blue_flag = QComboBox(); self.combo_blue_flag.setEditable(True)
        self.combo_blue_flag.addItems(["vietnam", "korea", "thailand", "japan", "usa", "china"])
        self.combo_blue_flag.setCurrentText("vietnam")
        
        self.combo_match_category = QComboBox(); self.combo_match_category.setEditable(True)
        self.combo_match_category.addItems(["VÒNG LOẠI", "TỨ KẾT", "BÁN KẾT", "CHUNG KẾT"]) 
        self.combo_match_category.setCurrentText("CHUNG KẾT")

        self.combo_match_num = QComboBox(); self.combo_match_num.setEditable(True)
        self.combo_match_num.addItems([str(i) for i in range(1, 101)])
        self.combo_gender = QComboBox(); self.combo_gender.addItems(["NAM", "NỮ"])
        self.combo_weight = QComboBox(); self.combo_weight.setEditable(True)
        self.combo_weight.addItems(["-45kg", "-48kg", "-51kg", "-54kg", "-58kg", "-63kg", "-68kg", "-74kg", "+80kg"])
        
        self.lbl_red_name_title = QLabel(); self.lbl_blue_name_title = QLabel()
        self.lbl_match_category_title = QLabel(); self.lbl_match_num_title = QLabel()
        self.lbl_gender_title = QLabel(); self.lbl_weight_title = QLabel()
        
        info_layout.addWidget(self.lbl_red_name_title, 0, 0); info_layout.addWidget(self.input_red_name, 0, 1)
        info_layout.addWidget(QLabel("Cờ:"), 0, 2); info_layout.addWidget(self.combo_red_flag, 0, 3)

        info_layout.addWidget(self.lbl_blue_name_title, 1, 0); info_layout.addWidget(self.input_blue_name, 1, 1)
        info_layout.addWidget(QLabel("Cờ:"), 1, 2); info_layout.addWidget(self.combo_blue_flag, 1, 3)
        
        info_layout.addWidget(self.lbl_match_category_title, 2, 0); info_layout.addWidget(self.combo_match_category, 2, 1, 1, 3)
        info_layout.addWidget(self.lbl_match_num_title, 3, 0); info_layout.addWidget(self.combo_match_num, 3, 1, 1, 3)
        info_layout.addWidget(self.lbl_gender_title, 4, 0); info_layout.addWidget(self.combo_gender, 4, 1, 1, 3)
        info_layout.addWidget(self.lbl_weight_title, 5, 0); info_layout.addWidget(self.combo_weight, 5, 1, 1, 3)
        
        from PyQt6.QtWidgets import QButtonGroup
        self.radio_bo3 = QCheckBox("Cá Nhân (BO3)")
        self.radio_team_bo3 = QCheckBox("Đồng Đội (BO3)")
        self.radio_team = QCheckBox("Đồng Đội (150 HP)")
        
        self.mode_group = QButtonGroup(self)
        self.mode_group.addButton(self.radio_bo3)
        self.mode_group.addButton(self.radio_team_bo3)
        self.mode_group.addButton(self.radio_team)
        
        self.radio_bo3.setChecked(True)
        self.radio_bo3.setStyleSheet("color: #00FFB2; font-weight: bold;")
        self.radio_team_bo3.setStyleSheet("color: #FFD700; font-weight: bold;")
        self.radio_team.setStyleSheet("color: #FF9999; font-weight: bold;")
        
        self.radio_bo3.toggled.connect(self.change_match_mode)
        self.radio_team_bo3.toggled.connect(self.change_match_mode)
        
        info_layout.addWidget(self.radio_bo3, 6, 0, 1, 2)
        info_layout.addWidget(self.radio_team_bo3, 6, 2, 1, 1)
        
        # Ô NHẬP ĐIỂM TRẦN CHO ĐỒNG ĐỘI BO3
        max_score_layout = QHBoxLayout()
        
        # Thay Label bằng CheckBox
        self.chk_max_score = QCheckBox("Áp dụng điểm trần:")
        self.chk_max_score.setChecked(False) # Mặc định tắt
        self.chk_max_score.setStyleSheet("color: #AAAAAA; font-size: 12px; font-weight: bold;")
        
        self.input_max_score = QLineEdit("30")
        self.input_max_score.setFixedWidth(40)
        self.input_max_score.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.input_max_score.setStyleSheet("color: #FFD700; font-weight: bold; background-color: #15151A; border: 1px solid #555;")
        self.input_max_score.setValidator(QIntValidator(1, 999, self)) 
        self.input_max_score.editingFinished.connect(self.log_max_score_change)
        
        # Liên kết nút tick: Nếu tắt tick thì làm mờ ô nhập số luôn cho xịn
        self.chk_max_score.toggled.connect(lambda checked: self.input_max_score.setEnabled(checked))
        
        max_score_layout.addWidget(self.chk_max_score)
        max_score_layout.addWidget(self.input_max_score)
        max_score_layout.addStretch()
        info_layout.addLayout(max_score_layout, 6, 3, 1, 1)

        info_layout.addWidget(self.radio_team, 7, 0, 1, 4)

        self.btn_update_display = QPushButton()
        self.btn_update_display.setStyleSheet("background-color: #008855; color: white; padding: 15px;")
        self.btn_update_display.clicked.connect(self.update_match_info)
        info_layout.addWidget(self.btn_update_display, 8, 0, 1, 4)
        
        col1_layout.addWidget(self.group_info)
        
        self.group_data = QGroupBox()
        self.group_data.setMinimumWidth(100)
        data_layout = QVBoxLayout(self.group_data)
        self.btn_import = QPushButton()
        self.btn_import.clicked.connect(self.import_csv) 
        data_layout.addWidget(self.btn_import)
        
        self.table_schedule = QTableWidget(0, 4) 
        self.table_schedule.setMinimumWidth(50)
        self.table_schedule.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_schedule.cellDoubleClicked.connect(self.load_match_from_table) 
        data_layout.addWidget(self.table_schedule)
        col1_layout.addWidget(self.group_data)

        self.w_col2 = QWidget()
        self.w_col2.setMinimumWidth(250)
        col2_layout = QVBoxLayout(self.w_col2)
        col2_layout.setContentsMargins(5, 0, 5, 0)
        
        self.group_preview = QGroupBox("MINI PREVIEW (CLONE TIVI)")
        self.group_preview.setMinimumWidth(100)
        
        self.group_preview.setStyleSheet("""
            QGroupBox { 
                border: 2px dashed #00FFB2; 
                background-color: #0F0F13; 
                font-weight: bold; 
                margin-top: 15px; 
                padding-top: 15px;
            } 
            QGroupBox::title { 
                color: #00FFB2; 
                subcontrol-origin: margin; 
                left: 10px; 
                padding: 0 5px; 
            }
        """)
        
        preview_layout = QVBoxLayout(self.group_preview)
        preview_layout.setContentsMargins(3, 0, 3, 3) 
        preview_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.lbl_live_preview = QLabel("Đang tải tín hiệu Tivi...")
        self.lbl_live_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_live_preview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.lbl_live_preview.setMinimumSize(100, 56) 
        self.lbl_live_preview.setStyleSheet("background-color: black; border-radius: 4px;") 
        preview_layout.addWidget(self.lbl_live_preview)

        self.group_preview.installEventFilter(self)
        col2_layout.addWidget(self.group_preview, stretch=0)
        
        self.group_timer = QGroupBox()
        self.group_timer.setMinimumWidth(100)
        timer_layout = QVBoxLayout(self.group_timer)
        
        self.lbl_control_timer = QLabel("02:00")
        self.lbl_control_timer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_control_timer.setStyleSheet("font-size: 65px; font-weight: bold; color: #00FFB2; font-family: 'Consolas'; border: none; margin-bottom: 5px;")
        timer_layout.addWidget(self.lbl_control_timer)
        
        self.btn_start_pause = QPushButton()
        self.btn_start_pause.setStyleSheet("background-color: #CC9900; color: white; font-size: 18px; padding: 15px;")
        self.btn_start_pause.clicked.connect(self.toggle_timer) 
        timer_layout.addWidget(self.btn_start_pause)
        
        self.btn_pause_menu = QPushButton()
        self.btn_pause_menu.setStyleSheet("background-color: #A03333; color: white; font-size: 16px; padding: 10px;")
        pause_menu = QMenu(self)
        pause_menu.setStyleSheet("QMenu { background-color: #2D2D3B; color: white; font-size: 14px; border: 1px solid #555; } QMenu::item { padding: 10px 30px; } QMenu::item:selected { background-color: #00FFB2; color: black; }")
        self.action_kyeshi = pause_menu.addAction("")
        self.action_shigan = pause_menu.addAction("")
        self.action_kyeshi.triggered.connect(self.toggle_kyeshi)
        self.action_shigan.triggered.connect(self.toggle_shigan)
        self.btn_pause_menu.setMenu(pause_menu)
        timer_layout.addWidget(self.btn_pause_menu)
        
        settings_grid = QGridLayout()
        self.lbl_round_time_title = QLabel(); self.lbl_break_time_title = QLabel()
        
        self.combo_round_time = QComboBox(); self.combo_round_time.setEditable(True)
        self.combo_round_time.addItems(["02:00", "01:30", "01:00", "00:30", "00:15"])
        self.combo_round_time.setCurrentIndex(0)
        self.combo_round_time.currentIndexChanged.connect(self.reset_timer_to_combo)
        
        self.combo_break_time = QComboBox(); self.combo_break_time.setEditable(True)
        self.combo_break_time.addItems(["01:00", "00:30", "00:15", "00:10"])
        self.combo_break_time.setCurrentIndex(0)
        
        settings_grid.addWidget(self.lbl_round_time_title, 0, 0); settings_grid.addWidget(self.combo_round_time, 0, 1)
        settings_grid.addWidget(self.lbl_break_time_title, 1, 0); settings_grid.addWidget(self.combo_break_time, 1, 1)
        
        self.chk_ptg = QCheckBox("Cách biệt 12đ")
        self.chk_ptg.setChecked(True)
        self.chk_pun = QCheckBox("5 Lỗi Gam-Jeom")
        self.chk_pun.setChecked(True)
        settings_grid.addWidget(self.chk_ptg, 2, 0)
        settings_grid.addWidget(self.chk_pun, 2, 1)

        self.btn_reset_timer = QPushButton()
        self.btn_reset_timer.clicked.connect(self.reset_timer_to_combo)
        settings_grid.addWidget(self.btn_reset_timer, 3, 0)
        
        override_layout = QHBoxLayout()
        self.input_manual_time = QLineEdit("00:00")
        self.input_manual_time.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.btn_set_time = QPushButton("SET")
        self.btn_set_time.setStyleSheet("background-color: #555;")
        self.btn_set_time.clicked.connect(self.apply_manual_timer)
        override_layout.addWidget(self.input_manual_time)
        override_layout.addWidget(self.btn_set_time)
        settings_grid.addLayout(override_layout, 3, 1)
        
        timer_layout.addLayout(settings_grid)
        col2_layout.addWidget(self.group_timer, stretch=0) 
        col2_layout.addStretch(1)

        self.w_col3 = QWidget()
        self.w_col3.setMinimumWidth(300)
        col3_layout = QVBoxLayout(self.w_col3)
        col3_layout.setContentsMargins(5, 0, 0, 0)
        
        self.group_manual = QGroupBox()
        self.group_manual.setMinimumWidth(100)
        self.group_manual.setStyleSheet("QGroupBox { border: 2px solid #A03333; } QGroupBox::title { color: #FF6666; }")
        manual_layout = QVBoxLayout(self.group_manual)
        
        btn_grid = QGridLayout()
        btn_grid.setSpacing(5)
        self.lbl_red_title = QLabel(); self.lbl_red_title.setStyleSheet("color: #FF6666; font-size: 18px; font-weight: bold;"); self.lbl_red_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_action_title = QLabel(); self.lbl_action_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_blue_title = QLabel(); self.lbl_blue_title.setStyleSheet("color: #6699FF; font-size: 18px; font-weight: bold;"); self.lbl_blue_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        btn_grid.addWidget(self.lbl_red_title, 0, 0, 1, 2)
        btn_grid.addWidget(self.lbl_action_title, 0, 2, 1, 1, Qt.AlignmentFlag.AlignCenter)
        btn_grid.addWidget(self.lbl_blue_title, 0, 3, 1, 2)

        self.action_labels = [] 
        actions_setup = [("punch", 1), ("body", 2), ("head", 3), ("tech_body", 2), ("tech_head", 3), ("gamjeom", 1)]
        
        for row, (act_key, pt) in enumerate(actions_setup, start=1):
            txt_plus = f"KT +{pt}" if act_key.startswith("tech_") else (f"+{pt}" if act_key != "gamjeom" else "+")
            txt_minus = f"KT -{pt}" if act_key.startswith("tech_") else (f"-{pt}" if act_key != "gamjeom" else "-")
            
            r_plus = QPushButton(txt_plus); r_plus.setStyleSheet("background-color: #552222; color: #FF9999;")
            r_minus = QPushButton(txt_minus); r_minus.setStyleSheet("background-color: #331111; color: #FF5555;")
            b_plus = QPushButton(txt_plus); b_plus.setStyleSheet("background-color: #223355; color: #99BBFF;")
            b_minus = QPushButton(txt_minus); b_minus.setStyleSheet("background-color: #111133; color: #5588FF;")
            
            for btn in [r_plus, r_minus, b_plus, b_minus]:
                btn.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
                btn.setMinimumWidth(0)

            r_plus.clicked.connect(lambda checked, c="red", a=act_key, v=pt: self.handle_manual_score(c, a, v))
            r_minus.clicked.connect(lambda checked, c="red", a=act_key, v=-pt: self.handle_manual_score(c, a, v))
            b_plus.clicked.connect(lambda checked, c="blue", a=act_key, v=pt: self.handle_manual_score(c, a, v))
            b_minus.clicked.connect(lambda checked, c="blue", a=act_key, v=-pt: self.handle_manual_score(c, a, v))

            btn_grid.addWidget(r_plus, row, 0); btn_grid.addWidget(r_minus, row, 1)
            lbl_center = QLabel(); lbl_center.setAlignment(Qt.AlignmentFlag.AlignCenter); lbl_center.setStyleSheet("font-weight: bold; color: #AAAAAA;")
            self.action_labels.append(lbl_center); btn_grid.addWidget(lbl_center, row, 2)
            btn_grid.addWidget(b_plus, row, 3); btn_grid.addWidget(b_minus, row, 4)

        self.btn_ivr_red = QPushButton("IVR ĐỎ: CÒN")
        self.btn_ivr_red.setStyleSheet("background-color: #552222; color: #FF9999; font-weight: bold;")
        self.btn_ivr_red.setMinimumSize(0, 40); self.btn_ivr_red.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
        self.btn_ivr_red.clicked.connect(lambda: self.toggle_ivr("red"))
        
        self.btn_ivr_blue = QPushButton("IVR XANH: CÒN")
        self.btn_ivr_blue.setStyleSheet("background-color: #223355; color: #99BBFF; font-weight: bold;")
        self.btn_ivr_blue.setMinimumSize(0, 40); self.btn_ivr_blue.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
        self.btn_ivr_blue.clicked.connect(lambda: self.toggle_ivr("blue"))
        
        btn_grid.addWidget(self.btn_ivr_red, 7, 0, 1, 2)
        btn_grid.addWidget(self.btn_ivr_blue, 7, 3, 1, 2)

        self.btn_sipcho_red = QPushButton("X2-GamJeom")
        self.btn_sipcho_red.setStyleSheet("background-color: #552222; color: #FF9999; font-weight: bold;")
        self.btn_sipcho_red.setMinimumSize(0, 40); self.btn_sipcho_red.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
        self.btn_sipcho_red.clicked.connect(lambda: self.trigger_passive("red"))
        
        self.btn_sipcho_blue = QPushButton("X2-GamJeom")
        self.btn_sipcho_blue.setStyleSheet("background-color: #223355; color: #99BBFF; font-weight: bold;")
        self.btn_sipcho_blue.setMinimumSize(0, 40); self.btn_sipcho_blue.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
        self.btn_sipcho_blue.clicked.connect(lambda: self.trigger_passive("blue"))

        btn_grid.addWidget(self.btn_sipcho_red, 8, 0, 1, 2)
        btn_grid.addWidget(self.btn_sipcho_blue, 8, 3, 1, 2)

        self.btn_sub_red = QPushButton("ĐỔI NGƯỜI(+15s)")
        self.btn_sub_red.setStyleSheet("background-color: #552222; color: #FF9999; font-weight: bold;")
        self.btn_sub_red.setMinimumSize(0, 40); self.btn_sub_red.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
        self.btn_sub_red.clicked.connect(lambda: self.trigger_substitution("red"))
        
        self.btn_sub_blue = QPushButton("ĐỔI NGƯỜI(+15s)")
        self.btn_sub_blue.setStyleSheet("background-color: #223355; color: #99BBFF; font-weight: bold;")
        self.btn_sub_blue.setMinimumSize(0, 40); self.btn_sub_blue.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
        self.btn_sub_blue.clicked.connect(lambda: self.trigger_substitution("blue"))

        btn_grid.addWidget(self.btn_sub_red, 9, 0, 1, 2)
        btn_grid.addWidget(self.btn_sub_blue, 9, 3, 1, 2)

        # ĐỎ
        self.btn_double_gj_red_plus = QPushButton("+LỖI(x2đ)")
        self.btn_double_gj_red_plus.setStyleSheet("background-color: #552222; color: #FF9999; font-weight: bold;")
        self.btn_double_gj_red_plus.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
        self.btn_double_gj_red_plus.setEnabled(False)
        self.btn_double_gj_red_plus.clicked.connect(lambda: self.handle_manual_score("red", "gamjeom_10s", 1))

        self.btn_double_gj_red_minus = QPushButton("-LỖI(x2đ)")
        self.btn_double_gj_red_minus.setStyleSheet("background-color: #331111; color: #FF5555; font-weight: bold;")
        self.btn_double_gj_red_minus.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
        self.btn_double_gj_red_minus.setEnabled(False)
        self.btn_double_gj_red_minus.clicked.connect(lambda: self.handle_manual_score("red", "gamjeom_10s", -1))

        # XANH
        self.btn_double_gj_blue_plus = QPushButton("+LỖI(x2đ)")
        self.btn_double_gj_blue_plus.setStyleSheet("background-color: #223355; color: #99BBFF; font-weight: bold;")
        self.btn_double_gj_blue_plus.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
        self.btn_double_gj_blue_plus.setEnabled(False)
        self.btn_double_gj_blue_plus.clicked.connect(lambda: self.handle_manual_score("blue", "gamjeom_10s", 1))

        self.btn_double_gj_blue_minus = QPushButton("-LỖI(x2đ)")
        self.btn_double_gj_blue_minus.setStyleSheet("background-color: #111133; color: #5588FF; font-weight: bold;")
        self.btn_double_gj_blue_minus.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
        self.btn_double_gj_blue_minus.setEnabled(False)
        self.btn_double_gj_blue_minus.clicked.connect(lambda: self.handle_manual_score("blue", "gamjeom_10s", -1))

        btn_grid.addWidget(self.btn_double_gj_red_plus, 10, 0)
        btn_grid.addWidget(self.btn_double_gj_red_minus, 10, 1)
        btn_grid.addWidget(self.btn_double_gj_blue_plus, 10, 3)
        btn_grid.addWidget(self.btn_double_gj_blue_minus, 10, 4)

        manual_layout.addLayout(btn_grid)
        self.btn_reset_match = QPushButton()
        self.btn_reset_match.setStyleSheet("background-color: #AA0000; color: white; padding: 15px; font-size: 16px; margin-top: 10px;")
        self.btn_reset_match.setMinimumWidth(0)
        self.btn_reset_match.clicked.connect(self.reset_match)
        manual_layout.addWidget(self.btn_reset_match)
        col3_layout.addWidget(self.group_manual)
        
        self.group_log = QGroupBox()
        self.group_log.setMinimumWidth(100)
        log_layout = QVBoxLayout(self.group_log)
        
        self.text_log = QTextEdit()
        self.text_log.setReadOnly(True)
        self.text_log.setMinimumWidth(50)
        log_layout.addWidget(self.text_log)
        
        log_btn_layout = QHBoxLayout()
        
        self.btn_clear_log = QPushButton("XÓA LOG")
        self.btn_clear_log.setStyleSheet("background-color: #444444; color: white; font-weight: bold; padding: 8px;")
        self.btn_clear_log.clicked.connect(self.clear_log)
        log_btn_layout.addWidget(self.btn_clear_log)

        btn_text = "XUẤT KẾT QUẢ & LOG (CSV)" if getattr(self, 'current_lang', 'VI') == "VI" else "EXPORT RESULT & LOG (CSV)"
        self.btn_export_log = QPushButton(btn_text)
        self.btn_export_log.setStyleSheet("background-color: #008855; color: white; font-weight: bold; padding: 8px;")
        self.btn_export_log.clicked.connect(self.export_match_stats)
        log_btn_layout.addWidget(self.btn_export_log)

        log_layout.addLayout(log_btn_layout)

        col3_layout.addWidget(self.group_log, stretch=1) 

        self.splitter.addWidget(self.w_col1)
        self.splitter.addWidget(self.w_col2)
        self.splitter.addWidget(self.w_col3)
        
        self.splitter.setStretchFactor(0, 2)
        self.splitter.setStretchFactor(1, 3)
        self.splitter.setStretchFactor(2, 4)

        self.main_layout.addWidget(self.splitter)

    def eventFilter(self, obj, event):
        if obj == self.group_preview and event.type() == QEvent.Type.Resize:
            margins = self.group_preview.layout().contentsMargins()
            w = self.group_preview.width() - margins.left() - margins.right()
            if w > 0:
                h = int(w * 9 / 16)
                self.lbl_live_preview.setFixedHeight(h)
        return super().eventFilter(obj, event)

    def log_max_score_change(self):
        val = self.input_max_score.text().strip()
        if not val: 
            val = "30" 
            self.input_max_score.setText(val)
        if getattr(self.state, 'match_format', 'BO3') == "TEAM_BO3":
            self.log_action("SYSTEM", f"Đã cập nhật Điểm Trần (Max Score) thành: {val}đ", f"Updated Max Score to: {val}pts")

    def change_match_mode(self):
        if self.radio_team.isChecked():
            self.state.match_format = "TEAM_HP"
            self.state.red.score = 150
            self.state.blue.score = 150
            self.log_action("SYSTEM", "Kích hoạt ĐỒNG ĐỘI (150 HP).", "Activated TEAM mode (150 HP).")
        elif self.radio_team_bo3.isChecked():
            self.state.match_format = "TEAM_BO3"
            self.state.red.score = 0
            self.state.blue.score = 0
            self.log_action("SYSTEM", "Kích hoạt ĐỒNG ĐỘI (BO3).", "Activated TEAM mode (BO3).")
        else:
            self.state.match_format = "BO3"
            self.state.red.score = 0
            self.state.blue.score = 0
            self.log_action("SYSTEM", "Kích hoạt CÁ NHÂN (BO3).", "Activated INDIVIDUAL mode (BO3).")
        
        if getattr(self.state, 'match_format', 'BO3') in ["TEAM_HP", "TEAM_BO3"]:
            self.state.red_sub_timer = 15.0
            self.state.blue_sub_timer = 15.0
        else:
            self.state.red_sub_timer = 0.0
            self.state.blue_sub_timer = 0.0
        
        self.sync_preview()

    def toggle_ivr(self, color):
        if color == "red":
            self.state.red.ivr_quota = not self.state.red.ivr_quota
            is_active = self.state.red.ivr_quota
            msg_vi = "Được phép khiếu nại" if is_active else "BỊ TƯỚC QUYỀN khiếu nại"
            msg_en = "VALID" if is_active else "REJECTED"
            self.log_action("red", f"Cập nhật IVR Đỏ: {msg_vi}", f"Update Red IVR: {msg_en}")
        else:
            self.state.blue.ivr_quota = not self.state.blue.ivr_quota
            is_active = self.state.blue.ivr_quota
            msg_vi = "Được phép khiếu nại" if is_active else "BỊ TƯỚC QUYỀN khiếu nại"
            msg_en = "VALID" if is_active else "REJECTED"
            self.log_action("blue", f"Cập nhật IVR Xanh: {msg_vi}", f"Update Blue IVR: {msg_en}")
        
        self.update_texts()
        self.sync_preview()

    def import_csv(self):
        dialog_title = "Chọn File Danh Sách (CSV)" if self.current_lang == "VI" else "Select Match List File (CSV)"
        file_name, _ = QFileDialog.getOpenFileName(self, dialog_title, "", "CSV Files (*.csv)")
        
        if file_name:
            try:
                with open(file_name, newline='', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    data = list(reader)
                    if len(data) > 0 and ("Trận" in data[0] or "Match" in data[0]): data.pop(0)
                    self.table_schedule.setRowCount(len(data))
                    for row_idx, row_data in enumerate(data):
                        for col_idx in range(min(4, len(row_data))):
                            self.table_schedule.setItem(row_idx, col_idx, QTableWidgetItem(row_data[col_idx]))
                
                self.log_action("SYSTEM", f"Đã nạp thành công {len(data)} trận từ file CSV.", f"Successfully loaded {len(data)} matches from CSV file.")
            except Exception as e:
                err_title = "Lỗi" if self.current_lang == "VI" else "Error"
                err_msg = f"Không thể đọc file: {str(e)}" if self.current_lang == "VI" else f"Cannot read file: {str(e)}"
                QMessageBox.warning(self, err_title, err_msg)

    def load_match_from_table(self, row, column):
        try:
            match_no = self.table_schedule.item(row, 0).text() if self.table_schedule.item(row, 0) else ""
            weight = self.table_schedule.item(row, 1).text() if self.table_schedule.item(row, 1) else ""
            red = self.table_schedule.item(row, 2).text() if self.table_schedule.item(row, 2) else ""
            blue = self.table_schedule.item(row, 3).text() if self.table_schedule.item(row, 3) else ""
            self.combo_match_num.setCurrentText(match_no)
            self.combo_weight.setCurrentText(weight)
            self.input_red_name.setText(red)
            self.input_blue_name.setText(blue)
            self.update_match_info()
            self.log_action("SYSTEM", f"Đã chuyển sang Trận {match_no}: Đỏ ({red}) vs Xanh ({blue})", f"Switched to Match {match_no}: Red ({red}) vs Blue ({blue})")
        except Exception: pass

    def toggle_language(self):
        self.current_lang = "EN" if self.current_lang == "VI" else "VI"
        self.update_texts()
        self.update_match_info() 
        self.render_logs() 
        
        if hasattr(self.scoreboard, 'update_language'):
            self.scoreboard.update_language(self.current_lang)
        
    def log_action(self, color, msg_vi, msg_en=None):
        if msg_en is None: msg_en = msg_vi 
        time_str = self.format_time(self.state.timer_seconds)
        
        self.log_history.append({
            "time": time_str,
            "color": color,
            "vi": msg_vi,
            "en": msg_en
        })
        self.render_logs()

    def render_logs(self):
        self.text_log.clear()
        is_vi = (self.current_lang == "VI")
        
        for item in self.log_history:
            prefix = "[SYS]" if item["color"] == "SYSTEM" else f"[{item['time']} ]"
            color_code = "#00FFB2"
            if item["color"] == "red": color_code = "#FF6666"
            elif item["color"] == "blue": color_code = "#6699FF"
            elif item["color"] == "SYSTEM": color_code = "#A0A0A0"
            
            msg = item["vi"] if is_vi else item["en"]
            self.text_log.append(f"<span style='color: {color_code}'>{prefix} {msg}</span>")
            
        scrollbar = self.text_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def update_texts(self):
        is_vi = (self.current_lang == "VI")
        self.btn_lang_toggle.setText(self.t('btn_lang_toggle'))
        self.setWindowTitle(self.t('window_title'))
        if hasattr(self, 'btn_dev_keymap'):
            self.btn_dev_keymap.setText(self.t('btn_dev_keymap'))
        if hasattr(self, 'btn_connect_com'):
            self.btn_connect_com.setText(self.t('btn_connect_com_default'))
        if hasattr(self, 'group_hotswap'):
            self.group_hotswap.setTitle(self.t('group_hotswap_title'))
        if hasattr(self, 'lbl_hw_status'):
            self.lbl_hw_status.setText(self.t('lbl_hw_status'))
        if hasattr(self, 'btn_hotswap'):
            self.btn_hotswap.setText(self.t('btn_hotswap'))
        if hasattr(self, 'lbl_live_preview'):
            self.lbl_live_preview.setText(self.t('lbl_live_preview'))
        self.group_info.setTitle(self.t('group_info_title'))
        self.lbl_red_name_title.setText(self.t('lbl_red_name_title'))
        self.lbl_blue_name_title.setText(self.t('lbl_blue_name_title'))
        self.lbl_match_category_title.setText(self.t('lbl_match_category_title'))
        self.lbl_match_num_title.setText(self.t('lbl_match_num_title'))
        self.lbl_gender_title.setText(self.t('lbl_gender_title'))
        self.lbl_weight_title.setText(self.t('lbl_weight_title'))
        
        if hasattr(self, 'radio_bo3'):
            self.radio_bo3.setText(self.t('radio_bo3'))
            self.radio_team.setText(self.t('radio_team'))

        self.btn_update_display.setText(self.t('btn_update_display'))
        self.group_data.setTitle(self.t('group_data_title'))
        self.btn_import.setText(self.t('btn_import'))
        self.table_schedule.setHorizontalHeaderLabels(self.t('table_schedule_headers'))
        self.group_preview.setTitle(self.t('group_preview_title'))
        self.group_timer.setTitle(self.t('group_timer_title'))
        self.btn_start_pause.setText(self.t('btn_start_pause'))
        self.btn_pause_menu.setText(self.t('btn_pause_menu'))
        self.action_kyeshi.setText(self.t('action_kyeshi'))
        self.action_shigan.setText(self.t('action_shigan'))
        self.lbl_round_time_title.setText(self.t('lbl_round_time_title'))
        self.lbl_break_time_title.setText(self.t('lbl_break_time_title'))
        
        self.chk_ptg.setText(self.t('chk_ptg'))
        self.chk_pun.setText(self.t('chk_pun'))

        self.btn_reset_timer.setText(self.t('btn_reset_timer'))
        self.group_manual.setTitle(self.t('group_manual_title'))
        self.lbl_red_title.setText(self.t('lbl_red_title'))
        self.lbl_blue_title.setText(self.t('lbl_blue_title'))
        self.lbl_action_title.setText(self.t('lbl_action_title'))
        self.group_log.setTitle(self.t('group_log_title'))
        self.btn_clear_log.setText(self.t('btn_clear_log'))
        
        if hasattr(self, 'btn_export_log'):
            self.btn_export_log.setText("XUẤT KẾT QUẢ & LOG (CSV)" if self.current_lang == "VI" else "EXPORT RESULT & LOG (CSV)")
            
        actions = self.t('actions')
        for i, lbl in enumerate(self.action_labels): lbl.setText(actions[i])
        self.btn_reset_match.setText(self.t('btn_reset_match'))
        
        if hasattr(self, 'btn_double_gj_red_plus'):
            self.btn_double_gj_red_plus.setText("+LỖI(x2đ)" if is_vi else "+1 PENALTY (10s, +2pt)")
            self.btn_double_gj_red_minus.setText("-LỖI(x2đ)" if is_vi else "-1 PENALTY (10s, -2pt)")
            self.btn_double_gj_blue_plus.setText("+LỖI(x2đ)" if is_vi else "+1 PENALTY (10s, +2pt)")
            self.btn_double_gj_blue_minus.setText("-LỖI(x2đ)" if is_vi else "-1 PENALTY (10s, -2pt)")
        
        if self.state.red.ivr_quota:
            self.btn_ivr_red.setText(self.t('btn_ivr_red_valid'))
            self.btn_ivr_red.setStyleSheet("background-color: #552222; color: #FF9999; font-weight: bold;")
        else:
            self.btn_ivr_red.setText(self.t('btn_ivr_red_rejected'))
            self.btn_ivr_red.setStyleSheet("background-color: #552222; color: #FF9999; font-weight: bold;")
            
        if self.state.blue.ivr_quota:
            self.btn_ivr_blue.setText(self.t('btn_ivr_blue_valid'))
            self.btn_ivr_blue.setStyleSheet("background-color: #223355; color: #99BBFF; font-weight: bold;")
        else:
            self.btn_ivr_blue.setText(self.t('btn_ivr_blue_rejected'))
            self.btn_ivr_blue.setStyleSheet("background-color: #223355; color: #99BBFF; font-weight: bold;")

        if is_vi:
            if self.input_red_name.text() == "RED": self.input_red_name.setText("VĐV ĐỎ")
            if self.input_blue_name.text() == "BLUE": self.input_blue_name.setText("VĐV XANH")
        else:
            if self.input_red_name.text() == "VĐV ĐỎ": self.input_red_name.setText("RED")
            if self.input_blue_name.text() == "VĐV XANH": self.input_blue_name.setText("BLUE")

        self.btn_sub_red.setText(self.t('btn_sub_red'))
        self.btn_sub_blue.setText(self.t('btn_sub_blue'))

        curr_cat_idx = self.combo_match_category.currentIndex()
        self.combo_match_category.clear()
        self.combo_match_category.addItems(self.t('combo_match_category_items'))
        if curr_cat_idx >= 0: self.combo_match_category.setCurrentIndex(curr_cat_idx)

        curr_gen_idx = self.combo_gender.currentIndex()
        self.combo_gender.clear()
        self.combo_gender.addItems(self.t('combo_gender_items'))
        if curr_gen_idx >= 0: self.combo_gender.setCurrentIndex(curr_gen_idx)

    def _parse_time_to_seconds(self, time_str):
        try:
            if ":" in time_str:
                m, s = map(int, time_str.split(":"))
                return float(m * 60 + s)
            return float(time_str)
        except Exception: return 60.0 

    def reset_timer_to_combo(self):
        if self.state.timer_running: return 

        if hasattr(self, 'scoreboard') and self.scoreboard:
            if hasattr(self.scoreboard, 'announcement'):
                self.scoreboard.announcement.hide()
            self.scoreboard.clear_winner_animation()
        
        txt = self.combo_round_time.currentText()
        total_secs = self._parse_time_to_seconds(txt)
        
        self.state.timer_seconds = total_secs
        self.state.timer_mode = "NORMAL"
        self.kyeshi_timer = 60.0 
        
        self.played_3s_warning = False
        
        if getattr(self.state, 'match_format', 'BO3') in ["TEAM_HP", "TEAM_BO3"]:
            self.state.red_sub_timer = 15.0
            self.state.blue_sub_timer = 15.0
        else:
            self.state.red_sub_timer = 0.0
            self.state.blue_sub_timer = 0.0
            
        self.sync_preview()
        self.scoreboard.update_ui()
        
        self.log_action("SYSTEM", f"Đã đặt lại đồng hồ ({txt})", f"Timer reset to ({txt})")

    def apply_manual_timer(self):
        val = self.input_manual_time.text().strip()
        secs = self._parse_time_to_seconds(val)
        if secs > 0:
            if hasattr(self, 'round_dialog') and self.round_dialog:
                self.round_dialog.close()
                self.round_dialog = None
            
            self.state.timer_seconds = secs
            self.state.timer_mode = "NORMAL" 
            self.played_3s_warning = False
            self.update_tick()
            self.log_action("SYSTEM", f"Ép thời gian thủ công: {val}", f"Manual time override: {val}")
        else:
            title = "Lỗi" if self.current_lang == "VI" else "Error"
            msg = "Định dạng sai. Vui lòng nhập số giây hoặc MM:SS (Ví dụ: 01:30)" if self.current_lang == "VI" else "Invalid format. Please enter seconds or MM:SS (e.g. 01:30)"
            QMessageBox.warning(self, title, msg)

    def toggle_timer(self):
        if hasattr(self, 'round_dialog') and self.round_dialog is not None: return
        if hasattr(self, 'match_dialog') and self.match_dialog is not None: return
        
        if self.state.timer_mode != "NORMAL": self.state.timer_mode = "NORMAL"
        self.state.timer_running = not self.state.timer_running
        self.update_tick()
        
        if not self.state.timer_running:
            if self.player_5s.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                self.player_5s.pause()
        else:
            self.setFocus()
            if self.state.timer_seconds <= 5.0 and self.state.timer_seconds > 0:
                self.player_5s.play()
        
        msg_vi = "Bắt đầu chạy đồng hồ trận đấu." if self.state.timer_running else "Tạm dừng đồng hồ trận đấu."
        msg_en = "Started match timer." if self.state.timer_running else "Paused match timer."
        self.log_action("SYSTEM", msg_vi, msg_en)

    def toggle_kyeshi(self):
        if self.state.timer_mode == "KYESHI":
            self.state.timer_mode = "NORMAL"; self.state.timer_running = False
            self.log_action("SYSTEM", "Kết thúc săn sóc KYESHI.", "Ended KYESHI medical time.")
        else:
            self.state.timer_mode = "KYESHI"; self.kyeshi_timer = 60.0; self.state.timer_running = True
            self.log_action("SYSTEM", "Kích hoạt KYESHI (Dừng săn sóc y tế).", "Activated KYESHI (Medical timeout).")
        self.update_tick()

    def toggle_shigan(self):
        if self.state.timer_mode == "SHIGAN":
            self.state.timer_mode = "NORMAL"; self.state.timer_running = False
            self.log_action("SYSTEM", "Kết thúc SHI-GAN.", "Ended SHI-GAN.")
        else:
            self.state.timer_mode = "SHIGAN"; self.state.timer_running = False
            self.log_action("SYSTEM", "Kích hoạt SHI-GAN (Xem xét Video / Dừng trọng tài).", "Activated SHI-GAN (Video Replay / Referee timeout).")
        self.update_tick()

    def format_time(self, seconds: float) -> str:
        secs = math.ceil(seconds)
        return f"{secs // 60:02d}:{secs % 60:02d}"

    def update_tick(self):
        if self.state.timer_running:
            if getattr(self.state, 'red_x2_timer', 0) > 0:
                self.state.red_x2_timer = max(0, self.state.red_x2_timer - 0.1)
            if getattr(self.state, 'blue_x2_timer', 0) > 0:
                self.state.blue_x2_timer = max(0, self.state.blue_x2_timer - 0.1)
                
            if getattr(self.state, 'red_sub_timer', 0) > 0:
                self.state.red_sub_timer = max(0, self.state.red_sub_timer - 0.1)
            if getattr(self.state, 'blue_sub_timer', 0) > 0:
                self.state.blue_sub_timer = max(0, self.state.blue_sub_timer - 0.1)

            if self.state.timer_mode == "NORMAL":
                self.check_auto_win_conditions() 
                if 0 < self.state.timer_seconds <= 10.0:
                    self.btn_double_gj_red_plus.setEnabled(True)
                    self.btn_double_gj_red_plus.setStyleSheet("background-color: #552222; color: #FF9999; font-weight: bold;")
                    self.btn_double_gj_red_minus.setEnabled(True)
                    self.btn_double_gj_red_minus.setStyleSheet("background-color: #331111; color: #FF5555; font-weight: bold;")
                    
                    self.btn_double_gj_blue_plus.setEnabled(True)
                    self.btn_double_gj_blue_plus.setStyleSheet("background-color: #223355; color: #99BBFF; font-weight: bold;")
                    self.btn_double_gj_blue_minus.setEnabled(True)
                    self.btn_double_gj_blue_minus.setStyleSheet("background-color: #111133; color: #5588FF; font-weight: bold;")
                else:
                    self.btn_double_gj_red_plus.setEnabled(False)
                    self.btn_double_gj_red_plus.setStyleSheet("background-color: #331111; color: #555555; font-weight: bold;")
                    self.btn_double_gj_red_minus.setEnabled(False)
                    self.btn_double_gj_red_minus.setStyleSheet("background-color: #331111; color: #555555; font-weight: bold;")
                    
                    self.btn_double_gj_blue_plus.setEnabled(False)
                    self.btn_double_gj_blue_plus.setStyleSheet("background-color: #111133; color: #555555; font-weight: bold;")
                    self.btn_double_gj_blue_minus.setEnabled(False)
                    self.btn_double_gj_blue_minus.setStyleSheet("background-color: #111133; color: #555555; font-weight: bold;")
                    
                if self.state.timer_seconds <= 0:
                    self.state.timer_seconds = 0
                    self.state.timer_running = False
                    self.state.timer_mode = "WAIT_CONFIRM"
                    
                    self.lbl_control_timer.setText("00:00")
                    if hasattr(self.scoreboard, 'set_timer_text'):
                        self.scoreboard.set_timer_text("00:00", "#FF3333", is_break=False)
                        self.scoreboard.update_ui()
                    from PyQt6.QtWidgets import QApplication
                    QApplication.processEvents()
                    
                    self.player_bell.play()
                    self.log_action("SYSTEM", f"HẾT GIỜ HIỆP {self.state.current_round}!", f"END OF ROUND {self.state.current_round}!")
                    self.trigger_end_round() 
                else:
                    if 0 < self.state.timer_seconds <= 3.0 and not getattr(self, 'played_3s_warning', False):
                        self.player_5s.setPosition(2000) 
                        self.player_5s.play()
                        self.played_3s_warning = True
                    self.state.timer_seconds -= 0.1
                    
            elif self.state.timer_mode == "BREAK":
                self.break_timer_seconds -= 0.1
                if round(self.break_timer_seconds, 1) == 3.0:
                    self.player_5s.setPosition(2000) 
                    self.player_5s.play()
                if self.break_timer_seconds <= 0:
                    self.break_timer_seconds = 0
                    self.state.timer_running = False 
                    
                    self.lbl_control_timer.setText("NGHỈ\n00:00")
                    if hasattr(self.scoreboard, 'set_timer_text'):
                        self.scoreboard.set_timer_text("00:00", "#FFD700", is_break=True)
                        self.scoreboard.update_ui()
                    from PyQt6.QtWidgets import QApplication
                    QApplication.processEvents()
                    
                    self.player_bell.play()
                    self.log_action("SYSTEM", "Hết giờ nghỉ giữa hiệp.", "Break time is over.")
                    self.trigger_start_new_round() 
                    
            elif self.state.timer_mode == "KYESHI":
                self.kyeshi_timer -= 0.1
                if self.kyeshi_timer <= 0:
                    self.kyeshi_timer = 0; self.state.timer_mode = "NORMAL"; self.state.timer_running = False

        if self.state.timer_mode == "NORMAL":
            txt = self.format_time(self.state.timer_seconds)
            color = "#00FFB2" if self.state.timer_running else "#A0A0A0"
        elif self.state.timer_mode == "BREAK":
            txt = f"{self.format_time(self.break_timer_seconds)}"
            color = "#FFD700"
        elif self.state.timer_mode == "KYESHI":
            secs = math.ceil(self.kyeshi_timer)
            txt = f"KYESHI\n{secs // 60:02d}:{secs % 60:02d}"
            color = "#FF3333"
        elif self.state.timer_mode == "SHIGAN":
            txt = "SHI-GAN"
            color = "#3399FF"
        elif self.state.timer_mode == "WAIT_CONFIRM":
            txt = "00:00"
            color = "#FF3333"

        display_text = txt
        prev_timer_text = getattr(self, 'last_timer_text', None)
        if display_text != prev_timer_text:
            self.lbl_control_timer.setText(display_text)
            self.last_timer_text = display_text

        if hasattr(self.scoreboard, 'set_timer_text') and (display_text != prev_timer_text or color != self.last_timer_color):
            self.scoreboard.set_timer_text(display_text, color, is_break=(self.state.timer_mode == "BREAK"))

        if color != self.last_timer_color:
            self.lbl_control_timer.setStyleSheet(f"font-size: 65px; font-weight: bold; color: {color}; font-family: 'Consolas'; border: none; margin-bottom: 5px;")
            self.last_timer_color = color

        now = time.time()
        red_flashes = self.engine.get_flash_state("red", now)
        blue_flashes = self.engine.get_flash_state("blue", now)
        self.scoreboard.update_lights(red_flashes, blue_flashes)
        
        self.sync_preview()

    def check_auto_win_conditions(self):
        if self.state.timer_mode in ["BREAK", "WAIT_CONFIRM"]: return
        if hasattr(self, 'round_dialog') and self.round_dialog is not None: return
        if hasattr(self, 'match_dialog') and self.match_dialog is not None: return

        is_hp_mode = getattr(self.state, 'match_format', 'BO3') == "TEAM_HP"
        is_team_bo3 = getattr(self.state, 'match_format', 'BO3') == "TEAM_BO3"

        if is_hp_mode:
            if self.state.red.score <= 0:
                self.player_5s.stop(); self.player_bell.play()
                self.trigger_special_round_win("BLUE", "ĐỐI THỦ HẾT MÁU", "OPPONENT OUT OF HP", "KO")
                return
            if self.state.blue.score <= 0:
                self.player_5s.stop(); self.player_bell.play()
                self.trigger_special_round_win("RED", "ĐỐI THỦ HẾT MÁU", "OPPONENT OUT OF HP", "KO")
                return
        else:
            # KIỂM TRA ĐIỂM TRẦN - ĐỒNG ĐỘI BO3
            # KIỂM TRA ĐIỂM TRẦN - ĐỒNG ĐỘI BO3
            # Chỉ xét điểm trần nếu chế độ BO3 và cái nút Tick đang được bật
            if is_team_bo3 and self.chk_max_score.isChecked():
                try:
                    max_score = int(self.input_max_score.text().strip())
                except ValueError:
                    max_score = 30 # Mặc định nếu lỡ xóa trống
                
                if self.state.red.score >= max_score:
                    self.player_5s.stop(); self.player_bell.play()
                    self.trigger_special_round_win("RED", f"CHẠM ĐIỂM TRẦN ({max_score}đ)", f"REACHED MAX SCORE ({max_score}pts)", "PTF")
                    return
                if self.state.blue.score >= max_score:
                    self.player_5s.stop(); self.player_bell.play()
                    self.trigger_special_round_win("BLUE", f"CHẠM ĐIỂM TRẦN ({max_score}đ)", f"REACHED MAX SCORE ({max_score}pts)", "PTF")
                    return

            # CÁC LUẬT BÌNH THƯỜNG KHÁC (12đ, 5 Lỗi)
            if self.chk_pun.isChecked():
                if self.state.red.gamjeom >= 5:
                    self.player_5s.stop(); self.player_bell.play()
                    self.trigger_special_round_win("BLUE", "THẮNG DO ĐỐI THỦ 5 LỖI", "WIN BY 5 PENALTIES", "PUN")
                    return
                if self.state.blue.gamjeom >= 5:
                    self.player_5s.stop(); self.player_bell.play()
                    self.trigger_special_round_win("RED", "THẮNG DO ĐỐI THỦ 5 LỖI", "WIN BY 5 PENALTIES", "PUN")
                    return
                    
            if self.chk_ptg.isChecked():
                if self.state.red.score - self.state.blue.score >= 12:
                    self.player_5s.stop(); self.player_bell.play()
                    self.trigger_special_round_win("RED", "CÁCH BIỆT ĐIỂM (12đ)", "POINT GAP (12pts)", "PTG")
                    return
                if self.state.blue.score - self.state.red.score >= 12:
                    self.player_5s.stop(); self.player_bell.play()
                    self.trigger_special_round_win("BLUE", "CÁCH BIỆT ĐIỂM (12đ)", "POINT GAP (12pts)", "PTG")
                    return

    def trigger_start_new_round(self):
        dialog = BreakEndDialog(self.state.current_round, self.current_lang == "VI", self)
        if dialog.exec():
            self.state.timer_running = False
            self.reset_timer_to_combo()
            
            if getattr(self.state, 'match_format', 'BO3') in ["TEAM_HP", "TEAM_BO3"]:
                self.state.red_sub_timer = 15.0
                self.state.blue_sub_timer = 15.0
            else:
                self.state.red_sub_timer = 0.0
                self.state.blue_sub_timer = 0.0

            self.state.timer_running = True 
            self.log_action("SYSTEM", f"BẮT ĐẦU HIỆP {self.state.current_round}!", f"ROUND {self.state.current_round} STARTED!")
            self.sync_preview() 
            self.update_tick()

    def evaluate_round_winner(self):
        r = self.state.red; b = self.state.blue
        is_hp_mode = getattr(self.state, 'match_format', 'BO3') == "TEAM_HP"
        
        if is_hp_mode:
            if r.score <= 0: return "BLUE", "KO"
            if b.score <= 0: return "RED", "KO"
            if r.score > b.score: return "RED", "HP"
            if b.score > r.score: return "BLUE", "HP"
        else:
            if self.chk_pun.isChecked():
                if r.gamjeom >= 5: return "BLUE", "PUN"
                if b.gamjeom >= 5: return "RED", "PUN"
                
            if self.chk_ptg.isChecked():
                if r.score - b.score >= 12: return "RED", "PTG"
                if b.score - r.score >= 12: return "BLUE", "PTG"
                
            if r.score > b.score: return "RED", "PTF"
            if b.score > r.score: return "BLUE", "PTF"
        
        if r.pts_turn > b.pts_turn: return "RED", "SUP"
        if b.pts_turn > r.pts_turn: return "BLUE", "SUP"
        if r.pts_head > b.pts_head: return "RED", "SUP"
        if b.pts_head > r.pts_head: return "BLUE", "SUP"
        if r.pts_body > b.pts_body: return "RED", "SUP"
        if b.pts_body > r.pts_body: return "BLUE", "SUP"
        if r.pts_punch > b.pts_punch: return "RED", "SUP"
        if b.pts_punch > r.pts_punch: return "BLUE", "SUP"
        if r.gamjeom < b.gamjeom: return "RED", "SUP"
        if b.gamjeom < r.gamjeom: return "BLUE", "SUP"
        
        return "TIE", ""

    def trigger_end_round(self, auto_winner=None, method=None):
        if auto_winner is None or method is None:
            auto_winner, method = self.evaluate_round_winner()
        
        self.state.timer_mode = "WAIT_CONFIRM"
        self.state.timer_running = False 
        is_vi = (self.current_lang == "VI")
        self.round_dialog = RoundEndDialog(self.state.red.name, self.state.blue.name, auto_winner, method, is_vi, self)
        self.round_dialog.setModal(False) 
        
        self.round_dialog.accepted.connect(self.process_round_result)
        
        self.round_dialog.rejected.connect(self.cancel_special_win)
        
        self.round_dialog.show()

    def process_round_result(self):
        if not self.round_dialog: return
        final_winner = self.round_dialog.get_winner()
        final_method = self.round_dialog.get_method()
        cr = self.state.current_round
        
        is_vi = (self.current_lang == "VI")
        main_txt = f"{final_winner} WINS" if not is_vi else f"{'ĐỎ' if final_winner=='RED' else 'XANH'} THẮNG"
        
        if final_method == "PTG": sub_txt = "CÁCH BIỆT ĐIỂM (12đ)" if is_vi else "POINT GAP (12pts)"
        elif final_method == "PUN": sub_txt = "THẮNG DO ĐỐI THỦ 5 LỖI" if is_vi else "WIN BY 5 PENALTIES"
        elif final_method == "KO": sub_txt = "ĐỐI THỦ HẾT MÁU" if is_vi else "OPPONENT OUT OF HP"
        else: sub_txt = f"THẮNG BẰNG {final_method}" if is_vi else f"WIN BY {final_method}"

        if hasattr(self.scoreboard, 'announcement'):
            self.scoreboard.announcement.show_announcement(final_winner, main_txt, sub_txt, self.scoreboard.scale)

        if cr <= 3:
            r = self.state.red
            b = self.state.blue
            self.state.round_results[cr] = {
                'red_score': r.score, 
                'blue_score': b.score, 
                'winner': final_winner, 
                'method': final_method,
                'red_stats': [r.pts_punch, r.pts_body, r.pts_head, r.pts_turn, r.gamjeom],
                'blue_stats': [b.pts_punch, b.pts_body, b.pts_head, b.pts_turn, b.gamjeom]
            }

        if not hasattr(self.state.red, 'rounds_won'): self.state.red.rounds_won = 0
        if not hasattr(self.state.blue, 'rounds_won'): self.state.blue.rounds_won = 0
        
        if final_winner == "RED":
            self.state.red.rounds_won += 1; self.log_action("red", f"VĐV ĐỎ THẮNG HIỆP {cr} bằng {final_method}!", f"RED WINS ROUND {cr} by {final_method}!")
        elif final_winner == "BLUE":
            self.state.blue.rounds_won += 1; self.log_action("blue", f"VĐV XANH THẮNG HIỆP {cr} bằng {final_method}!", f"BLUE WINS ROUND {cr} by {final_method}!")
        
        self.sync_preview() 
        self.round_dialog = None

        if self.state.red.rounds_won >= 2 or self.state.blue.rounds_won >= 2 or cr >= 3:
            self.state.timer_running = False 
            if self.state.red.rounds_won == self.state.blue.rounds_won:
                if hasattr(self.scoreboard, 'announcement'): self.scoreboard.announcement.hide()
                msg = "HIỆP 3 KHÔNG ĐƯỢC PHÉP HÒA!\nNếu các chỉ số ưu thế bằng nhau, Trọng tài chính phải rút thẻ quyết định (PUN)!" if self.current_lang == "VI" else "ROUND 3 CANNOT TIE!\nReferee must decide the winner (PUN)!"
                title = "Lỗi Luật WT" if self.current_lang == "VI" else "WT Rule Error"
                QMessageBox.warning(self, title, msg)
                self.trigger_end_round()
                return
            
            match_auto = "RED" if self.state.red.rounds_won > self.state.blue.rounds_won else "BLUE"
            is_vi = (self.current_lang == "VI")
            self.match_dialog = MatchEndDialog(self.state.red.name, self.state.blue.name, match_auto, is_vi, self)
            self.match_dialog.setModal(False) 
            self.match_dialog.accepted.connect(self.process_match_result)
            self.match_dialog.show()
            return 
        
        is_vi = (self.current_lang == "VI")
        title = "Bắt đầu nghỉ giữa hiệp" if is_vi else "Start Break"
        text = (f"Đã chốt kết quả Hiệp {cr} thành công.\nBấm OK để tắt thông báo trên Tivi và chạy giờ nghỉ!" if is_vi else f"Round {cr} result confirmed.\nPress OK to clear TV announcement and start break timer.")
        
        QMessageBox.information(self, title, text)
        self.start_break_time()

    def process_match_result(self):
        if not self.match_dialog: return
        match_final = self.match_dialog.get_winner()
        self.log_action(match_final.lower(), f"VĐV {match_final} GIÀNH CHIẾN THẮNG CHUNG CUỘC!", f"{match_final} WINS THE MATCH!")
        
        if hasattr(self.scoreboard, 'announcement'):
            self.scoreboard.announcement.hide()
            
        self.scoreboard.play_winner_animation(match_final.lower())
        self.match_dialog = None
    
    def toggle_serial(self):
        """Bật/Tắt luồng đọc tín hiệu từ tay cầm"""
        is_vi = (self.current_lang == "VI")
        if self.serial_thread and self.serial_thread.running:
            self.serial_thread.stop()
            self.serial_thread = None
            self.btn_connect_com.setText("KẾT NỐI TAY CẦM" if is_vi else "CONNECT GAMEPAD")
            self.btn_connect_com.setStyleSheet("background-color: #006699; font-weight: bold; padding: 10px;")
            self.com_combo.setEnabled(True)
            self.log_action("SYSTEM", "Đã ngắt kết nối.", "Disconnected.")
        else:
            port = self.com_combo.currentData()
            if not port:
                title = "Lỗi" if is_vi else "Error"
                msg = "Chưa có cổng nào được chọn!" if is_vi else "No port selected!"
                QMessageBox.warning(self, title, msg)
                return

            self.serial_thread = SerialReader(port, 115200)
            self.serial_thread.data_received.connect(self.process_hardware_input)
            self.serial_thread.error_signal.connect(lambda e: self.log_action("SYSTEM", f"Lỗi: {e}"))
            self.serial_thread.start()

            self.btn_connect_com.setText("NGẮT KẾT NỐI TAY CẦM" if is_vi else "DISCONNECT GAMEPAD")
            self.btn_connect_com.setStyleSheet("background-color: #A03333; font-weight: bold; padding: 10px;")
            self.com_combo.setEnabled(False)
            self.log_action("SYSTEM", f"Hệ thống đã sẵn sàng tại {port}", f"System Ready at {port}")

    def trigger_hotswap(self):
        """Xử lý bật/tắt chế độ dùng Tay cầm dự phòng"""
        if self.gamepad_routing[4] is None:
            dialog = HotSwapDialog(self)
            if dialog.exec() and dialog.selected_target is not None:
                target = dialog.selected_target
                self.gamepad_routing[target] = None 
                self.gamepad_routing[4] = target
                
                self.lbl_hw_status.setText(f"Trạng thái: TAY 4 ĐANG CHẠY (Thay TT{target})")
                self.lbl_hw_status.setStyleSheet("color: #FFD700; font-weight: bold;")
                self.btn_hotswap.setText("TẮT TAY CẦM DỰ PHÒNG (KHÔI PHỤC MẶC ĐỊNH)")
                self.btn_hotswap.setStyleSheet("background-color: #225522; color: #99FF99; padding: 10px;")
                self.log_action("SYSTEM", f"Kích hoạt Tay 4: Thay thế cho Trọng tài {target}", f"Gamepad 4 activated for Judge {target}")
        else:
            self.gamepad_routing = {1: 1, 2: 2, 3: 3, 4: None}
            self.lbl_hw_status.setText("Trạng thái: Đang dùng Tay 1, 2, 3 chuẩn.")
            self.lbl_hw_status.setStyleSheet("color: #00FFB2; font-weight: bold;")
            self.btn_hotswap.setText(" KÍCH HOẠT TAY CẦM DỰ PHÒNG ")
            self.btn_hotswap.setStyleSheet("background-color: #552222; color: #FF9999; padding: 10px;")
            self.log_action("SYSTEM", "Tắt Tay 4. Khôi phục mặc định 3 tay gốc.", "Disabled Gamepad 4. Restored defaults.")

    def process_hardware_input(self, key_signal):
        """Hàm dùng chung cho cả Cổng COM và Bàn phím vật lý"""
        key_str = str(key_signal) 
        if key_str in self.hardware_keymap:
            hw_judge_id, action = self.hardware_keymap[key_str]
            if hw_judge_id == "SYS":
                return True

            if self.state.timer_running and self.state.timer_mode == "NORMAL":
                logical_judge = self.gamepad_routing.get(int(hw_judge_id))
                if logical_judge is None: 
                    return True 
                is_valid_press = self.engine.register_press(logical_judge, action)
                if is_valid_press:
                    def trigger_score():
                        import time
                        judges_list = self.engine.evaluate(time.time())
                        if judges_list:
                            self.sync_preview() 
                            color = "red" if action.startswith("R") else "blue"
                            act_vi = "Kỹ thuật" if action.endswith("T") else ("Đấm" if action.endswith("1") else ("Bụng" if action.endswith("2") else "Đầu"))
                            danh_sach = " & ".join([f"TT{j}" for j in sorted(list(judges_list))])
                            self.log_action(color, f"Ghi điểm -> {act_vi} (Bởi: {danh_sach})")
                    from PyQt6.QtCore import QTimer
                    QTimer.singleShot(150, trigger_score)
                return True
        return False

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key.Key_Space:
            if not isinstance(self.focusWidget(), QLineEdit) and not isinstance(self.focusWidget(), QComboBox):
                self.toggle_timer(); event.accept(); return
        if self.process_hardware_input(str(key)):
            event.accept()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        """Đảm bảo tắt luồng COM an toàn khi tắt ứng dụng"""
        if hasattr(self, 'serial_thread') and self.serial_thread and self.serial_thread.running:
            self.serial_thread.stop()
        super().closeEvent(event)

    def sync_preview(self):
        self.scoreboard.update_ui()
        now = time.time()
        if now - getattr(self, 'last_grab_time', 0.0) >= getattr(self, 'preview_interval', 0.3):
            try:
                pixmap = self.scoreboard.grab()
                if not pixmap.isNull():
                    lbl_w = self.lbl_live_preview.width()
                    lbl_h = self.lbl_live_preview.height()
                    scaled_pixmap = pixmap.scaled(
                        lbl_w, lbl_h,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.FastTransformation
                    )
                    self.lbl_live_preview.setPixmap(scaled_pixmap)
                self.last_grab_time = now
            except Exception:
                pass

    def update_match_info(self):
        self.state.match_category = self.combo_match_category.currentText().upper()
        self.state.red.name = self.input_red_name.text().upper()
        self.state.red.flag = self.combo_red_flag.currentText().lower() 
        self.state.blue.name = self.input_blue_name.text().upper()
        self.state.blue.flag = self.combo_blue_flag.currentText().lower() 
        self.state.match_number = self.combo_match_num.currentText()
        self.state.gender = self.combo_gender.currentText()
        self.state.weight_class = self.combo_weight.currentText()
        
        self.sync_preview()

    def handle_manual_score(self, color, action, value):
        target_player = self.state.red if color == "red" else self.state.blue
        opp_player = self.state.blue if color == "red" else self.state.red
        is_hp_mode = getattr(self.state, 'match_format', 'BO3') == "TEAM_HP"

        if action == "gamjeom_10s":
            if value > 0:
                target_player.gamjeom += 1 
                if is_hp_mode:
                    target_player.score -= 10 
                else:
                    opp_player.score += 2 
                
                msg_vi = f"Bị trừ 10 HP (Thụ động 10s cuối)" if is_hp_mode else f"Đối phương +2đ (Thụ động 10s cuối)"
                msg_en = f"-10 HP (Passive last 10s)" if is_hp_mode else f"Opponent +2 (Passive last 10s)"
                self.log_action(color, f"Lỗi 10s cuối -> {msg_vi}", f"Last 10s Penalty -> {msg_en}")
                
            elif value < 0 and target_player.gamjeom > 0:
                target_player.gamjeom -= 1 
                if is_hp_mode:
                    target_player.score += 10 
                else:
                    opp_player.score = max(0, opp_player.score - 2) 
                
                msg_vi = f"Được trả 10 HP" if is_hp_mode else f"Đối phương -2đ"
                msg_en = f"+10 HP" if is_hp_mode else f"Opponent -2"
                self.log_action(color, f"Gỡ Lỗi 10s cuối -> {msg_vi}", f"Remove 10s Penalty -> {msg_en}")

        elif action == "gamjeom":
            if value > 0:
                target_player.gamjeom += value
                if is_hp_mode:
                    target_player.score -= (5 * value) 
                else:
                    opp_player.score += value
                
                msg_vi = f"Bị trừ {5 * value} HP" if is_hp_mode else f"Đối phương +{value}"
                msg_en = f"-{5 * value} HP" if is_hp_mode else f"Opponent +{value}"
                self.log_action(color, f"Lỗi (Gam-Jeom x{value}) -> {msg_vi}", f"Penalty x{value} -> {msg_en}")
                
            elif value < 0 and target_player.gamjeom > 0:
                remove_amount = min(abs(value), target_player.gamjeom)
                target_player.gamjeom -= remove_amount
                
                if is_hp_mode:
                    target_player.score += (5 * remove_amount) 
                else:
                    opp_player.score = max(0, opp_player.score - remove_amount)
                self.log_action(color, "Xóa Lỗi (Gam-Jeom) -> " + ("Được trả 5 HP" if is_hp_mode else "Đối phương -1"), "Remove Penalty -> " + ("+5 HP" if is_hp_mode else "Opponent -1"))
        else:
            # === THÊM CHỐT CHẶN: NẾU LÀ LỆNH TRỪ VÀ BỘ ĐẾM BẰNG 0 THÌ HỦY BỎ LỆNH ===
            if value < 0:
                if action == "punch" and target_player.pts_punch <= 0: return
                elif action == "body" and target_player.pts_body <= 0: return
                elif action == "head" and target_player.pts_head <= 0: return
                elif action in ["tech_body", "tech_head"] and target_player.pts_turn <= 0: return
            # =========================================================================

            if is_hp_mode:
                multiplier = 1
                if color == "red" and getattr(self.state, 'red_x2_timer', 0) > 0:
                    multiplier = 2
                elif color == "blue" and getattr(self.state, 'blue_x2_timer', 0) > 0:
                    multiplier = 2

                damage = value * 5 * multiplier
                if value > 0: 
                    opp_player.score -= damage
                else: 
                    opp_player.score += abs(damage)
                
                x2_str = " [X2 DAMAGE!]" if multiplier == 2 else ""
            else:
                target_player.score = max(0, target_player.score + value)
                x2_str = ""
            
            act_vi = "Đấm" if action=="punch" else ("Bụng" if action=="body" else ("Đầu" if action=="head" else ("Kỹ Thuật Bụng" if action=="tech_body" else ("Kỹ Thuật Đầu" if action=="tech_head" else "Lỗi"))))
            act_en = "Punch" if action=="punch" else ("Body Kick" if action=="body" else ("Head Kick" if action=="head" else ("Tech Body" if action=="tech_body" else ("Tech Head" if action=="tech_head" else "Penalty"))))
            
            self.log_action(color, f"Chỉnh tay: {'+' if value > 0 else ''}{value} ({act_vi}){x2_str}", f"Manual Override: {'+' if value > 0 else ''}{value} ({act_en}){x2_str}")
            
            increment = 1 if value > 0 else -1
            if action == "punch": target_player.pts_punch = max(0, target_player.pts_punch + increment)
            elif action == "body": target_player.pts_body = max(0, target_player.pts_body + increment)
            elif action == "head": target_player.pts_head = max(0, target_player.pts_head + increment)
            elif action == "tech_body": 
                target_player.pts_turn = max(0, target_player.pts_turn + value) 
            elif action == "tech_head":
                target_player.pts_turn = max(0, target_player.pts_turn + value)
                
        self.sync_preview()

        if hasattr(self, 'round_dialog') and self.round_dialog is not None and self.round_dialog.isVisible():
            r = self.state.red
            b = self.state.blue
            
            still_end = False
            
            # --- ĐÃ SỬA CHỖ NÀY: NẾU HẾT GIỜ THÌ CHẮC CHẮN VẪN ĐANG KẾT THÚC HIỆP ---
            if self.state.timer_seconds <= 0:
                still_end = True
                
            if is_hp_mode:
                if r.score <= 0 or b.score <= 0: still_end = True
            else:
                if self.chk_pun.isChecked() and (r.gamjeom >= 5 or b.gamjeom >= 5): still_end = True
                if self.chk_ptg.isChecked() and (abs(r.score - b.score) >= 12): still_end = True
                
            if not still_end:
                self.round_dialog.close()
                self.round_dialog = None
                self.state.timer_mode = "NORMAL" 
                
                is_vi = (self.current_lang == "VI")
                self.log_action("SYSTEM", "Khoảng cách thay đổi. HỦY KẾT THÚC HIỆP, ĐÁNH TIẾP!", "Gap changed. ROUND RESUMED!")
            else:
                # TỰ ĐỘNG XÉT LẠI LÝ DO THẮNG VÀ NGƯỜI THẮNG NGAY LẬP TỨC
                new_auto_winner, new_method = self.evaluate_round_winner()
                self.round_dialog.update_winner(new_auto_winner, new_method)
        else:
            self.check_auto_win_conditions()

    def clear_log(self):
        self.log_history.clear() 
        self.render_logs() 
        self.log_action("SYSTEM", "Đã dọn dẹp lịch sử thao tác.", "Match log cleared.")

    def reset_match(self):
        msg = 'Bạn có chắc chắn muốn xóa toàn bộ điểm, lỗi và reset về HIỆP 1 không?' if self.current_lang == "VI" else 'Are you sure you want to clear all scores, penalties and reset to ROUND 1?'
        title_confirm = 'Xác nhận' if self.current_lang == 'VI' else 'Confirm'
        
        reply = QMessageBox.question(self, title_confirm, msg, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            if hasattr(self.scoreboard, 'announcement'):
                self.scoreboard.announcement.hide()
            
            if hasattr(self, 'round_dialog') and self.round_dialog:
                self.round_dialog.close(); self.round_dialog = None
            if hasattr(self, 'match_dialog') and self.match_dialog:
                self.match_dialog.close(); self.match_dialog = None
            
            self.state.reset_round_scores()
            self.state.current_round = 1
            self.state.red.gamjeom = 0
            self.state.blue.gamjeom = 0
            self.state.red.pts_punch = 0; self.state.red.pts_body = 0; self.state.red.pts_head = 0; self.state.red.pts_turn = 0
            self.state.blue.pts_punch = 0; self.state.blue.pts_body = 0; self.state.blue.pts_head = 0; self.state.blue.pts_turn = 0
            
            if hasattr(self.state.red, 'rounds_won'): self.state.red.rounds_won = 0
            if hasattr(self.state, 'blue') and hasattr(self.state.blue, 'rounds_won'): self.state.blue.rounds_won = 0
            
            self.state.red_x2_timer = 0.0
            self.state.blue_x2_timer = 0.0
            
            self.played_3s_warning = False
            
            if getattr(self.state, 'match_format', 'BO3') in ["TEAM_HP", "TEAM_BO3"]:
                self.state.red_sub_timer = 15.0
                self.state.blue_sub_timer = 15.0
            else:
                self.state.red_sub_timer = 0.0
                self.state.blue_sub_timer = 0.0
            
            if getattr(self.state, 'match_format', 'BO3') == "TEAM_HP":
                self.state.red.score = 150
                self.state.blue.score = 150

            self.state.red.ivr_quota = True
            self.state.blue.ivr_quota = True
            self.state.timer_running = False
            self.state.timer_mode = "NORMAL"
            self.state.round_results = {1: None, 2: None, 3: None}
            
            self.scoreboard.clear_winner_animation()
            self.reset_timer_to_combo()
            self.update_match_info() 
            self.update_texts()
            
            self.scoreboard.update_ui()
            self.sync_preview()
            
            self.log_action("SYSTEM", "Đã reset sạch sẽ trận đấu!", "Match completely reset!")
    
    def open_keymap_tool(self):
        dialog = KeymapDialog(self); dialog.exec(); self.load_keymap_file()

    def trigger_passive(self, penalized_side):
        if getattr(self.state, 'match_format', 'BO3') != "TEAM_HP":
            title = "Thông báo" if self.current_lang == "VI" else "Notice"
            msg = "Chế độ Sip-cho chỉ áp dụng cho mode ĐỒNG ĐỘI!" if self.current_lang == "VI" else "Sip-cho mode only applies in TEAM mode!"
            QMessageBox.information(self, title, msg)
            return

        if penalized_side == "red":
            self.state.red.gamjeom += 1
            self.state.red.score -= 5
            self.state.blue_x2_timer = 10.0 
            self.log_action("red", "Lỗi thụ động! XANH ĐƯỢC X2 SÁT THƯƠNG 10s", "Passive Penalty! BLUE X2 DAMAGE 10s")
        else:
            self.state.blue.gamjeom += 1
            self.state.blue.score -= 5
            self.state.red_x2_timer = 10.0 
            self.log_action("blue", "Lỗi thụ động! ĐỎ ĐƯỢC X2 SÁT THƯƠNG 10s", "Passive Penalty! RED X2 DAMAGE 10s")
        
        self.sync_preview()
        self.check_auto_win_conditions()

    def trigger_substitution(self, color):
        if getattr(self.state, 'match_format', 'BO3') not in ["TEAM_HP", "TEAM_BO3"]:
            title = "Thông báo" if self.current_lang == "VI" else "Notice"
            msg = "Đổi người chỉ áp dụng cho chế độ ĐỒNG ĐỘI!" if self.current_lang == "VI" else "Substitution only applies in TEAM mode!"
            QMessageBox.information(self, title, msg)
            return
            
        if color == "red":
            self.state.red_sub_timer = 15.0
            self.state.blue_sub_timer = 10.0  # Ép thẳng Xanh về 10s
            self.log_action("red", "ĐỎ ĐỔI NGƯỜI! (Đỏ khóa 15s, Ép Xanh 10s)", "RED SUBSTITUTION! (Red 15s, Blue 10s)")
        else:
            self.state.blue_sub_timer = 15.0
            self.state.red_sub_timer = 10.0  # Ép thẳng Đỏ về 10s
            self.log_action("blue", "XANH ĐỔI NGƯỜI! (Xanh khóa 15s, Ép Đỏ 10s)", "BLUE SUBSTITUTION! (Blue 15s, Red 10s)")
            
        self.sync_preview()
    
    def trigger_special_round_win(self, color, reason_vi, reason_en, method_code):
        """Chỉ khóa giờ và gọi popup chốt kết quả (Chưa hiện Tivi)"""
        self.state.timer_running = False 
        self.state.timer_mode = "WAIT_CONFIRM" 
        self.trigger_end_round(auto_winner=color, method=method_code)
    
    def cancel_special_win(self):
        """Ẩn thông báo trên Tivi và mở khóa lại trận đấu"""
        if hasattr(self.scoreboard, 'announcement'):
            self.scoreboard.announcement.hide()
        
        if self.state.timer_mode == "WAIT_CONFIRM":
            self.state.timer_mode = "NORMAL"

    def start_break_time(self, button=None):
        """Tắt Tivi và bắt đầu chạy thời gian nghỉ"""
        if hasattr(self.scoreboard, 'announcement'):
            self.scoreboard.announcement.hide()
        
        txt_break = self.combo_break_time.currentText()
        self.break_timer_seconds = self._parse_time_to_seconds(txt_break)
        self.state.timer_mode = "BREAK"
        self.state.timer_running = True
        
        self.state.current_round += 1
        self.state.reset_round_scores()
        
        if getattr(self.state, 'match_format', 'BO3') == "TEAM_HP":
            self.state.red.score = 150
            self.state.blue.score = 150
            
        self.sync_preview()
        self.update_tick() # Ép đồng hồ cập nhật số ngay lập tức

    def export_match_stats(self):
        dialog_title = "Lưu Báo Cáo Trận Đấu (CSV)" if self.current_lang == "VI" else "Save Match Report (CSV)"
        
        match_no = self.state.match_number
        default_name = f"Match_{match_no}_{self.state.red.name}_vs_{self.state.blue.name}.csv"
        
        file_name, _ = QFileDialog.getSaveFileName(self, dialog_title, default_name, "CSV Files (*.csv)")
        
        if file_name:
            try:
                with open(file_name, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    
                    writer.writerow(["THÔNG TIN TRẬN ĐẤU", f"Trận số {match_no} - {self.state.match_category} - {self.state.gender} {self.state.weight_class}"])
                    writer.writerow(["VĐV ĐỎ:", self.state.red.name, "VĐV XANH:", self.state.blue.name])
                    writer.writerow([])
                    
                    writer.writerow([
                        "HIỆP", 
                        "ĐỎ-TỔNG ĐIỂM", "Đỏ-Đấm", "Đỏ-Bụng", "Đỏ-Đầu", "Đỏ-Xoay", "Đỏ-Lỗi", 
                        "XANH-TỔNG ĐIỂM", "Xanh-Đấm", "Xanh-Bụng", "Xanh-Đầu", "Xanh-Xoay", "Xanh-Lỗi", 
                        "NGƯỜI THẮNG", "CÁCH THẮNG"
                    ])
                    
                    for i in [1, 2, 3]:
                        res = self.state.round_results.get(i)
                        if res:
                            rs = res.get('red_stats', [0,0,0,0,0])
                            bs = res.get('blue_stats', [0,0,0,0,0])
                            writer.writerow([
                                f"Hiệp {i}",
                                res['red_score'], rs[0], rs[1], rs[2], rs[3], rs[4],
                                res['blue_score'], bs[0], bs[1], bs[2], bs[3], bs[4],
                                res['winner'], res['method']
                            ])
                    
                    writer.writerow([])
                    
                    writer.writerow(["--- NHẬT KÝ THAO TÁC TRỌNG TÀI (MATCH LOG) ---"])
                    writer.writerow(["Thời gian", "Bên bị tác động", "Hành động / Nội dung"])
                    
                    for log in self.log_history:
                        side = log['color'].upper() if log['color'] != "SYSTEM" else "HỆ THỐNG"
                        writer.writerow([log['time'], side, log['vi']])
                        
                title = "THÀNH CÔNG" if self.current_lang == "VI" else "SUCCESS"
                msg = f"Đã lưu báo cáo trận đấu ra file:\n{file_name}" if self.current_lang == "VI" else f"Match report saved to:\n{file_name}"
                QMessageBox.information(self, title, msg)
            except Exception as e:
                title = "LỖI XUẤT FILE" if self.current_lang == "VI" else "EXPORT ERROR"
                msg = f"Không thể lưu file CSV: {str(e)}" if self.current_lang == "VI" else f"Cannot save CSV file: {str(e)}"
                QMessageBox.critical(self, title, msg)