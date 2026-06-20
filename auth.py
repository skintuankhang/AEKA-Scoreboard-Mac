import os
import requests
import json
import threading
import time
import winreg
import platform
from datetime import datetime, timedelta, timezone
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QMessageBox, QApplication)
from PyQt6.QtCore import Qt, QObject, pyqtSignal

FIREBASE_URL = "https://aeka-key-active-default-rtdb.firebaseio.com/"
# [MAC VERSION] - Lưu vào thư mục Library chuẩn của macOS / AppData của Windows
APP_DATA_DIR = os.path.join(os.getenv('APPDATA'), 'AEKA_ScoreBoard')
os.makedirs(APP_DATA_DIR, exist_ok=True)
LICENSE_FILE = os.path.join(APP_DATA_DIR, "license.dat")
MSG_LOG_FILE = os.path.join(APP_DATA_DIR, "last_msg.dat")  # File lưu vết thông báo

heartbeat_active = False
msg_receiver = None

def get_last_seen_msg():
    """Đọc thời gian của thông báo cuối cùng đã xem từ file tạm."""
    if os.path.exists(MSG_LOG_FILE):
        try:
            with open(MSG_LOG_FILE, "r") as f: return f.read().strip()
        except: pass
    return ""

def set_last_seen_msg(time_str):
    """Ghi đè thời gian thông báo mới nhất xuống file."""
    try:
        with open(MSG_LOG_FILE, "w") as f: f.write(str(time_str))
    except: pass

