# main.py
#
# semi-simple GUI that utilizes the library to allow for editing of files inside packfiles.

# this file is nasty and gross i am sorry :pray:

import json
import sys
import traceback
import os
import ctypes
import requests
import qdarkstyle
import re

from PyQt5.QtCore import Qt

from PyQt5.QtWidgets import \
QApplication, \
QMainWindow, \
QAction, \
QFileDialog, \
QListWidget, \
QWidget, \
QPushButton, \
QMenuBar, \
QMenu, \
QLineEdit, \
QLabel, \
QComboBox, \
QCheckBox, \
QSpinBox, \
QFormLayout, \
QGridLayout, \
QMessageBox

from PyQt5.QtGui import \
QIcon, \
QFont, \
QColor, \
QPixmap

from PyQt5.Qsci import \
QsciScintilla, \
QsciLexerJSON, \
QsciLexerLua, \
QsciLexerXML

from epicmickeylib.formats.packfile import Packfile
from epicmickeylib.formats.dct import DCT
from epicmickeylib.formats.scene import SceneFile
from epicmickeylib.formats.script import Script
from epicmickeylib.formats.collectible_database import CollectibleDatabase
from epicmickeylib.formats.subtitle_file import SubtitleFile
from epicmickeylib.internal.file_manipulator import EndianType, FileManipulator

# Defines the tool's name in the taskbar and the EXE (used in build.py)
APP_NAME = "BlueThinner Lite"
# Version, must match GitHub release's version for the auto update notifier to work
APP_VERSION = "v1.0.1"
# link to the modding/research server
DISCORD_LINK = "https://google.com/" # usually a discord link, stripped out for collegeboard

# used when no config.json is found
DEFAULT_CONFIG = {
    "font": "Consolas",
    "font_size": 12,
    "text_background_color": [25, 35, 45],
    "save_pak_on_update": True,
    "update_shortcut": "Ctrl+S",
    "unluac_path": "./thirdparty/unluac.jar",
    "luac_path": "./thirdparty/luac.exe",
    "ignore_updates": False
}

# some patches over qdarkstyle to make the scrollbar match
scrollbar_stylesheet = """
QScrollBar {
    background: rgb(25, 35, 45);
    border: 1px solid #222222;
}

QScrollBar::handle {
    background: rgb(53, 69, 84);
    border-radius: 5px;
    min-height: 20px;
}

QScrollBar::handle:hover {
    background: rgb(73, 89, 104);
}

QScrollBar::add-line, QScrollBar::sub-line {
    background: rgb(25, 35, 45);
}

QScrollBar::add-line:hover, QScrollBar::sub-line:hover {
    background: rgb(39, 53, 66);
}

QScrollBar::add-page, QScrollBar::sub-page {
    background: rgb(25, 35, 45);
}

QScrollBar::add-page:hover, QScrollBar::sub-page:hover {
    background: rgb(39, 53, 66);
}

QScrollBar::add-line:vertical {
    height: 0px;
}

QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:vertical {
    width: 15px;
}

QScrollBar:horizontal {
    height: 15px;
}

QScrollBar::add-line:horizontal {
    width: 0px;
}

QScrollBar::sub-line:horizontal {
    width: 0px;
}
"""

