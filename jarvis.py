import sys, time, random, datetime, math, os, subprocess, webbrowser, ctypes, threading, requests, asyncio
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QThread
from PyQt5.QtGui import QPainter, QPen, QColor, QFont, QRadialGradient, QBrush, QLinearGradient
import speech_recognition as sr
import edge_tts
import pygame
import pyautogui
from groq import Groq
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# ========== CONFIG ==========
GROQ_API_KEY = "."
TELEGRAM_TOKEN = "APNA_TELEGRAM_TOKEN_YAHAN_LIKHO"
TELEGRAM_CHAT_ID = "6146886118"
INSTAGRAM_USER = "hassbuilds"
TIKTOK_USER = "dawatehaq.q"
YOUTUBE_USER = "Dawatehaq.q"

try:
    client = Groq(api_key=GROQ_API_KEY)
except:
    client = None
try:
    pygame.mixer.init()
except:
    pass

# ========== NODES & CONNECTIONS ==========
NODES = [
    {"id": 0, "label": "PREFRONTAL",    "x": 0.55, "y": 0.15, "color": (255, 68, 68),  "neurons": 140},
    {"id": 1, "label": "MOTOR CORTEX",  "x": 0.72, "y": 0.22, "color": (255, 102, 0),  "neurons": 190},
    {"id": 2, "label": "ASSOCIATION",   "x": 0.68, "y": 0.35, "color": (255, 68, 68),  "neurons": 260},
    {"id": 3, "label": "SENSORY CORTEX","x": 0.65, "y": 0.45, "color": (255, 68, 68),  "neurons": 200},
    {"id": 4, "label": "CONCEPT LAYER", "x": 0.28, "y": 0.38, "color": (255, 170, 0),  "neurons": 160},
    {"id": 5, "label": "FEATURE LAYER", "x": 0.50, "y": 0.55, "color": (170, 68, 255), "neurons": 180},
    {"id": 6, "label": "LANGUAGE",      "x": 0.62, "y": 0.58, "color": (0, 170, 255),  "neurons": 170},
    {"id": 7, "label": "PREDICTIVE",    "x": 0.45, "y": 0.65, "color": (255, 68, 68),  "neurons": 180},
    {"id": 8, "label": "HIPPOCAMPUS",   "x": 0.38, "y": 0.75, "color": (68, 255, 136), "neurons": 160},
    {"id": 9, "label": "CORE",          "x": 0.52, "y": 0.42, "color": (255, 255, 255),"neurons": 320},
]

CONNECTIONS = [
    (0,1),(0,2),(0,9),(1,2),(1,3),(2,3),(2,9),(3,6),(3,9),
    (4,5),(4,9),(4,7),(5,6),(5,7),(5,9),(6,3),(6,9),(7,8),
    (7,9),(8,9),(0,4),(1,6),(2,7),(3,8),(4,6),(5,8),
]

class JarvisSignals(QObject):
    set_mode = pyqtSignal(str)
    minimize_window = pyqtSignal()
    maximize_window = pyqtSignal()
signals = JarvisSignals()

