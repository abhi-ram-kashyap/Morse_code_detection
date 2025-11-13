#include <Arduino.h>

// --- Timing Definitions (Adjust as needed) ---
// Based on the standard 1:3:1:3:7 timing ratio
int dotTime = 200; // The base unit of time (dot duration/inter-element gap)
int dashTime = 3 * dotTime; // Dash duration (3 units)

// Inter-element gap (gap between dot/dash within a letter) is implicitly 1 unit (dotTime)
// Inter-letter gap (3 units total, so 2 more units after the inter-element gap)
int interLetterPause = 2 * dotTime; 
// Inter-word gap (7 units total, so 6 more units after the inter-element gap)
int interWordPause = 6 * dotTime; 

// --- Morse Code Dictionary ---
// Using a function for simplicity, but consider an array for memory efficiency in larger projects.
String morseTable(char c) {
  switch (c) {
    case 'A': return ".-"; case 'B': return "-...";
    case 'C': return "-.-."; case 'D': return "-..";
    case 'E': return "."; case 'F': return "..-.";
    case 'G': return "--."; case 'H': return "....";
    case 'I': return ".."; case 'J': return ".---";
    case 'K': return "-.-"; case 'L': return ".-..";
    case 'M': return "--"; case 'N': return "-.";
    case 'O': return "---"; case 'P': return ".--.";
    case 'Q': return "--.-"; case 'R': return ".-.";
    case 'S': return "..."; case 'T': return "-";
    case 'U': return "..-"; case 'V': return "...-";
    case 'W': return ".--"; case 'X': return "-..-";
    case 'Y': return "-.--"; case 'Z': return "--..";

    case '0': return "-----"; case '1': return ".----";
    case '2': return "..---"; case '3': return "...--";
    case '4': return "....-"; case '5': return ".....";
    case '6': return "-...."; case '7': return "--...";
    case '8': return "---.."; case '9': return "----.";
    // Other characters (Punctuation) can be added here if needed
  }
  return ""; // Return empty string for unsupported characters
}

// --- LED Blinking Functions ---

void sendSymbol(char s) {
  digitalWrite(13, HIGH);
  // Ternary operator: if s is '.', use dotTime, otherwise use dashTime
  delay(s == '.' ? dotTime : dashTime); 
  
  digitalWrite(13, LOW);
  // Inter-element gap (1 unit)
  delay(dotTime); 
}

void sendLetter(String morseCode) {
  for (char s : morseCode) {
    sendSymbol(s);
  }
  // Inter-letter gap (3 units total, 1 unit used by the last sendSymbol's delay, so add 2 more)
  delay(interLetterPause); 
}

// --- Setup ---

void setup() {
  pinMode(13, OUTPUT); // Built-in LED
  Serial.begin(9600);
  Serial.println("--- Morse Code Transmitter Ready ---");
  Serial.println("Type your message below and press Send.");
}

// --- Main Loop for Serial Input ---

void loop() {
  // 1. Check if the user has sent data in the Serial Monitor
  if (Serial.available() > 0) {
    // 2. Read the incoming message string until a newline character is received
    String message = Serial.readStringUntil('\n'); 
    message.trim(); // Remove any leading or trailing whitespace
    
    if (message.length() > 0) {
      Serial.println("\nTransmitting: " + message + "");
      Serial.print("Code: ");
      
      // 3. Process the message character by character
      for (char c : message) {
        char up = toupper(c); // Convert to uppercase for lookup
        
        // Handle Space (Word Gap)
        if (c == ' ') { 
          // Inter-word gap (7 units total, 1 unit used by the last sendSymbol or letter gap, so add 6 more)
          delay(interWordPause); 
          Serial.print(" / "); // Print a space marker for clarity
          continue; 
        } 

        // Handle Letters/Numbers
        String morse = morseTable(up);
        
        if (morse.length() > 0) {
          Serial.print(up);
          Serial.print(":");
          Serial.print(morse);
          Serial.print(" ");
          
          sendLetter(morse); // Send the blinking sequence
        }
      }
      
      Serial.println("\n--- Transmission Complete. Type a new message. ---");
    }
  }
  // The loop runs very fast, constantly checking for serial data
}
