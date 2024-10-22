import deepl
import sys
import json
import requests
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QComboBox, QPushButton, QLabel, QMenuBar, QAction, QInputDialog, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSettings
from pynput import keyboard  # For global hotkey detection

class DeepLTranslator(QWidget):
    double_copy_detected = pyqtSignal()
    def __init__(self):
        super().__init__()
        self.settings = QSettings('frobledo', 'DeepLTranslator')
        self.auth_key = self.settings.value('auth_key', '')
        self.init_ui()
        self.fetch_languages()

        # Start global hotkey listener
        self.listener = keyboard.GlobalHotKeys({
            '<ctrl>+c': self.on_copy
        })
        self.listener.start()

        # Variables to detect double Ctrl+C
        self.last_copy_time = None

        # Connect the custom signal to the slot
        self.double_copy_detected.connect(self.handle_double_copy)


    def init_ui(self):
        """
        Initialize the user interface for the DeepL Translator window.
        
        Sets up the window title, geometry, menu bar, source and target language ComboBoxes,
        text areas for source and translated text, translate button, and layouts.
        """
        self.setWindowTitle('DeepL Translator')
        self.setGeometry(100, 100, 800, 600)

        # Menu Bar
        menubar = QMenuBar(self)
        settings_menu = menubar.addMenu('Settings')

        # API Key Menu Action
        api_key_action = QAction('Set API Key', self)
        api_key_action.triggered.connect(self.set_api_key)
        settings_menu.addAction(api_key_action)

        # Layouts
        main_layout = QVBoxLayout()
        main_layout.setMenuBar(menubar)
        options_layout = QHBoxLayout()
        text_layout = QHBoxLayout()

        # Source Language ComboBox
        self.source_lang_combo = QComboBox()
        self.source_lang_combo.setCurrentText('Auto')
        options_layout.addWidget(QLabel('Source Language:'))
        options_layout.addWidget(self.source_lang_combo)

        # Target Language ComboBox
        self.target_lang_combo = QComboBox()
        self.target_lang_combo.setCurrentText('EN')
        options_layout.addWidget(QLabel('Target Language:'))
        options_layout.addWidget(self.target_lang_combo)

        # Text Areas
        self.source_text = QTextEdit()
        self.translated_text = QTextEdit()
        self.translated_text.setReadOnly(True)
        text_layout.addWidget(self.source_text)
        text_layout.addWidget(self.translated_text)

        # Translate Button
        self.translate_button = QPushButton('Translate')
        self.translate_button.clicked.connect(self.translate_text)

        # Shortcut for Ctrl+Enter
        self.source_text.installEventFilter(self)

        # Assemble Layouts
        main_layout.addLayout(options_layout)
        main_layout.addLayout(text_layout)
        main_layout.addWidget(self.translate_button)
        self.setLayout(main_layout)

    def eventFilter(self, source, event):
        """
        Filters events for the source widget.

        Parameters:
        source: The source widget that the event is filtered for.
        event: The event object to filter.

        Returns:
        bool: True if the event is handled, False otherwise.
        """
        if event.type() == event.KeyPress and source is self.source_text:
            if event.key() == Qt.Key_Return and (event.modifiers() & Qt.ControlModifier):
                self.translate_text()
                return True
        return super().eventFilter(source, event)

    def set_api_key(self):
        """
        Set the DeepL API key.

        Opens a dialog to enter the API key, and if the user clicks OK, it
        sets the API key and fetches the list of supported languages from the
        DeepL API.
        """
        api_key, ok = QInputDialog.getText(self, 'Set API Key', 'Enter your DeepL API Key:', text=self.auth_key)
        if ok:
            self.auth_key = api_key.strip()
            self.settings.setValue('auth_key', self.auth_key)
            self.fetch_languages()

    def fetch_languages(self):
        """
        Fetches the list of supported languages from the DeepL API and sets the
        source and target language combo boxes.

        If the API key is not set, it returns immediately. Otherwise, it disables
        the translate button and sets the wait cursor until the languages are
        fetched. If the languages are fetched successfully, it sets the source and
        target language combo boxes and enables the translate button. If not, it
        shows an error message box.

        This function is called when the API key is set or changed.
        """
        if not self.auth_key:
            return
        self.translate_button.setEnabled(False)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.source_lang_combo.clear()
        self.target_lang_combo.clear()

        # Fetch source languages
        source_langs = self.get_supported_languages(type='source')

        # Fetch target languages
        target_langs = self.get_supported_languages(type='target')

        if source_langs and target_langs:
            self.source_lang_combo.addItem('Auto')
            self.source_lang_combo.addItems(sorted([lang['name'] for lang in source_langs]))
            self.target_lang_combo.addItems(sorted([lang['name'] for lang in target_langs]))
            self.translate_button.setEnabled(True)
        else:
            QMessageBox.warning(self, 'Error', 'Failed to fetch languages. Check your API key.')

        QApplication.restoreOverrideCursor()

    def get_supported_languages(self, type='target'):
        """
        Fetches the list of supported languages from the DeepL API.

        Parameters:
        type (str): Either 'target' or 'source', default is 'target'.

        Returns:
        list: A list of language dictionaries with keys 'language' and 'name'.
              If the request fails, returns None.
        """
        url = 'https://api-free.deepl.com/v2/languages'  # Use 'https://api.deepl.com/v2/languages' for Pro accounts
        params = {
            'auth_key': self.auth_key,
            'type': type
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            languages = response.json()
            return languages
        except requests.exceptions.RequestException as e:
            print(f'Error fetching languages: {e}')
            return None

    
    def translate_text(self):
        """
        Translate the text from the source_text field.

        If the API key is missing, a warning message is displayed to set the API key first.
        Retrieves the text from the source_text field, along with the selected source and target languages.
        If no text is provided, a message prompts the user to enter text for translation.
        Maps the language names to their respective language codes.
        Disables the translate button, sets a 'Translating...' message in the translated text field, and updates the UI.
        Initiates the translation process in a separate thread using the TranslationThread class.
        """
        if not self.auth_key:
            QMessageBox.warning(self, 'API Key Missing', 'Please set your API key in Settings > Set API Key.')
            return

        text = self.source_text.toPlainText()
        source_lang_name = self.source_lang_combo.currentText()
        target_lang_name = self.target_lang_combo.currentText()

        if not text.strip():
            self.translated_text.setPlainText('Please enter text to translate.')
            return

        # Map language names to codes
        source_lang = self.get_language_code(source_lang_name)
        target_lang = self.get_language_code(target_lang_name)

        self.translate_button.setEnabled(False)
        self.translated_text.setPlainText('Translating...')
        QApplication.processEvents()  # Update UI

        # Start translation in a separate thread
        self.translation_thread = TranslationThread(
            self.auth_key, text, source_lang, target_lang)
        self.translation_thread.translation_done.connect(self.display_translation)
        self.translation_thread.start()

    def display_translation(self, translation):
        """
        Updates the translated text field with the translated text
        and enables the translate button again.

        Parameters:
        translation (str): The translated text.
        """
        self.translated_text.setPlainText(translation)
        self.translate_button.setEnabled(True)

    def get_language_code(self, language_name):
        # Fetch the code corresponding to the language name
        """
        Maps a language name to its corresponding code.

        Parameters:
        language_name (str): The name of the language.

        Returns:
        str: The language code corresponding to the given language name.
              Empty string if the language name is not found.
        """
        for lang in self.get_supported_languages(type='target') + self.get_supported_languages(type='source'):
            if lang['name'] == language_name:
                return lang['language']
        return ''

    def on_copy(self):
        """
        Handles the Ctrl+C event for copying text.

        If two Ctrl+C events occur within 0.5 seconds, it copies the text from the clipboard
        to the source text field. It then activates the window and brings it to the front.

        Updates the last copy time to the current time.
        """
        from time import time
        current_time = time()
        if self.last_copy_time and current_time - self.last_copy_time < 0.5:
            # Detected double Ctrl+C
            self.double_copy_detected.emit()
        self.last_copy_time = current_time
      
    def handle_double_copy(self):
        """
        Handles double Ctrl+C event. Copies the text from the clipboard to the source text field.
        Activates the window and brings it to the front.
        """
        clipboard = QApplication.clipboard()
        copied_text = clipboard.text()
        self.source_text.setPlainText(copied_text)
        self.activateWindow()
        self.raise_()


class TranslationThread(QThread):
    translation_done = pyqtSignal(str)

    def __init__(self, auth_key, text, source_lang, target_lang):
        super().__init__()
        self.auth_key = auth_key
        self.text = text
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.translator = deepl.Translator(self.auth_key)

    def run(self):
        """
        Translate the given text using the DeepL API and emit the translated text
        using the translation_done signal.

        The translation is done in a separate thread to avoid blocking the GUI.

        Parameters:
        None

        Returns:
        None
        """
        try:
            if self.source_lang == 'Auto':
                result = self.translator.translate_text(self.text, target_lang=self.target_lang)
            else:
                result = self.translator.translate_text(self.text, source_lang=self.source_lang, target_lang=self.target_lang)
            
            self.translation_done.emit(result.text)
        except deepl.exceptions.DeepLException as e:
            self.translation_done.emit(f'Error: {e}')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    translator_app = DeepLTranslator()
    translator_app.show()
    sys.exit(app.exec_())

