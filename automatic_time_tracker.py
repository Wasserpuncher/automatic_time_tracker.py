import time
import threading
import tkinter as tk
from tkinter import messagebox, simpledialog
import os
import json
import cv2
import numpy as np
from datetime import datetime, timedelta
from firebase import Firebase  # Firebase Python SDK
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Globale Variablen
tasks = {}
current_task = None
running = True
firebase = None
db = None

# Firebase Konfiguration (Beispiel - bitte durch eigene Firebase-Konfiguration ersetzen)
firebase_config = {
    'apiKey': 'your_api_key',
    'authDomain': 'your_auth_domain',
    'databaseURL': 'your_database_url',
    'projectId': 'your_project_id',
    'storageBucket': 'your_storage_bucket',
    'messagingSenderId': 'your_messaging_sender_id',
    'appId': 'your_app_id',
    'measurementId': 'your_measurement_id'
}

# Datei für die Speicherung der Aufgaben und Arbeitszeiten
data_file = 'tasks.json'

# Laden der gespeicherten Daten, falls vorhanden
if os.path.exists(data_file):
    with open(data_file, 'r') as f:
        tasks = json.load(f)

# Firebase-Initialisierung
def initialize_firebase():
    global firebase, db
    firebase = Firebase(firebase_config)
    db = firebase.database()

# Funktion zur automatischen Aktivitätserkennung und Zeitverfolgung
def track_activities():
    global current_task, running
    
    while running:
        if current_task:
            tasks[current_task] += 1  # Simuliert 1 Sekunde Arbeit
            print(f"Aktuelle Aufgabe: {current_task}, Zeit: {tasks[current_task]} Sekunden")
        
        time.sleep(1)  # Simuliert 1 Sekunde

# Funktion zur manuellen Eingabe von Aufgaben
def manual_input_task():
    global current_task, tasks, running
    
    while running:
        print("\nMöchten Sie eine neue Aufgabe hinzufügen oder die aktuelle ändern?")
        choice = input("Geben Sie 'hinzufügen' oder 'ändern' ein (oder 'beenden' zum Beenden): ").lower()
        
        if choice == 'beenden':
            running = False
            break
        elif choice == 'hinzufügen':
            new_task_name = input("Geben Sie den Namen der neuen Aufgabe ein: ")
            tasks[new_task_name] = 0
            print(f"Neue Aufgabe '{new_task_name}' hinzugefügt.")
            save_tasks()
        elif choice == 'ändern':
            print("Aktuelle Aufgaben:")
            for idx, task in enumerate(tasks.keys(), start=1):
                print(f"{idx}. {task}")
            
            try:
                idx = int(input("Geben Sie die Nummer der Aufgabe ein, die Sie ändern möchten: ")) - 1
                if idx >= 0 and idx < len(tasks):
                    selected_task = list(tasks.keys())[idx]
                    new_time = int(input(f"Geben Sie die neue Zeit für '{selected_task}' ein (in Sekunden): "))
                    tasks[selected_task] = new_time
                    print(f"Aufgabe '{selected_task}' geändert. Neue Zeit: {new_time} Sekunden")
                    save_tasks()
                else:
                    print("Ungültige Auswahl.")
            except ValueError:
                print("Ungültige Eingabe. Bitte geben Sie eine Nummer ein.")
    
    save_tasks()

# Funktion zur Speicherung der Aufgaben in einer JSON-Datei
def save_tasks():
    with open(data_file, 'w') as f:
        json.dump(tasks, f, indent=4)