class SettingsWindow(QMainWindow):
    config: dict
    font_combo: QComboBox
    font_size_spinbox: QSpinBox
    save_pak_on_update_checkbox: QCheckBox
    update_shortcut_line_edit: QLineEdit
    search_text_shortcut_line_edit: QLineEdit
    search_files_shortcut_line_edit: QLineEdit
    # lua paths
    unluac_path_line_edit: QLineEdit
    luac_path_line_edit: QLineEdit
    ignore_updates_checkbox: QCheckBox

    def __init__(self, parent):
        super(SettingsWindow, self).__init__(parent)

        self.config = DEFAULT_CONFIG

        # if the config file doesn't exist, create it
        if not os.path.exists("config.json"):
            with open("config.json", "w") as f:
                json.dump(DEFAULT_CONFIG, f)
        # copy any config from the file to the config
        with open("config.json", "r") as f:
            new_config = json.load(f)

        for key in new_config:
            self.config[key] = new_config[key]

        self.setWindowTitle("Settings")

        # create the main widget
        widget = QWidget()
        layout = QFormLayout()

        layout.addRow(QLabel("Settings are saved when the window is closed and changes show when the app is restarted"))

        self.font_combo = QComboBox()
        self.font_combo.addItems(["Consolas", "Courier New", "Lucida Console", "Monospace"])
        self.font_combo.setCurrentText(self.config["font"])
        layout.addRow(QLabel("Font"), self.font_combo)

        self.font_size_spinbox = QSpinBox()
        self.font_size_spinbox.setMinimum(8)
        self.font_size_spinbox.setMaximum(72)
        self.font_size_spinbox.setValue(self.config["font_size"])
        layout.addRow(QLabel("Font Size"), self.font_size_spinbox)

        self.save_pak_on_update_checkbox = QCheckBox()
        self.save_pak_on_update_checkbox.setChecked(self.config["save_pak_on_update"])
        layout.addRow(QLabel("Save .pak on update"), self.save_pak_on_update_checkbox)

        self.update_shortcut_line_edit = QLineEdit()
        self.update_shortcut_line_edit.setText(self.config["update_shortcut"])
        layout.addRow(QLabel("Update Shortcut"), self.update_shortcut_line_edit)

        self.unluac_path_line_edit = QLineEdit()
        self.unluac_path_line_edit.setText(self.config["unluac_path"])
        layout.addRow(QLabel("unluac Path"), self.unluac_path_line_edit)

        self.luac_path_line_edit = QLineEdit()
        self.luac_path_line_edit.setText(self.config["luac_path"])
        layout.addRow(QLabel("luac Path"), self.luac_path_line_edit)

        # ignore updates checkbox
        self.ignore_updates_checkbox = QCheckBox()
        self.ignore_updates_checkbox.setChecked(self.config["ignore_updates"])
        layout.addRow(QLabel("Ignore Updates"), self.ignore_updates_checkbox)

        widget.setLayout(layout)
        self.setCentralWidget(widget)

        self.setStyleSheet(qdarkstyle.load_stylesheet())

    def save_config(self):
        self.config["font"] = self.font_combo.currentText()
        self.config["font_size"] = self.font_size_spinbox.value()
        self.config["save_pak_on_update"] = self.save_pak_on_update_checkbox.isChecked()
        self.config["update_shortcut"] = self.update_shortcut_line_edit.text()
        self.config["unluac_path"] = self.unluac_path_line_edit.text()
        self.config["luac_path"] = self.luac_path_line_edit.text()
        self.config["ignore_updates"] = self.ignore_updates_checkbox.isChecked()

        # save the config to a file
        with open("config.json", "w") as f:
            json.dump(self.config, f)

    def closeEvent(self, event):
        self.save_config()
        event.accept()
    
    def showEvent(self, event):
        self.parent().settings_action.setEnabled(False)
        event.accept()
    
    def hideEvent(self, event):
        self.parent().settings_action.setEnabled(True)
        event.accept()
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        event.accept()

class InfoWindow(QMainWindow):
    def __init__(self):
        super(InfoWindow, self).__init__()

        self.setWindowTitle("Info")

        widget = QWidget()
        layout = QFormLayout()

        # banner
        banner = QLabel()
        banner.setPixmap(QPixmap("assets/banner.png").scaledToWidth(400))
        layout.addRow(banner)

        # separator
        layout.addRow(QLabel(""))

        # app name
        app_name = QLabel(f"<b>{APP_NAME}</b>")
        app_name.setStyleSheet("font-size: 16px;")
        layout.addRow(app_name)

        # credits
        credits = QLabel("Developed by Ryan \"abso1utezer0\" Koop")
        layout.addRow(credits)

        # discord link, should be a clickable link
        discord_link = QLabel(f"<a href=\"{DISCORD_LINK}\">Visit the Discord Server</a>")
        discord_link.setOpenExternalLinks(True)
        layout.addRow(discord_link)

        # separator
        layout.addRow(QLabel(""))

        thanks = QLabel("<b>Special Thanks</b>")
        thanks.setStyleSheet("font-size: 16px;")
        layout.addRow(thanks)

        recievers_of_thanks = [
            "Rampy - Reseached the game early on before any tools existed",
            "AltruisticNut - Texture research, testing, and feedback",
            "SlayCap - SFX insight, testing, and feedback",
            "Spek - Moral support",
            "Kalsvik - Feedback, creator of the Epic Mickey Launcher",
            "Kriesk/EMP - Creator of the BlueThinner name",
            "YawningDog - Creator of the BlueThinner Lite icon and banner",
            "SoraTrash - Creator of the OpenEM server, which has helped with research",
            "FungusNitrogen - Initial inspiration for dialog editing",
            "Anyone who has stuck with me through the development of this tool",
            "Everyone who has contributed to the Epic Mickey modding community"
        ]
        for person in recievers_of_thanks:
            layout.addRow(QLabel(person))

        # close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        layout.addRow(close_button)

        widget.setLayout(layout)
        self.setCentralWidget(widget)

        self.setStyleSheet(qdarkstyle.load_stylesheet())

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        event.accept()

