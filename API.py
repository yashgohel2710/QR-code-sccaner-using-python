# -*- coding: utf-8 -*-
"""
Created on Wed Sep 11 09:27:29 2024

@author: rahul
"""

import sys
import cv2
import requests
from PyQt5 import QtWidgets, uic
from PyQt5.QtGui import QPixmap, QImage, QPainter
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QFileDialog
from googletrans import Translator
import speech_recognition as sr

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi("Structure.ui", self)
        self.setStyleSheet("background-color : #D2E0FB")

        self.background_image_path = "D:\\MediPlant\\download.jpeg"
        self.background_pixmap = QPixmap(self.background_image_path)
        
        # Find the elements from the .ui file
        self.qr_label = self.findChild(QtWidgets.QLabel, "qr_label")
        self.scan_button = self.findChild(QtWidgets.QPushButton, "scan_button")
        self.load_button = self.findChild(QtWidgets.QPushButton, "load_button")
        self.decode_button = self.findChild(QtWidgets.QPushButton, "decode_button")
        self.text_edit = self.findChild(QtWidgets.QTextEdit, "text_edit")
        self.language_combo = self.findChild(QtWidgets.QComboBox, "language_combo")
        self.voice_button = self.findChild(QtWidgets.QPushButton, "voice_button")  # Add a button for voice commands

        # Initialize translator and default language
        self.translator = Translator()
        self.current_language = 'en'  # Default to English

        # Connect ComboBox and buttons to their functions
        self.language_combo.currentIndexChanged.connect(self.language_changed)
        self.scan_button.clicked.connect(self.scan_qr)
        self.load_button.clicked.connect(self.load_qr)
        self.decode_button.clicked.connect(self.decode_text)
        self.voice_button.clicked.connect(self.handle_voice_command)  # Connect the voice button

        # Set a border around the QLabel
        self.qr_label.setStyleSheet("border: 3px solid black;")
        self.text_edit.setStyleSheet("border: 3px solid black;")
        
        # Timer for webcam
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

        self.cap = None
        self.qr_detector = cv2.QRCodeDetector()
        self.scanned_data = ""  # Store the scanned data here
        
        # Override the paintEvent to draw the background image
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), self.background_pixmap)  # Draw the background image across the window

    def scan_qr(self):
        if self.cap is None or not self.cap.isOpened():
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                print("Error: Unable to access the webcam")
                return

        self.qr_label.setStyleSheet("border: 2px solid green;")
        self.timer.start(20)

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.qr_label.setPixmap(QPixmap.fromImage(convert_to_Qt_format).scaled(self.qr_label.width(), self.qr_label.height(), Qt.KeepAspectRatio))

            data, bbox, _ = self.qr_detector.detectAndDecode(frame)
            if bbox is not None and data:
                print(f"QR Code detected: {data}")
                self.qr_label.setStyleSheet("border: 2px solid black;")
                self.timer.stop()
                self.cap.release()
                self.cap = None
                self.scanned_data = data  # Save the scanned data
                self.text_edit.setText("Scan complete. Click 'Decode' to translate.")
                return

    def language_changed(self):
        language = self.language_combo.currentText()
        if language == "Select":
            self.current_language = 'en'  # Default to English if "Select" is chosen
        elif language == "English":
            self.current_language = 'en'
        elif language == "Hindi":
            self.current_language = 'hi'
        elif language == "Gujarati":
            self.current_language = 'gu'
        else:
            self.current_language = 'en'  # Default to English for any unknown value
        print(f"Language set to: {self.current_language}")

    def translate_text(self, text):
        if self.current_language == 'en':  # Do not translate if the language is English
            return text
        try:
            print(f"Translating text: {text} to language: {self.current_language}")
            translated = self.translator.translate(text, dest=self.current_language)
            print(f"Translated text: {translated.text}")
            return translated.text
        except Exception as e:
            print(f"Translation error: {e}")
            return text

    def decode_text(self):
        if self.scanned_data:
            translated_text = self.translate_text(self.scanned_data)
            self.text_edit.setText(translated_text)
        else:
            self.text_edit.setText("No data to decode. Please scan or load a QR code.")

    def load_qr(self):
        if self.cap and self.cap.isOpened():
            self.timer.stop()
            self.cap.release()
            self.cap = None
            self.qr_label.setStyleSheet("border: 2px solid black;")

        file_path, _ = QFileDialog.getOpenFileName(self, "Load QR Code", "", "Image Files (*.png *.jpg *.bmp)")
        if file_path:
            pixmap = QPixmap(file_path)
            self.qr_label.setPixmap(pixmap.scaled(self.qr_label.width(), self.qr_label.height(), Qt.KeepAspectRatio))

            loaded_image = cv2.imread(file_path)
            data, bbox, _ = self.qr_detector.detectAndDecode(loaded_image)

            if data:
                self.scanned_data = data  # Save the loaded QR code data
                self.text_edit.setText("Loaded QR code. Click 'Decode' to translate.")
                # Fetch information from Google
                self.fetch_image_info(file_path)
            else:
                self.text_edit.clear()
                self.text_edit.setText("No QR code detected.")

    def fetch_image_info(self, image_path):
        # Replace with your Google Custom Search API credentials
        api_key = 'AIzaSyCJ4w6yaGjQ2Hsj_eFn_xEFT2UwT3lW5eE'
        search_engine_id = "051d079c17d794cf9"
        

        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'q': 'image',
            'cx': search_engine_id,
            'key': api_key,
            'searchType': 'image',
            'imgUrl': image_path
        }

        response = requests.get(url, params=params)
        if response.status_code == 200:
            results = response.json()
            if 'items' in results:
                first_result = results['items'][0]
                title = first_result.get('title', 'No title available')
                link = first_result.get('link', 'No link available')
                self.text_edit.append(f"\nImage Information:\nTitle: {title}\nLink: {link}")
            else:
                self.text_edit.append("No image results found.")
        else:
            self.text_edit.append("Error fetching image information.")

    def handle_voice_command(self):
        recognizer = sr.Recognizer()
        mic = sr.Microphone()

        with mic as source:
            print("Listening...")
            audio = recognizer.listen(source)

        try:
            command = recognizer.recognize_google(audio)
            print(f"Recognized command: {command}")
            if "scan" in command.lower():
                self.scan_qr()
            elif "load image" in command.lower():
                self.load_qr()
            elif "select gujarati" in command.lower():
                self.language_combo.setCurrentText("Gujarati")
                self.language_changed()
            else:
                print("Command not recognized.")
        except sr.UnknownValueError:
            print("Sorry, I did not understand that.")
        except sr.RequestError as e:
            print(f"Sorry, there was an error with the speech recognition service: {e}")

if __name__ == "__main__":
      app = QtWidgets.QApplication(sys.argv)
      pp = QtWidgets.QApplication(sys.argv)
      window = MainWindow()
      window.show()
      sys.exit(app.exec_())