# ==========================================
# CỤC THU SÓNG TIN NHẮN TỪ ADMIN
# ==========================================
class MessageReceiver(QObject):
    show_msg_signal = pyqtSignal(str, str, str, str)

    def __init__(self):
        super().__init__()
        self.show_msg_signal.connect(self.show_msg)

    def show_msg(self, msg_type, title, content, key_path):
        msg_box = QMessageBox()
        
        # ---> ÉP ĐỒNG BỘ GIAO DIỆN TỐI (DARK THEME) GIỐNG Y HỆT CONTROL PANEL <---
        msg_box.setStyleSheet("""
            QMessageBox { background-color: #1E1E24; color: #E0E0E0; font-family: 'Segoe UI', Arial; font-size: 14px; }
            QLabel { color: #E0E0E0; font-size: 14px; }
            QPushButton { background-color: #2D2D3B; border: 1px solid #444; border-radius: 5px; padding: 6px 15px; font-weight: bold; color: white; }
            QPushButton:hover { background-color: #3D3D4B; border: 1px solid #00FFB2; }
        """)

        msg_box.setWindowTitle(title)
        msg_box.setText(content)
        
        if msg_type == "PRIVATE":
            msg_box.setIcon(QMessageBox.Icon.Warning)
        else:
            msg_box.setIcon(QMessageBox.Icon.Information)
            
        msg_box.addButton("ĐÃ ĐỌC VÀ XÁC NHẬN", QMessageBox.ButtonRole.AcceptRole)
        msg_box.setWindowFlags(msg_box.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        msg_box.exec()

        if msg_type == "PRIVATE" and key_path:
            try:
                requests.patch(f"{FIREBASE_URL}keys/{key_path}.json", json.dumps({"private_message": None}), timeout=5)
            except: pass

def get_hwid():
    try:
        registry = winreg.HKEY_LOCAL_MACHINE
        address = 'SOFTWARE\\Microsoft\\Cryptography'
        key = winreg.OpenKey(registry, address, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
        value, _ = winreg.QueryValueEx(key, 'MachineGuid')
        return value
    except Exception: 
        return "WIN-UNKNOWN-HWID"

def verify_license():
    if not os.path.exists(LICENSE_FILE): return False
    try:
        with open(LICENSE_FILE, "r") as f: saved_key = f.read().strip().splitlines()[0]
    except Exception: return False
        
    current_hwid = get_hwid()
    now_utc = datetime.now(timezone.utc)
    
    try:
        url = f"{FIREBASE_URL}keys/{saved_key}.json"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200 and response.json() is not None:
            data = response.json()
            if not data.get("is_active", True): return False 
            
            server_expiry = data.get("expiry_date")
            if server_expiry: 
                if now_utc > datetime.fromisoformat(server_expiry): return False 

            active_hwid = data.get("active_hwid") or data.get("hwid")
            last_online_str = data.get("last_online") or data.get("last_ping")
            
            # KIỂM TRA MÁY KHÁC ĐANG SỬ DỤNG
            if active_hwid and active_hwid != current_hwid:
                if last_online_str:
                    try:
                        last_online = datetime.fromisoformat(str(last_online_str))
                        if now_utc - last_online < timedelta(seconds=120):
                            return "IN_USE" 
                    except Exception: pass
            
            requests.patch(url, json.dumps({
                "active_hwid": current_hwid,
                "hwid": current_hwid,
                "last_online": now_utc.isoformat(),
                "os_version": f"{platform.system()} {platform.release()}"
            }), timeout=5)
            
            return True 
        else: return False 
    except Exception:
        return False 

def heartbeat_worker(key):
    global heartbeat_active, msg_receiver
    hwid = get_hwid()
    while heartbeat_active:
        try:
            now_utc = datetime.now(timezone.utc)
            os_info = f"{platform.system()} {platform.release()}"
            
            requests.patch(f"{FIREBASE_URL}keys/{key}.json", json.dumps({
                "last_online": now_utc.isoformat(),
                "last_ping": now_utc.isoformat(),
                "active_hwid": hwid,
                "os_version": os_info
            }), timeout=5)
            
            res_pm = requests.get(f"{FIREBASE_URL}keys/{key}/private_message.json", timeout=5)
            if res_pm.status_code == 200 and res_pm.json():
                pm_data = res_pm.json()
                if isinstance(pm_data, dict) and pm_data.get("text"):
                    if msg_receiver:
                        msg_receiver.show_msg_signal.emit("PRIVATE", "THÔNG BÁO TỪ QUẢN TRỊ VIÊN", pm_data.get("text"), key)

            res_g = requests.get(f"{FIREBASE_URL}system/announcement.json", timeout=5)
            if res_g.status_code == 200 and res_g.json():
                ann_data = res_g.json()
                if isinstance(ann_data, dict):
                    bm = ann_data.get("message", "")
                    bm_time = ann_data.get("time", "")
                    
                    last_seen = get_last_seen_msg()
                    if bm and bm_time != last_seen:
                        set_last_seen_msg(bm_time)  # Lưu vào file ngay lập tức
                        if msg_receiver:
                            msg_receiver.show_msg_signal.emit("GLOBAL", "THÔNG BÁO HỆ THỐNG", bm, "")

        except Exception: pass 
        time.sleep(15)

def start_heartbeat():
    global heartbeat_active, msg_receiver
    if not heartbeat_active and os.path.exists(LICENSE_FILE):
        try:
            with open(LICENSE_FILE, "r") as f: saved_key = f.read().strip().splitlines()[0]
            if msg_receiver is None:
                msg_receiver = MessageReceiver()
            heartbeat_active = True
            threading.Thread(target=heartbeat_worker, args=(saved_key,), daemon=True).start()
        except Exception: pass

def release_session():
    global heartbeat_active
    heartbeat_active = False
    if os.path.exists(LICENSE_FILE):
        try:
            with open(LICENSE_FILE, "r") as f: saved_key = f.read().strip().splitlines()[0]
            requests.patch(f"{FIREBASE_URL}keys/{saved_key}.json", json.dumps({
                "active_hwid": "",
                "last_online": "",
                "last_ping": ""
            }), timeout=3)
        except Exception: pass

# ==========================================
# GIAO DIỆN XÁC THỰC BẢN QUYỀN
# ==========================================
class LicenseDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AEKA - KÍCH HOẠT BẢN QUYỀN")
        self.setFixedSize(550, 350)
        self.setStyleSheet("""
            QDialog { background-color: #1E1E24; color: white; font-family: Arial; border: 2px solid #00FFB2; }
            QLabel { font-size: 14px; border: none; }
            QLineEdit { background-color: #2D2D3B; color: #00FFB2; border: 1px solid #555; padding: 10px; font-size: 16px; font-weight: bold; text-align: center;}
            QPushButton { background-color: #008855; color: white; font-size: 16px; font-weight: bold; padding: 12px; border-radius: 5px; border: none; }
            QPushButton:hover { background-color: #00FFB2; color: black; }
        """)

        self.hwid = get_hwid()
        layout = QVBoxLayout(self)
        
        lbl_info = QLabel("NHẬP MÃ KÍCH HOẠT (KEY) ĐỂ SỬ DỤNG PHẦN MỀM:")
        lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_info.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFD700;")
        layout.addWidget(lbl_info)
        
        self.input_key = QLineEdit()
        self.input_key.setPlaceholderText("Dán mã Key vào đây (VD: AEKA-XXXX-XXXX)")
        layout.addWidget(self.input_key)
        
        self.btn_activate = QPushButton("KÍCH HOẠT NGAY")
        self.btn_activate.clicked.connect(self.check_activation)
        layout.addWidget(self.btn_activate)

        layout.addSpacing(15)

        lbl_contact = QLabel("Hỗ trợ kỹ thuật - LH: 0337502711")
        lbl_contact.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_contact.setStyleSheet("color: #00FFB2; font-size: 13px; font-weight: bold;")
        layout.addWidget(lbl_contact)

        lbl_id = QLabel(f"ID Thiết Bị: {self.hwid}")
        lbl_id.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_id.setStyleSheet("color: #777; font-size: 11px;")
        layout.addWidget(lbl_id)

    def check_activation(self):
        entered_key = self.input_key.text().strip().upper()
        if not entered_key: return
        self.btn_activate.setText("ĐANG KIỂM TRA...")
        self.btn_activate.setDisabled(True)

        try:
            url = f"{FIREBASE_URL}keys/{entered_key}.json"
            response = requests.get(url, timeout=7)
            
            if response.status_code == 200 and response.json() is not None:
                key_data = response.json()
                if not key_data.get("is_active", True):
                    QMessageBox.critical(self, "Lỗi", "Mã kích hoạt này đã bị vô hiệu hóa bởi Admin!")
                else:
                    now_utc = datetime.now(timezone.utc)
                    status = key_data.get("status", "NEW")
                    active_hwid = key_data.get("active_hwid") or key_data.get("hwid")
                    last_online_str = key_data.get("last_online") or key_data.get("last_ping")
                    
                    if status == "USED" and active_hwid and active_hwid != self.hwid:
                        if last_online_str:
                            try:
                                last_online = datetime.fromisoformat(str(last_online_str))
                                if now_utc - last_online < timedelta(seconds=120):
                                    QMessageBox.warning(self, "Từ chối", "Mã Key này đang được MỞ trên thiết bị khác!\nVui lòng tắt app ở máy kia trước khi sử dụng.")
                                    self.btn_activate.setText("KÍCH HOẠT NGAY")
                                    self.btn_activate.setDisabled(False)
                                    return
                            except Exception: pass

                    duration = key_data.get("duration_days")
                    expiry_date = key_data.get("expiry_date")
                    display_date = "Vĩnh viễn"
                    
                    patch_payload = {
                        "status": "USED",
                        "active_hwid": self.hwid,
                        "hwid": self.hwid,
                        "last_online": now_utc.isoformat(),
                        "os_version": f"{platform.system()} {platform.release()}"
                    }
                    
                    if status == "NEW" and duration:
                        dt_expiry = now_utc + timedelta(days=duration)
                        expiry_date = dt_expiry.isoformat()
                        patch_payload["activated_at"] = now_utc.isoformat()
                        patch_payload["expiry_date"] = expiry_date
                        
                    requests.patch(url, json.dumps(patch_payload))

                    if expiry_date:
                        dt_vn = datetime.fromisoformat(expiry_date) + timedelta(hours=7)
                        display_date = dt_vn.strftime("%d/%m/%Y lúc %H:%M:%S")

                    with open(LICENSE_FILE, "w") as f: f.write(entered_key)
                    QMessageBox.information(self, "Thành công", f"KÍCH HOẠT THÀNH CÔNG!\nHạn dùng: {display_date}")
                    self.accept()
            else:
                QMessageBox.critical(self, "Lỗi", "Mã Key không tồn tại hoặc đã bị xóa khỏi hệ thống!")
        except Exception:
            QMessageBox.warning(self, "Lỗi", "Vui lòng kiểm tra lại đường truyền Internet và thử lại!")
            
        self.btn_activate.setText("KÍCH HOẠT NGAY")
        self.btn_activate.setDisabled(False)