import time
from dataclasses import dataclass
from typing import List, Dict, Tuple, Set

# ===== CẤU HÌNH THỜI GIAN THEO LUẬT WT =====
CONSENSUS_WINDOW = 1.0     # Khung thời gian đồng thuận
TECH_FOLLOW_WINDOW = 1.5   # Khung thời gian chờ đòn kỹ thuật
FLASH_DURATION = 0.8       # Thời gian đèn LED nháy sáng

@dataclass
class Press:
    judge: int
    action: str
    t: float

class ScoreEngine:
    def __init__(self, state):
        self.state = state
        self.actions = ["R1", "R2", "R3", "RT", "B1", "B2", "B3", "BT"]
        self.buffers: Dict[str, List[Press]] = {a: [] for a in self.actions}
        self.consumed_ids: Set[Tuple[int, str, float]] = set()
        self.last_press_flash: Dict[Tuple[int, str], float] = {}
        
        self.last_award = {
            "red": {"value": 0, "t": 0.0, "bucket": "", "pending_tech": False},
            "blue": {"value": 0, "t": 0.0, "bucket": "", "pending_tech": False}
        }

    def register_press(self, judge: int, action: str):
        now = time.time()
        
        # 🔥 1. BỘ LỌC CHỐNG DỘI PHÍM (Chặn 1 ông bấm 2 lần liên tiếp trong 0.8s)
        for p in reversed(self.buffers[action]):
            # Dùng getattr để tương thích mọi kiểu dữ liệu (Class, Tuple)
            if getattr(p, 'judge', p[0] if isinstance(p, tuple) else p) == judge and (now - p.t) < 0.3:
                return False # Phím bị nảy/dội -> Bỏ qua ngay!

        self.buffers[action].append(Press(judge, action, now))
        self.last_press_flash[(judge, action)] = now
        
        # 🔥 2. CHỈ GHI NHẬN VÀO BỘ NHỚ, KHÔNG TÍNH ĐIỂM NGAY LẬP TỨC NỮA
        return True

    def get_flash_state(self, color: str, now: float) -> Dict[int, List[int]]:
        state = {1: [], 2: [], 3: []}
        prefix = "R" if color == "red" else "B"
        for (j, act), t in self.last_press_flash.items():
            if act.startswith(prefix) and (now - t) <= FLASH_DURATION:
                if act[1] in ["1", "2", "3"]:
                    pts = int(act[1])
                    state.setdefault(j, []).append(pts) if pts not in state.get(j, []) else None
                elif act[1] == "T":
                    state[j] = [1, 2, 3]
        return state

    def evaluate(self, now: float):
        keep_for = max(CONSENSUS_WINDOW, TECH_FOLLOW_WINDOW) + 0.5
        for act in self.actions:
            self.buffers[act] = [p for p in self.buffers[act] if now - p.t <= keep_for]

        scoring_judges = set()

        # 2. XÉT ĐÒN CƠ BẢN
        for act in ["R1", "R2", "R3", "B1", "B2", "B3"]:
            picked = self._get_consensus(act, now, CONSENSUS_WINDOW)
            if len(picked) >= 2:
                # 🔥 Lấy hết toàn bộ trọng tài đã bấm (không cắt [:2] nữa)
                for p in picked:
                    scoring_judges.add(p.judge)
                    
                self._consume(picked) # Đưa hết vào lịch sử để không bị nhảy điểm double
                color = "red" if act[0] == "R" else "blue"
                pts = int(act[1])
                self._award_base_point(color, pts, now)

        # 3. XÉT ĐÒN KỸ THUẬT
        for act in ["RT", "BT"]:
            picked = self._get_consensus(act, now, CONSENSUS_WINDOW)
            if len(picked) >= 2:
                for p in picked:
                    scoring_judges.add(p.judge)

                self._consume(picked) 
                color = "red" if act[0] == "R" else "blue"
                self._apply_tech(color, now)

        return list(scoring_judges) if scoring_judges else False

    def _get_consensus(self, action: str, now: float, window: float) -> List[Press]:
        candidates = [p for p in self.buffers[action] if now - p.t <= window]
        candidates.sort(key=lambda p: p.t, reverse=True)
        seen = set()
        picked = []
        for p in candidates:
            if (p.judge, p.action, p.t) in self.consumed_ids: continue
            if p.judge in seen: continue
            seen.add(p.judge)
            picked.append(p)
            #if len(picked) == 2: break
        return picked

    def _consume(self, presses: List[Press]):
        for p in presses:
            self.consumed_ids.add((p.judge, p.action, p.t))

    def _award_base_point(self, color: str, pts: int, now: float):
        """Cộng điểm hoặc trừ máu kèm hệ số nhân X2 Sip-cho"""
        player = self.state.red if color == "red" else self.state.blue
        opp = self.state.blue if color == "red" else self.state.red
        bucket = "punch" if pts == 1 else ("body" if pts == 2 else "head")
        
        # 🔥 LOGIC NHÂN ĐÔI SÁT THƯƠNG (SIP-CHO)
        multiplier = 1
        if color == "red" and getattr(self.state, 'red_x2_timer', 0) > 0:
            multiplier = 2
        elif color == "blue" and getattr(self.state, 'blue_x2_timer', 0) > 0:
            multiplier = 2

        if getattr(self.state, 'match_format', 'BO3') == "TEAM_HP":
            # Trừ máu đối phương: (Điểm gốc * 5) * Hệ số nhân Sip-cho
            damage = pts * 5 * multiplier
            opp.score = max(0, opp.score - damage)
        else:
            # Mode BO3 thường: Vẫn nhân hệ số nếu muốn (tùy luật giải của đại ca)
            player.score += (pts * multiplier)
        
        if bucket == "punch": player.pts_punch += 1
        elif bucket == "body": player.pts_body += 1
        elif bucket == "head": player.pts_head += 1

        self.last_award[color] = {
            "value": pts,
            "t": now,
            "bucket": bucket,
            "pending_tech": (pts in [2, 3]),
            "multiplier": multiplier # Lưu lại để tính đòn xoay cho đúng
        }

    def _apply_tech(self, color: str, now: float) -> bool:
        """Nâng cấp đòn kỹ thuật kèm hệ số nhân Sip-cho"""
        la = self.last_award[color]
        if not la["pending_tech"]: return False
        if now - la["t"] > TECH_FOLLOW_WINDOW: 
            la["pending_tech"] = False
            return False

        player = self.state.red if color == "red" else self.state.blue
        opp = self.state.blue if color == "red" else self.state.red
        
        base = la["value"]
        multiplier = la.get("multiplier", 1) # Lấy lại multiplier từ đòn gốc
        
        total_turn = base * 2 
        diff = total_turn - base 

        player.pts_turn += total_turn
        
        if getattr(self.state, 'match_format', 'BO3') == "TEAM_HP":
            # 🔥 CHẶN ĐÁY Ở ĐÂY: Trừ bù thêm máu cho đòn xoay, chặn không cho âm
            extra_damage = diff * 5 * multiplier
            opp.score = max(0, opp.score - extra_damage)
        else:
            player.score += (diff * multiplier)

        la["pending_tech"] = False 
        return True