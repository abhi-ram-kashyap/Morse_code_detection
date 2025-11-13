import cv2
import numpy as np
import time

# --- 1. CONFIGURATION CONSTANTS ---
# Morse timing from Phase 2 (in milliseconds)
DOT_DURATION_MS = 200
DASH_DURATION_MS = 600
GAP_ELEMENT_MS = 200
GAP_LETTER_MS = 600
GAP_WORD_MS = 1400

# Decoding Thresholds (in seconds)
DOT_DASH_THRESHOLD_S = 0.400
LETTER_GAP_THRESHOLD_S = 0.500
WORD_GAP_THRESHOLD_S = 1.000

# LED Brightness Threshold: Set a default for the trackbar
DEFAULT_BRIGHTNESS_THRESHOLD = 100

# UI Color Palette (BGR format) - Matching the Soft Light Aesthetic
BG_GRADIENT_START = (255, 230, 180)  # Sidebar color
BG_GRADIENT_END = (180, 230, 255)
CARD_WHITE = (255, 255, 255)  # Pure white cards
CARD_WHITE_ALPHA = (255, 255, 255)
CARD_ALPHA_VAL = 0.8
HEADER_TEXT = (20, 20, 20)  # Dark text
ACCENT_BLUE = (255, 100, 50)  # Bright Blue/Aqua for highlights
ACCENT_RED = (0, 0, 255)  # Alert color
GRAY_TEXT = (150, 150, 150)
WHITE_TEXT = (255, 255, 255)  # White text (for sidebar)

# Camera Feed Placement (Coordinates for the area where detection happens)
ROI_W, ROI_H = 100, 100
ROI_CENTER_X = 1030
ROI_CENTER_Y = 470
CAMERA_WIDTH = 400
CAMERA_HEIGHT = 200
CAMERA_X = 830
CAMERA_Y = 370

# Morse Code Lookup Table
MORSE_TO_TEXT = {
    '.-': 'A', '-...': 'B', '-.-.': 'C', '-..': 'D', '.': 'E', '..-.': 'F',
    '--.': 'G', '....': 'H', '..': 'I', '.---': 'J', '-.-': 'K', '.-..': 'L',
    '--': 'M', '-.': 'N', '---': 'O', '.--.': 'P', '--.-': 'Q', '.-.': 'R',
    '...': 'S', '-': 'T', '..-': 'U', '...-': 'V', '.--': 'W', '-..-': 'X',
    '-.--': 'Y', '--..': 'Z',
    '.----': '1', '..---': '2', '...--': '3', '....-': '4', '.....': '5',
    '-....': '6', '--...': '7', '---..': '8', '----.': '9', '-----': '0',
}


# Dummy function for trackbar creation
def nothing(x):
    pass


# Helper function for drawing text
def put_text(img, text, org, font, scale, color, thickness):
    cv2.putText(img, text, org, font, scale, color, thickness)


# Function to draw a semi-transparent, rounded card (blending with background)
def draw_rounded_card_alpha(frame, x1, y1, x2, y2, color, alpha=0.8, radius=20):
    overlay = frame.copy()

    # 1. Draw solid shape on the overlay
    cv2.rectangle(overlay, (x1 + radius, y1), (x2 - radius, y2), color, -1)
    cv2.rectangle(overlay, (x1, y1 + radius), (x2, y2 - radius), color, -1)
    cv2.circle(overlay, (x1 + radius, y1 + radius), radius, color, -1)
    cv2.circle(overlay, (x2 - radius, y1 + radius), radius, color, -1)
    cv2.circle(overlay, (x1 + radius, y2 - radius), radius, color, -1)
    cv2.circle(overlay, (x2 - radius, y2 - radius), radius, color, -1)

    # 2. Blend the overlay with the original frame
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)


# --- 2. STATE MACHINE AND DECODING LOGIC ---