class VoiceWorker(QThread):
    def get_startup_greeting(self):
        try:
            now = datetime.datetime.now()
            hour = now.hour
            if hour < 12: tg = "Good morning"
            elif hour < 17: tg = "Good afternoon"
            else: tg = "Good evening"
            date_str = now.strftime("%B %d, %Y")
            day_str = now.strftime("%A")
            time_str = now.strftime("%I:%M %p")
            try:
                weather = requests.get("https://wttr.in/Sargodha?format=%t+%C", timeout=5).text.strip()
                wp = f"Current weather in Sargodha is {weather}."
            except:
                wp = "I could not fetch the weather right now."
            return f"{tg} Hassan! Welcome back. Today is {day_str}, {date_str}, and the time is {time_str}. {wp}  All systems are online and ready for your commands, sir ."
        except:
            return "Welcome back Hassan. Jarvis is online and ready, sir."

    def run(self):
        greeting = self.get_startup_greeting()
        self.speak(greeting)
        signals.set_mode.emit("LISTENING")
        threading.Thread(target=self.telegram_listener, daemon=True).start()
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=1.0)
            while True:
                try:
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=8)
                    signals.set_mode.emit("THINKING")
                    text = recognizer.recognize_google(audio, language="en-US")
                    if "jarvis" in text.lower():
                        command = text.lower().replace("hey jarvis","").replace("ok jarvis","").replace("jarvis","").strip()
                        if command:
                            self.handle_command(command)
                        else:
                            self.speak("Yes sir, how can I help?")
                    else:
                        signals.set_mode.emit("LISTENING")
                except sr.WaitTimeoutError:
                    signals.set_mode.emit("LISTENING")
                except sr.UnknownValueError:
                    signals.set_mode.emit("LISTENING")
                except Exception as e:
                    print(f"[ERROR]: {e}")
                    signals.set_mode.emit("LISTENING")

    def telegram_listener(self):
        offset = None
        while True:
            try:
                url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
                res = requests.get(url, params={"timeout": 30, "offset": offset}, timeout=35).json()
                for update in res.get("result", []):
                    offset = update["update_id"] + 1
                    msg = update.get("message", {})
                    chat_id = str(msg.get("chat", {}).get("id", ""))
                    text = msg.get("text", "").lower()
                    if chat_id == TELEGRAM_CHAT_ID and text:
                        self.send_telegram("⚡ " + text)
                        self.handle_command(text)
                        self.send_telegram("✅ Done, sir!")
            except Exception as e:
                print(f"[TELEGRAM ERROR]: {e}")
                time.sleep(3)

    def send_telegram(self, message):
        try:
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                         json={"chat_id": TELEGRAM_CHAT_ID, "text": message})
        except: pass

    def speak(self, text):
        try:
            filename = "jarvis_temp_voice.mp3"
            async def gen():
                comm = edge_tts.Communicate(text, voice="en-GB-RyanNeural", rate="+5%", pitch="-10Hz")
                await comm.save(filename)
            asyncio.run(gen())
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.05)
            pygame.mixer.music.unload()
            try: os.remove(filename)
            except: pass
        except Exception as e:
            print(f"[SPEAK ERROR]: {e}")

    def ask_groq(self, question, system=None):
        if not client: return "Groq API key not configured, sir."
        try:
            sys_msg = system or "You are Jarvis, a sophisticated AI assistant. Be extremely brief and polite. Reply in under 2 sentences."
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": sys_msg}, {"role": "user", "content": question}],
                max_tokens=150
            )
            return completion.choices[0].message.content
        except Exception as e:
            return "I encountered an error, sir."

    def get_driver(self):
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    def check_instagram(self):
        try:
            self.speak("Checking Instagram stats, sir.")
            driver = self.get_driver()
            driver.get(f"https://www.instagram.com/{INSTAGRAM_USER}/")
            time.sleep(4)
            followers = following = posts = "unknown"
            for meta in driver.find_elements(By.XPATH, "//meta[@name='description']"):
                content = meta.get_attribute("content")
                if content and "Followers" in content:
                    for part in content.split(","):
                        part = part.strip()
                        if "Followers" in part: followers = part.replace("Followers","").strip()
                        elif "Following" in part: following = part.replace("Following","").strip()
                        elif "Posts" in part: posts = part.replace("Posts","").strip()
            driver.quit()
            return f"Instagram {INSTAGRAM_USER}: {followers} followers, {following} following, {posts} posts."
        except Exception as e:
            return "Could not fetch Instagram stats, sir."

    def check_youtube(self):
        try:
            self.speak("Checking YouTube stats, sir.")
            driver = self.get_driver()
            driver.get(f"https://www.youtube.com/@{YOUTUBE_USER}")
            time.sleep(4)
            subs = "unknown"
            try:
                subs = driver.find_element(By.XPATH, "//yt-formatted-string[@id='subscriber-count']").text
            except: pass
            driver.quit()
            return f"YouTube channel Dawat E Haq has {subs} subscribers, sir."
        except:
            return "Could not fetch YouTube stats, sir."

    def check_tiktok(self):
        try:
            self.speak("Checking TikTok stats, sir.")
            driver = self.get_driver()
            driver.get(f"https://www.tiktok.com/@{TIKTOK_USER}")
            time.sleep(5)
            info = "unknown"
            for meta in driver.find_elements(By.XPATH, "//meta[@name='description']"):
                content = meta.get_attribute("content")
                if content and "followers" in content.lower():
                    info = content[:100]
            driver.quit()
            return f"TikTok {TIKTOK_USER}: {info}"
        except:
            return "Could not fetch TikTok stats, sir."

    def set_reminder(self, command):
        try:
            words = command.split()
            hour = minute = None
            ampm = None
            for i, word in enumerate(words):
                if ":" in word:
                    parts = word.split(":")
                    hour = int(parts[0])
                    minute = int(parts[1])
                elif word.isdigit() and hour is None:
                    hour = int(word)
                if word in ["am", "pm"]:
                    ampm = word
            if hour is None:
                return "Could not understand the time, sir."
            if ampm == "pm" and hour != 12: hour += 12
            elif ampm == "am" and hour == 12: hour = 0
            now = datetime.datetime.now()
            remind_time = now.replace(hour=hour, minute=minute or 0, second=0, microsecond=0)
            if remind_time < now:
                remind_time += datetime.timedelta(days=1)
            diff = (remind_time - now).total_seconds()
            def rt():
                time.sleep(diff)
                self.speak("Sir, time to post on social media!")
                self.send_telegram("🔔 Reminder: Time to post!")
            threading.Thread(target=rt, daemon=True).start()
            return f"Reminder set for {remind_time.strftime('%I:%M %p')}, sir."
        except:
            return "Could not set reminder, sir."

    def handle_command(self, command):
        if not command.strip(): return
        reply = ""

        if "minimize" in command or "hide yourself" in command:
            self.speak("Minimizing, sir.")
            signals.minimize_window.emit()
            return
        elif "show yourself" in command or "come back" in command or "maximize" in command:
            self.speak("Coming back, sir.")
            signals.maximize_window.emit()
            return
        elif "check my instagram" in command:
            reply = self.check_instagram()
        elif "check my youtube" in command:
            reply = self.check_youtube()
        elif "check my tiktok" in command:
            reply = self.check_tiktok()
        elif "check all" in command:
            reply = self.check_instagram() + " " + self.check_youtube() + " " + self.check_tiktok()
        elif "video idea" in command:
            prompt = "Islamic dawah video idea for TikTok" if "islamic" in command or "dawat" in command else "Tech/coding video idea for HassBuilds TikTok"
            reply = self.ask_groq(prompt, "You are a social media expert. Give 1 creative video idea in 2 sentences.")
        elif "write caption" in command or "caption" in command:
            prompt = "Islamic dawah Instagram caption with emojis" if "islamic" in command or "dawat" in command else "Tech coding Instagram caption with emojis for HassBuilds"
            reply = self.ask_groq(prompt, "You are a social media expert. Write an engaging caption.")
        elif "hashtags" in command:
            prompt = "15 hashtags for Islamic dawah content" if "islamic" in command or "dawat" in command else "15 hashtags for coding tech content"
            reply = self.ask_groq(prompt, "You are a social media expert. Give hashtags only.")
        elif "remind me to post" in command:
            reply = self.set_reminder(command)
        elif command.startswith("type "):
            pyautogui.typewrite(command.replace("type ", "", 1) + " ", interval=0.05)
            signals.set_mode.emit("LISTENING")
            return
        elif "press enter" in command: pyautogui.press('enter'); reply = "Enter pressed."
        elif "select all" in command: pyautogui.hotkey('ctrl','a'); reply = "Selected all."
        elif "copy" in command: pyautogui.hotkey('ctrl','c'); reply = "Copied."
        elif "paste" in command: pyautogui.hotkey('ctrl','v'); reply = "Pasted."
        elif "undo" in command: pyautogui.hotkey('ctrl','z'); reply = "Undone."
        elif "time" in command: reply = f"It is {datetime.datetime.now().strftime('%I:%M %p')}, sir."
        elif "date" in command: reply = f"Today is {datetime.datetime.now().strftime('%B %d, %Y')}, sir."
        elif "weather" in command:
            try: reply = f"Weather in Sargodha: {requests.get('https://wttr.in/Sargodha?format=%t+%C', timeout=5).text.strip()}"
            except: reply = "Could not fetch weather, sir."
        elif "battery" in command:
            try:
                import psutil
                b = psutil.sensors_battery()
                reply = f"Battery at {int(b.percent)}%, {'charging' if b.power_plugged else 'not charging'}, sir."
            except: reply = "Could not get battery info."
        elif "open chrome" in command: os.system("start chrome"); reply = "Opening Chrome."
        elif "open youtube" in command: webbrowser.open(f"https://www.youtube.com/@{YOUTUBE_USER}"); reply = "Opening YouTube."
        elif "open instagram" in command: webbrowser.open(f"https://www.instagram.com/{INSTAGRAM_USER}"); reply = "Opening Instagram."
        elif "open tiktok" in command: webbrowser.open(f"https://www.tiktok.com/@{TIKTOK_USER}"); reply = "Opening TikTok."
        elif "open claude" in command: webbrowser.open("https://claude.ai"); reply = "Opening Claude."
        elif "open chatgpt" in command: webbrowser.open("https://chatgpt.com"); reply = "Opening ChatGPT."
        elif "open notepad" in command: os.system("start notepad"); reply = "Opening Notepad."
        elif "open calculator" in command: os.system("start calc"); reply = "Opening Calculator."
        elif "open vs code" in command: os.system("start code"); reply = "Opening VS Code."
        elif "open task manager" in command: os.system("start taskmgr"); reply = "Opening Task Manager."
        elif "open file explorer" in command: os.system("start explorer"); reply = "Opening File Explorer."
        elif "close chrome" in command: os.system("taskkill /f /im chrome.exe"); reply = "Closing Chrome."
        elif "close tab" in command: pyautogui.hotkey('ctrl','w'); reply = "Tab closed."
        elif "switch tab" in command: pyautogui.hotkey('ctrl','tab'); reply = "Tab switched."
        elif "search google for" in command:
            q = command.replace("search google for","").strip()
            webbrowser.open(f"https://www.google.com/search?q={q}"); reply = f"Searching {q}."
        elif "play" in command and "on youtube" in command:
            song = command.replace("play","").replace("on youtube","").strip()
            webbrowser.open(f"https://www.youtube.com/results?search_query={song}"); reply = f"Playing {song}."
        elif "volume up" in command:
            for _ in range(5): pyautogui.press("volumeup"); reply = "Volume up."
        elif "volume down" in command:
            for _ in range(5): pyautogui.press("volumedown"); reply = "Volume down."
        elif "mute" in command: pyautogui.press("volumemute"); reply = "Muted."
        elif "lock" in command and ("pc" in command or "computer" in command):
            self.speak("Locking, sir.")
            ctypes.windll.user32.LockWorkStation(); return
        elif "screenshot" in command:
            p = os.path.join(os.path.expanduser("~"), "Pictures", f"Jarvis_{int(time.time())}.png")
            pyautogui.screenshot(p); reply = "Screenshot saved."
        elif "sleep" in command and "computer" in command:
            self.speak("Sleeping, sir.")
            os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0"); return
        elif "shutdown" in command or "shut down" in command:
            self.speak("Shutting down in 10 seconds, sir.")
            os.system("shutdown /s /t 10"); sys.exit()
        elif "restart" in command or "reboot" in command:
            self.speak("Restarting, sir.")
            os.system("shutdown /r /t 0"); sys.exit()
        elif "cancel shutdown" in command:
            os.system("shutdown /a"); reply = "Shutdown cancelled."
        elif "bye" in command or "allah hafiz" in command or "exit" in command:
            self.speak("Goodbye Hassan. Allah Hafiz!")
            sys.exit()
        else:
            signals.set_mode.emit("THINKING")
            reply = self.ask_groq(command)

        signals.set_mode.emit("SPEAKING")
        self.speak(reply)
        signals.set_mode.emit("LISTENING")

