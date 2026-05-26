DARK_STYLESHEET = """
QMainWindow, QDialog {
    background-color: #1e1e2e;
    color: #cdd6f4;
}

QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: "Segoe UI", "Ubuntu", sans-serif;
    font-size: 13px;
}

QTabWidget::pane {
    border: 1px solid #313244;
    background-color: #1e1e2e;
    border-radius: 4px;
}

QTabBar::tab {
    background-color: #2a2a3e;
    color: #a6adc8;
    padding: 8px 18px;
    border: 1px solid #313244;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    min-width: 120px;
}

QTabBar::tab:selected {
    background-color: #1e1e2e;
    color: #cdd6f4;
    border-bottom: 2px solid #4a9eff;
}

QTabBar::tab:hover:!selected {
    background-color: #313244;
    color: #cdd6f4;
}

QGroupBox {
    background-color: #2a2a3e;
    border: 1px solid #313244;
    border-radius: 6px;
    margin-top: 14px;
    padding: 10px;
    color: #4a9eff;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    color: #4a9eff;
}

QPushButton {
    background-color: #4a9eff;
    color: #1e1e2e;
    border: none;
    border-radius: 5px;
    padding: 7px 16px;
    font-weight: bold;
    min-width: 90px;
}

QPushButton:hover {
    background-color: #6ab4ff;
}

QPushButton:pressed {
    background-color: #2d7dd2;
}

QPushButton:disabled {
    background-color: #45475a;
    color: #6c7086;
}

QPushButton[danger="true"] {
    background-color: #f38ba8;
    color: #1e1e2e;
}

QPushButton[danger="true"]:hover {
    background-color: #f5a0b7;
}

QPushButton[success="true"] {
    background-color: #a6e3a1;
    color: #1e1e2e;
}

QLabel {
    color: #cdd6f4;
    background: transparent;
}

QLabel[status="online"] {
    color: #a6e3a1;
    font-weight: bold;
}

QLabel[status="offline"] {
    color: #f38ba8;
    font-weight: bold;
}

QLabel[status="checking"] {
    color: #f9e2af;
    font-weight: bold;
}

QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 5px 8px;
    selection-background-color: #4a9eff;
    selection-color: #1e1e2e;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #4a9eff;
}

QComboBox {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 5px 8px;
    min-width: 140px;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #4a9eff;
    width: 0;
    height: 0;
    margin-right: 6px;
}

QComboBox QAbstractItemView {
    background-color: #2a2a3e;
    color: #cdd6f4;
    selection-background-color: #4a9eff;
    selection-color: #1e1e2e;
    border: 1px solid #45475a;
}

QScrollBar:vertical {
    background-color: #2a2a3e;
    width: 10px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background-color: #45475a;
    border-radius: 5px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #4a9eff;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background-color: #2a2a3e;
    height: 10px;
    border-radius: 5px;
}

QScrollBar::handle:horizontal {
    background-color: #45475a;
    border-radius: 5px;
    min-width: 30px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #4a9eff;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

QTableWidget {
    background-color: #2a2a3e;
    alternate-background-color: #313244;
    color: #cdd6f4;
    gridline-color: #45475a;
    border: 1px solid #45475a;
    border-radius: 4px;
    selection-background-color: #4a9eff;
    selection-color: #1e1e2e;
}

QTableWidget::item {
    padding: 4px 8px;
}

QHeaderView::section {
    background-color: #181825;
    color: #4a9eff;
    padding: 6px 8px;
    border: 1px solid #45475a;
    font-weight: bold;
}

QStatusBar {
    background-color: #181825;
    color: #a6adc8;
    border-top: 1px solid #313244;
}

QToolBar {
    background-color: #181825;
    border-bottom: 1px solid #313244;
    padding: 4px;
    spacing: 6px;
}

QProgressBar {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 4px;
    color: #cdd6f4;
    text-align: center;
}

QProgressBar::chunk {
    background-color: #4a9eff;
    border-radius: 3px;
}

QFrame[card="true"] {
    background-color: #2a2a3e;
    border: 1px solid #313244;
    border-radius: 8px;
}

QFrame[card="true"]:hover {
    border: 1px solid #4a9eff;
}

QMessageBox {
    background-color: #1e1e2e;
}

QMessageBox QLabel {
    color: #cdd6f4;
}

QSplitter::handle {
    background-color: #313244;
}

QCheckBox {
    color: #cdd6f4;
    spacing: 6px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #45475a;
    border-radius: 3px;
    background-color: #313244;
}

QCheckBox::indicator:checked {
    background-color: #4a9eff;
    border-color: #4a9eff;
}

QToolTip {
    background-color: #2a2a3e;
    color: #cdd6f4;
    border: 1px solid #4a9eff;
    padding: 4px;
    border-radius: 4px;
}
"""

STATUS_INDICATOR = {
    "online":    "background-color: #a6e3a1; border-radius: 7px; min-width: 14px; min-height: 14px; max-width: 14px; max-height: 14px;",
    "offline":   "background-color: #f38ba8; border-radius: 7px; min-width: 14px; min-height: 14px; max-width: 14px; max-height: 14px;",
    "checking":  "background-color: #f9e2af; border-radius: 7px; min-width: 14px; min-height: 14px; max-width: 14px; max-height: 14px;",
    "unknown":   "background-color: #45475a; border-radius: 7px; min-width: 14px; min-height: 14px; max-width: 14px; max-height: 14px;",
}