class MainWindow(QMainWindow):
    pak_path = ""
    pak: Packfile
    endian: int
    config: dict
    menu: QMenuBar
    file_menu: QMenu
    edit_menu: QMenu
    settings_action: QAction
    discord_action: QAction
    info_action: QAction
    docs_action: QAction
    list_widget: QListWidget
    list_search_bar: QLineEdit
    text_edit: QsciScintilla
    text_edit_search_bar: QLineEdit
    update_button: QPushButton

    def __init__(self):
        super(MainWindow, self).__init__()

        self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")

        self.pak = Packfile()
        self.endian = EndianType.BIG

        self.config = DEFAULT_CONFIG

        # Menu
        self.menu = self.menuBar()
        self.file_menu = self.menu.addMenu("File")
        self.edit_menu = self.menu.addMenu("Edit")

        # File menu actions
        open_action = QAction("Open", self)
        open_action.triggered.connect(self.open_file)
        self.file_menu.addAction(open_action)

        save_action = QAction("Save", self)
        save_action.triggered.connect(self.save_file)
        self.file_menu.addAction(save_action)

        save_as_action = QAction("Save As", self)
        save_as_action.triggered.connect(self.save_file_as)
        self.file_menu.addAction(save_as_action)

        # Edit menu actions
        add_action = QAction("Add File", self)
        add_action.triggered.connect(self.add_item)
        self.edit_menu.addAction(add_action)

        remove_action = QAction("Remove", self)
        remove_action.triggered.connect(self.remove_item)
        self.edit_menu.addAction(remove_action)

        rename_action = QAction("Rename", self)
        rename_action.triggered.connect(self.rename_item)
        self.edit_menu.addAction(rename_action)

        # Settings action
        self.settings_action = QAction("Settings", self)
        # when clicked, we show the settings window until it's closed
        self.settings_action.triggered.connect(self.show_settings)
        self.menu.addAction(self.settings_action)

        # Info action
        info_action = QAction("Info", self)
        info_action.triggered.connect(self.show_info)
        self.menu.addAction(info_action)

        # Docs action
        docs_action = QAction("Docs", self)
        # website is owned by another person
        docs_action.triggered.connect(lambda: os.system(f"start https://docs.epicmickey.wiki"))
        self.menu.addAction(docs_action)

        # Discord action
        discord_action = QAction("Discord", self)
        discord_action.triggered.connect(lambda: os.system(f"start {DISCORD_LINK}"))
        self.menu.addAction(discord_action)
        
        # Left list widget
        self.list_widget = QListWidget()
        # if we right click on the list widget, we can add, remove, or rename items
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.open_menu)
        self.list_widget.itemChanged.connect(self.item_changed)
        # allow moving items order
        self.list_widget.setDragDropMode(QListWidget.InternalMove)
        # set the scrollbar stylesheet
        self.list_widget.setStyleSheet(scrollbar_stylesheet)

        # Right text edit
        self.text_edit = QsciScintilla()
        self.text_edit.setUtf8(True)
        self.text_edit.setCaretWidth(2)
        self.text_edit.setIndentationsUseTabs(True)
        self.text_edit.setIndentationWidth(4)
        self.text_edit.setTabWidth(4)
        self.text_edit.setTabIndents(True)
        self.text_edit.setBackspaceUnindents(True)
        # set the scrollbar stylesheet
        self.text_edit.setStyleSheet(scrollbar_stylesheet)

        self.text_edit_search_bar = QLineEdit()
        self.text_edit_search_bar.setPlaceholderText("Search")
        # when enter is pressed, we search the text edit
        self.text_edit_search_bar.returnPressed.connect(self.search_text_edit)

        # add a search bar above the list widget
        self.list_search_bar = QLineEdit()
        self.list_search_bar.setPlaceholderText("Search")
        # filter the list widget when we type in the search bar
        self.list_search_bar.textChanged.connect(self.filter_list_widget)

        # when we select an item in the list widget, we display the file in the text edit
        self.list_widget.itemSelectionChanged.connect(self.select_item)

        # Update button
        self.update_button = QPushButton("Update Currently Selected Virtual File")
        self.update_button.clicked.connect(self.update_data)

        # Layout
        # list on left and text on right, USE GRID, allow for resizing
        layout = QGridLayout()
        layout.addWidget(self.list_search_bar, 0, 0)
        layout.addWidget(self.list_widget, 1, 0)
        layout.addWidget(self.text_edit_search_bar, 0, 1)
        layout.addWidget(self.text_edit, 1, 1)
        layout.addWidget(self.update_button, 2, 1)

        # resizing
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 2)

        self.config_updated()

        # set the layout
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        self.setup_text_edit_style()

        stylesheet = qdarkstyle.load_stylesheet()

        self.setStyleSheet(stylesheet)
        self.setWindowIcon(QIcon("assets/icon.ico"))
        

    def show_settings(self):
        self.settings_window = SettingsWindow(self)
        self.settings_window.show()
    
    def config_updated(self):
        # if the config file doesn't exist, create it
        if not os.path.exists("config.json"):
            with open("config.json", "w") as f:
                json.dump(DEFAULT_CONFIG, f)
        # open the config file and update the config
        with open("config.json", "r") as f:
            new_config = json.load(f)
        for key in new_config:
            self.config[key] = new_config[key]
        # update the text edit font and font size
        self.text_edit.setFont(QFont(self.config["font"], self.config["font_size"]))
        self.setStyleSheet(f"QsciScintilla{{font-family: {self.config['font']}; font-size: {self.config['font_size']}pt;}}")
        # update the save action shortcut
        self.update_button.setShortcut(self.config["update_shortcut"])

    def show_info(self):
        self.info_window = InfoWindow()
        self.info_window.show()
    
    def show_message_box(self, title, message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText(message)
        msg.setWindowTitle(title)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    
    def search_text_edit(self):
        # find the next occurrence of the text from the search bar, from the current position
        text = self.text_edit_search_bar.text()
        self.text_edit.findFirst(text, True, False, False, True, True)
    
    def filter_list_widget(self):
        text = self.list_search_bar.text()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if text.lower() in item.text().lower():
                item.setHidden(False)
            else:
                item.setHidden(True)

    def change_pak_path(self, path):
        self.pak_path = path
        # get the first 4 bytes of the file
        magic = b""
        with open(self.pak_path, "rb") as f:
            magic = f.read(4)
        # check the magic to determine the endian
        if magic == b"PAK ":
            self.endian = EndianType.LITTLE
        elif magic == b" KAP":
            self.endian = EndianType.BIG
        self.setWindowTitle(f"{APP_NAME} {APP_VERSION} - {path}")
    
    def open_menu(self, position):
        menu = QMenu()
        remove_action = menu.addAction("Remove")
        rename_action = menu.addAction("Rename")
        replace_action = menu.addAction("Replace")
        add_below_action = menu.addAction("Add File Below")
        add_model_and_dependencies_below_action = menu.addAction("Add Model and Dependencies Below")
        action = menu.exec_(self.list_widget.mapToGlobal(position))
        if action == remove_action:
            self.remove_item()
        elif action == rename_action:
            self.rename_item()
        elif action == replace_action:
            self.replace_item()
        elif action == add_below_action:
            self.add_item_below()
        elif action == add_model_and_dependencies_below_action:
            self.add_model_and_dependencies_below()
        
    def add_model_and_dependencies_below(self):
        # ask for relative folder
        folder = QFileDialog.getExistingDirectory(self, "Select the relative project folder")
        if folder:
            # ask for file
            file_name, _ = QFileDialog.getOpenFileName(self, "Open file", folder, "All files (*.*)")
            if file_name:
                # add the file to the packfile
                self.insert_file_below_selected(folder, file_name)
                data = open(file_name, "rb").read()
                # if the file is a .nif_wii or .nif, we add the dependencies
                if file_name.endswith(".nif_wii") or file_name.endswith(".nif"):
                    # get the dependencies
                    relative_dependencies_start_offsets = []
                    # search for all occurances of b"_tex.nif"
                    for match in re.finditer(b"_tex.nif", data):
                        # get the start and end of the match
                        start = match.start()
                        relative_dependencies_start_offsets.append(start)
                    fm = FileManipulator(data, self.endian)
                    relative_dependencies = []
                    for start in relative_dependencies_start_offsets:
                        fm.seek(start)
                        # go back until we find a null byte
                        while fm.read_backwards(1) != b"\x00":
                            # continue reading backwards
                            continue
                        if self.endian == EndianType.BIG:
                            # go back until we find a non-null byte
                            while fm.read_backwards(1) == b"\x00":
                                # continue reading backwards
                                continue
                            fm.move(1)
                        else:
                            fm.move(-3)
                        # read the length of the string
                        length = fm.r_u32()
                        # read the string
                        relative_dependencies.append(fm.r_str(length))
                    # remove the beginning slash
                    relative_dependencies = [dep[1:] for dep in relative_dependencies]
                    # add the dependencies to the packfile
                    for dep in relative_dependencies:
                        dep_path = os.path.join(folder, dep)
                        # if the file doesnt exist, add _wii to the end of the path and try again
                        if not os.path.exists(dep_path):
                            dep_path = dep_path + "_wii"
                        if os.path.exists(dep_path):
                            self.insert_file_below_selected(folder, dep_path)
    
    def insert_file_below_selected(self, project_folder, path):
        relative_path = os.path.relpath(path, project_folder)
        relative_path = relative_path.replace("\\", "/")
        if relative_path[0] == "/":
            relative_path = relative_path[1:]
        # add the file to the packfile
        self.pak.add_file_from_path(path, relative_path, self.list_widget.currentRow() + 1)
        # add the file to the list widget
        self.list_widget.insertItem(self.list_widget.currentRow() + 1, relative_path)
        self.update_pak_ordering()
    
    def add_item_below(self):
        # ask for relative folder
        folder = QFileDialog.getExistingDirectory(self, "Select the relative project folder")
        if folder:
            # ask for file
            file_name, _ = QFileDialog.getOpenFileName(self, "Open file", folder, "All files (*.*)")
            if file_name:
                relative_path = os.path.relpath(file_name, folder)
                relative_path = relative_path.replace("\\", "/")
                if relative_path[0] == "/":
                    relative_path = relative_path[1:]
                # add the file to the packfile
                self.pak.add_file_from_path(file_name, relative_path, self.list_widget.currentRow() + 1)
                # add the file to the list widget
                self.list_widget.insertItem(self.list_widget.currentRow() + 1, relative_path)
                self.update_pak_ordering()
        
    def replace_item(self):
        # get the selected item
        item = self.list_widget.selectedItems()[0]
        # get the path
        path = item.text()
        # ask for the new file
        file_name, _ = QFileDialog.getOpenFileName(self, "Open file", "", "All files (*.*)")
        if file_name:
            # replace the file
            self.pak.set_data_from_path(path, open(file_name, "rb").read())
            # deselect the item
            item.setSelected(False)
            # select the item again
            item.setSelected(True)
            # update the text edit
            self.select_item()
            if self.config["save_pak_on_update"]:
                self.save_file()

    def open_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open file", "", "Packfiles (*.pak)")
        if file_name:
            self.change_pak_path(file_name)
            # load the packfile
            self.pak = Packfile.from_binary_path(file_name)
            self.list_widget.clear()
            self.text_edit.clear()
            # deselect all items
            self.list_widget.clearSelection()
            for file in self.pak.files:
                self.list_widget.addItem(file.path)
    
    def item_changed(self, item):
        path = item.text()
        path = path.replace("\\", "/")
        if path[0] == "/":
            path = path[1:]
        self.pak.files[self.list_widget.row(item)].path = path
        self.update_pak_ordering()
    
    def to_text(self, path:str):
        path = path.lower()
        data = self.pak.get_data_from_path(path)
        if data:
            if path.endswith(".dct"):
                return DCT.from_binary(data).to_xml()
            elif path.endswith(".clb"):
                return CollectibleDatabase.from_binary(data, self.endian).to_xml()
            elif path.endswith(".sub"):
                return SubtitleFile.from_binary(data, endian=self.endian).to_xml()
            elif path.endswith(".bin"):
                return SceneFile.from_binary(data, endian=self.endian).to_json()
            elif path.endswith(".lua"):
                unluac_path = os.path.abspath(self.config["unluac_path"])
                luac_path = os.path.abspath(self.config["luac_path"])
                try:
                    data = Script.from_binary(data, unluac_path=unluac_path, luac_path=luac_path).to_text()
                except Exception as e:
                    # decompilation failed, this file is likely an EM2 script (which uses an undocumented Lua format)
                    # let the user edit hex since we can't edit the lua code
                    data = MainWindow.binary_to_hex(data)
                    self.show_message_box("Error", f"An error occurred while decompiling the script: {e}")
                return data
            elif path.endswith(".hkw") or path.endswith(".level") or path.endswith(".part") or path.endswith(".r3mt") or path.endswith(".rtsa") or path.endswith(".rcla"):
                return data.decode("utf-8")
            else:
                return MainWindow.binary_to_hex(data)
        return ""
    
    def setup_text_edit_style(self):
        self.text_edit.setCursorPosition(0, 0)
        # make the text editor use the font and font size defined in the config
        self.text_edit.setFont(QFont(self.config["font"], self.config["font_size"]))
        # change the background color to match the dark theme
        self.text_edit.setPaper(QColor(*self.config["text_background_color"]))
        self.text_edit.setPaper(QColor(*self.config["text_background_color"]))
        self.text_edit.setMarginsBackgroundColor(QColor(*self.config["text_background_color"]))
        self.text_edit.setMarginsForegroundColor(QColor(255, 255, 255))
        self.text_edit.setMarginsFont(QFont("Consolas", 10))
        self.text_edit.setMarginWidth(0, 50)
        # set cursor color to white
        self.text_edit.setCaretForegroundColor(QColor(255, 255, 255))
    
    def select_item(self):
        for item in self.list_widget.selectedItems():
            path = item.text()
            lexer = None
            if path.endswith(".bin"):
                # json syntax highlighting
                lexer = QsciLexerJSON(self.text_edit)
                # setup colors
                lexer.setColor(QColor(255, 255, 255), QsciLexerJSON.String)
                lexer.setColor(QColor(255, 91, 79), QsciLexerJSON.Number)
                # brackets and braces
                lexer.setColor(QColor(99, 255, 219), QsciLexerJSON.Operator)
                lexer.setColor(QColor(0, 255, 140), QsciLexerJSON.Keyword)
                # keys
                lexer.setColor(QColor(159, 99, 255), QsciLexerJSON.Property)
            elif path.endswith(".lua"):
                # lua syntax highlighting
                lexer = QsciLexerLua(self.text_edit)
                # setup colors
                lexer.setColor(QColor(255, 255, 255))
                lexer.setColor(QColor(128, 136, 255), QsciLexerLua.Keyword)
                lexer.setColor(QColor(255, 91, 79), QsciLexerLua.Number)
                lexer.setColor(QColor(183, 128, 255), QsciLexerLua.String)
                lexer.setColor(QColor(99, 255, 219), QsciLexerLua.Operator)
            elif path.endswith(".dct") or path.endswith(".clb") or path.endswith(".sub") or path.endswith(".r3mt") or path.endswith(".rtsa") or path.endswith(".rcla"):
                # xml syntax highlighting
                lexer = QsciLexerXML(self.text_edit)
                # setup colors
                lexer.setColor(QColor(255, 255, 255))
                lexer.setColor(QColor(128, 136, 255), QsciLexerXML.Tag)
                lexer.setColor(QColor(128, 208, 255), QsciLexerXML.Attribute)
                # attribute values
                lexer.setColor(QColor(255, 255, 255), QsciLexerXML.OtherInTag)
                lexer.setColor(QColor(255, 255, 255), QsciLexerXML.HTMLValue)
                lexer.setColor(QColor(183, 128, 255), QsciLexerXML.HTMLDoubleQuotedString)
                lexer.setColor(QColor(183, 128, 255), QsciLexerXML.HTMLSingleQuotedString)
                lexer.setColor(QColor(255, 255, 255), QsciLexerXML.Entity)
            else:
                # no syntax highlighting
                lexer = None
            if lexer:
                lexer.setDefaultPaper(QColor(*self.config["text_background_color"]))
                lexer.setPaper(QColor(*self.config["text_background_color"]))
                lexer.setFont(QFont(self.config["font"], self.config["font_size"]))
                self.text_edit.setLexer(lexer)
            self.text_edit.setText(self.to_text(path))
                # set the cursor to the start of the text
            self.setup_text_edit_style()
            
    def update_pak_ordering(self):
        new_files_order = []
        for i in range(self.list_widget.count()):
            path = self.list_widget.item(i).text()
            file = self.pak.get_file_from_path(path)
            new_files_order.append(file)
        self.pak.files = new_files_order

    def save_file(self):
        # if we have a file open, save it
        if self.pak_path != "":
            self.update_pak_ordering()
            self.pak.to_binary_path(self.pak_path, self.endian)
        else:
            self.save_file_as()

    def save_file_as(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Save file", "", "Packfiles (*.pak)")
        if file_name:
            self.change_pak_path(file_name)
            self.update_pak_ordering()
            self.pak.to_binary_path(file_name, self.endian)

    def add_item(self):
        # ask for relative folder
        folder = QFileDialog.getExistingDirectory(self, "Select the relative project folder")
        if folder:
            # ask for file
            file_name, _ = QFileDialog.getOpenFileName(self, "Open file", folder, "All files (*.*)")
            if file_name:
                relative_path = os.path.relpath(file_name, folder)
                relative_path = relative_path.replace("\\", "/")
                if relative_path[0] == "/":
                    relative_path = relative_path[1:]
                # add the file to the packfile
                self.pak.add_file_from_path(file_name, relative_path)
                # add the file to the list widget
                self.list_widget.addItem(relative_path)
                self.update_pak_ordering()

    def remove_item(self):
        for item in self.list_widget.selectedItems():
            # get the path
            path = item.text()
            # remove the file from the packfile
            self.pak.remove_file_from_path(path)
            # remove the item from the list widget
            self.list_widget.takeItem(self.list_widget.row(item))

    def rename_item(self):
        # allow the user to rename the item, when they press enter, we rename the item and its path in the packfile
        for item in self.list_widget.selectedItems():
            old_path = item.text()
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.list_widget.editItem(item)

    def update_data(self):
        for item in self.list_widget.selectedItems():
            path = item.text()
            data = self.text_edit.text()
            binary = b""
            if path.endswith(".dct"):
                binary = DCT.from_xml(data).to_binary()
            elif path.endswith(".clb"):
                binary = CollectibleDatabase.from_xml(data).to_binary()
            elif path.endswith(".sub"):
                binary = SubtitleFile.from_xml(data).to_binary(endian=self.endian)
            elif path.endswith(".bin"):
                binary = SceneFile.from_json(data).to_binary(endian=self.endian)
            elif path.endswith(".lua"):
                unluac_path = os.path.abspath(self.config["unluac_path"])
                luac_path = os.path.abspath(self.config["luac_path"])
                try:
                    binary = Script.from_text(data, unluac_path=unluac_path, luac_path=luac_path).to_binary()
                except Exception as e:
                    # the data is already in hex
                    binary = MainWindow.hex_to_binary(data)
            elif path.endswith(".hkw") or path.endswith(".level") or path.endswith(".part") or path.endswith(".r3mt") or path.endswith(".rtsa") or path.endswith(".rcla"):
                binary = data.encode("utf-8")
            else:
                binary = MainWindow.hex_to_binary(data)
            self.pak.set_data_from_path(path, binary)
        if self.config["save_pak_on_update"]:
            self.save_file()
    
    @staticmethod
    def binary_to_hex(binary):
        text = " ".join("{:02x}".format(c) for c in binary)
        # split into lines of 16 bytes
        lines = [text[i:i+48] for i in range(0, len(text), 48)]
        return "\n".join(lines)
    
    @staticmethod
    def hex_to_binary(text):
        text = text.replace(" ", "").replace("\n", "")
        return bytes.fromhex(text)

def main():
    # set the app id for the taskbar icon
    myappid = "abso1utezer0.BlueThinnerLite"
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    # check if java is installed
    if os.system("java -version") != 0:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("Java is not installed. Please install Java to use this application. It is required for decompiling Lua scripts.")
        msg.setWindowTitle("Error")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
        return
    
    app = QApplication(sys.argv)

    def excepthook(exctype, value, tb):
        # show the exception in a message box
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText(f"An error occurred: {value}")
        msg.setWindowTitle("Error")
        msg.setStandardButtons(QMessageBox.Ok)
        # add the traceback to the message box
        detailed_text = f"An error occurred: {value}\n\n"
        detailed_text += "Traceback (most recent call last):\n"
        for line in traceback.format_tb(tb):
            detailed_text += line
        
        save_button = msg.addButton("Save Current Pak", QMessageBox.ActionRole)
        def save_pak():
            window.save_file()
        save_button.clicked.connect(save_pak)

        copy_button = msg.addButton("Copy Detailed Info and Exit", QMessageBox.ActionRole)
        def copy_to_clipboard():
            app.clipboard().setText(detailed_text)
            close_app()
        copy_button.clicked.connect(copy_to_clipboard)

        def close_app():
            app.quit()
        
        msg.buttonClicked.connect(close_app)
        msg.exec_()
        
        # call the original excepthook
        sys.__excepthook__(exctype, value, traceback)

    # if icon.ico exists, set the icon
    if os.path.exists("assets/icon.ico"):
        app.setWindowIcon(QIcon("assets/icon.ico"))

    sys.excepthook = excepthook

    window = MainWindow()
    
    if not window.config["ignore_updates"]:
        # check the version against the github to see if there's a new build available
        try:
            # get the latest release from the github api
            # if the version is different, show a message box
            response = requests.get("https://api.github.com/repos/abso1utezer0/BlueThinnerLite/releases/latest")
            if response.status_code == 200:
                data = response.json()
                latest_version = data["tag_name"]
                if latest_version != APP_VERSION:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Information)
                    msg.setText(f"A new version of BlueThinner Lite is available: {latest_version}\n\n"
                                "Please download the new version from the releases page on the GitHub repository.")
                    msg.setWindowTitle("Update Available")
                    open_button = msg.addButton("Open Releases Page", QMessageBox.ActionRole)
                    def open_releases_page():
                        # open the releases page in the default browser
                        os.startfile("https://github.com/abso1utezer0/BlueThinnerLite/releases/latest")
                    open_button.clicked.connect(open_releases_page)
                    # add a button to ignore updates in the future
                    ignore_button = msg.addButton("Ignore Updates", QMessageBox.ActionRole)
                    def ignore_updates():
                        with open("config.json", "r") as f:
                            config = json.load(f)
                        config["ignore_updates"] = True
                        with open("config.json", "w") as f:
                            json.dump(config, f)
                    ignore_button.clicked.connect(ignore_updates)
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()
                else:
                    print("BlueThinner Lite is up to date")
            else:
                print(f"An error occurred while checking for updates: {response.status_code}")
        except Exception as e:
            print(f"An error occurred while checking for updates: {e}")
    
    window.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()