import os
import sys
import subprocess
import urllib.request
import json
import time
import platform
import psutil

# Xử lý nhập winreg an toàn để không chết trên Mac
try:
    import winreg
except ImportError:
    winreg = None

from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QFrame, QProgressBar, QPushButton, QTextEdit, 
                             QGraphicsDropShadowEffect, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QIcon

# ==========================================
# THÔNG TIN ĐƯỜNG DẪN CẤU HÌNH & FIREBASE
# ==========================================

if getattr(sys, 'frozen', False) or '__compiled__' in globals():
    CURRENT_EXE = os.path.abspath(sys.argv[0])
    BASE_DIR = os.path.dirname(CURRENT_EXE)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MAIN_APP_EXE = os.path.join(BASE_DIR, "main.exe" if platform.system() == "Windows" else "main")
VERSION_FILE = os.path.join(BASE_DIR, "version.txt")

def get_local_version():
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, "r") as f:
            return f.read().strip()
    return "1.0.0"

def get_firebase_config_url(local_version):
    """Hàm tự động đổi link Firebase dựa vào Hệ điều hành và Phiên bản (Khách/Admin)"""
    is_mac = platform.system() == "Darwin"
    is_admin = local_version.startswith("9.") # Nhận diện Admin
    
    if is_admin:
        node = "app_config_admin_mac" if is_mac else "app_config_admin"
    else:
        node = "app_config_mac" if is_mac else "app_config"
        
    return f"https://aeka-key-active-default-rtdb.firebaseio.com/{node}.json"

# ==========================================
# CÁC LUỒNG XỬ LÝ NGẦM (CHỐNG ĐƠ GIAO DIỆN)
# ==========================================
class DiagnosticWorker(QThread):
    log_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str, str, str)
    done_signal = pyqtSignal(bool)

    def run(self):
        try:
            all_clear = True
            local_ver = get_local_version()
            self.log_signal.emit(f"[SYS] Phiên bản hiện tại: v{local_ver}")
            time.sleep(1)

            # 1. KIỂM TRA BẢN CẬP NHẬT TỪ FIREBASE (AUTO-UPDATE)
            self.log_signal.emit("[SYS] Đang kiểm tra bản cập nhật...")
            self.status_signal.emit("update", "Đang kiểm tra...", "#FFB200")
            
            try:
                firebase_url = get_firebase_config_url(local_ver)
                self.log_signal.emit(f"[SYS] Đang Check nhánh: {firebase_url.split('/')[-1].replace('.json', '')}")
                
                res = urllib.request.urlopen(firebase_url, timeout=5)
                data = res.read().decode()
                
                if data == "null":
                    raise ValueError("Node Firebase này chưa được tạo!")
                    
                config = json.loads(data)
                latest_ver = config.get("latest_version", "1.0.0")
                dl_url = config.get("download_url", "")
                
                if latest_ver > local_ver and dl_url:
                    self.log_signal.emit(f"[UPDATE] Phát hiện phiên bản mới: v{latest_ver}!")
                    self.log_signal.emit("[UPDATE] Đang tải bản cập nhật. Vui lòng không tắt máy...")
                    self.status_signal.emit("update", f"Đang tải v{latest_ver}...", "#00B4DB")
                    
                    temp_exe = os.path.join(BASE_DIR, "main_update_temp.exe" if platform.system() == "Windows" else "main_update_temp")
                    urllib.request.urlretrieve(dl_url, temp_exe)
                    
                    if os.path.exists(MAIN_APP_EXE):
                        os.remove(MAIN_APP_EXE)
                    os.rename(temp_exe, MAIN_APP_EXE)
                    
                    # Cấp quyền thực thi nếu ở trên Mac
                    if platform.system() == "Darwin":
                        os.chmod(MAIN_APP_EXE, 0o755)
                    
                    with open(VERSION_FILE, "w") as f: 
                        f.write(latest_ver)
                    
                    self.log_signal.emit("[UPDATE] Cập nhật thành công!")
                    self.status_signal.emit("update", f"✅ Đã cập nhật (v{latest_ver})", "#00E6A8")
                else:
                    self.log_signal.emit(f"[SYS] Bạn đang dùng phiên bản mới nhất (Server: v{latest_ver}).")
                    self.status_signal.emit("update", f"✅ Mới nhất (v{local_ver})", "#00E6A8")
            except Exception as e:
                self.log_signal.emit(f"[WARN] Bỏ qua cập nhật: {str(e)}")
                self.status_signal.emit("update", f"⚠️ Bỏ qua (v{local_ver})", "#FFB200")

            time.sleep(1)

            # 2. RÀ SOÁT FILE MAIN CHÍNH
            self.log_signal.emit("[SYS] Rà soát File hệ thống...")
            if not os.path.exists(MAIN_APP_EXE):
                self.status_signal.emit("files", "❌ Thiếu file hệ thống", "#FF4A4A")
                self.log_signal.emit(f"[ERROR] KHÔNG TÌM THẤY FILE CHÍNH '{os.path.basename(MAIN_APP_EXE)}'.")
                all_clear = False
            else:
                self.status_signal.emit("files", "✅ Đầy đủ", "#00E6A8")
                self.log_signal.emit("[SYS] File hệ thống nguyên vẹn.")

            time.sleep(1)

            # 3. MÔI TRƯỜNG OS
            os_name = "macOS" if platform.system() == "Darwin" else "Windows"
            self.status_signal.emit("cpp", f"✅ Native {os_name}", "#00E6A8")
            self.log_signal.emit(f"[SYS] Môi trường {os_name} đã sẵn sàng.")

            self.done_signal.emit(all_clear)
            
        except Exception as e:
            self.log_signal.emit(f"[FATAL ERROR] Lỗi sập luồng Diagnostic: {str(e)}")
            self.status_signal.emit("update", "❌ Lỗi luồng", "#FF4A4A")
            self.done_signal.emit(False)

