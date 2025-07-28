from __future__ import annotations

from typing import Callable, List, Optional, Tuple
from PyQt6.QtCore import Qt, QObject, pyqtSignal, QEvent
from PyQt6.QtGui import QColor, QGuiApplication
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGraphicsDropShadowEffect, QFrame, QGraphicsOpacityEffect
)
from typing import Optional, Callable, Any, List, Tuple
from enum import Enum
from PyQt6.QtWidgets import QDialog as QDialogBase  # zbog QDialog.DialogCode

class ModernMessageDialog(QDialog):
    """
    Jednostavan, konzistentan dijalog:
      - buttons: [(text, code, callback), ...]
      - klik => callback() (ako postoji), pa self.done(code)
      - exec() vraća taj 'code'
    """

    def __init__(
        self,
        parent=None,
        title: str = "",
        message: str = "",
        dialog_type: str = "info",
        auto_close: bool = False,
        timeout: int = 3000,
        buttons: Optional[List[Tuple[str, int, Optional[Callable[[], None]]]]] = None,
        fixed_size: tuple[int, int] = (500, 400)
    ):
        super().__init__(parent.window() if parent and hasattr(parent, 'window') else parent)

        self.dialog_type = dialog_type
        self.auto_close = auto_close
        self.timeout = timeout
        self.buttons = buttons or []
        self._fixed_size = fixed_size

        self._setup_ui(title, message)

        if self.auto_close:
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(self.timeout, lambda: self.done(QDialogBase.DialogCode.Rejected))

    # ---------------- UI ----------------

    def _setup_ui(self, title: str, message: str):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)

        self.main_frame = QFrame(self)
        self.main_frame.setObjectName("mainFrame")
        self.main_frame.setFixedSize(*self._fixed_size)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 5)
        self.main_frame.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.addWidget(self.main_frame)
        layout.setContentsMargins(20, 20, 20, 20)

        frame_layout = QVBoxLayout(self.main_frame)
        frame_layout.setSpacing(20)
        frame_layout.setContentsMargins(30, 30, 30, 30)

        # Icon
        icon_layout = QHBoxLayout()
        icon_layout.addStretch()

        icon_label = QLabel()
        icon_label.setFixedSize(60, 60)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        colors = self._get_colors_for_type(self.dialog_type)
        icon_text = self._get_icon_for_type(self.dialog_type)

        icon_label.setText(icon_text)
        icon_label.setStyleSheet(f"""
            QLabel {{
                background-color: {colors['icon_bg']};
                color: {colors['icon_color']};
                border-radius: 30px;
                font-size: 24px;
                font-weight: bold;
            }}
        """)

        icon_layout.addWidget(icon_label)
        icon_layout.addStretch()
        frame_layout.addLayout(icon_layout)

        # Title
        if title:
            title_label = QLabel(title)
            title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            title_label.setWordWrap(True)
            title_label.setStyleSheet("""
                QLabel {
                    font-size: 18px;
                    font-weight: bold;
                    color: #2c3e50;
                    margin: 0px;
                }
            """)
            frame_layout.addWidget(title_label)

        # Message
        message_label = QLabel(message)
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #5a6c7d;
                line-height: 1.4;
                margin: 5px 0px;
            }
        """)
        frame_layout.addWidget(message_label)

        frame_layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        if not self.auto_close:
            if self.buttons:
                for text, code, cb in self.buttons:
                    btn = QPushButton(text)
                    btn.setFixedHeight(45)
                    btn.clicked.connect(lambda _, c=code, callback=cb: self._finish(c, callback))
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {colors['button_bg']};
                            color: white;
                            border: none;
                            border-radius: 22px;
                            font-size: 14px;
                            font-weight: bold;
                            padding: 0px 20px;
                            min-width: 100px;
                        }}
                        QPushButton:hover {{
                            background-color: {colors['button_hover']};
                        }}
                        QPushButton:pressed {{
                            background-color: {colors['button_pressed']};
                        }}
                    """)
                    button_layout.addWidget(btn)
            else:
                # default OK
                ok_btn = QPushButton("U redu")
                ok_btn.setFixedHeight(45)
                ok_btn.clicked.connect(lambda: self._finish(QDialogBase.DialogCode.Accepted, None))
                ok_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {colors['button_bg']};
                        color: white;
                        border: none;
                        border-radius: 22px;
                        font-size: 14px;
                        font-weight: bold;
                        padding: 0px 20px;
                        min-width: 100px;
                    }}
                    QPushButton:hover {{
                        background-color: {colors['button_hover']};
                    }}
                    QPushButton:pressed {{
                        background-color: {colors['button_pressed']};
                    }}
                """)
                button_layout.addWidget(ok_btn)
        else:
            auto_label = QLabel("Automatsko zatvaranje…")
            auto_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            auto_label.setStyleSheet("""
                QLabel {
                    font-size: 12px;
                    color: #7f8c8d;
                    font-style: italic;
                }
            """)
            button_layout.addWidget(auto_label)

        frame_layout.addLayout(button_layout)

        self.main_frame.setStyleSheet(f"""
            QFrame#mainFrame {{
                background-color: white;
                border-radius: 15px;
                border: 1px solid {colors['border']};
            }}
        """)

    def showEvent(self, event):
        super().showEvent(event)
        self.adjustSize()
        self._center_on_screen()

    def _center_on_screen(self):
        geo_screen = QGuiApplication.primaryScreen().availableGeometry()
        geo_dlg = self.frameGeometry()
        geo_dlg.moveCenter(geo_screen.center())
        self.move(geo_dlg.topLeft())

    def _finish(self, code: int, callback: Optional[Callable[[], None]]):
        if callback:
            try:
                callback()
            except Exception as e:
                print("Button callback error:", e)
        self.done(code)

    # --------- helpers ---------

    def _get_colors_for_type(self, dialog_type: str):
        schemes = {
            "success": {
                "icon_bg": "#27ae60",
                "icon_color": "white",
                "button_bg": "#27ae60",
                "button_hover": "#229954",
                "button_pressed": "#1e8449",
                "border": "#d5f4e6",
            },
            "error": {
                "icon_bg": "#e74c3c",
                "icon_color": "white",
                "button_bg": "#e74c3c",
                "button_hover": "#c0392b",
                "button_pressed": "#a93226",
                "border": "#fadbd8",
            },
            "warning": {
                "icon_bg": "#f39c12",
                "icon_color": "white",
                "button_bg": "#f39c12",
                "button_hover": "#e67e22",
                "button_pressed": "#d68910",
                "border": "#fdebd0",
            },
            "info": {
                "icon_bg": "#3498db",
                "icon_color": "white",
                "button_bg": "#3498db",
                "button_hover": "#2980b9",
                "button_pressed": "#2471a3",
                "border": "#d6eaf8",
            },
            "question": {
                "icon_bg": "#8e44ad",
                "icon_color": "white",
                "button_bg": "#8e44ad",
                "button_hover": "#7d3c98",
                "button_pressed": "#6c3483",
                "border": "#e8daef"
            }
        }
        return schemes.get(dialog_type, schemes["info"])

    def _get_icon_for_type(self, dialog_type: str):
        icons = {
            "success": "✓",
            "error": "✕",
            "warning": "⚠",
            "info": "ℹ",
            "question": "?"
        }
        return icons.get(dialog_type, "ℹ")


class MessageType(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"
    QUESTION = "question"


class ModalService(QObject):
    """
    Servis za upravljanje modalnim dijalozima.
    """

    action_confirmed = pyqtSignal(str, object)  # (action_name, data)
    action_cancelled = pyqtSignal(str, object)  # (action_name, data)
    message_shown = pyqtSignal(str, str)        # (message_type, message)

    def __init__(self, parent_widget=None):
        super().__init__()
        self.parent_widget = parent_widget
        self._active_dialogs = {}

    def set_parent_widget(self, widget):
        self.parent_widget = widget

    # -------------------------------
    # Poruke
    # -------------------------------
    def show_message(
        self,
        message: str,
        title: str = "Poruka",
        msg_type: MessageType = MessageType.INFO,
        auto_close: bool = True,
        timeout: int = 2000,
        callback: Optional[Callable] = None
    ):
        try:
            dialog = ModernMessageDialog(
                parent=self.parent_widget,
                title=title,
                message=message,
                dialog_type=msg_type.value,
                auto_close=auto_close,
                timeout=timeout,
                buttons=None  # nema dugmadi kod auto_close
            )

            if callback:
                dialog.finished.connect(lambda _: callback())

            self.message_shown.emit(msg_type.value, message)
            dialog.exec()

        except Exception as e:
            print(f"Greška pri prikazivanju poruke: {e}")

    def show_empty_basket_warning(self, callback: Optional[Callable] = None):
        self.show_message(
            message="Dodajte proizvode pre završetka kupovine.",
            title="Prazna korpa",
            msg_type=MessageType.WARNING,
            auto_close=True,
            timeout=1500,
            callback=callback
        )

    def show_success_message(self, message: str, title: str = "Uspeh", callback: Optional[Callable] = None):
        self.show_message(
            message=message,
            title=title,
            msg_type=MessageType.SUCCESS,
            auto_close=False,
            callback=callback
        )

    def show_error_message(self, message: str, title: str = "Greška", callback: Optional[Callable] = None):
        self.show_message(
            message=message,
            title=title,
            msg_type=MessageType.ERROR,
            auto_close=False,
            callback=callback
        )

    # -------------------------------
    # Potvrdni dijalozi
    # -------------------------------
    def show_confirmation_dialog(
        self,
        action_name: str = "action",
        message: str = "Da li ste sigurni?",
        title: str = "Potvrda",
        on_confirm: Optional[Callable] = None,
        on_cancel: Optional[Callable] = None,
        **kwargs
    ):
        try:
            dialog = ModernMessageDialog(
                parent=self.parent_widget,
                title=title,
                message=message,
                dialog_type="question",
                buttons=[
                    ("Da", QDialog.DialogCode.Accepted, lambda: self._handle_confirmation(action_name, None, on_confirm)),
                    ("Ne", QDialog.DialogCode.Rejected, lambda: self._handle_cancellation(action_name, None, on_cancel)),
                ],
                **kwargs
            )

            self._active_dialogs[action_name] = dialog
            dialog.exec()

        except Exception as e:
            self.show_error_message(f"Greška pri prikazivanju dijaloga: {e}")

    def _handle_confirmation(self, action_name: str, data: Any, callback: Optional[Callable]):
        self.action_confirmed.emit(action_name, data)
        if callback:
            callback(data)
        self._active_dialogs.pop(action_name, None)

    def _handle_cancellation(self, action_name: str, data: Any, callback: Optional[Callable]):
        self.action_cancelled.emit(action_name, data)
        if callback:
            callback(data)
        self._active_dialogs.pop(action_name, None)

    def close_all_dialogs(self):
        for dialog in self._active_dialogs.values():
            if dialog:
                dialog.close()
        self._active_dialogs.clear()

    # -------------------------------
    # Delete confirmation
    # -------------------------------
    def ask_delete_confirmation(
        self,
        item_name: str,
        on_confirm: Optional[Callable] = None,
        on_cancel: Optional[Callable] = None
    ):
        self.show_confirmation_dialog(
            action_name="delete_item",
            title="Potvrda brisanja",
            message=f"Da li ste sigurni da želite da obrišete '{item_name}'?",
            on_confirm=on_confirm,
            on_cancel=on_cancel
        )

    def show_operation_result(
        self,
        success: bool,
        success_msg: str = "Operacija je uspešno završena",
        error_msg: str = "Došlo je do greške"
    ):
        if success:
            self.show_success_message(success_msg)
        else:
            self.show_error_message(error_msg)

# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    def on_closed(result):
        print(f"[DEMO] Modal zatvoren sa rezultatom: {result}")

    svc = ModalService()

    # 1) Obična info poruka sa auto-close
    svc.show_message(
        "Ovo je info poruka koja će nestati za 2s.",
        title="Info",
        msg_type="info",
        auto_close=True,
        timeout=2000,
        on_closed=on_closed
    )

    # 2) Poruka sa 'Nazad' i 'U redu'
    def back_cb():
        print("Kliknuto NAZAD!")

    def ok_cb():
        print("Kliknuto OK!")

    svc.show_with_back(
        title="Pitanje",
        message="Da li želiš da se vratiš ili potvrdiš?",
        on_back=back_cb,
        on_ok=ok_cb,
        on_closed=on_closed
    )

    sys.exit(app.exec())
