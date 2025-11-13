# Optical Morse Code Decoder (Python + OpenCV + PyQt5)

This project implements a real-time **Optical Morse Code Decoder** that reads LED blinks through a webcam, classifies DOT and DASH timings, and converts the optical signal into readable English text.  
A modern PyQt5 GUI displays the video feed, ROI, brightness, threshold slider, and decoded output.

---

<h4>  Features</h4>

- Live webcam feed with central ROI  
- LED brightness detection using OpenCV  
- Adjustable threshold slider  
- DOT / DASH classification using timing  
  - DOT: < 0.4 seconds  
  - DASH: ≥ 0.4 seconds  
- Letter gap and word gap detection  
- Modern, dark-themed PyQt5 UI  
- Start / Stop / Reset controls  
- Real-time decoded message display  
- Supports A–Z and 0–9 Morse codes  

---

<h4> How It Works </h4>

1. Webcam captures the LED blinking pattern  
2. A Region of Interest (ROI) is extracted  
3. Maximum brightness in the ROI determines LED ON/OFF  
4. Timing logic is applied:  
   - ON duration → DOT or DASH  
   - OFF duration → symbol/letter/word separation  
5. Morse code is built and decoded using a lookup table  
6. GUI updates all results live  

---

<h4> Morse Timing Parameters </h4>

| Type | Time |
|------|------|
| DOT | ~200 ms |
| DASH | ~600 ms |
| DOT/DASH threshold | **0.4 s** |
| Letter gap | **0.5 s** |
| Word gap | **1.0 s** |

