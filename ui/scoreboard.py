import os
import sys
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QFrame, QSizePolicy, QProgressBar
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QFont, QFontMetrics 
import math




def get_install_dir():
    if getattr(sys, 'frozen', False) or '__compiled__' in globals():
        return os.path.dirname(os.path.abspath(sys.argv[0]))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_path(relative_path):
    """
    Hàm lấy đường dẫn Tối Thượng: Chống lạc đường cho Nuitka Onefile.
    Định vị chính xác thư mục gốc chứa assets dù file code nằm ở đâu.
    """
    if hasattr(sys, '_MEIPASS'):
        # Dành cho PyInstaller (nếu có xài)
        base_path = sys._MEIPASS
    else:
        # Dành cho Nuitka Onefile hoặc Code Python thường
        # Dùng __main__ để luôn trỏ về thư mục gốc chứa file main đang chạy
        import __main__
        base_path = os.path.dirname(os.path.abspath(__main__.__file__))
    
    full_path = os.path.join(base_path, relative_path)
    return full_path if os.path.exists(full_path) else relative_path

class ScoreboardWindow(QWidget):
    def __init__(self, state):
        super().__init__()
        self.state = state
        self.setWindowTitle("AEKA Scoreboard - Audience Display")
        self.resize(1280, 720) 
        self.setStyleSheet("background-color: #0F0F13; color: white; font-family: 'Consolas', monospace;")
        
        self.scale = 1.0 
        self.icon_refs = []
        self.judge_labels = []
        self.last_red_flashes = {1: [], 2: [], 3: []}
        self.last_blue_flashes = {1: [], 2: [], 3: []}
        
        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self._toggle_blink)
        self.blink_count = 0
        self.winner_color = ""

        self._is_scaling = False
        self.current_timer_text = "02:00"
        self.current_timer_color = "#00FFB2"
        self.is_break_time = False

        self.setup_ui()
        self.update_ui()
        self.announcement = BigAnnouncementOverlay(self)

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. HEADER 
        self.top_container = QFrame()
        self.top_container.setStyleSheet("background-color: #0F0F13; border: none; margin: 0; padding: 0;")
        top_layout = QVBoxLayout(self.top_container)
        top_layout.setContentsMargins(20, 10, 20, 10)

        self.lbl_header = QLabel("CHUNG KẾT  |  NAM -58KG")
        self.lbl_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_header.setMinimumSize(1, 1) 
        top_layout.addWidget(self.lbl_header)
        main_layout.addWidget(self.top_container) 

        # 2. KHU VỰC TÊN VÀ CỜ
        self.names_container = QFrame()
        self.names_container.setStyleSheet("border: none; margin: 0; padding: 0;")
        names_layout = QHBoxLayout(self.names_container)
        names_layout.setSpacing(0)
        names_layout.setContentsMargins(0, 0, 0, 0)

        red_name_bg = QFrame()
        red_name_bg.setStyleSheet("background-color: #4A0E0E; border: none; margin: 0; padding: 0;")
        self.red_name_layout = QHBoxLayout(red_name_bg) 
        self.red_name_layout.setContentsMargins(20, 10, 20, 10) 
        
        self.lbl_red_flag = QLabel()
        self.lbl_red_flag.setScaledContents(True)
        self.lbl_red_flag.setMinimumSize(1, 1)
        self.red_name_layout.addWidget(self.lbl_red_flag)
        
        self.lbl_red_name = QLabel("VĐV ĐỎ")
        self.lbl_red_name.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.lbl_red_name.setMinimumSize(1, 1) 
        self.red_name_layout.addWidget(self.lbl_red_name, stretch=1)

        blue_name_bg = QFrame()
        blue_name_bg.setStyleSheet("background-color: #081226; border: none; margin: 0; padding: 0;")
        self.blue_name_layout = QHBoxLayout(blue_name_bg)
        self.blue_name_layout.setContentsMargins(20, 10, 20, 10) 
        
        self.lbl_blue_name = QLabel("VĐV XANH")
        self.lbl_blue_name.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.lbl_blue_name.setMinimumSize(1, 1) 
        self.blue_name_layout.addWidget(self.lbl_blue_name, stretch=1)
        
        self.lbl_blue_flag = QLabel()
        self.lbl_blue_flag.setScaledContents(True) 
        self.lbl_blue_flag.setMinimumSize(1, 1)
        self.blue_name_layout.addWidget(self.lbl_blue_flag)

        names_layout.addWidget(red_name_bg, stretch=1)
        names_layout.addWidget(blue_name_bg, stretch=1)
        main_layout.addWidget(self.names_container) 

        # 🔥🔥🔥 BẮT ĐẦU KHU VỰC THANH MÁU (HP BAR + SIP-CHO BUFF) 🔥🔥🔥
        self.hp_container = QFrame()
        self.hp_container.setStyleSheet("background-color: #0F0F13; border: none; margin: 0; padding: 0;")
        hp_layout = QHBoxLayout(self.hp_container)
        hp_layout.setContentsMargins(20, 0, 20, 10)
        hp_layout.setSpacing(10)

        # --- CỤM BÊN ĐỎ ---
        self.lbl_red_edge_hp = QLabel("150")
        self.lbl_red_edge_hp.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        red_vbox = QVBoxLayout()
        red_vbox.setSpacing(4) # Khoảng cách giữa máu chính và thanh buff

        self.red_hp_bar = QProgressBar()
        self.red_hp_bar.setMaximum(150); self.red_hp_bar.setValue(150)
        self.red_hp_bar.setTextVisible(False)
        self.red_hp_bar.setInvertedAppearance(False) 
        self.red_hp_bar.setStyleSheet("""
            QProgressBar { border: 2px solid #5a5a5a; background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0f0f0f, stop:0.5 #333333, stop:1 #0f0f0f); border-radius: 8px; }
            QProgressBar::chunk { background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #7a0000, stop:0.3 #ff2a2a, stop:0.5 #ff8888, stop:0.7 #ff2a2a, stop:1 #7a0000); border-radius: 5px; margin: 2px; }
        """)

        # THANH BUFF X2 ĐỎ (Hiện khi đối phương bị Sip-cho)
        self.red_buff_bar = QProgressBar()
        self.red_buff_bar.setMaximum(100); self.red_buff_bar.setValue(0)
        self.red_buff_bar.setTextVisible(False)
        self.red_buff_bar.setVisible(False) # Bình thường ẩn đi
        self.red_buff_bar.setInvertedAppearance(False)
        self.red_buff_bar.setStyleSheet("""
            QProgressBar { border: 1px solid #444; background: rgba(0,0,0,50); border-radius: 2px; }
            QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFD700, stop:0.5 #FFFFAA, stop:1 #B8860B); border-radius: 1px; }
        """)
        
        red_vbox.addWidget(self.red_hp_bar)
        red_vbox.addWidget(self.red_buff_bar)

        # --- CỤM BÊN XANH ---
        self.blue_hp_bar = QProgressBar()
        self.blue_hp_bar.setMaximum(150); self.blue_hp_bar.setValue(150)
        self.blue_hp_bar.setTextVisible(False)
        self.blue_hp_bar.setInvertedAppearance(True) 
        self.blue_hp_bar.setStyleSheet("""
            QProgressBar { border: 2px solid #5a5a5a; background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0f0f0f, stop:0.5 #333333, stop:1 #0f0f0f); border-radius: 8px; }
            QProgressBar::chunk { background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #00007a, stop:0.3 #2a2aff, stop:0.5 #8888ff, stop:0.7 #2a2aff, stop:1 #00007a); border-radius: 5px; margin: 2px; }
        """)

        # THANH BUFF X2 XANH
        self.blue_buff_bar = QProgressBar()
        self.blue_buff_bar.setMaximum(100); self.blue_buff_bar.setValue(0)
        self.blue_buff_bar.setTextVisible(False)
        self.blue_buff_bar.setVisible(False)
        self.blue_buff_bar.setInvertedAppearance(True)
        self.blue_buff_bar.setStyleSheet("""
            QProgressBar { border: 1px solid #444; background: rgba(0,0,0,50); border-radius: 2px; }
            QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFD700, stop:0.5 #FFFFAA, stop:1 #B8860B); border-radius: 1px; }
        """)

        blue_vbox = QVBoxLayout()
        blue_vbox.setSpacing(4)
        blue_vbox.addWidget(self.blue_hp_bar)
        blue_vbox.addWidget(self.blue_buff_bar)

        self.lbl_blue_edge_hp = QLabel("150")
        self.lbl_blue_edge_hp.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Xếp hàng vào Layout chính
        hp_layout.addWidget(self.lbl_red_edge_hp, alignment=Qt.AlignmentFlag.AlignVCenter)
        hp_layout.addLayout(red_vbox, stretch=1)
        hp_layout.addSpacing(30)
        hp_layout.addLayout(blue_vbox, stretch=1)
        hp_layout.addWidget(self.lbl_blue_edge_hp, alignment=Qt.AlignmentFlag.AlignVCenter)

        main_layout.addWidget(self.hp_container) 
        # 🔥🔥🔥 KẾT THÚC KHU VỰC THANH MÁU 🔥🔥🔥


        # 3. KHU VỰC BẢNG ĐIỂM + CỘT ĐEN
        self.body_container = QFrame()
        self.body_container.setStyleSheet("background-color: #000000; border: none; margin: 0; padding: 0;")
        body_layout = QHBoxLayout(self.body_container)
        body_layout.setSpacing(0) 
        body_layout.setContentsMargins(0, 0, 0, 0)

        # ------------------- BÊN ĐỎ -------------------
        self.red_score_bg = QFrame()
        self.red_score_bg.setStyleSheet("background-color: #4A0E0E; border: none; margin: 0; padding: 0;")
        self.red_score_layout = QHBoxLayout(self.red_score_bg)

        red_lights_box = QVBoxLayout()
        red_lights_box.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.red_lights = {1: {}, 2: {}, 3: {}}
        for i in [1, 2, 3]:
            block, j_lights, j_lbl = self.create_judge_block(f"J{i}", "red")
            self.judge_labels.append(j_lbl)
            red_lights_box.addLayout(block)
            red_lights_box.addSpacing(20)
            self.red_lights[i] = j_lights
        self.red_score_layout.addLayout(red_lights_box)

        self.red_center_v = QVBoxLayout()
        self.red_center_v.setSpacing(0)
        
        self.red_bright_frame = QFrame()
        self.red_bright_frame.setStyleSheet("background-color: #B31212; border-radius: 0px; border: none;") 
        self.red_bright_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding) 
        self.red_bright_frame.setMinimumSize(1, 1) 
        
        red_bright_layout = QGridLayout(self.red_bright_frame)
        red_bright_layout.setContentsMargins(20, 5, 20, 20)
        
        self.red_rounds = {}
        red_rounds_vbox = QVBoxLayout()
        red_rounds_vbox.setContentsMargins(0, 0, 0, 0)
        red_rounds_vbox.setSpacing(5) # Khoảng cách dọc giữa các hàng R1 R2 R3
        
        for i in [1, 2, 3]:
            row_layout = QHBoxLayout()
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(10) # Khoảng cách ngang siêu đẹp giữa các chữ
            
            r_lbl = QLabel(f"R{i}"); s_lbl = QLabel(""); dot = QLabel(); m_lbl = QLabel("") 
            r_lbl.setMinimumSize(1, 1); m_lbl.setMinimumSize(1, 1)
            
            # 🔥 Tuyệt chiêu khóa cứng độ rộng, căn giữa để số 0 và 12 luôn thẳng hàng
            s_lbl.setFixedWidth(50) 
            s_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            row_layout.addWidget(r_lbl, 0, Qt.AlignmentFlag.AlignVCenter)
            row_layout.addWidget(s_lbl, 0, Qt.AlignmentFlag.AlignVCenter)
            row_layout.addWidget(dot, 0, Qt.AlignmentFlag.AlignVCenter)
            row_layout.addWidget(m_lbl, 0, Qt.AlignmentFlag.AlignVCenter)
            row_layout.addStretch(1) # 🔥 Lò xo khổng lồ đẩy tụi nó dính chặt vào lề TRÁI
            
            red_rounds_vbox.addLayout(row_layout)
            self.red_rounds[i] = {'r': r_lbl, 's': s_lbl, 'd': dot, 'm': m_lbl}

        top_row_red = QHBoxLayout()
        top_row_red.addLayout(red_rounds_vbox)
        top_row_red.addStretch()
        red_bright_layout.addLayout(top_row_red, 0, 0, alignment=Qt.AlignmentFlag.AlignTop)
        
        self.lbl_red_score = QLabel("0")
        self.lbl_red_score.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_red_score.setMinimumSize(1, 1) 
        red_bright_layout.addWidget(self.lbl_red_score, 0, 0, alignment=Qt.AlignmentFlag.AlignCenter)

        # 🔥 VÁ LỖI: Xóa 1 block self.lbl_red_sub để diệt Ghost Widget
        self.lbl_red_sub = QLabel()
        self.lbl_red_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        red_bright_layout.addWidget(self.lbl_red_sub, 0, 0, alignment=Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft)

        # 🔥 ĐÃ THÊM: Icon IVR Camera ở mép dưới bên Đỏ
        self.lbl_red_ivr = QLabel()
        self.lbl_red_ivr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        red_bright_layout.addWidget(self.lbl_red_ivr, 0, 0, alignment=Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)

        self.red_center_v.addWidget(self.red_bright_frame, stretch=1)
        self.red_center_v.addSpacing(20) 
        
        self.red_icons_wrapper = QWidget()
        self.red_icons_layout = QHBoxLayout(self.red_icons_wrapper)
        self.red_icons_layout.setContentsMargins(0, 0, 0, 0)
        self.red_icons_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.create_breakdown_item(self.red_icons_layout, "GJ", "red")      
        self.create_breakdown_item(self.red_icons_layout, "PUNCH", "red")
        self.create_breakdown_item(self.red_icons_layout, "BODY", "red")
        self.create_breakdown_item(self.red_icons_layout, "HEAD", "red")
        self.create_breakdown_item(self.red_icons_layout, "PTK", "red")     
        
        self.red_center_v.addWidget(self.red_icons_wrapper, stretch=0)
        self.red_score_layout.addLayout(self.red_center_v, stretch=1)
        body_layout.addWidget(self.red_score_bg, stretch=4) 

        # ------------------- CỘT ĐEN TRUNG TÂM -------------------
        self.center_col = QFrame()
        self.center_col.setStyleSheet("background-color: transparent; border: none; margin: 0; padding: 0;")
        self.center_vlayout = QVBoxLayout(self.center_col)
        self.center_vlayout.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter)

        self.lbl_match_title = QLabel("TRẬN")
        self.lbl_match_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_match_title.setMinimumSize(1, 1)
        
        self.lbl_match_num = QLabel("1")
        self.lbl_match_num.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_match_num.setMinimumSize(1, 1)
        
        self.lbl_time_title = QLabel("THỜI GIAN")
        self.lbl_time_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_time_title.setMinimumSize(1, 1)
        
        self.lbl_timer = QLabel("02:00")
        self.lbl_timer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_timer.setMinimumSize(1, 1) 
        
        self.lbl_round_title = QLabel("HIỆP")
        self.lbl_round_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_round_title.setMinimumSize(1, 1)
        
        self.lbl_round_num = QLabel("1")
        self.lbl_round_num.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_round_num.setMinimumSize(1, 1)


        self.center_vlayout.addWidget(self.lbl_match_title)
        self.center_vlayout.addWidget(self.lbl_match_num)
        
        self.spacing_1 = QWidget(); self.center_vlayout.addWidget(self.spacing_1)
        self.center_vlayout.addWidget(self.lbl_time_title)
        self.center_vlayout.addWidget(self.lbl_timer)
        self.spacing_2 = QWidget(); self.center_vlayout.addWidget(self.spacing_2)

        self.center_vlayout.addStretch(10) 
        
        self.center_vlayout.addWidget(self.lbl_round_title)
        self.center_vlayout.addWidget(self.lbl_round_num)
        self.center_vlayout.addStretch(4)

        body_layout.addWidget(self.center_col, stretch=2) 

        # ------------------- BÊN XANH -------------------
        self.blue_score_bg = QFrame()
        self.blue_score_bg.setStyleSheet("background-color: #081226; border: none; margin: 0; padding: 0;")
        self.blue_score_layout = QHBoxLayout(self.blue_score_bg)

        self.blue_center_v = QVBoxLayout()
        self.blue_center_v.setSpacing(0)

        self.blue_bright_frame = QFrame()
        self.blue_bright_frame.setStyleSheet("background-color: #0B3E96; border-radius: 0px; border: none;") 
        self.blue_bright_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding) 
        self.blue_bright_frame.setMinimumSize(1, 1) 
        
        blue_bright_layout = QGridLayout(self.blue_bright_frame)
        blue_bright_layout.setContentsMargins(20, 5, 20, 20)
        
        self.blue_rounds = {}
        blue_rounds_vbox = QVBoxLayout()
        blue_rounds_vbox.setContentsMargins(0, 0, 0, 0)
        blue_rounds_vbox.setSpacing(5) 
        
        for i in [1, 2, 3]:
            row_layout = QHBoxLayout()
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(10) 
            
            r_lbl = QLabel(f"R{i}"); s_lbl = QLabel(""); dot = QLabel(); m_lbl = QLabel("") 
            r_lbl.setMinimumSize(1, 1); m_lbl.setMinimumSize(1, 1)
            
            # 🔥 Khóa cứng độ rộng giống y xì bên Đỏ
            s_lbl.setFixedWidth(50) 
            s_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            row_layout.addStretch(1) # 🔥 Lò xo khổng lồ chặn ở đầu, đẩy tụi nó dính chặt vào lề PHẢI
            row_layout.addWidget(m_lbl, 0, Qt.AlignmentFlag.AlignVCenter)
            row_layout.addWidget(dot, 0, Qt.AlignmentFlag.AlignVCenter)
            row_layout.addWidget(s_lbl, 0, Qt.AlignmentFlag.AlignVCenter)
            row_layout.addWidget(r_lbl, 0, Qt.AlignmentFlag.AlignVCenter)
            
            blue_rounds_vbox.addLayout(row_layout)
            self.blue_rounds[i] = {'r': r_lbl, 's': s_lbl, 'd': dot, 'm': m_lbl}

        top_row_blue = QHBoxLayout()
        top_row_blue.addStretch()
        top_row_blue.addLayout(blue_rounds_vbox)
        blue_bright_layout.addLayout(top_row_blue, 0, 0, alignment=Qt.AlignmentFlag.AlignTop)
        
        self.lbl_blue_score = QLabel("0")
        self.lbl_blue_score.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_blue_score.setMinimumSize(1, 1) 
        blue_bright_layout.addWidget(self.lbl_blue_score, 0, 0, alignment=Qt.AlignmentFlag.AlignCenter)

        self.lbl_blue_sub = QLabel()
        self.lbl_blue_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        blue_bright_layout.addWidget(self.lbl_blue_sub, 0, 0, alignment=Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)

        # 🔥 ĐÃ THÊM: Icon IVR Camera ở mép dưới bên Xanh
        self.lbl_blue_ivr = QLabel()
        self.lbl_blue_ivr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        blue_bright_layout.addWidget(self.lbl_blue_ivr, 0, 0, alignment=Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)

        self.blue_center_v.addWidget(self.blue_bright_frame, stretch=1)
        self.blue_center_v.addSpacing(20)
        
        self.blue_icons_wrapper = QWidget()
        self.blue_icons_layout = QHBoxLayout(self.blue_icons_wrapper)
        self.blue_icons_layout.setContentsMargins(0, 0, 0, 0)
        self.blue_icons_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.create_breakdown_item(self.blue_icons_layout, "PTK", "blue")    
        self.create_breakdown_item(self.blue_icons_layout, "HEAD", "blue")
        self.create_breakdown_item(self.blue_icons_layout, "BODY", "blue")
        self.create_breakdown_item(self.blue_icons_layout, "PUNCH", "blue")
        self.create_breakdown_item(self.blue_icons_layout, "GJ", "blue")     
        
        self.blue_center_v.addWidget(self.blue_icons_wrapper, stretch=0)
        self.blue_score_layout.addLayout(self.blue_center_v, stretch=1)

        blue_lights_box = QVBoxLayout()
        blue_lights_box.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.blue_lights = {1: {}, 2: {}, 3: {}}
        for i in [1, 2, 3]:
            block, j_lights, j_lbl = self.create_judge_block(f"J{i}", "blue")
            self.judge_labels.append(j_lbl)
            blue_lights_box.addLayout(block)
            blue_lights_box.addSpacing(20)
            self.blue_lights[i] = j_lights
        self.blue_score_layout.addLayout(blue_lights_box)

        body_layout.addWidget(self.blue_score_bg, stretch=4) 
        main_layout.addWidget(self.body_container, stretch=1) 

        self._apply_dynamic_scaling()

    def update_language(self, lang):
        self.current_lang = lang
        is_vi = (lang == "VI")
        
        self.lbl_match_title.setText("TRẬN" if is_vi else "MATCH")
        self.lbl_round_title.setText("HIỆP" if is_vi else "ROUND")
        
        self.update_ui()
        self._refresh_timer_ui()

    def play_winner_animation(self, color):
        self.winner_color = color
        self.blink_count = 0
        self.blink_timer.start(250) 

    def _toggle_blink(self):
        self.blink_count += 1
        is_gold = (self.blink_count % 2 != 0) 
        self.red_bright_frame.setStyleSheet("background-color: #B31212; border-radius: 0px; border: none;")
        self.blue_bright_frame.setStyleSheet("background-color: #0B3E96; border-radius: 0px; border: none;")

        if is_gold:
            if self.winner_color == "red": self.red_bright_frame.setStyleSheet("background-color: #FFD700; border-radius: 0px; border: none;")
            elif self.winner_color == "blue": self.blue_bright_frame.setStyleSheet("background-color: #FFD700; border-radius: 0px; border: none;")

        if self.blink_count >= 10: 
            self.blink_timer.stop()
            if self.winner_color == "red": self.red_bright_frame.setStyleSheet("background-color: #FFD700; border-radius: 0px; border: none;")
            elif self.winner_color == "blue": self.blue_bright_frame.setStyleSheet("background-color: #FFD700; border-radius: 0px; border: none;")

    def clear_winner_animation(self):
        self.blink_timer.stop()
        self.red_bright_frame.setStyleSheet("background-color: #B31212; border-radius: 0px; border: none;")
        self.blue_bright_frame.setStyleSheet("background-color: #0B3E96; border-radius: 0px; border: none;")

        if hasattr(self, 'announcement'):
            self.announcement.hide()

    def _get_fitted_css(self, text, max_base_px, color, max_width, extra=""):
        max_px = int(max_base_px * self.scale)
        if max_px < 15: max_px = 15
        if max_width < 50: max_width = 50

        font = QFont("Consolas")
        font.setBold(True)
        current_px = max_px

        font.setPixelSize(current_px)
        fm = QFontMetrics(font)

        while fm.horizontalAdvance(text) > max_width and current_px > 12:
            current_px -= 2 
            font.setPixelSize(current_px)
            fm = QFontMetrics(font)

        return f"font-size: {current_px}px; color: {color}; background: transparent; border: none; {extra}"

    def set_timer_text(self, text, color, is_break=False):
        self.current_timer_text = text
        self.current_timer_color = color
        self.is_break_time = is_break
        self._refresh_timer_ui()

    def _refresh_timer_ui(self):
        is_vi = getattr(self, 'current_lang', 'VI') == "VI"
        if self.is_break_time:
            self.lbl_time_title.setText("NGHỈ\nGIỮA HIỆP" if is_vi else "BREAK\nTIME")
            self.lbl_time_title.setStyleSheet(f"font-size: {max(10, int(22 * self.scale))}px; color: #FFD700; font-weight: bold; background: transparent; border: none; text-align: center;")
        else:
            self.lbl_time_title.setText("THỜI GIAN" if is_vi else "TIME")
            self.lbl_time_title.setStyleSheet(f"font-size: {max(10, int(22 * self.scale))}px; color: #888; font-weight: bold; background: transparent; border: none;")
            
        allowed_width = (self.width() * 0.2) - (20 * self.scale) 
        css = self._get_fitted_css(
            self.current_timer_text, 85, self.current_timer_color, allowed_width, "font-family: 'Consolas';"
        )
        self.lbl_timer.setText(self.current_timer_text)
        self.lbl_timer.setStyleSheet(css)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self._is_scaling:
            self._is_scaling = True
            self._apply_dynamic_scaling()
            self._is_scaling = False
        if hasattr(self, 'announcement'):
            self.announcement.update_scaling(self.scale)

    def _apply_dynamic_scaling(self):
        w = self.width(); h = self.height()
        if w == 0 or h == 0: return 

        s = min(w / 1280.0, h / 720.0) 
        if s < 0.1: s = 0.1
        self.scale = s

        self.top_container.setFixedHeight(int(50 * s))
        self.names_container.setFixedHeight(int(100 * s))
        
        # Mở rộng chiều cao của cả khu vực thanh máu cho thoải mái
        self.hp_container.setFixedHeight(int(60 * s))
        self.blue_hp_bar.setMinimumHeight(int(35 * s))
        self.red_hp_bar.setMinimumHeight(int(35 * s))

        # TĂNG KÍCH THƯỚC CHỮ VÀ KHUNG CHỨA CHO 2 SỐ Ở MÉP
        if hasattr(self, 'lbl_red_edge_hp'):
            self.lbl_red_edge_hp.setFixedWidth(int(100 * s)) # Nới rộng lồng chứa số
            self.lbl_blue_edge_hp.setFixedWidth(int(100 * s))
            
            # Tăng font size từ 24 lên thẳng 45 cho nó chà bá lửa
            edge_style = f"font-size: {max(24, int(45 * s))}px; font-weight: bold; font-family: 'Arial Black'; background: transparent; border: none;"
            self.lbl_red_edge_hp.setStyleSheet(edge_style + " color: #ff9999;")
            self.lbl_blue_edge_hp.setStyleSheet(edge_style + " color: #99bbff;")

        self.red_name_layout.setSpacing(int(20 * s))
        self.blue_name_layout.setSpacing(int(20 * s))

        self.lbl_red_flag.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.lbl_blue_flag.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self.red_score_layout.setContentsMargins(int(35 * s), 0, 0, int(20 * s))
        self.blue_score_layout.setContentsMargins(0, 0, int(35 * s), int(20 * s))
        
        self.spacing_1.setFixedHeight(int(20 * s))
        self.spacing_2.setFixedHeight(int(30 * s))
        self.center_vlayout.setContentsMargins(int(10 * s), int(20 * s), int(10 * s), int(20 * s))

        def style(base_px, color, extra=""):
            return f"font-size: {max(10, int(base_px * s))}px; color: {color}; background: transparent; border: none; {extra}"

        self.lbl_header.setStyleSheet(style(26, "#E0E0E0", "font-weight: bold; letter-spacing: 2px;"))
        is_hp = getattr(self.state, 'match_format', 'BO3') == "TEAM_HP"
        score_px = 140 if is_hp else 300
        safe_score_width = (w / 2.0) - (100 * s) # Ước lượng độ rộng an toàn dựa trên scale
        
        self.lbl_red_score.setStyleSheet(self._get_fitted_css(self.lbl_red_score.text(), score_px, "white", safe_score_width, "font-weight: bold;"))
        self.lbl_blue_score.setStyleSheet(self._get_fitted_css(self.lbl_blue_score.text(), score_px, "white", safe_score_width, "font-weight: bold;"))

        self.lbl_match_title.setStyleSheet(style(22, "#888", "font-weight: bold;"))
        self.lbl_match_num.setStyleSheet(style(50, "white", "font-weight: bold;"))
        self.lbl_round_title.setStyleSheet(style(22, "#888", "font-weight: bold;"))
        self.lbl_round_num.setStyleSheet(style(50, "white", "font-weight: bold;"))

        for lbl in self.judge_labels: lbl.setStyleSheet(style(22, "#999", "font-weight: bold;"))

        self.red_icons_layout.setSpacing(int(15 * s)) 
        self.blue_icons_layout.setSpacing(int(15 * s))
        
        icon_area_h = int(100 * s)
        self.red_icons_wrapper.setFixedHeight(icon_area_h)
        self.blue_icons_wrapper.setFixedHeight(icon_area_h)
        
        for lbl_icon, lbl_score, path in self.icon_refs:
            lbl_score.setStyleSheet(style(35, "white", "font-weight: bold;")) 
            lbl_score.setFixedHeight(int(40 * s)) 
            
            lbl_icon.setStyleSheet("background: transparent; border: none;")
            
            if path == "PTK":
                lbl_icon.setFixedSize(int(85 * s), int(50 * s)) 
                lbl_icon.setText(f"<div align='center'>"
                                 f"<span style='font-size: {int(15 * s)}px; color: #FFD700; font-weight: bold;'>POINTS</span><br>"
                                 f"<span style='font-size: {int(9 * s)}px; color: #FFFFAA; font-weight: bold;'>TURNING-KICK</span>"
                                 f"</div>")
            elif path == "GJ":
                lbl_icon.setFixedSize(int(85 * s), int(50 * s)) 
                lbl_icon.setText(f"<div align='center'>"
                                 f"<span style='font-size: {int(15 * s)}px; color: #FFD700; font-weight: bold;'>GAM-JEOM</span><br>"
                                 f"</div>")
            else:
                lbl_icon.setFixedSize(int(60 * s), int(50 * s)) 
                if os.path.exists(path):
                    pixmap = QPixmap(path).scaled(int(50 * s), int(45 * s), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation) 
                    lbl_icon.setPixmap(pixmap)

        r_font = style(22, "#FFAAAA", "font-weight: bold; padding: 0px; margin: 0px;")
        b_font = style(22, "#AAAAFF", "font-weight: bold; padding: 0px; margin: 0px;")
        s_font = style(26, "white", "font-weight: bold; padding: 0px; margin: 0px;")
        m_red_font = style(20, "#FFD700", "font-weight: bold;") 
        m_blue_font = style(20, "#FFD700", "font-weight: bold;")
        dot_s = int(18 * s)
        row_h = int(24 * s)

        for i in [1, 2, 3]:
            self.red_rounds[i]['r'].setStyleSheet(r_font); self.red_rounds[i]['r'].setFixedHeight(row_h)
            self.red_rounds[i]['s'].setStyleSheet(s_font); self.red_rounds[i]['s'].setFixedSize(int(45 * s), row_h)
            self.red_rounds[i]['d'].setFixedSize(dot_s, dot_s)
            self.red_rounds[i]['m'].setStyleSheet(m_red_font); self.red_rounds[i]['m'].setFixedHeight(row_h)
            
            self.blue_rounds[i]['r'].setStyleSheet(b_font); self.blue_rounds[i]['r'].setFixedHeight(row_h)
            self.blue_rounds[i]['s'].setStyleSheet(s_font); self.blue_rounds[i]['s'].setFixedSize(int(45 * s), row_h)
            self.blue_rounds[i]['d'].setFixedSize(dot_s, dot_s)
            self.blue_rounds[i]['m'].setStyleSheet(m_blue_font); self.blue_rounds[i]['m'].setFixedHeight(row_h)

        ls = int(30 * s) 
        for j in [1, 2, 3]:
            for pts in [1, 2, 3]:
                self.red_lights[j][pts].setFixedSize(ls, ls); self.blue_lights[j][pts].setFixedSize(ls, ls)

        # Căn size cho Icon IVR Camera (40x40 pixel trên Tivi to)
        ivr_s = int(90 * s)
        self.lbl_red_ivr.setFixedSize(ivr_s, ivr_s)
        self.lbl_blue_ivr.setFixedSize(ivr_s, ivr_s)

        self._apply_ivr_icon(self.lbl_red_ivr, getattr(self.state.red, 'ivr_quota', True))
        self._apply_ivr_icon(self.lbl_blue_ivr, getattr(self.state.blue, 'ivr_quota', True))

        self._update_flags()
        self._update_names_css_only()
        self._refresh_timer_ui()
        self.update_lights(self.last_red_flashes, self.last_blue_flashes)

    def _update_names_css_only(self):
        safe_width = (self.width() / 2.0) - (160 * self.scale)
        self.lbl_red_name.setStyleSheet(self._get_fitted_css(self.state.red.name, 65, "white", safe_width, "font-weight: bold; padding-bottom: 5px;"))
        self.lbl_blue_name.setStyleSheet(self._get_fitted_css(self.state.blue.name, 65, "white", safe_width, "font-weight: bold; padding-bottom: 5px;"))

    def _update_flags(self):
        red_flag_name = getattr(self.state.red, 'flag', 'vietnam')
        blue_flag_name = getattr(self.state.blue, 'flag', 'vietnam')
        red_path = get_path(f"assets/img/{red_flag_name}.png")
        blue_path = get_path(f"assets/img/{blue_flag_name}.png")
        
        flag_w = int(100 * self.scale); flag_h = int(65 * self.scale)

        self.lbl_red_flag.setFixedSize(flag_w, flag_h)
        if os.path.exists(red_path):
            self.lbl_red_flag.clear()
            self.lbl_red_flag.setStyleSheet("border: 2px solid rgba(255,255,255,0.2); border-radius: 4px; background: transparent;")
            self.lbl_red_flag.setPixmap(QPixmap(red_path).scaled(flag_w, flag_h, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            self.lbl_red_flag.clear()
            self.lbl_red_flag.setStyleSheet(f"background: rgba(255,255,255,0.1); border: 2px dashed #FF6666; border-radius: 4px; font-size: {max(12, int(18 * self.scale))}px; color: white; font-weight: bold;")
            self.lbl_red_flag.setText(f"[{red_flag_name.upper()}]") 
            self.lbl_red_flag.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_blue_flag.setFixedSize(flag_w, flag_h)
        if os.path.exists(blue_path):
            self.lbl_blue_flag.clear()
            self.lbl_blue_flag.setStyleSheet("border: 2px solid rgba(255,255,255,0.2); border-radius: 4px; background: transparent;")
            self.lbl_blue_flag.setPixmap(QPixmap(blue_path).scaled(flag_w, flag_h, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            self.lbl_blue_flag.clear()
            self.lbl_blue_flag.setStyleSheet(f"background: rgba(255,255,255,0.1); border: 2px dashed #6699FF; border-radius: 4px; font-size: {max(12, int(18 * self.scale))}px; color: white; font-weight: bold;")
            self.lbl_blue_flag.setText(f"[{blue_flag_name.upper()}]")
            self.lbl_blue_flag.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def create_judge_block(self, judge_name, side):
        block_layout = QHBoxLayout()
        block_layout.setContentsMargins(0, 0, 0, 0); block_layout.setSpacing(int(5 * self.scale))
        lbl_judge = QLabel(judge_name); lbl_judge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_judge.setMinimumSize(1,1)
        lights_vbox = QVBoxLayout(); lights_vbox.setSpacing(4)
        
        judge_lights = {}
        for pts in [1, 2, 3]:
            light = QLabel(str(pts)); light.setAlignment(Qt.AlignmentFlag.AlignCenter); lights_vbox.addWidget(light)
            judge_lights[pts] = light

        if side == "red": block_layout.addWidget(lbl_judge); block_layout.addLayout(lights_vbox)
        else: block_layout.addLayout(lights_vbox); block_layout.addWidget(lbl_judge)
        return block_layout, judge_lights, lbl_judge

    def create_breakdown_item(self, parent_layout, label_text, side):
        item_layout = QVBoxLayout()
        item_layout.setAlignment(Qt.AlignmentFlag.AlignCenter); item_layout.setSpacing(0) 
        
        lbl_icon = QLabel(); lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter); lbl_icon.setScaledContents(False) 
        lbl_icon.setMinimumSize(1,1)
        
        if label_text == "PTK": icon_file = "PTK"
        elif label_text == "GJ": icon_file = "GJ"
        else:
            suffix = "D" if side == "red" else "X"
            if label_text == "HEAD": file_name = f"head{suffix}.png"
            elif label_text == "BODY": file_name = f"body{suffix}.png"
            else: file_name = "punch.png" 
            icon_file = get_path(f"assets/icons/{file_name}")
            
        lbl_score = QLabel("0"); lbl_score.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        lbl_score.setMinimumSize(1,1)
        self.icon_refs.append((lbl_icon, lbl_score, icon_file))
        item_layout.addWidget(lbl_icon)
        item_layout.addWidget(lbl_score)
        
        if side == "red": setattr(self, f"lbl_red_pts_{label_text.lower()}", lbl_score)
        else: setattr(self, f"lbl_blue_pts_{label_text.lower()}", lbl_score)
        parent_layout.addLayout(item_layout)

    def _apply_ivr_icon(self, lbl, has_quota):
        ivr_s = int(90 * self.scale)
        file_name = "camera.png" if has_quota else "nocamera.png"
        path = get_path(f"assets/icons/{file_name}")
        
        if os.path.exists(path):
            lbl.clear()
            pixmap = QPixmap(path).scaled(ivr_s, ivr_s, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            lbl.setPixmap(pixmap)
            lbl.setStyleSheet("background: transparent; border: none;")
        else:
            # Dùng Emoji thay thế nếu quên tải icon
            lbl.setText("🎥" if has_quota else "❌")
            lbl.setStyleSheet(f"font-size: {max(15, int(90 * self.scale))}px; background: transparent; border: none;")

    def update_ui(self):
        cat = getattr(self.state, 'match_category', 'VÒNG LOẠI').upper()
        is_vi = getattr(self, 'current_lang', 'VI') == "VI"
        cat_map = {"VÒNG LOẠI": "PRELIMINARY", "TỨ KẾT": "QUARTER-FINAL", "BÁN KẾT": "SEMI-FINAL", "CHUNG KẾT": "FINAL"}
        cat_str = cat if is_vi else cat_map.get(cat, cat)
        
        gender_str = getattr(self.state, 'gender', 'NAM')
        if not is_vi:
            if gender_str == "NAM": gender_str = "MALE"
            elif gender_str == "NỮ": gender_str = "FEMALE"

        self.lbl_header.setText(f"{cat_str}  |  {gender_str} {self.state.weight_class}")
        self.lbl_match_num.setText(str(self.state.match_number))
        self.lbl_round_num.setText(str(self.state.current_round))
        
        self.lbl_red_name.setText(self.state.red.name)
        self.lbl_blue_name.setText(self.state.blue.name)

        # CẬP NHẬT CHỈ SỐ PHỤ (ĐẾM SỐ LẦN, CHỈ PTK LÀ NHÂN HỆ SỐ)
        is_hp_mode = getattr(self.state, 'match_format', 'BO3') == "TEAM_HP"
        m = 5 if is_hp_mode else 1 

        self.lbl_red_pts_gj.setText(str(self.state.red.gamjeom))
        self.lbl_blue_pts_gj.setText(str(self.state.blue.gamjeom))
        
        self.lbl_red_pts_punch.setText(str(self.state.red.pts_punch))
        self.lbl_red_pts_body.setText(str(self.state.red.pts_body))
        self.lbl_red_pts_head.setText(str(self.state.red.pts_head))
        self.lbl_red_pts_ptk.setText(str(self.state.red.pts_turn * m))

        self.lbl_blue_pts_punch.setText(str(self.state.blue.pts_punch))
        self.lbl_blue_pts_body.setText(str(self.state.blue.pts_body))
        self.lbl_blue_pts_head.setText(str(self.state.blue.pts_head))
        self.lbl_blue_pts_ptk.setText(str(self.state.blue.pts_turn * m))
        
        self._apply_ivr_icon(self.lbl_red_ivr, getattr(self.state.red, 'ivr_quota', True))
        self._apply_ivr_icon(self.lbl_blue_ivr, getattr(self.state.blue, 'ivr_quota', True))

        # 🔥 CẬP NHẬT THANH BUFF X2 (SIP-CHO)
        r_timer = getattr(self.state, 'red_x2_timer', 0)
        if r_timer > 0:
            self.red_buff_bar.setVisible(True)
            self.red_buff_bar.setValue(int(r_timer * 10)) # 10s = 100% thanh
        else:
            self.red_buff_bar.setVisible(False)

        b_timer = getattr(self.state, 'blue_x2_timer', 0)
        if b_timer > 0:
            self.blue_buff_bar.setVisible(True)
            self.blue_buff_bar.setValue(int(b_timer * 10))
        else:
            self.blue_buff_bar.setVisible(False)

        # =========================================================
        # 🔥 KIỂM TRA CHẾ ĐỘ ĐỂ BẬT/TẮT THANH MÁU VÀ CẬP NHẬT ĐIỂM
        # =========================================================
        if is_hp_mode:
            # CHẶN TỨ PHÍA: Không âm và không vượt 150
            self.state.red.score = max(0, min(150, self.state.red.score))
            self.state.blue.score = max(0, min(150, self.state.blue.score))

            self.hp_container.setVisible(True)
            self.blue_hp_bar.setValue(self.state.blue.score)
            self.red_hp_bar.setValue(self.state.red.score)
            
            # ĐỒNG BỘ 2 SỐ NHỎ Ở MÉP VỚI MÁU HIỆN TẠI
            self.lbl_red_edge_hp.setText(str(self.state.red.score))
            self.lbl_blue_edge_hp.setText(str(self.state.blue.score))

            # SỐ TO ĐÙNG Ở GIỮA MÀN HÌNH
            self.lbl_red_score.setText(str(self.state.red.score))
            self.lbl_blue_score.setText(str(self.state.blue.score))
            score_px = 140 
        else:
            # Chế độ đấu BO3 bình thường (Chặn không cho điểm lùi xuống số âm)
            self.state.red.score = max(0, self.state.red.score)
            self.state.blue.score = max(0, self.state.blue.score)
            
            self.hp_container.setVisible(False)
            self.lbl_red_score.setText(str(self.state.red.score))
            self.lbl_blue_score.setText(str(self.state.blue.score))
            score_px = 300 
            
        # Tính toán chiều rộng tối đa an toàn của khung điểm (Trừ đi 40px margin)
        safe_score_width = self.red_bright_frame.width() - 40
        if safe_score_width < 100: safe_score_width = 300 # Fallback an toàn lúc màn hình chưa load xong

        # Sử dụng hàm _get_fitted_css có sẵn để tự co font nếu số điểm lên 1xx
        red_score_css = self._get_fitted_css(str(self.state.red.score), score_px, "white", safe_score_width, "font-weight: bold;")
        blue_score_css = self._get_fitted_css(str(self.state.blue.score), score_px, "white", safe_score_width, "font-weight: bold;")

        self.lbl_red_score.setStyleSheet(red_score_css)
        self.lbl_blue_score.setStyleSheet(blue_score_css)

        results = getattr(self.state, 'round_results', {1: None, 2: None, 3: None})
        rad = int(11 * self.scale)
        b_px = int(3 * self.scale)
        
        for i in [1, 2, 3]:
            res = results.get(i)
            if res:
                self.red_rounds[i]['s'].setText(str(res['red_score']))
                if res['winner'] == "RED": 
                    self.red_rounds[i]['d'].setStyleSheet(f"background-color: #FFD700; border: {b_px}px solid #FFFFAA; border-radius: {rad}px;")
                    self.red_rounds[i]['m'].setText(f"- {res['method']}") 
                else: 
                    self.red_rounds[i]['d'].setStyleSheet(f"background-color: transparent; border: none; border-radius: {rad}px;")
                    self.red_rounds[i]['m'].setText("")
            else:
                self.red_rounds[i]['s'].setText(""); self.red_rounds[i]['m'].setText("")
                self.red_rounds[i]['d'].setStyleSheet(f"background-color: transparent; border: none; border-radius: {rad}px;")
            
            if res:
                self.blue_rounds[i]['s'].setText(str(res['blue_score']))
                if res['winner'] == "BLUE": 
                    self.blue_rounds[i]['d'].setStyleSheet(f"background-color: #FFD700; border: {b_px}px solid #FFFFAA; border-radius: {rad}px;")
                    self.blue_rounds[i]['m'].setText(f"{res['method']} -") 
                else: 
                    self.blue_rounds[i]['d'].setStyleSheet(f"background-color: transparent; border: none; border-radius: {rad}px;")
                    self.blue_rounds[i]['m'].setText("")
            else:
                self.blue_rounds[i]['s'].setText(""); self.blue_rounds[i]['m'].setText("")
                self.blue_rounds[i]['d'].setStyleSheet(f"background-color: transparent; border: none; border-radius: {rad}px;")
                
        self._update_names_css_only()

        # 🔥 HIỂN THỊ ĐẾM NGƯỢC ĐỔI NGƯỜI (BẢN CHUẨN CUỐI CÙNG - KHÔNG LỆCH, KHÔNG TRÀN, CĂN GIỮA BẰNG LỆNH CỦA QT)
        if getattr(self.state, 'match_format', 'BO3') in ["TEAM_HP", "TEAM_BO3"]:
            # 1. Bóp chiều rộng lại để không đè lên cái Camera (IVR)
            w = int(75 * self.scale)
            h = int(55 * self.scale)
            font_size = int(35 * self.scale)
            
            # 2. Ép cứng kích thước vật lý
            self.lbl_red_sub.setFixedSize(w, h)
            self.lbl_blue_sub.setFixedSize(w, h)
            
            # 3. Fix lỗi CSS: Gỡ bỏ qproperty-alignment và dùng thẳng lệnh Native của Qt
            css_wait = f"font-size: {font_size}px; color: #FFD700; font-weight: bold; background: rgba(0,0,0,150); border-radius: 8px;"
            css_ready = f"font-size: {font_size}px; color: #00FFB2; font-weight: bold; background: rgba(0,0,0,150); border-radius: 8px;"

            # XỬ LÝ BÊN ĐỎ
            r_sub = getattr(self.state, 'red_sub_timer', 0)
            if r_sub > 0:
                self.lbl_red_sub.setText(f"{math.ceil(r_sub)}s")
                self.lbl_red_sub.setStyleSheet(css_wait)
            else:
                self.lbl_red_sub.setText("SS")
                self.lbl_red_sub.setStyleSheet(css_ready)
            self.lbl_red_sub.setAlignment(Qt.AlignmentFlag.AlignCenter) # Ép cứng lề giữa bằng Qt

            # XỬ LÝ BÊN XANH
            b_sub = getattr(self.state, 'blue_sub_timer', 0)
            if b_sub > 0:
                self.lbl_blue_sub.setText(f"{math.ceil(b_sub)}s")
                self.lbl_blue_sub.setStyleSheet(css_wait)
            else:
                self.lbl_blue_sub.setText("SS")
                self.lbl_blue_sub.setStyleSheet(css_ready)
            self.lbl_blue_sub.setAlignment(Qt.AlignmentFlag.AlignCenter) # Ép cứng lề giữa bằng Qt
        else:
            # Ẩn đi khi không phải chế độ đồng đội
            self.lbl_red_sub.setText("")
            self.lbl_blue_sub.setText("")
            self.lbl_red_sub.setStyleSheet("background: transparent;")
            self.lbl_blue_sub.setStyleSheet("background: transparent;")
            self.lbl_red_sub.setFixedSize(0, 0)
            self.lbl_blue_sub.setFixedSize(0, 0)
            

    

    def update_lights(self, red_flashes: dict, blue_flashes: dict):
        self.last_red_flashes = red_flashes; self.last_blue_flashes = blue_flashes
        
        ls = int(30 * self.scale)
        rad = ls // 2 
        
        font_px = int(14 * self.scale)
        b_w = max(1, int(2 * self.scale))
        for j in [1, 2, 3]:
            r_val = red_flashes.get(j, False); r_active = []
            if isinstance(r_val, bool) and r_val: r_active = [1, 2, 3] 
            elif isinstance(r_val, int) and not isinstance(r_val, bool) and r_val > 0: r_active = [r_val]
            elif isinstance(r_val, list): r_active = r_val
            for pts in [1, 2, 3]:
                if pts in r_active: self.red_lights[j][pts].setStyleSheet(f"background-color: #00FF55; color: black; border-radius: {rad}px; border: {b_w}px solid #FFFFFF; font-weight: bold; font-size: {font_px}px;")
                else: self.red_lights[j][pts].setStyleSheet(f"background-color: #1A1A1A; color: #666; border-radius: {rad}px; border: {b_w}px solid #333; font-weight: bold; font-size: {font_px}px;")

            b_val = blue_flashes.get(j, False); b_active = []
            if isinstance(b_val, bool) and b_val: b_active = [1, 2, 3] 
            elif isinstance(b_val, int) and not isinstance(b_val, bool) and b_val > 0: b_active = [b_val]
            elif isinstance(b_val, list): b_active = b_val
            for pts in [1, 2, 3]:
                if pts in b_active: self.blue_lights[j][pts].setStyleSheet(f"background-color: #00FF55; color: black; border-radius: {rad}px; border: {b_w}px solid #FFFFFF; font-weight: bold; font-size: {font_px}px;")
                else: self.blue_lights[j][pts].setStyleSheet(f"background-color: #1A1A1A; color: #666; border-radius: {rad}px; border: {b_w}px solid #333; font-weight: bold; font-size: {font_px}px;")

class BigAnnouncementOverlay(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.hide()
        # Nền tối mờ để làm nổi bật thông báo
        self.setStyleSheet("background-color: rgba(0, 0, 0, 135); border: none;")
        self.layout = QVBoxLayout(self)
        
        self.lbl_main = QLabel("")
        self.lbl_main.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_sub = QLabel("")
        self.lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.layout.addStretch()
        self.layout.addWidget(self.lbl_main)
        self.layout.addWidget(self.lbl_sub)
        self.layout.addStretch()
        
        # Định nghĩa size gốc (Base size) - sẽ nhân với self.scale
        self.base_main_px = 150
        self.base_sub_px = 65
        self.current_color = "WHITE"

    def update_scaling(self, scale):
        """Cập nhật kích thước và font chữ dựa trên tỷ lệ hiện tại của cửa sổ"""
        if self.parent():
            self.setGeometry(0, 0, self.parent().width(), self.parent().height())
        
        main_size = int(self.base_main_px * scale)
        sub_size = int(self.base_sub_px * scale)
        
        color_hex = "#FF3B3B" if self.current_color == "RED" else "#3B82F6"
        self.lbl_main.setStyleSheet(f"color: {color_hex}; font-weight: bold; font-size: {main_size}px;")
        self.lbl_sub.setStyleSheet(f"color: #FFD700; font-weight: bold; font-size: {sub_size}px;")

    def show_announcement(self, color, main_text, sub_text, scale):
        self.current_color = color.upper()
        self.lbl_main.setText(main_text)
        self.lbl_sub.setText(sub_text)
        self.update_scaling(scale) 
        self.show()
        self.raise_()