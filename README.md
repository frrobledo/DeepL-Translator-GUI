# DeepL Translator GUI for Linux

This is a simple Python application that provides a GUI for using the DeepL translation service on Linux systems. It uses PyQt5 for the interface and DeepL's API for translation.

![Screenshot](images/screenshot.png)

## Features

- **Translate Text:** Input text and translate it to a target language.
- **Source Language Detection:** Automatically detect the source language or select manually.
- **Hotkey Integration:** Double-press `Ctrl+C` to copy text to the application for translation.
- **API Key Storage:** Store and reuse your DeepL API key across sessions.
- **Multi-Threading:** Translations run in the background, ensuring the UI remains responsive.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/deepl-translator-gui.git
   cd deepl-translator-gui
   ```

2. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python main.py
   ```

## Setting the API Key

1. Open the application.
2. In the top menu, select "Settings" > "Set API Key".
3. Enter your DeepL API key.

If you don't have a DeepL API key, you can sign up for one [here](https://www.deepl.com/pro-api).

## Requirements

- Python 3.x
- DeepL API key

### Dependencies

All dependencies are listed in the `requirements.txt` file, including:

- `deepl`
- `PyQt5`
- `requests`
- `pynput`

## How to Use

1. Launch the app.
2. Select your source and target languages from the dropdown menus.
3. Type or paste text into the input area.
4. Press the "Translate" button or use `Ctrl+Enter` to translate the text.
5. The translated text will appear in the output area.

## Hotkeys

- **Double Ctrl+C**: Copies the selected text from the clipboard into the translation input box.

## Contributing

Feel free to fork this repository, open issues, and submit pull requests.

## License

This project is licensed under the MIT License.