class HardwareWorker(QThread):
    update_signal = pyqtSignal(int, int, str)

    def run(self):
        while True:
            try:
                cpu_pct = int(psutil.cpu_percent(interval=None))
                mem = psutil.virtual_memory()
                ram_pct = int(mem.percent)
                used_gb = round(mem.used / (1024**3), 1)

                self.update_signal.emit(cpu_pct, ram_pct, f"{ram_pct}% ({used_gb}GB Used)")
            except: pass
            time.sleep(2)

class AppRunnerWorker(QThread):
    log_signal = pyqtSignal(str)
    done_signal = pyqtSignal(bool, str)

    def run(self):
        try:
            creationflags = 0x08000000 if platform.system() == "Windows" else 0
            process = subprocess.Popen(
                [MAIN_APP_EXE], cwd=BASE_DIR, 
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                creationflags=creationflags
            )
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                self.log_signal.emit(f"\n[CRITICAL ERROR] AEKA bị sập! Mã lỗi: {process.returncode}")
                self.log_signal.emit(f"[TRACEBACK]\n{stderr}")
                
                desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
                log_path = os.path.join(desktop, "AEKA_Crash_Report.txt")
                with open(log_path, "w", encoding="utf-8") as f:
                    f.write(f"EXIT CODE: {process.returncode}\nSTDERR:\n{stderr}\nSTDOUT:\n{stdout}")
                
                self.done_signal.emit(False, "Phần mềm gặp sự cố và bị tắt đột ngột.\nLog lỗi đã lưu tại Desktop.")
            else:
                self.log_signal.emit("\n[SYS] Tiến trình đã đóng an toàn (Exit code 0).")
                self.done_signal.emit(True, "")
        except Exception as e:
            self.log_signal.emit(f"\n[FATAL] Không thể gọi file hệ thống: {str(e)}")
            self.done_signal.emit(False, f"Bị chặn quyền truy cập hoặc mất file:\n{MAIN_APP_EXE}")