# ========== NEURAL HUD ==========
class JarvisHUD(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JARVIS")
        self.showFullScreen()
        self.setStyleSheet("background: #00000a;")

        self.time_val = 0.0
        self.mode = "BOOTING"
        self.node_firing = [0.0] * len(NODES)
        self.spin_angle = 0.0

        # Particles
        self.particles = []
        for _ in range(100):
            conn = random.choice(CONNECTIONS)
            self.particles.append({
                "conn": conn,
                "progress": random.uniform(0, 1),
                "speed": random.uniform(0.0008, 0.003),
                "size": random.uniform(1, 3),
                "color": NODES[conn[0]]["color"],
            })

        # Stars
        self.stars = [{"x": random.random(), "y": random.random(),
                       "size": random.uniform(0.3, 1.8),
                       "twinkle": random.uniform(0, math.pi * 2),
                       "speed": random.uniform(0.005, 0.02)} for _ in range(250)]

        signals.set_mode.connect(self.on_mode_change)
        signals.minimize_window.connect(self.showMinimized)
        signals.maximize_window.connect(self.showFullScreen)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(16)

        self.worker = VoiceWorker()
        self.worker.start()

    def on_mode_change(self, mode):
        self.mode = mode

    def update_frame(self):
        self.time_val += 0.016
        self.spin_angle = (self.spin_angle + 1.0) % 360

        # Update firing
        speed = 0.05 if self.mode == "SPEAKING" else 0.08 if self.mode == "THINKING" else 0.02
        for i in range(len(self.node_firing)):
            if random.random() < speed:
                self.node_firing[i] = 1.0
            else:
                self.node_firing[i] = max(0.0, self.node_firing[i] - 0.018)

        # Update particles
        pspeed = 2.5 if self.mode == "SPEAKING" else 1.8 if self.mode == "THINKING" else 1.0
        for p in self.particles:
            p["progress"] += p["speed"] * pspeed
            if p["progress"] > 1:
                p["progress"] = 0
                conn = random.choice(CONNECTIONS)
                p["conn"] = conn
                p["color"] = NODES[conn[0]]["color"]
                p["speed"] = random.uniform(0.0008, 0.003)
                p["size"] = random.uniform(1, 3)

        # Update stars
        for star in self.stars:
            star["twinkle"] += star["speed"]

        self.update()

    def get_mode_color(self):
        if self.mode == "THINKING": return QColor(255, 204, 0)
        elif self.mode == "SPEAKING": return QColor(0, 255, 136)
        else: return QColor(0, 170, 255)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.worker.terminate()
            QApplication.quit()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        W = self.width()
        H = self.height()
        mc = self.get_mode_color()

        # Background
        painter.fillRect(0, 0, W, H, QColor(0, 0, 10))

        # Nebula center glow
        cx_core = int(NODES[9]["x"] * W)
        cy_core = int(NODES[9]["y"] * H)
        nebula = QRadialGradient(cx_core, cy_core, int(W * 0.35))
        nebula.setColorAt(0.0, QColor(30, 0, 80, 35))
        nebula.setColorAt(0.5, QColor(0, 20, 60, 20))
        nebula.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(nebula))
        painter.setPen(Qt.NoPen)
        painter.drawRect(0, 0, W, H)

        # Stars
        for star in self.stars:
            alpha = int((0.2 + math.sin(star["twinkle"]) * 0.25) * 255)
            painter.setBrush(QBrush(QColor(255, 255, 255, max(0, alpha))))
            painter.setPen(Qt.NoPen)
            x = int(star["x"] * W)
            y = int(star["y"] * H)
            r = star["size"]
            painter.drawEllipse(int(x-r), int(y-r), int(r*2), int(r*2))

        # Connections
        for a, b in CONNECTIONS:
            na, nb = NODES[a], NODES[b]
            ax, ay = int(na["x"] * W), int(na["y"] * H)
            bx, by = int(nb["x"] * W), int(nb["y"] * H)
            firing = max(self.node_firing[a], self.node_firing[b])
            alpha = int((0.06 + firing * 0.35) * 255)
            ca, cb = QColor(*na["color"], alpha), QColor(*nb["color"], alpha)
            grad = QLinearGradient(ax, ay, bx, by)
            grad.setColorAt(0, ca)
            grad.setColorAt(1, cb)
            pen = QPen(QBrush(grad), 0.4 + firing * 2)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawLine(ax, ay, bx, by)

        # Particles
        for p in self.particles:
            a, b = p["conn"]
            na, nb = NODES[a], NODES[b]
            px = int((na["x"] + (nb["x"] - na["x"]) * p["progress"]) * W)
            py = int((na["y"] + (nb["y"] - na["y"]) * p["progress"]) * H)
            r = p["size"]
            c = QColor(*p["color"])

            glow = QRadialGradient(px, py, int(r * 6))
            gc = QColor(c)
            gc.setAlpha(180)
            glow.setColorAt(0, gc)
            gc2 = QColor(c)
            gc2.setAlpha(0)
            glow.setColorAt(1, gc2)
            painter.setBrush(QBrush(glow))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(int(px - r*6), int(py - r*6), int(r*12), int(r*12))

            painter.setBrush(QBrush(QColor(255, 255, 255, 220)))
            painter.drawEllipse(int(px - r), int(py - r), int(r*2), int(r*2))

        # Nodes
        for i, node in enumerate(NODES):
            nx = int(node["x"] * W)
            ny = int(node["y"] * H)
            firing = self.node_firing[i]
            pulse = math.sin(self.time_val * 2 + i * 0.8) * 0.3 + 0.7
            base_r = 22 if node["id"] == 9 else 11
            r = base_r + firing * 9 + pulse * 4

            c = QColor(*node["color"])

            # Multi glow
            for g in range(4, 0, -1):
                alpha = int((0.1 / g + firing * 0.08) * 255)
                glow_r = int(r * g * 1.6)
                gr = QRadialGradient(nx, ny, glow_r)
                gc = QColor(c); gc.setAlpha(min(255, alpha))
                gr.setColorAt(0, gc)
                gc2 = QColor(c); gc2.setAlpha(0)
                gr.setColorAt(1, gc2)
                painter.setBrush(QBrush(gr))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(nx - glow_r, ny - glow_r, glow_r*2, glow_r*2)

            # Core fill
            core_gr = QRadialGradient(nx, ny, int(r))
            core_gr.setColorAt(0, QColor(255, 255, 255))
            core_gr.setColorAt(0.25, c)
            c33 = QColor(c); c33.setAlpha(51)
            core_gr.setColorAt(1, c33)
            painter.setBrush(QBrush(core_gr))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(int(nx-r), int(ny-r), int(r*2), int(r*2))

            # Ring
            ring_c = QColor(c)
            ring_c.setAlpha(int((0.35 + firing * 0.65) * 255))
            painter.setPen(QPen(ring_c, 1.2))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(int(nx-r-4), int(ny-r-4), int((r+4)*2), int((r+4)*2))

            # Spinning rings for core
            if node["id"] == 9:
                painter.save()
                painter.translate(nx, ny)
                painter.rotate(self.spin_angle)
                spin_c = QColor(255, 255, 255, 80)
                painter.setPen(QPen(spin_c, 1.5))
                painter.drawArc(int(-r-14), int(-r-14), int((r+14)*2), int((r+14)*2), 0, 216*16)
                painter.rotate(180)
                spin_c2 = QColor(255, 255, 255, 40)
                painter.setPen(QPen(spin_c2, 1))
                painter.drawArc(int(-r-14), int(-r-14), int((r+14)*2), int((r+14)*2), 0, 90*16)
                painter.restore()

                # Mode pulse ring
                mp = math.sin(self.time_val * (6 if self.mode == "SPEAKING" else 4 if self.mode == "THINKING" else 2)) * 0.5 + 0.5
                pulse_r = int(r + 25 + mp * 20)
                pulse_c = QColor(mc)
                pulse_c.setAlpha(int((0.15 + mp * 0.3) * 255))
                painter.setPen(QPen(pulse_c, 2))
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(nx - pulse_r, ny - pulse_r, pulse_r*2, pulse_r*2)

                # Mode text below core
                mode_text = "● LISTENING" if self.mode == "LISTENING" else "◆ THINKING" if self.mode == "THINKING" else "▶ SPEAKING"
                painter.setPen(mc)
                painter.setFont(QFont("Courier New", 10, QFont.Bold))
                fm = painter.fontMetrics()
                tw = fm.width(mode_text)
                painter.drawText(nx - tw//2, ny + int(r) + 30, mode_text)

            # Label box for non-core nodes
            else:
                label = node["label"]
                sub = f"{node['neurons']} neurons · {firing*100:.1f}%"
                painter.setFont(QFont("Courier New", 7, QFont.Bold))
                fm = painter.fontMetrics()
                lw = fm.width(label)
                sw = fm.width(sub)
                bw = max(lw, sw) + 16
                bh = 30
                bx = int(nx + r + 8)
                by = int(ny - 15)

                painter.setBrush(QBrush(QColor(0, 0, 8, 210)))
                bc = QColor(c); bc.setAlpha(85)
                painter.setPen(QPen(bc, 1))
                painter.drawRoundedRect(bx, by, bw, bh, 3, 3)

                painter.setBrush(QBrush(c))
                painter.setPen(Qt.NoPen)
                painter.drawRect(bx, by, bw, 2)

                painter.setPen(c)
                painter.setFont(QFont("Courier New", 7, QFont.Bold))
                painter.drawText(bx + 7, by + 13, label)
                sub_c = QColor(255, 255, 255, 100)
                painter.setPen(sub_c)
                painter.setFont(QFont("Courier New", 6))
                painter.drawText(bx + 7, by + 24, sub)

        # Top HUD bar
        painter.fillRect(0, 0, W, 45, QColor(0, 0, 10, 160))
        painter.setPen(QColor(0, 150, 255, 30))
        painter.drawLine(0, 45, W, 45)
        painter.setPen(QColor(0, 170, 255))
        painter.setFont(QFont("Courier New", 13, QFont.Bold))
        painter.drawText(24, 28, "J.A.R.V.I.S")
        painter.setPen(QColor(0, 150, 255, 100))
        painter.setFont(QFont("Courier New", 8))
        painter.drawText(24, 40, "NEURAL INTERFACE v2.0")
        painter.setPen(mc)
        painter.setFont(QFont("Courier New", 10, QFont.Bold))
        mode_text = "● LISTENING" if self.mode == "LISTENING" else "◆ THINKING" if self.mode == "THINKING" else "▶ SPEAKING"
        painter.drawText(W//2 - 60, 28, mode_text)
        painter.setPen(QColor(255, 255, 255, 140))
        painter.setFont(QFont("Courier New", 11))
        t_str = datetime.datetime.now().strftime("%I:%M:%S %p")
        painter.drawText(W - 160, 25, t_str)
        painter.setPen(QColor(0, 150, 255, 90))
        painter.setFont(QFont("Courier New", 8))
        painter.drawText(W - 160, 40, "HASSAN · SARGODHA")

        # Bottom HUD bar
        painter.fillRect(0, H-35, W, 35, QColor(0, 0, 10, 160))
        painter.setPen(QColor(0, 150, 255, 30))
        painter.drawLine(0, H-35, W, H-35)
        active = sum(1 for f in self.node_firing if f > 0.1)
        avg_firing = sum(self.node_firing) / len(self.node_firing) * 100
        painter.setPen(QColor(0, 150, 255, 115))
        painter.setFont(QFont("Courier New", 8))
        painter.drawText(24, H-12, f"NODES: {active}/{len(NODES)}  ·  FIRING: {avg_firing:.1f}%  ·  PARTICLES: 100")
        painter.drawText(W - 220, H-12, "DAWAT E HAQ  ·  HASSBUILDS")

        painter.end()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = JarvisHUD()
    sys.exit(app.exec_())