# -*- coding: utf-8 -*-
"""
Created on Wed Sep 11 09:53:50 2024

@author: rahul
"""

import sys
import requests
import cv2
from PyQt5.QtCore import Qt  
from PyQt5.QtWidgets import *
from PyQt5 import uic, QtGui
from googletrans import Translator

class MYGUI(QMainWindow):
    def _init_(self):
        super(MYGUI, self)._init_()
        
        try:
            uic.loadUi("Modernn.ui", self)
            print("UI loaded successfully!")
        except Exception as e:
            print(f"Failed to load UI: {e}")
            return
        
        self.setStyleSheet(f"background-color: #D2E0FB")
        self.translator = Translator()
        self.current_file = ""
        self.trefle_token = '8XgnCUyHyjSW0ljlhm4AN96wTAgnxF1gFgRaMOOwNxs'  # Replace with your actual Trefle API token

        # Load the image
        self.actionLoad = QAction("Load Image", self)
        self.actionLoad.triggered.connect(self.load_image)

        self.toolbar = self.addToolBar("Toolbar")
        self.toolbar.addAction(self.actionLoad)

        # Push button
        self.pushButton.clicked.connect(self.read_code)

        # Connect ComboBox for language selection
        self.comboBox.currentTextChanged.connect(self.language_selected)
        self.selected_language = "en"  # Default language is English

        # Show the window
        self.show()

    def load_image(self):
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*)", options=options)

        if filename != "":
            self.current_file = filename
            pixmap = QtGui.QPixmap(self.current_file)
            pixmap = pixmap.scaled(400, 300)
            self.label.setScaledContents(True)
            self.label.setPixmap(pixmap)

    def language_selected(self, language):
        """Set the selected language based on ComboBox selection."""
        if language == "English":
            self.selected_language = 'en'
        elif language == "Hindi":
            self.selected_language = 'hi'
        elif language == "Gujarati":
            self.selected_language = 'gu'
        print(f"Selected language: {language}")

    def read_code(self):
        if self.current_file == "":
            self.textEdit.setText("No image loaded!")
            return

        img = cv2.imread(self.current_file)
        detector = cv2.QRCodeDetector()
        data, _, _ = detector.detectAndDecode(img)

        if data == "":
            self.textEdit.setText("No QR code found!")
        else:
            # Translate the QR code data based on the selected language
            translated_data = self.translate_text(data, self.selected_language)

            # Fetch tree location info using Trefle API
            location_info = self.get_tree_location_from_trefle(data)  # Tree name is in 'data'

            # Show both the translated data and location information
            self.textEdit.setText(f"{translated_data}\n\nLocation Info: {location_info}")

    def get_tree_location_from_trefle(self, tree_name):
        """Fetch tree information, including location, from Trefle API."""
        base_url = f"https://trefle.io/api/v1/plants/search"
        params = {
            'q': tree_name,  # Tree name to search for
            'token': self.trefle_token
        }
        
        response = requests.get(base_url, params=params)
        if response.status_code == 200:
            try:
                plant_data = response.json()
                if plant_data['data']:
                    # Extract useful data from the first matching plant (if available)
                    plant_info = plant_data['data'][0]
                    common_name = plant_info.get('common_name', 'Unknown')
                    family = plant_info.get('family', 'Unknown')
                    native_region = plant_info.get('native', 'Unknown')  # Native region info
                    return f"Common Name: {common_name}\nFamily: {family}\nNative Region: {native_region}"
                else:
                    return "No location data found for this tree."
            except Exception as e:
                return f"Error processing API response: {e}"
        else:
            return "Failed to fetch data from Trefle API."

    def translate_text(self, text, target_language):
        """Translate the text into the selected language using googletrans."""
        if target_language != 'en':  # Skip translation if English is selected
            translated = self.translator.translate(text, dest=target_language)
            return translated.text
        return text


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MYGUI()
    sys.exit(app.exec_())
