
import cv2
import mediapipe as mp
import numpy as np
import math


class HandDetector:
    """
    Klasa za detekciju ruke i prepoznavanje prstiju/gesti.
    Koristi MediaPipe Hands model koji detektira 21 ključnu točku na ruci.
    """

   
    FINGER_TIPS = [4, 8, 12, 16, 20]       # Palac, Kažiprst, Srednji, Prstenjak, Mali
    FINGER_PIPS = [3, 6, 10, 14, 18]       # Zglobovi ispod vrhova (za usporedbu)

    def __init__(self, max_hands=1, detection_confidence=0.82, tracking_confidence=0.82):
        # POVEĆAN CONFIDENCE: Postavljen na 0.82 kako bi se spriječilo titranje i lažni unosi
        self.mp_hands = mp.solutions.hands
        self.mp_draw = mp.solutions.drawing_utils
        self.mp_draw_styles = mp.solutions.drawing_styles

        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_hands,
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence
        )

    def find_hands(self, frame, draw=True):
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(img_rgb)
        
        all_hands = []
        if results.multi_hand_landmarks:
            for hand_idx, hand_lms in enumerate(results.multi_hand_landmarks):
                lbl = results.multi_handedness[hand_idx].classification[0].label
                
                h, w, _ = frame.shape
                lm_list = []
                for lm in hand_lms.landmark:
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    lm_list.append((cx, cy))
                
                all_hands.append({"lm_list": lm_list, "handedness": lbl})
                
                if draw:
                    self.mp_draw.draw_landmarks(
                        frame, hand_lms, self.mp_hands.HAND_CONNECTIONS,
                        self.mp_draw_styles.get_default_hand_landmarks_style(),
                        self.mp_draw_styles.get_default_hand_connections_style()
                    )
        return all_hands

    def count_fingers(self, hand):
        lm = hand["lm_list"]
        handedness = hand["handedness"]
        
        fingers_up = self._get_fingers_state(lm, handedness)
        return sum(1 for f in fingers_up if f)

    def detect_gesture(self, hand):
        lm = hand["lm_list"]
        handedness = hand["handedness"]
        
        fingers_up = self._get_fingers_state(lm, handedness)
        thumb, index, middle, ring, pinky = fingers_up

        # ✊ Šaka = zbrajanje (+) -> niti jedan prst nije podignut
        if not any(fingers_up):
            return "+"

        # ✌️ V znak (Kažiprst + Srednji) = oduzimanje (-)
        if index and middle and not thumb and not ring and not pinky:
            return "-"

        # 👍 Samo palac gore (množenje *)
        if thumb and not index and not middle and not ring and not pinky:
            return "*"

        # 🤙 Palac + Mali prst = dijeljenje (/)
        if thumb and pinky and not index and not middle and not ring:
            return "/"

        return None

    def _get_fingers_state(self, lm, handedness):
        """
        Vraća tuple (thumb, index, middle, ring, pinky) – True ako je prst podignut.
        Savršeno rješava problem šake (0), znaka mir (2) i palca (za množenje)
        koristeći anatomsku stranu ruke ovisno o tome je li lijeva ili desna.
        """
        #
        tip_buffer = 20   
        mcp_buffer = 10   
        other = [
            (lm[self.FINGER_TIPS[i]][1] < lm[self.FINGER_PIPS[i]][1] - tip_buffer)
            and
            (lm[self.FINGER_TIPS[i]][1] < lm[self.FINGER_TIPS[i] - 3][1] - mcp_buffer)
            for i in range(1, 5)
        ]
        
        
        if handedness == "Right":
            thumb_horiz = lm[4][0] < (lm[5][0] - 10)
        else:
            thumb_horiz = lm[4][0] > (lm[5][0] + 10)

        
        thumb_vert = lm[4][1] < (lm[2][1] - 20) and lm[4][1] < (lm[9][1] - 10)

        thumb = thumb_horiz or thumb_vert

        return (thumb, *other)

    def get_gesture_name(self, gesture_symbol):
        """Vraća tekstualni naziv operacije na temelju simbola."""
        return {
            "+": "ZBRAJANJE (+)",
            "-": "ODUZIMANJE (-)",
            "*": "MNOZENJE (*)",
            "/": "DIJELJENJE (/)"
        }.get(gesture_symbol, "Nepoznato")