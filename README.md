# ShieldHer - Safety Check-in Application

## Project Overview

ShieldHer is a desktop safety check-in application designed to help users assess their safety in real-time and connect with trusted contacts when needed. The app runs on your computer and uses smart analysis to evaluate potential risks based on your current situation.

---

## How It Works

### Quick Summary for Friends

1. **Login/Sign Up** – Create an account with your name, phone number, and add up to 3 trusted contacts (friends or family you'd contact in an emergency)

2. **Answer Safety Questions** – The app asks simple questions about your current situation:
   - Are you in an isolated area?
   - Is there poor lighting?
   - Is it late at night?
   - Do you feel like someone is following you?
   - Is your phone battery low (below 20%)?
   - Are you in a crowded but non-protective environment?

3. **Set Confidence Level** – Rate how confident you feel about your safety (1-5 scale)

4. **Set a Timer** – Set a check-in timer (10 seconds to 10 minutes). If you don't reset it before it expires, the app marks it as a risk factor.

5. **Get Your Location** – The app can fetch your approximate location using your internet connection, or use your browser's GPS for precise coordinates.

6. **Analyze** – Click "Analyze Safety" and the app calculates your risk level and shows personalized safety advice.

7. **View Results** – See your risk score (0-100), risk level (low/medium/high/critical), trend over time, and specific recommendations.

8. **Send SOS (Optional)** – If the risk is high (score ≥50), the app generates an SOS draft message. You can send this via email to your trusted contacts.

---

## Core Technology

### Two-Part System

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Frontend App** | Python + Tkinter | User interface, data collection, location services |
| **Risk Engine** | C Program | Fast analysis of safety factors |

The Python app collects user input and passes it to the C analyzer (a compiled binary) for risk calculation. The C program uses a weighted scoring system to evaluate risk and provides actionable advice.

---

## Features

✅ **User Authentication** – Secure login/signup with password hashing  
✅ **Smart Risk Scoring** – Weighted algorithm analyzes multiple factors  
✅ **Location Tracking** – Approximate (IP) and precise (GPS) location support  
✅ **Timer Check-in** – Countdown safety timer with expiration alerts  
✅ **History Tracking** – View trends in your safety scores over time  
✅ **Trust Network** – Save up to 3 trusted contacts for emergencies  
✅ **SOS Draft Generation** – Pre-written emergency message template  
✅ **Email Notifications** – Send alerts via SMTP or mailto link  
✅ **Night Warning** – Automatic alert when using at late hours  
✅ **Offline Capable** – Works without internet (except location features)

---

## Tech Stack (Non-Technical View)

| What It Does | How It Works |
|--------------|--------------|
| **Window Interface** | Creates screens for login, safety questions, and results using a built-in desktop toolkit |
| **User Accounts** | Saves your profile and contacts in simple text files on your computer |
| **Location Finding** | Uses the internet to find your city (approximate) or browser GPS for exact coordinates |
| **Risk Calculator** | A small fast program that adds up points from your answers and calculates how risky your situation is |
| **Timer System** | Counts down from your chosen time; if it hits zero you get a warning |
| **Email Alerts** | Opens your email app with a pre-written message to your emergency contacts |
| **History Tracking** | Remembers your past safety scores and shows if you're trending safer or at higher risk |

---

## Risk Scoring (Simplified)

The app calculates risk on a 0-100 scale:

- **0-25**: Low Risk (✓ Safe)
- **26-50**: Medium Risk (⚠️ Caution)
- **51-75**: High Risk (🔴 Warning)
- **76-100**: Critical Risk (🚨 Emergency)

**Factor Weights:**
- Someone following you: +25 points
- Isolated area: +20 points
- Late night: +20 points
- Poor lighting: +15 points
- Crowded (non-protective): +15 points
- Low battery: +10 points
- Timer expired: +20 points
- Short timer (rushing): +5-15 points

Your confidence level adjusts the score:
- **Very Uncertain (1)**: Increases risk by 150%
- **Uncertain (2)**: Increases risk by 125%
- **Moderate (3)**: No adjustment
- **Confident (4)**: Reduces risk by 15%
- **Very Confident (5)**: Reduces risk by 30%

---

## Installation & Running

### Requirements
- Python 3.x installed
- C compiler (gcc/clang) for the analyzer

### Quick Start

```bash
# Build the C analyzer
make build

# Run the app
python app.py
# OR on macOS/Linux
./run_mac.sh
```

On Windows, run `run_windows.bat` (one-click: builds `analyzer.exe`, verifies Python/tkinter, launches the app), or compile with MinGW and run `python app.py` manually.

---

## File Structure

```
shieldher/
├── app.py              # Main Python application
├── analyzer.c          # Risk calculation engine (C source)
├── analyzer            # Compiled risk analyzer (macOS/Linux)
├── run_mac.sh          # One-click launcher (macOS/Linux)
├── run_windows.bat     # One-click launcher (Windows)
├── Makefile            # Build file for macOS/Linux
├── data/               # User data storage
│   ├── users.json      # User accounts
│   ├── contacts.txt    # Default trusted contacts
│   ├── safe_places.txt # Safe locations list
│   └── users/          # Per-user data folders
│       └── [username]/
│           ├── contacts.txt    # User's trusted contacts
│           ├── input.txt       # Current safety assessment
│           ├── output.txt      # Analysis results
│           ├── history.csv     # Risk score history
│           └── sos_draft.txt   # Emergency message draft
```

---

## Libraries Used

### Python (for the interface)
- **tkinter** – Creates windows, buttons, text boxes, and all visual elements
- **json** – Saves and reads user account information
- **hashlib** – Securely encrypts passwords
- **datetime** – Tracks current time for safety warnings
- **threading** – Runs the timer in the background without freezing the app
- **urllib** – Fetches location from internet
- **webbrowser** – Opens browser for GPS location
- **smtplib** – Sends emails through email servers
- **http.server** – Creates a temporary local server for GPS data

### C (for the calculator)
- **stdio.h** – Reads input files and writes results
- **stdlib.h** – Standard functions
- **string.h** – Text processing
- **time.h** – Timestamps for history

---

## Privacy & Security

✅ **Local Data Storage** – All data stays on your computer, no cloud servers  
✅ **Password Hashing** – Passwords are encrypted before storage  
✅ **No Tracking** – Location data only fetched when you request it  
✅ **Open Source** – You can inspect all code  
✅ **No Account Required for Demo** – You can test without creating an account  

---

## Example Use Case

1. Sarah walks home from the library at 11 PM (late night - +20 points)
2. She's on a quiet street with few people (isolated - +20 points)
3. The street lights are dim (poor lighting - +15 points)
4. She feels 60% confident about her safety (confidence level 2 - +25% multiplier)
5. Base score: 55 points → Adjusted: 69 points → **HIGH RISK**

The app would advise her to "Move to a well-lit, populated area" and generate an SOS draft message.

---

## Future Improvements (Ideas)

- Mobile app version (iOS/Android)
- SMS alerts via Twilio API
- Integration with campus security systems
- Real-time GPS tracking during walks
- Machine learning to predict high-risk areas
- Dark mode UI theme
- Multi-language support

---

## For Your Presentation

**Key Points to Mention:**
1. **Problem** – Personal safety is critical, especially for students walking alone at night
2. **Solution** – Quick check-in app that assesses risk and connects to trusted contacts
3. **Technology** – Hybrid Python+Tkinter (frontend) + C (fast risk calculation)
4. **Security** – Password hashing, local storage, privacy-first design
5. **Practical Value** – Automatic SOS draft, timer check-in, history tracking

**Demo Script:**
1. Show login → signup screen
2. Create account → fill in 3 trusted contacts
3. Login → answer safety questions
4. Set confidence → set timer → click Analyze
5. Show risk result + advice
6. View SOS draft → show how email would work

---

## Technical Quick Reference

| Component | Lines of Code | Language | Primary Technology |
|-----------|---------------|----------|-------------------|
| Frontend App | 1,540 | Python 3 | Tkinter GUI Toolkit |
| Risk Engine | 432 | C | Standard C Library |
| **Total** | **1,972** | **Python + C** | **Desktop Application** |

---

## How Libraries Are Used

### Python's Role (app.py)

**Tkinter** is like a digital LEGO set for building windows. It creates:
- The login screen with username/password boxes
- The main safety dashboard with checkboxes and sliders
- The results display area

**Hashlib** is a security tool that scrambles passwords so they can't be reversed. Like turning "mypassword123" into a random string like "a7f3b2c9d1..." – even the app can't see your original password.

**Threading** is like having a stopwatch running in the background while you can still use the app. The timer counts down without freezing your screen.

**urllib** connects to free internet services that know approximately where your internet connection is located, giving you a rough city-level location without needing GPS.

**http.server + webbrowser** work together: the app opens your browser to ask for precise GPS location, then runs a small temporary server on your computer to receive those coordinates back.

### C's Role (analyzer.c)

Think of the C program as a calculator that adds up risk points:

1. **Reads** your answers from a text file
2. **Calculates** the risk score by adding weighted points
3. **Checks** your past scores to see if you're trending safer or riskier
4. **Generates** specific advice based on which boxes you checked
5. **Writes** results to a text file the Python app can show you

The C program is fast because it's "closer to the metal" – it runs as raw machine code, making calculations instantly without the overhead of Python's interpretation layer.

---

## Why This Approach?

### Python for Interface
- ✅ Easy to write and understand
- ✅ Built-in GUI tools (Tkinter)
- ✅ Rich library ecosystem for networking, email, etc.
- ✅ Cross-platform (works on Windows, Mac, Linux)

### C for Risk Calculation
- ✅ Lightning-fast execution (compiled to machine code)
- ✅ Perfect for mathematical calculations
- ✅ Minimal dependencies (.exe or binary runs anywhere)
- ✅ Separate from interface = easier to test independently

---

## Summary for Non-Technical Audience

**ShieldHer is like a digital safety buddy.**

Imagine you're walking alone and feel uneasy. You open the app, check a few boxes about your situation, and it tells you "Hey, your risk level is HIGH because it's late, you're alone, and the lighting is poor. Here's what you should do: move to a well-lit area and call a friend."

It's not connected to any servers – everything stays on your laptop. It just reads your inputs, calculates risk like a simple math equation, and shows you results.

The "calculator" part (C program) is like having a mini-robot that only knows how to add up risk points. The "window" part (Python app) is like a friendly translator that asks you questions and shows the robot's answers in plain English.

**In your presentation, say:**
> "We built a safety check-in app. The front end uses Python with Tkinter for the interface, and we wrote a custom risk analysis engine in C for fast calculations. When users input their situation, the C program calculates a weighted risk score and provides specific safety advice. It runs locally for privacy, uses password hashing for security, and can send SOS emails to trusted contacts."

---

## Contact & Credits

**Project:** ShieldHer - Safety Check-in Application  
**Type:** Minor Project  
**Language:** Python 3 + C  
**GUI Framework:** Tkinter  
**License:** Open Source  

---

*This document is intended as a project overview for presentations and non-technical audiences.*
## Project Contribution

This was developed as a collaborative academic project. My primary responsibility was the C-based risk-analysis engine, including risk scoring, timer and confidence adjustments, risk classification, trend analysis, advice generation, and SOS generation. I also contributed to integration, debugging, and other application functionality as needed.

AI-assisted development tools were used during implementation; code was tested and refined as part of development.
