from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QToolButton, 
)
from PyQt6.QtGui import QIcon 
from PyQt6.QtCore import Qt, QSize, pyqtSignal


class ChargePage(QWidget):
    # Signali koje screen_manager povezuje automatski
    decrease_credit_requested = pyqtSignal(float)
    increase_credit_requested = pyqtSignal(float)
    back_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_amount = "0.00"
        self.card_id = "1111-2222-3333-4444"
        self.balance = "0"
        self.setup_ui()

    def update_card_info(self, card_id: str, balance: float):
        self.card_id = card_id
        self.balance = balance
        self.card_id_value_label.setText(card_id)
        self.balance_value_label.setText(f"{balance}.00 RSD")


    def setup_ui(self):
        self.setStyleSheet("font-family: Inter; background-color: white;")
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Header with back button and title
        header_layout = QHBoxLayout()
        self.back_button = self.create_button("back", border=True, icon=QIcon("./icons/back.svg"), iconSize=48)
        self.back_button.setFixedSize(40, 40)
        # Dodeli objectName za screen_manager
        self.back_button.setObjectName("btnChargeBack")
        
        self.title_label = QLabel("KREDIT NA KARTICI")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 28px; color: #E1B10D; margin-bottom:20px;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        header_layout.addWidget(self.back_button)
        header_layout.addStretch()
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()

        # Card Info (ID and Stanje in rows with padding)
        card_info_layout = QVBoxLayout()
        card_info_layout.setSpacing(12)

        info_container = QVBoxLayout()
        info_container.setContentsMargins(10, 0, 10, 0)

        style_1 = "font-size: 18px; color: #606060; font-weight: 600; font-family: Inter;"

        # ID row
        id_row = QHBoxLayout()
        id_label = QLabel("ID:")
        id_label.setStyleSheet(style_1)
        self.card_id_value_label = QLabel(self.card_id)
        self.card_id_value_label.setStyleSheet(style_1)
        id_row.addWidget(id_label)
        id_row.addStretch()
        id_row.addWidget(self.card_id_value_label)

        # Balance row
        balance_row = QHBoxLayout()
        balance_label = QLabel("STANJE:")
        balance_label.setStyleSheet(style_1)
        self.balance_value_label = QLabel(f"{self.balance} rsd")
        self.balance_value_label.setStyleSheet(style_1)
        balance_row.addWidget(balance_label)
        balance_row.addStretch()
        balance_row.addWidget(self.balance_value_label)

        info_container.addLayout(id_row)
        info_container.addLayout(balance_row)

        # Add to main info layout
        card_info_layout.addLayout(info_container)

        # Uneti iznos
        self.current_amount_label = QLabel(self.current_amount)
        self.current_amount_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.current_amount_label.setStyleSheet("font-weight: bold; font-size: 28px; color: #FFD33E; padding: 10px; margin-top: 4px; margin-bottom: 8px;")

        # Numpad
        numpad_layout = QGridLayout()
        self.number_buttons = {}
        numpad_layout.setHorizontalSpacing(6)
        numpad_layout.setVerticalSpacing(6)
        for i in range(1, 10):
            btn = self.create_button(str(i))
            self.number_buttons[str(i)] = btn
            numpad_layout.addWidget(btn, (i - 1) // 3, (i - 1) % 3)

        self.clear_button = self.create_button("C")
        self.zero_button = self.create_button("0")
        self.number_buttons["0"] = self.zero_button
        numpad_layout.addWidget(self.clear_button, 3, 0)
        numpad_layout.addWidget(self.zero_button, 3, 1)
        
        numpad_container = QWidget()
        numpad_container.setLayout(numpad_layout)
        numpad_container.setMaximumWidth(300)

        # Credit action buttons
        self.decrease_button = self.create_button("Umanji kredit", icon=QIcon("./icons/umanji.svg"), iconSize=[300, 100])
        self.increase_button = self.create_button("Uvećaj za unet iznos", icon=QIcon("./icons/uvecaj.svg"), iconSize=[300, 100])

        # Dodeli objectName za screen_manager
        self.decrease_button.setObjectName("btnDecreaseCredit")
        self.increase_button.setObjectName("btnIncreaseCredit")
        
        action_buttons_layout = QHBoxLayout()
        action_buttons_layout.setSpacing(12)
        action_buttons_layout.addWidget(self.decrease_button)
        action_buttons_layout.addWidget(self.increase_button)

        # Assemble all
        main_layout.addLayout(header_layout)
        main_layout.addLayout(card_info_layout)
        main_layout.addSpacing(12) 
        main_layout.addWidget(self.current_amount_label)
        main_layout.addWidget(numpad_container, alignment=Qt.AlignmentFlag.AlignHCenter)
        main_layout.addStretch()
        main_layout.addLayout(action_buttons_layout)

        self.connect_signals()

    def create_button(self, text, font_size=18, wide=False, border=False, icon=None, iconSize=0):
        if icon:
            btn = QToolButton()
            btn.setIcon(icon)
            if type(iconSize) == type(list()): 
                btn.setIconSize(QSize(iconSize[0], iconSize[1]))
            else:
                btn.setIconSize(QSize(iconSize, iconSize))
            return btn

        btn = QPushButton(text)
        btn.setFixedSize(82, 82 if not wide else 60)
        style = f"""
            QPushButton {{
                background-color: white;
                color: black;
                border: 1px solid #c0c0c0;
                border-radius: 8px;
                font-size: {font_size}px;
            }}
            QPushButton:pressed {{
                background-color: #eaeaea;
            }}
        """
        btn.setStyleSheet(style)

        if wide:
            btn.setMinimumHeight(60)
            btn.setMaximumWidth(280)

        return btn

    def connect_signals(self):
        # Samo numpad funkcije - ostalo će screen_manager da poveže
        for n, btn in self.number_buttons.items():
            btn.clicked.connect(lambda _, x=n: self.add_number(x))
        self.clear_button.clicked.connect(self.clear_amount)

    def add_number(self, number):
        if self.current_amount in ("0.00", "0"):
            self.current_amount = number
        else:
            if len(self.current_amount) < 6:
                self.current_amount += number
        self.current_amount_label.setText(self.current_amount)

    def get_current_amount(self):
        try:
            return float(self.current_amount)
        except ValueError:
            return 0.0

    def clear_amount(self):
        self.current_amount = "0.00"
        self.current_amount_label.setText(self.current_amount)

    def get_current_amount(self):
        """Vraća trenutno uneseni iznos kao float."""
        return float(self.current_amount.replace(".00", ""))

    def refresh_state(self, balance):
        self.clear_amount()
        self.balance = balance
        self.balance_value_label.setText(f"{balance}.00 RSD")