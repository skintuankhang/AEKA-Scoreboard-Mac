from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class PlayerState:
    name: str = ""
    score: int = 0
    gamjeom: int = 0
    
    # Bộ đếm điểm đòn đánh (hiển thị tổng điểm để xét Ưu thế)
    pts_punch: int = 0  
    pts_body: int = 0   
    pts_head: int = 0   
    pts_turn: int = 0   
    
    # 🔥 VÁ LỖI CẤU TRÚC: Khai báo rõ ràng các biến trạng thái
    rounds_won: int = 0     # Số hiệp đã thắng (Dùng cho thể thức BO3)
    ivr_quota: bool = True  # Quyền khiếu nại Video Replay (Còn/Hết)


@dataclass
class MatchState:
    # Thông tin chung
    match_number: str = "1"
    gender: str = "NAM"
    weight_class: str = "-58KG"
    match_category: str = "CHUNG KẾT"
    current_round: int = 1
    
    # Biến ngôn ngữ chung cho toàn hệ thống
    language: str = "VI"

    # CHẾ ĐỘ THI ĐẤU (BO3 hoặc TEAM_HP hoặc TEAM_BO3)
    match_format: str = "BO3"
    
    # Trạng thái thời gian
    timer_seconds: float = 120.0  # Mặc định 2 phút
    timer_running: bool = False
    timer_mode: str = "NORMAL"    # NORMAL, KYESHI (Săn sóc), SHIGAN (Xem xét), BREAK, WAIT_CONFIRM
    
    # Dữ liệu 2 VĐV
    red: PlayerState = field(default_factory=PlayerState)
    blue: PlayerState = field(default_factory=PlayerState)
    
    # Kết quả 3 hiệp (Best of 3)
    round_results: Dict[int, dict] = field(default_factory=lambda: {1: None, 2: None, 3: None})

    # Quản lý thời gian thay người (Dành cho mode Đồng đội)
    red_sub_timer: float = 0.0
    blue_sub_timer: float = 0.0

    # 🔥 VÁ LỖI CẤU TRÚC: Quản lý thời gian phạt Sip-cho (X2 Sát thương)
    red_x2_timer: float = 0.0
    blue_x2_timer: float = 0.0

    def reset_round_scores(self):
        """Reset điểm số và lỗi khi bắt đầu hiệp mới"""
        self.red.score = self.blue.score = 0
        self.red.gamjeom = self.blue.gamjeom = 0
        self.red.pts_punch = self.red.pts_body = self.red.pts_head = self.red.pts_turn = 0
        self.blue.pts_punch = self.blue.pts_body = self.blue.pts_head = self.blue.pts_turn = 0