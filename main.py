import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from core.state import MatchState
from ui.scoreboard import ScoreboardWindow
from ui.control_panel import ControlPanelWindow
import os

# 🔥 IMPORT THÊM CÁC HÀM NHỊP TIM
from auth import LicenseDialog, verify_license, start_heartbeat, release_session

global_state = MatchState()

def get_real_base_path():
    """Hàm tối thượng để tìm thư mục cài đặt thực tế"""
    if getattr(sys, 'frozen', False) or '__compiled__' in globals():
        return os.path.dirname(os.path.abspath(sys.argv[0]))
    return os.path.dirname(os.path.abspath(__file__))

# Gán vào biến môi trường để các file con (control_panel, scoreboard) gọi cho dễ
os.environ["APP_ROOT"] = get_real_base_path()

def main():
    app = QApplication(sys.argv)
    auth_status = verify_license()
    
    if auth_status == "IN_USE":
        # Phát hiện máy khác đang xài!
        QMessageBox.critical(None, "Từ chối truy cập", "Mã Key này đang được sử dụng trên một thiết bị khác!\nVui lòng tắt ứng dụng ở máy kia rồi thử lại.")
        sys.exit(0)
    elif not auth_status:
        dialog = LicenseDialog()
        if dialog.exec() == 0:
            sys.exit(0)
            
    start_heartbeat()
    scoreboard = ScoreboardWindow(global_state)
    control_panel = ControlPanelWindow(global_state, scoreboard)
    
    def close_all():
        release_session() # 🔥 NHẢ KEY CHO NGƯỜI KHÁC TRƯỚC KHI TẮT APP
        scoreboard.close()

    # Ràng buộc tắt app
    control_panel.closeEvent = lambda event: close_all() or event.accept()

    # Xử lý 2 màn hình
    screens = app.screens()
    if len(screens) > 1:
        landscape_screens = [s for s in screens if s.geometry().width() > s.geometry().height()]
        portrait_screens = [s for s in screens if s.geometry().height() >= s.geometry().width()]
        ctrl_screen = screens[0]
        tv_screen = screens[1]

        if landscape_screens and portrait_screens:
            tv_screen = landscape_screens[0]
            ctrl_screen = portrait_screens[0]
        else:
            tv_screen = screens[1]
            ctrl_screen = screens[0]

        control_panel.move(ctrl_screen.geometry().topLeft())
        control_panel.showMaximized() 

        scoreboard.move(tv_screen.geometry().topLeft())
        scoreboard.showFullScreen()   
    else:
        control_panel.showMaximized()
        scoreboard.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()