def decode_morse(morse_code, morse_table):
    """Converts a single Morse code pattern (e.g., '....') to a letter."""
    return morse_table.get(morse_code, '#')


def main_receiver():
    WINDOW_NAME = 'Optical Morse Decoder'

    # OpenCV setup - Request HD resolution
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    # Create the display window and the threshold trackbar
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    cv2.createTrackbar('Threshold', WINDOW_NAME, DEFAULT_BRIGHTNESS_THRESHOLD, 255, nothing)

    # State variables
    led_state = 0
    current_morse_symbol = ""
    decoded_message = ""

    # Timing variables (in seconds)
    last_state_change_time = time.time()
    current_on_duration = 0.0

    # Variables for UI display and debugging
    live_brightness = 0
    display_symbol_action = "IDLE"
    last_print_time = time.time()
    PRINT_INTERVAL = 0.5

    print("--- DEBUGGING STARTED ---")

    while True:
        brightness_threshold = cv2.getTrackbarPos('Threshold', WINDOW_NAME)
        ret, frame = cap.read()  # Read directly into 'frame'

        if not ret:
            break

        frame_h, frame_w, _ = frame.shape

        # --- UI BACKGROUND BASE (Apply subtle color filter over video feed) ---
        # This keeps the video visible but applies a light, soft filter
        cv2.addWeighted(frame, 0.7, np.full_like(frame, (230, 240, 245)), 0.3, 0, frame)

        # --- 1. DETECTION LOGIC ---

        # Calculate detection ROI coordinates relative to the frame
        detection_roi_x = ROI_CENTER_X - ROI_W // 2
        detection_roi_y = ROI_CENTER_Y - ROI_H // 2

        # Ensure ROI is within bounds for safety
        if detection_roi_y + ROI_H > frame_h or detection_roi_x + ROI_W > frame_w:
            # If the window size changes, this might trigger. Skip frame.
            continue

        # Extract detection ROI from the live frame
        detection_area = frame[detection_roi_y:detection_roi_y + ROI_H, detection_roi_x:detection_roi_x + ROI_W]

        gray_roi = cv2.cvtColor(detection_area, cv2.COLOR_BGR2GRAY)
        max_brightness = np.max(gray_roi)
        live_brightness = int(max_brightness)
        is_led_on = max_brightness > brightness_threshold

        current_time = time.time()
        time_elapsed = current_time - last_state_change_time

        # --- State Machine (LOGIC REMAINS THE SAME) ---

        if led_state == 0:
            if is_led_on:
                off_duration = time_elapsed

                if off_duration >= WORD_GAP_THRESHOLD_S:
                    if current_morse_symbol:
                        decoded_message += decode_morse(current_morse_symbol, MORSE_TO_TEXT)
                        current_morse_symbol = ""
                    if not decoded_message.endswith(" "):
                        decoded_message += " "
                        display_symbol_action = "WORD_SPACE"

                elif off_duration >= LETTER_GAP_THRESHOLD_S:
                    if current_morse_symbol:
                        decoded_message += decode_morse(current_morse_symbol, MORSE_TO_TEXT)
                        current_morse_symbol = ""
                        display_symbol_action = "LETTER_SPACE"

                led_state = 1
                last_state_change_time = current_time
            else:
                if current_time - last_print_time > PRINT_INTERVAL:
                    if time_elapsed > WORD_GAP_THRESHOLD_S and not decoded_message.endswith(" "):
                        if current_morse_symbol:
                            decoded_message += decode_morse(current_morse_symbol, MORSE_TO_TEXT)
                            current_morse_symbol = ""
                        decoded_message += " "
                        display_symbol_action = "WORD_SPACE (Continuous)"
                    last_print_time = current_time

        elif led_state == 1:
            if not is_led_on:
                on_duration = time_elapsed

                if on_duration < DOT_DASH_THRESHOLD_S:
                    current_morse_symbol += "."
                    display_symbol_action = "DOT"
                else:
                    current_morse_symbol += "-"
                    display_symbol_action = "DASH"

                led_state = 0
                last_state_change_time = current_time

        # --- 3. UI RENDERING (Draw cards/text) ---

        # A. Sidebar Panel (Left)
        draw_rounded_card_alpha(frame, 30, 30, 150, frame_h - 30, BG_GRADIENT_START, alpha=1.0, radius=30)

        # Sidebar Icons/Text
        put_text(frame, "RX", (45, 150), cv2.FONT_HERSHEY_COMPLEX, 1.0, ACCENT_BLUE, 2)
        put_text(frame, "DEVICES", (45, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.5, WHITE_TEXT, 1)
        put_text(frame, "SETTINGS", (45, frame_h - 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, WHITE_TEXT, 1)

        # Header and Greeting
        put_text(frame, "Hello, Hackathon Team", (170, 60), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1.2, HEADER_TEXT, 2)
        put_text(frame, "Optical Morse Decoder", (170, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.7, GRAY_TEXT, 1)

        # C. Decoded Message Card (Large, Center Top)
        CARD_X1, CARD_Y1 = 170, 100
        CARD_X2, CARD_Y2 = 600, 350
        draw_rounded_card_alpha(frame, CARD_X1, CARD_Y1, CARD_X2, CARD_Y2, CARD_WHITE_ALPHA, alpha=CARD_ALPHA_VAL)
        put_text(frame, "Decoded Message", (CARD_X1 + 20, CARD_Y1 + 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, HEADER_TEXT, 1)

        decoded_display = decoded_message.strip() if decoded_message.strip() else "..."
        if len(decoded_display) > 30:
            decoded_display = decoded_display[-30:]

        put_text(frame, decoded_display, (CARD_X1 + 20, CARD_Y1 + 100), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1.0,
                 ACCENT_BLUE, 2)
        put_text(frame, "Current Buffer", (CARD_X1 + 20, CARD_Y1 + 200), cv2.FONT_HERSHEY_SIMPLEX, 0.6, GRAY_TEXT, 1)
        put_text(frame, current_morse_symbol, (CARD_X1 + 20, CARD_Y1 + 230), cv2.FONT_HERSHEY_COMPLEX_SMALL, 0.8,
                 HEADER_TEXT, 2)

        # D. Brightness/Threshold Card (Top Right)
        CARD_X1, CARD_Y1 = 610, 100
        CARD_X2, CARD_Y2 = 820, 250
        draw_rounded_card_alpha(frame, CARD_X1, CARD_Y1, CARD_X2, CARD_Y2, CARD_WHITE_ALPHA, alpha=CARD_ALPHA_VAL)
        put_text(frame, "LED BRIGHTNESS", (CARD_X1 + 20, CARD_Y1 + 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, HEADER_TEXT, 1)

        brightness_color = ACCENT_BLUE if is_led_on else ACCENT_RED
        put_text(frame, f"{live_brightness}", (CARD_X1 + 20, CARD_Y1 + 100), cv2.FONT_HERSHEY_COMPLEX, 1.5,
                 brightness_color, 2)
        put_text(frame, f"Threshold: {brightness_threshold}", (CARD_X1 + 20, CARD_Y1 + 130), cv2.FONT_HERSHEY_SIMPLEX,
                 0.6, GRAY_TEXT, 1)

        # E. Detection/Timing Status Cards (Bottom Row)
        CARD_WIDTH = 200
        Y_START = 370

        # Card 1: LAST ACTION
        draw_rounded_card_alpha(frame, 170, Y_START, 170 + CARD_WIDTH, Y_START + 120, CARD_WHITE_ALPHA,
                                alpha=CARD_ALPHA_VAL)
        put_text(frame, "Last Action", (170 + 10, Y_START + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, HEADER_TEXT, 1)
        put_text(frame, display_symbol_action, (170 + 10, Y_START + 70), cv2.FONT_HERSHEY_COMPLEX, 0.8, ACCENT_BLUE, 2)

        # Card 2: ON Duration
        draw_rounded_card_alpha(frame, 170 + CARD_WIDTH + 10, Y_START, 170 + 2 * CARD_WIDTH + 10, Y_START + 120,
                                CARD_WHITE_ALPHA, alpha=CARD_ALPHA_VAL)
        put_text(frame, "ON Duration (s)", (170 + CARD_WIDTH + 20, Y_START + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                 HEADER_TEXT, 1)
        put_text(frame, f"{current_on_duration:.3f}", (170 + CARD_WIDTH + 20, Y_START + 70), cv2.FONT_HERSHEY_COMPLEX,
                 0.8, ACCENT_BLUE, 2)

        # Card 3: GAP DURATION
        draw_rounded_card_alpha(frame, 170 + 2 * CARD_WIDTH + 20, Y_START, 170 + 3 * CARD_WIDTH + 20, Y_START + 120,
                                CARD_WHITE_ALPHA, alpha=CARD_ALPHA_VAL)
        put_text(frame, "OFF Duration (s)", (170 + 2 * CARD_WIDTH + 30, Y_START + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                 HEADER_TEXT, 1)
        put_text(frame, f"{time_elapsed:.3f}", (170 + 2 * CARD_WIDTH + 30, Y_START + 70), cv2.FONT_HERSHEY_COMPLEX, 0.8,
                 ACCENT_BLUE, 2)

        # F. Live Camera Feed (ROI) Card (The base video is already visible beneath the overlay)
        CARD_X1, CARD_Y1 = CAMERA_X, CAMERA_Y
        CARD_X2, CARD_Y2 = CAMERA_X + CAMERA_WIDTH, CAMERA_Y + CAMERA_HEIGHT
        draw_rounded_card_alpha(frame, CARD_X1, CARD_Y1, CARD_X2, CARD_Y2, CARD_WHITE_ALPHA, alpha=CARD_ALPHA_VAL)

        # Draw the TITLE over the card
        put_text(frame, "Live Camera Feed (ROI)", (CARD_X1 + 20, CARD_Y1 + 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                 HEADER_TEXT, 1)

        # --- Draw the green/red ROI box ON TOP of the live feed area ---
        roi_viz_x1 = detection_roi_x
        roi_viz_y1 = detection_roi_y
        roi_viz_x2 = detection_roi_x + ROI_W
        roi_viz_y2 = detection_roi_y + ROI_H

        roi_border_color = (0, 255, 0) if is_led_on else (0, 0, 255)  # Green/Red

        # The ROI box is drawn using the detection coordinates defined in constants.
        cv2.rectangle(frame, (roi_viz_x1, roi_viz_y1), (roi_viz_x2, roi_viz_y2), roi_border_color, 5)

        # Display the result
        cv2.imshow(WINDOW_NAME, frame)

        # --- Keyboard Controls ---
        key = cv2.waitKey(1) & 0xFF

        # 1. Exit on 'q' press
        if key == ord('q'):
            break

        # 2. CLEAR OUTPUT on 'c' press
        if key == ord('c'):
            current_morse_symbol = ""
            decoded_message = ""
            display_symbol_action = "OUTPUT CLEARED"
            last_state_change_time = time.time()  # Reset timing to prevent immediate word space trigger
            print("\n-------------------------------------------------")
            print("--- Output Cleared by User (Key 'c') ---")
            print("-------------------------------------------------\n")

    # Cleanup
    cap.release()
    cv2.destroyAllWindows()

    # Final decode check
    if current_morse_symbol:
        decoded_message += decode_morse(current_morse_symbol, MORSE_TO_TEXT)

    print("\n--- DEBUGGING ENDED ---")
    print("Final Decoded Message:", decoded_message.strip())


if __name__ == '__main__':
    main_receiver()