# ==========================================
# GIAO DIỆN CHÍNH (GUI)
# ==========================================
class ModernLauncher(QWidget):
    def __init__(self):
        super().__init__()
        edition = "macOS" if platform.system() == "Darwin" else "Windows"
        self.setWindowTitle(f"AEKA Launcher - {edition} Edition")
        self.resize(850, 680)
        self.setStyleSheet("""
            QWidget { background-color: #09090C; color: #E2E8F0; font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; }
            QLabel { background: transparent; }
            QFrame#Card { background-color: #111118; border-radius: 14px; border: 1px solid #1E1E28; }
            QProgressBar { background-color: #1A1A24; border-radius: 6px; text-align: center; border: none; max-height: 12px; }
            QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00B4DB, stop:1 #0083B0); border-radius: 6px; }
            QProgressBar#ProgRed::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FF416C, stop:1 #FF4B2B); }
            QPushButton#BtnRun { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #11998e, stop:1 #38ef7d); color: white; font-weight: bold; font-size: 15px; border-radius: 10px; border: none; padding: 15px; }
            QPushButton#BtnRun:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #15B3A6, stop:1 #42F58A); }
            QPushButton#BtnRun:disabled { background: #2A2A35; color: #666; }
            QPushButton#BtnForce { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #cb2d3e, stop:1 #ef473a); color: white; font-weight: bold; font-size: 15px; border-radius: 10px; border: none; padding: 15px; }
            QPushButton#BtnForce:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #E03345, stop:1 #FA5548); }
            QTextEdit { background-color: #050508; border: 1px solid #1E1E28; border-radius: 10px; padding: 15px; color: #00E6A8; font-family: 'Consolas', monospace; font-size: 13px; }
        """)

        self.labels_map = {}
        self.setup_ui()
        self.fetch_static_hardware()

        # Khởi chạy luồng
        self.diag_worker = DiagnosticWorker()
        self.diag_worker.log_signal.connect(self.log)
        self.diag_worker.status_signal.connect(self.update_status)
        self.diag_worker.done_signal.connect(self.on_diag_done)
        self.diag_worker.start()

        self.hw_worker = HardwareWorker()
        self.hw_worker.update_signal.connect(self.update_hardware_live)
        self.hw_worker.start()

    def apply_shadow(self, widget):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20); shadow.setColor(QColor(0, 0, 0, 150)); shadow.setOffset(0, 5)
        widget.setGraphicsEffect(shadow)

    def setup_ui(self):
        edition = "macOS" if platform.system() == "Darwin" else "Windows"
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)

        header_layout = QVBoxLayout()
        lbl_title = QLabel("AEKA LAUNCHER")
        lbl_title.setStyleSheet("font-size: 28px; font-weight: 900; color: #FFFFFF; letter-spacing: 1px;")
        lbl_sub = QLabel(f"Diagnostic & Startup Environment ({edition} Edition)")
        lbl_sub.setStyleSheet("font-size: 13px; font-weight: 500; color: #8888A0;")
        header_layout.addWidget(lbl_title); header_layout.addWidget(lbl_sub)
        main_layout.addLayout(header_layout)
        main_layout.addSpacing(20)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)

        card_hw = QFrame(); card_hw.setObjectName("Card"); self.apply_shadow(card_hw)
        hw_layout = QVBoxLayout(card_hw); hw_layout.setContentsMargins(20, 20, 20, 20)
        lbl_hw_title = QLabel("SYSTEM SPECS"); lbl_hw_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #8C8CFA; margin-bottom: 10px;")
        hw_layout.addWidget(lbl_hw_title)

        self.lbl_os = self._add_spec_row(hw_layout, "OS")
        self.lbl_py = QLabel("Analyzing..."); self.lbl_py.setStyleSheet("color: #888; font-weight: bold; margin-bottom: 10px;")
        hw_layout.addWidget(self.lbl_py)

        self.lbl_cpu = self._add_spec_row(hw_layout, "CPU")
        self.lbl_gpu = self._add_spec_row(hw_layout, "GPU")
        self.lbl_ram = self._add_spec_row(hw_layout, "RAM")
        hw_layout.addSpacing(15)

        hw_layout.addWidget(self._create_progress_label("CPU Load"))
        self.prog_cpu = QProgressBar(); self.prog_cpu.setValue(0); hw_layout.addWidget(self.prog_cpu)
        self.lbl_cpu_txt = QLabel("0%"); self.lbl_cpu_txt.setAlignment(Qt.AlignmentFlag.AlignRight); self.lbl_cpu_txt.setStyleSheet("color: #aaa; font-family: Consolas;")
        hw_layout.addWidget(self.lbl_cpu_txt)

        hw_layout.addWidget(self._create_progress_label("Memory Usage"))
        self.prog_ram = QProgressBar(); self.prog_ram.setValue(0); hw_layout.addWidget(self.prog_ram)
        self.lbl_ram_txt = QLabel("0%"); self.lbl_ram_txt.setAlignment(Qt.AlignmentFlag.AlignRight); self.lbl_ram_txt.setStyleSheet("color: #aaa; font-family: Consolas;")
        hw_layout.addWidget(self.lbl_ram_txt)

        hw_layout.addStretch()
        cards_layout.addWidget(card_hw, stretch=5)

        card_sys = QFrame(); card_sys.setObjectName("Card"); self.apply_shadow(card_sys)
        sys_layout = QVBoxLayout(card_sys); sys_layout.setContentsMargins(20, 20, 20, 20)
        lbl_sys_title = QLabel("INTEGRITY CHECK"); lbl_sys_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #FFD700; margin-bottom: 10px;")
        sys_layout.addWidget(lbl_sys_title)

        self.labels_map["update"] = self._add_status_row(sys_layout, "App Version:")
        self.labels_map["files"] = self._add_status_row(sys_layout, "App Files:")
        self.labels_map["cpp"] = self._add_status_row(sys_layout, "Environment:")
        sys_layout.addSpacing(15)

        lbl_log_title = QLabel("EVENT LOG"); lbl_log_title.setStyleSheet("color: #555566; font-weight: bold; font-size: 11px;")
        sys_layout.addWidget(lbl_log_title)
        
        self.log_area = QTextEdit(); self.log_area.setReadOnly(True)
        self.log_area.append("[SYS] Booting Launcher...")
        sys_layout.addWidget(self.log_area)

        cards_layout.addWidget(card_sys, stretch=6)
        main_layout.addLayout(cards_layout)

        main_layout.addSpacing(10)
        self.btn_run = QPushButton("SYSTEM CHECKING..."); self.btn_run.setObjectName("BtnRun")
        self.btn_run.setDisabled(True)
        self.btn_run.clicked.connect(self.launch_app)
        self.apply_shadow(self.btn_run)
        main_layout.addWidget(self.btn_run)

    def _add_spec_row(self, layout, title):
        row = QHBoxLayout(); row.setSpacing(10)
        lbl_t = QLabel(title); lbl_t.setFixedWidth(40); lbl_t.setStyleSheet("color: #777788; font-weight: bold;")
        lbl_v = QLabel("..."); lbl_v.setStyleSheet("color: #E2E8F0; font-weight: 500;")
        row.addWidget(lbl_t); row.addWidget(lbl_v, stretch=1)
        layout.addLayout(row)
        return lbl_v

    def _add_status_row(self, layout, title):
        row = QHBoxLayout(); row.setSpacing(10)
        lbl_t = QLabel(title); lbl_t.setFixedWidth(100); lbl_t.setStyleSheet("color: #9999AA; font-weight: 600;")
        lbl_v = QLabel("⏳ Waiting..."); lbl_v.setStyleSheet("color: #FFB200; font-weight: bold;")
        row.addWidget(lbl_t); row.addWidget(lbl_v, stretch=1)
        layout.addLayout(row)
        return lbl_v
        
    def _create_progress_label(self, text):
        lbl = QLabel(text); lbl.setStyleSheet("color: #888899; font-size: 12px; font-weight: bold; margin-top: 5px;")
        return lbl

    def log(self, text):
        self.log_area.append(text)
        self.log_area.verticalScrollBar().setValue(self.log_area.verticalScrollBar().maximum())

    def update_status(self, target, text, hex_color):
        lbl = self.labels_map.get(target)
        if lbl:
            lbl.setText(text)
            lbl.setStyleSheet(f"color: {hex_color}; font-weight: bold;")

    def update_hardware_live(self, cpu, ram, ram_txt):
        self.prog_cpu.setValue(cpu)
        self.lbl_cpu_txt.setText(f"{cpu}%")
        self.prog_cpu.setObjectName("ProgRed" if cpu > 85 else "")
        self.prog_cpu.style().unpolish(self.prog_cpu); self.prog_cpu.style().polish(self.prog_cpu)

        self.prog_ram.setValue(ram)
        self.lbl_ram_txt.setText(ram_txt)
        self.prog_ram.setObjectName("ProgRed" if ram > 85 else "")
        self.prog_ram.style().unpolish(self.prog_ram); self.prog_ram.style().polish(self.prog_ram)

    def fetch_static_hardware(self):
        try:
            os_name = f"{platform.system()} {platform.release()}"
            try:
                build_num = int(platform.version().split('.')[2])
                if build_num >= 22000 and platform.system() == "Windows":
                    os_name = "Windows 11"
            except: pass
            self.lbl_os.setText(os_name)
            
            # --- LẤY TÊN CPU CHUẨN CHO CẢ WIN LẪN MAC ---
            cpu_name = platform.processor()
            if platform.system() == "Windows" and winreg:
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
                    cpu_name, _ = winreg.QueryValueEx(key, "ProcessorNameString")
                    cpu_name = cpu_name.strip()
                except: pass
            elif platform.system() == "Darwin":
                try:
                    cpu_name = subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"], text=True).strip()
                except: pass
            
            self.lbl_cpu.setText(cpu_name[:35] + "..." if len(cpu_name) > 35 else cpu_name)

            self.lbl_py.setText("✅Compatible with Python Engine")
            self.lbl_py.setStyleSheet("color: #00E6A8; font-weight: bold; margin-bottom: 10px;")

            # --- LẤY TÊN GPU CHUẨN CHO CẢ WIN LẪN MAC ---
            if platform.system() == "Windows":
                try:
                    gpu_cmd = "powershell \"(Get-CimInstance Win32_VideoController).Name\""
                    output = subprocess.check_output(gpu_cmd, shell=True, text=True).strip().split('\n')
                    gpus = [g.strip() for g in output if g.strip()]
                    gpu_name = " + ".join(gpus) if gpus else "Windows Graphics"
                except:
                    gpu_name = "Windows Graphics"
            elif platform.system() == "Darwin":
                try:
                    gpu_cmd = "system_profiler SPDisplaysDataType | grep Chipset"
                    output = subprocess.check_output(gpu_cmd, shell=True, text=True).strip()
                    gpu_name = output.split(":")[-1].strip() if output else "Apple Silicon GPU"
                except:
                    gpu_name = "Apple Mac Graphics"
            else:
                gpu_name = "Unknown Graphics"
                
            self.lbl_gpu.setText(gpu_name[:35] + "..." if len(gpu_name) > 35 else gpu_name)

            mem = psutil.virtual_memory()
            self.lbl_ram.setText(f"{round(mem.total / (1024**3))} GB")
        except Exception as e:
            print(f"Lỗi hiển thị phần cứng: {e}")

    def on_diag_done(self, all_clear):
        if all_clear:
            self.log("\n[SYS] Môi trường hệ thống hoàn hảo. Sẵn sàng khởi động!")
            self.btn_run.setText("LAUNCH AEKA SCOREBOARD")
            self.btn_run.setObjectName("BtnRun")
            
            import threading
            threading.Timer(2.0, self.launch_app).start()
        else:
            self.log("\n[SYS] ⚠️ Phát hiện rủi ro hệ thống. Phần mềm có thể không hoạt động.")
            self.btn_run.setText("⚠️ IGNORE WARNINGS & FORCE LAUNCH")
            self.btn_run.setObjectName("BtnForce")
        
        self.btn_run.setDisabled(False)
        self.btn_run.style().unpolish(self.btn_run); self.btn_run.style().polish(self.btn_run)

    def launch_app(self):
        self.btn_run.setDisabled(True); self.btn_run.setText("RUNNING...")
        self.log("\n[SYS] Calling Main Executable...")
        
        try:
            creationflags = 0x08000000 if platform.system() == "Windows" else 0
            subprocess.Popen([MAIN_APP_EXE], cwd=BASE_DIR, creationflags=creationflags)
            sys.exit(0)
        except Exception as e:
            self.log(f"\n[ERROR] Không thể chạy phần mềm chính: {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ModernLauncher()
    window.show()
    sys.exit(app.exec())
