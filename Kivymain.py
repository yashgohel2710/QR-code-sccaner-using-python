from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.core.window import Window
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup

import cv2
from googletrans import Translator
from kivy.utils import platform
if platform == "android":
    from android.permissions import request_permissions, Permission

import numpy as np
import os
import imghdr

class QRScannerApp(App):
    def build(self):
        self.title = 'QR Code Scanner and Translator'
        return MainScreen()

class MainScreen(BoxLayout):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 10
        self.spacing = 10

        self.image = Image()
        self.add_widget(self.image)

        button_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
        self.scan_button = Button(text='Scan')
        self.scan_button.bind(on_press=self.start_scanning)
        button_layout.add_widget(self.scan_button)

        self.load_button = Button(text='Load')
        self.load_button.bind(on_press=self.show_load_dialog)
        button_layout.add_widget(self.load_button)

        self.add_widget(button_layout)

        self.language_spinner = Spinner(
            text='Select Language',
            values=('English', 'Hindi', 'Gujarati'),
            size_hint_y=None, height=50
        )
        self.add_widget(self.language_spinner)

        self.text_input = TextInput(
            multiline=True, readonly=True,
            size_hint_y=None, height=100
        )
        self.add_widget(self.text_input)

        self.decode_button = Button(text='Translate', size_hint_y=None, height=50)
        self.decode_button.bind(on_press=self.decode_text)
        self.add_widget(self.decode_button)

        self.capture = None
        self.qr_detector = cv2.QRCodeDetector()
        self.scanned_data = ""
        self.translator = Translator()
        self.current_language = 'en'

        if platform == "android":
            request_permissions([Permission.CAMERA, Permission.READ_EXTERNAL_STORAGE])

    def start_scanning(self, instance):
        if self.capture is None:
            self.capture = cv2.VideoCapture(0)
            Clock.schedule_interval(self.update, 1.0/30.0)
        else:
            Clock.unschedule(self.update)
            self.capture.release()
            self.capture = None

    def update(self, dt):
        ret, frame = self.capture.read()
        if ret:
            buf1 = cv2.flip(frame, 0)
            buf = buf1.tostring()
            image_texture = Texture.create(
                size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
            image_texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
            self.image.texture = image_texture

            data, bbox, _ = self.qr_detector.detectAndDecode(frame)
            if bbox is not None and data:
                print(f"QR Code detected: {data}")
                Clock.unschedule(self.update)
                self.capture.release()
                self.capture = None
                self.scanned_data = data
                self.text_input.text = "Scan complete. Click 'Translate' to translate."

    def show_load_dialog(self, instance):
        content = BoxLayout(orientation='vertical')
        self.file_chooser = FileChooserListView(
            path=os.path.expanduser("~")
        )
        content.add_widget(self.file_chooser)
        
        buttons = BoxLayout(size_hint_y=None, height=50)
        select_button = Button(text="Select")
        select_button.bind(on_release=self.load_file)
        buttons.add_widget(select_button)
        
        cancel_button = Button(text="Cancel")
        cancel_button.bind(on_release=self.dismiss_popup)
        buttons.add_widget(cancel_button)
        
        content.add_widget(buttons)
        
        self._popup = Popup(title="Load file", content=content, size_hint=(0.9, 0.9))
        self._popup.open()

    def load_file(self, instance):
        selected_file = self.file_chooser.selection and self.file_chooser.selection[0]
        if selected_file:
            self.process_loaded_file(selected_file)
        self.dismiss_popup()

    def dismiss_popup(self, instance=None):
        self._popup.dismiss()

    def process_loaded_file(self, filename):
        # Check if the file is an image
        if self.is_image_file(filename):
            self.process_image_file(filename)
        else:
            self.process_non_image_file(filename)

    def is_image_file(self, filename):
        return imghdr.what(filename) is not None

    def process_image_file(self, filename):
        img = cv2.imread(filename)
        if img is None:
            self.text_input.text = "Failed to load the image."
            return

        # Detect and decode QR code
        data, bbox, _ = self.qr_detector.detectAndDecode(img)

        if data:
            self.scanned_data = data
            self.text_input.text = "QR code loaded. Click 'Translate' to translate."
            
            # Display the loaded image
            buf1 = cv2.flip(img, 0)
            buf = buf1.tostring()
            image_texture = Texture.create(
                size=(img.shape[1], img.shape[0]), colorfmt='bgr')
            image_texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
            self.image.texture = image_texture
        else:
            self.text_input.text = "No QR code found in the image."

    def process_non_image_file(self, filename):
        try:
            with open(filename, 'r') as file:
                content = file.read()
            self.scanned_data = content
            self.text_input.text = f"File loaded: {os.path.basename(filename)}. Click 'Translate' to translate content."
            self.image.source = ''  # Clear any previous image
        except Exception as e:
            self.text_input.text = f"Error reading file: {str(e)}"

    def decode_text(self, instance):
        if self.scanned_data:
            translated_text = self.translate_text(self.scanned_data)
            self.text_input.text = translated_text
        else:
            self.text_input.text = "No data to decode. Please scan or load a file."

    def translate_text(self, text):
        language = self.language_spinner.text
        if language == "English":
            self.current_language = 'en'
        elif language == "Hindi":
            self.current_language = 'hi'
        elif language == "Gujarati":
            self.current_language = 'gu'
        else:
            self.current_language = 'en'

        if self.current_language == 'en':
            return text
        try:
            translated = self.translator.translate(text, dest=self.current_language)
            return translated.text
        except Exception as e:
            print(f"Translation error: {e}")
            return text

if __name__ == '__main__':
    QRScannerApp().run()