from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGraphicsDropShadowEffect, QFrame,
    QScrollArea, QWidget, QScroller, QScrollerProperties
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QGuiApplication


class PurchaseConfirmationDialog(QDialog):
    purchase_confirmed = pyqtSignal()
    modal_closed = pyqtSignal()

    def __init__(self, parent=None, cart_items=None, timeout=None):
        super().__init__(parent.window() if parent and hasattr(parent, 'window') else parent)
        self.cart_items = cart_items or {}
        self.timeout = timeout
        self._setup_ui()

        if self.timeout:
            QTimer.singleShot(self.timeout, self.reject)

    def _setup_ui(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)

        # Glavni okvir
        self.main_frame = QFrame(self)
        self.main_frame.setObjectName("purchaseFrame")
        self.main_frame.setFixedSize(500, 400)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 5)
        self.main_frame.setGraphicsEffect(shadow)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(20, 20, 20, 20)
        outer_layout.addWidget(self.main_frame, 0, Qt.AlignmentFlag.AlignCenter)

        frame_layout = QVBoxLayout(self.main_frame)
        frame_layout.setContentsMargins(30, 30, 30, 30)
        frame_layout.setSpacing(15)

        # Naslov
        title_label = QLabel("Potvrda kupovine", parent=self.main_frame)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
            }
        """)
        frame_layout.addWidget(title_label)

        # Scroll area
        scroll_area = QScrollArea(self.main_frame)
        scroll_area.setFixedHeight(200)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setWidgetResizable(True)
        scroll_area.viewport().setStyleSheet("background-color: white;")
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollArea > QWidget > QWidget {
                background-color: white;
            }
        """)

        # Omogući touch scroll
        viewport = scroll_area.viewport()
        viewport.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, True)
        for gesture in (
            QScroller.ScrollerGestureType.TouchGesture,
            QScroller.ScrollerGestureType.LeftMouseButtonGesture
        ):
            QScroller.grabGesture(viewport, gesture)

        scroller = QScroller.scroller(viewport)
        props = scroller.scrollerProperties()
        props.setScrollMetric(QScrollerProperties.ScrollMetric.AxisLockThreshold, 1.0)
        scroller.setScrollerProperties(props)

        # Dodavanje stavki
        items_widget = QWidget()
        items_layout = QVBoxLayout(items_widget)
        items_layout.setSpacing(4)
        items_layout.setContentsMargins(0, 0, 0, 0)

        for prod_id, entry in self.cart_items.items():
            prod = entry.get('product', {})
            name = prod.get('name', f'Proizvod {prod_id}')
            price = prod.get('price', 0)
            qty = entry.get('quantity', 1)
            total_item = price * qty

            item_label = QLabel(f"{name} × {qty} kom — {total_item} RSD", parent=items_widget)
            item_label.setWordWrap(True)
            item_label.setStyleSheet("""
                QLabel {
                    background-color: white;
                    color: #000;
                    border: none;
                    padding: 4px 0px;
                    font-size: 14px;
                }
            """)
            items_layout.addWidget(item_label)

        items_layout.addStretch()
        scroll_area.setWidget(items_widget)
        frame_layout.addWidget(scroll_area)

        # Ukupna cena
        total = sum(
            entry.get('product', {}).get('price', 0) * entry.get('quantity', 1)
            for entry in self.cart_items.values()
        )
        total_label = QLabel(f"Ukupno: {total} RSD", parent=self.main_frame)
        total_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        total_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                padding: 5px 0px;
            }
        """)
        frame_layout.addWidget(total_label)

        frame_layout.addStretch()

        # Dugmad
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        btn_layout.addStretch()

        cancel_btn = QPushButton("Zatvori", parent=self.main_frame)
        cancel_btn.setObjectName("purchaseCancelBtn")
        cancel_btn.setFixedHeight(45)
        cancel_btn.setMinimumWidth(100)
        cancel_btn.clicked.connect(self._on_close)
        cancel_btn.setStyleSheet("""
            QPushButton#purchaseCancelBtn {
                background-color: #e0e0e0;
                color: #000;
                border: none;
                border-radius: 22px;
                font-size: 14px;
                padding: 0px 20px;
            }
        """)
        btn_layout.addWidget(cancel_btn)

        confirm_btn = QPushButton("Potvrdi", parent=self.main_frame)
        confirm_btn.setObjectName("purchaseConfirmBtn")
        confirm_btn.setFixedHeight(45)
        confirm_btn.setMinimumWidth(100)
        confirm_btn.clicked.connect(self._on_confirm)
        confirm_btn.setStyleSheet("""
            QPushButton#purchaseConfirmBtn {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 22px;
                font-size: 14px;
                padding: 0px 20px;
            }
        """)
        btn_layout.addWidget(confirm_btn)

        btn_layout.addStretch()
        frame_layout.addLayout(btn_layout)

        self.main_frame.setStyleSheet("""
            QFrame#purchaseFrame {
                background-color: white;
                border-radius: 15px;
                border: 1px solid #d6eaf8;
            }
        """)

    def _on_confirm(self):
        self.purchase_confirmed.emit()
        self.accept()

    def _on_close(self):
        self.modal_closed.emit()
        self.reject()

    def closeEvent(self, event):
        self.modal_closed.emit()
        super().closeEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        self.adjustSize()
        self._center_on_screen()

    def _center_on_screen(self):
        geo = QGuiApplication.primaryScreen().availableGeometry()
        dlg = self.frameGeometry()
        dlg.moveCenter(geo.center())
        self.move(dlg.topLeft())