# Funktion zur Aktivitätserkennung mit OpenCV
def activity_recognition():
    global current_task
    
    cap = cv2.VideoCapture(0)
    while running:
        ret, frame = cap.read()
        if not ret:
            continue
        
        # Hier würde die eigentliche Aktivitätserkennung mit OpenCV erfolgen
        # Beispiel: Erkenne Bewegung oder bestimmte Muster
        
        cv2.imshow('Activity Recognition', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

# Funktion zur Anzeige des Echtzeit-Dashboards mit GUI
def display_realtime_dashboard():
    global current_task, running
    
    root = tk.Tk()
    root.title("Arbeitszeit-Tracker")
    
    label = tk.Label(root, text="Aktuelle Aufgabe:")
    label.pack(pady=10)
    
    current_task_label = tk.Label(root, text="")
    current_task_label.pack()
    
    def update_task_label():
        while running:
            if current_task:
                current_task_label.config(text=f"Aktuelle Aufgabe: {current_task}, Zeit: {tasks[current_task]} Sekunden")
            time.sleep(1)
    
    update_thread = threading.Thread(target=update_task_label)
    update_thread.start()
    
    def on_task_selection(event):
        nonlocal current_task
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            current_task = event.widget.get(index)
            messagebox.showinfo("Aufgabe ausgewählt", f"Aktuelle Aufgabe ist jetzt: {current_task}")
    
    task_listbox = tk.Listbox(root)
    for task in tasks.keys():
        task_listbox.insert(tk.END, task)
    task_listbox.pack(pady=10)
    task_listbox.bind("<Double-Button-1>", on_task_selection)
    
    def add_task():
        new_task_name = simpledialog.askstring("Neue Aufgabe hinzufügen", "Geben Sie den Namen der neuen Aufgabe ein:")
        if new_task_name:
            tasks[new_task_name] = 0
            task_listbox.insert(tk.END, new_task_name)
            save_tasks()
            messagebox.showinfo("Aufgabe hinzugefügt", f"Neue Aufgabe '{new_task_name}' hinzugefügt.")
    
    add_task_button = tk.Button(root, text="Neue Aufgabe hinzufügen", command=add_task)
    add_task_button.pack(pady=10)
    
    def quit_tracker():
        global running
        running = False
        root.quit()
    
    root.protocol("WM_DELETE_WINDOW", quit_tracker)
    root.mainloop()

# Funktion zur Speicherung der Daten in Firebase
def upload_to_firebase():
    global tasks, firebase, db
    
    if not firebase or not db:
        print("Firebase ist nicht initialisiert.")
        return
    
    try:
        # Beispiel: Speichere die Aufgaben und Zeiten in Firebase
        db.child("tasks").set(tasks)
        print("Daten erfolgreich in Firebase hochgeladen.")
    except Exception as e:
        print(f"Fehler beim Hochladen der Daten nach Firebase: {e}")

# Funktion zur Versendung von E-Mails
def send_email(subject, message):
    sender_email = "your_email@example.com"  # Absender-E-Mail-Adresse eintragen
    receiver_email = "recipient_email@example.com"  # Empfänger-E-Mail-Adresse eintragen
    password = "your_password"  # Passwort für die Absender-E-Mail-Adresse eintragen

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject
    msg.attach(MIMEText(message, 'plain'))

    try:
        with smtplib.SMTP_SSL('smtp.example.com', 465) as smtp:
            smtp.login(sender_email, password)
            smtp.send_message(msg)
        print("E-Mail erfolgreich gesendet.")
    except Exception as e:
        print(f"Fehler beim Senden der E-Mail: {e}")

# Funktion zur Benachrichtigung über Slack
def send_slack_message(message):
    client = WebClient(token='your_slack_token')  # Slack API Token eintragen

    try:
        response = client.chat_postMessage(channel='#general', text=message)
        print("Nachricht erfolgreich über Slack gesendet.")
    except SlackApiError as e:
        print(f"Fehler beim Senden der Slack-Nachricht: {e}")

# Hauptprogramm
def main():
    global firebase
    
    initialize_firebase()
    
    # Starte Threads für automatische Aktivitätserkennung, manuelle Eingabe, GUI-Dashboard und Cloud-Upload
    auto_track_thread = threading.Thread(target=track_activities)
    manual_input_thread = threading.Thread(target=manual_input_task)
    gui_thread = threading.Thread(target=display_realtime_dashboard)
    activity_recognition_thread = threading.Thread(target=activity_recognition)
    upload_thread = threading.Thread(target=upload_to_firebase)
    
    auto_track_thread.start()
    manual_input_thread.start()
    gui_thread.start()
    activity_recognition_thread.start()
    upload_thread.start()
    
    # Warte auf Beendigung der Threads (eigentliches Programmende)
    auto_track_thread.join()
    manual_input_thread.join()
    gui_thread.join()
    activity_recognition_thread.join()
    upload_thread.join()

if __name__ == "__main__":
    main()
