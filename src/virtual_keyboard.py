from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QGridLayout, QFrame, QSizePolicy, QApplication, QLineEdit)
from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor

class VirtualKeyboard(QFrame):
    """Moderna virtuelna tastatura za touchscreen uređaje"""
    
    # Signali
    key_pressed = pyqtSignal(str)  # Emituje kada se pritisne taster
    backspace_pressed = pyqtSignal()  # Emituje za backspace
    enter_pressed = pyqtSignal()  # Emituje za enter
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_caps_lock = False
        self.is_shift = False
        self.target_widget = None  # Widget koji prima input
        
        self.setupUI()
        self.setupAnimation()


    def setupUI(self):
        """Postavlja UI tastaturi"""
        self.setFixedSize(800, 300)
        self.setFrameStyle(QFrame.Box)
        self.setStyleSheet("""
            VirtualKeyboard {
                background-color: #2b2b2b;
                border: 2px solid #404040;
                border-radius: 12px;
            }
        """)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(5)
        
        # Kreiraj redove tastature
        self.create_number_row(main_layout)
        self.create_first_letter_row(main_layout)
        self.create_second_letter_row(main_layout)
        self.create_third_letter_row(main_layout)
        self.create_bottom_row(main_layout)
        
    def setupAnimation(self):
        """Postavlja animacije za prikaz/sakrivanje"""
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        
    def create_key_button(self, text, width_factor=1, is_special=False):
        """Kreira dugme za taster"""
        btn = QPushButton(text)
        btn.setFixedSize(int(60 * width_factor), 50)
        btn.setFont(QFont("Arial", 12, QFont.Bold))
        
        if is_special:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #404040;
                    color: #ffffff;
                    border: 1px solid #555555;
                    border-radius: 8px;
                    font-weight: bold;
                }
                QPushButton:pressed {
                    background-color: #303030;
                    border: 1px solid #777777;
                }
            """)
        else:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #f0f0f0;
                    color: #333333;
                    border: 1px solid #cccccc;
                    border-radius: 8px;
                    font-weight: bold;
                }
                QPushButton:pressed {
                    background-color: #d0d0d0;
                    border: 1px solid #888888;
                }
            """)
        
        return btn
        
    def create_number_row(self, parent_layout):
        """Kreira red sa brojevima"""
        layout = QHBoxLayout()
        layout.setSpacing(3)
        
        # Brojevi 1-0
        numbers = "1234567890"
        symbols = "!@#$%^&*()"
        
        for i, (num, sym) in enumerate(zip(numbers, symbols)):
            btn = self.create_key_button(num)
            btn.setProperty("shift_char", sym)
            btn.clicked.connect(lambda checked, char=num, s_char=sym: self.on_key_click(char, s_char))
            layout.addWidget(btn)
            
        # Backspace
        backspace_btn = self.create_key_button("⌫", width_factor=1.5, is_special=True)
        backspace_btn.clicked.connect(self.on_backspace_click)
        layout.addWidget(backspace_btn)
        
        parent_layout.addLayout(layout)
        
    def create_first_letter_row(self, parent_layout):
        """Kreira prvi red slova (QWERTY)"""
        layout = QHBoxLayout()
        layout.setSpacing(3)
        
        letters = "qwertyuiop"
        special_chars = "[]\\;',./"
        
        # Tab dugme
        tab_btn = self.create_key_button("Tab", width_factor=1.2, is_special=True)
        tab_btn.clicked.connect(lambda: self.key_pressed.emit("\t"))
        layout.addWidget(tab_btn)
        
        for letter in letters:
            btn = self.create_key_button(letter.upper())
            btn.clicked.connect(lambda checked, char=letter: self.on_letter_click(char))
            layout.addWidget(btn)
            
        parent_layout.addLayout(layout)
        
    def create_second_letter_row(self, parent_layout):
        """Kreira drugi red slova"""
        layout = QHBoxLayout()
        layout.setSpacing(3)
        
        letters = "asdfghjkl"
        
        # Caps Lock
        self.caps_btn = self.create_key_button("Caps", width_factor=1.3, is_special=True)
        self.caps_btn.clicked.connect(self.toggle_caps_lock)
        layout.addWidget(self.caps_btn)
        
        for letter in letters:
            btn = self.create_key_button(letter.upper())
            btn.clicked.connect(lambda checked, char=letter: self.on_letter_click(char))
            layout.addWidget(btn)
            
        # Enter (sa drugačijim stilom da naglasi da završava unos)
        enter_btn = self.create_key_button("Enter ✓", width_factor=1.3, is_special=True)
        enter_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: 1px solid #005a9e;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:pressed {
                background-color: #005a9e;
                border: 1px solid #004578;
            }
        """)
        enter_btn.clicked.connect(self.on_enter_click)
        layout.addWidget(enter_btn)
        
        parent_layout.addLayout(layout)
        
    def create_third_letter_row(self, parent_layout):
        """Kreira treći red slova"""
        layout = QHBoxLayout()
        layout.setSpacing(3)
        
        letters = "zxcvbnm"
        
        # Shift
        self.shift_btn = self.create_key_button("Shift", width_factor=1.5, is_special=True)
        self.shift_btn.clicked.connect(self.toggle_shift)
        layout.addWidget(self.shift_btn)
        
        for letter in letters:
            btn = self.create_key_button(letter.upper())
            btn.clicked.connect(lambda checked, char=letter: self.on_letter_click(char))
            layout.addWidget(btn)
            
        # Drugi shift
        shift_btn2 = self.create_key_button("Shift", width_factor=1.5, is_special=True)
        shift_btn2.clicked.connect(self.toggle_shift)
        layout.addWidget(shift_btn2)
        
        parent_layout.addLayout(layout)
        
    def create_bottom_row(self, parent_layout):
        """Kreira donji red (space, specijalni karakteri)"""
        layout = QHBoxLayout()
        layout.setSpacing(3)
        
        # Ctrl
        ctrl_btn = self.create_key_button("Ctrl", width_factor=1.2, is_special=True)
        layout.addWidget(ctrl_btn)
        
        # Alt
        alt_btn = self.create_key_button("Alt", width_factor=1.2, is_special=True)
        layout.addWidget(alt_btn)
        
        # Space (najveće dugme)
        space_btn = self.create_key_button("Space", width_factor=6, is_special=True)
        space_btn.clicked.connect(lambda: self.key_pressed.emit(" "))
        layout.addWidget(space_btn)
        
        # Specijalni karakteri
        special_chars = ["@", ".", "-", "_"]
        for char in special_chars:
            btn = self.create_key_button(char)
            btn.clicked.connect(lambda checked, c=char: self.key_pressed.emit(c))
            layout.addWidget(btn)
            
        parent_layout.addLayout(layout)
        
    def on_key_click(self, normal_char, shift_char):
        """Obrađuje klik na broj/simbol dugme"""
        if self.is_shift:
            self.key_pressed.emit(shift_char)
            self.is_shift = False
            self.update_shift_style()
        else:
            self.key_pressed.emit(normal_char)
            
    def on_letter_click(self, letter):
        """Obrađuje klik na slovo"""
        if self.is_caps_lock or self.is_shift:
            self.key_pressed.emit(letter.upper())
        else:
            self.key_pressed.emit(letter.lower())
            
        if self.is_shift:
            self.is_shift = False
            self.update_shift_style()
            
    def on_backspace_click(self):
        """Obrađuje backspace"""
        self.backspace_pressed.emit()
        
    def on_enter_click(self):
        """Obrađuje enter"""
        self.enter_pressed.emit()
        
    def toggle_caps_lock(self):
        """Uključuje/isključuje caps lock"""
        self.is_caps_lock = not self.is_caps_lock
        self.update_caps_style()
        
    def toggle_shift(self):
        """Uključuje/isključuje shift"""
        self.is_shift = not self.is_shift
        self.update_shift_style()
        
    def update_caps_style(self):
        """Ažurira stil caps dugmeta"""
        if self.is_caps_lock:
            self.caps_btn.setStyleSheet("""
                QPushButton {
                    background-color: #0078d4;
                    color: white;
                    border: 1px solid #005a9e;
                    border-radius: 8px;
                    font-weight: bold;
                }
            """)
        else:
            self.caps_btn.setStyleSheet("""
                QPushButton {
                    background-color: #404040;
                    color: #ffffff;
                    border: 1px solid #555555;
                    border-radius: 8px;
                    font-weight: bold;
                }
            """)
            
    def update_shift_style(self):
        """Ažurira stil shift dugmeta"""
        style = """
            QPushButton {
                background-color: %s;
                color: white;
                border: 1px solid %s;
                border-radius: 8px;
                font-weight: bold;
            }
        """ % (("#0078d4", "#005a9e") if self.is_shift else ("#404040", "#555555"))
        
        self.shift_btn.setStyleSheet(style)
        
    def set_target_widget(self, widget):
        """Postavlja ciljni widget koji prima input"""
        self.target_widget = widget
        
    def show_animated(self, target_pos=None):
        """Prikazuje tastaturu sa animacijom"""
        print("[KEYBOARD WIDGET] Show animated called")
        
        if not self.isVisible():
            print("[KEYBOARD WIDGET] Making keyboard visible")
            self.show()
            
        if target_pos:
            start_rect = QRect(target_pos.x(), target_pos.y() + 100, self.width(), 0)
            end_rect = QRect(target_pos.x(), target_pos.y(), self.width(), self.height())
        else:
            # Centriraj na parent
            if self.parent():
                parent_rect = self.parent().rect()
                x = (parent_rect.width() - self.width()) // 2
                y = parent_rect.height() - self.height() - 20
                start_rect = QRect(x, parent_rect.height(), self.width(), 0)
                end_rect = QRect(x, y, self.width(), self.height())
            else:
                return
                
        print(f"[KEYBOARD WIDGET] Animation from {start_rect} to {end_rect}")
        self.animation.setStartValue(start_rect)
        self.animation.setEndValue(end_rect)
        self.animation.start()
        
    def hide_animated(self):
        """Sakriva tastaturu sa animacijom"""
        print(f"[KEYBOARD WIDGET] Hide animated called, visible: {self.isVisible()}")
        
        if self.isVisible():
            current_rect = self.geometry()
            end_rect = QRect(current_rect.x(), current_rect.y() + current_rect.height(), 
                           current_rect.width(), 0)
            
            print(f"[KEYBOARD WIDGET] Hide animation from {current_rect} to {end_rect}")
            self.animation.setStartValue(current_rect)
            self.animation.setEndValue(end_rect)
            
            # Disconnect any previous connections to prevent multiple calls
            try:
                self.animation.finished.disconnect()
            except:
                pass
                
            self.animation.finished.connect(self._on_hide_finished)
            self.animation.start()
        else:
            print("[KEYBOARD WIDGET] Already hidden")
            
    def _on_hide_finished(self):
        """Called when hide animation finishes"""
        print("[KEYBOARD WIDGET] Hide animation finished - hiding widget")
        self.hide()
        # Disconnect to prevent memory leaks
        try:
            self.animation.finished.disconnect()
        except:
            pass

class KeyboardManager:
    """Manager klasa za upravljanje virtuelnom tastaturom"""
    
    def __init__(self, parent_widget):
        self.parent_widget = parent_widget
        self.keyboard = VirtualKeyboard(parent_widget)
        self.current_input_widget = None
        self.is_keyboard_active = False
        self.hide_timer = None
        
        # Povezuj signale
        self.keyboard.key_pressed.connect(self.on_key_pressed)
        self.keyboard.backspace_pressed.connect(self.on_backspace)
        self.keyboard.enter_pressed.connect(self.on_enter)
        
        # Sakrij tastaturu na početku
        self.keyboard.hide()
        
        print("[KEYBOARD] KeyboardManager initialized")

    def setVisible(self, visible: bool):
        """Prikazuje ili sakriva tastaturu."""
        if visible:
            self.keyboard.show()
            self.keyboard.raise_()
        else:
            self.keyboard.hide()

        
    def show_keyboard_for_widget(self, widget):
        """Prikazuje tastaturu za određeni widget"""
        print(f"[KEYBOARD] Show for widget: {widget}")
        
        # PRVO otkaži sve postojeće timere
        if self.hide_timer:
            print("[KEYBOARD] Canceling existing timer")
            self.hide_timer.stop()
            self.hide_timer = None
            
        self.current_input_widget = widget
        self.keyboard.set_target_widget(widget)
        self.is_keyboard_active = True
        
        print(f"[KEYBOARD] Keyboard active: {self.is_keyboard_active}")
        
        # Pozicioniraj tastaturu
        widget_pos = widget.mapToGlobal(widget.rect().bottomLeft())
        parent_pos = self.parent_widget.mapFromGlobal(widget_pos)
        
        # TEMP: Pokušaj bez animacije
        if self.parent_widget:
            parent_rect = self.parent_widget.rect()
            x = (parent_rect.width() - self.keyboard.width()) // 2
            y = parent_rect.height() - self.keyboard.height() - 20
            self.keyboard.setGeometry(x, y, self.keyboard.width(), self.keyboard.height())
            self.keyboard.show()
            self.keyboard.raise_()
            print("[KEYBOARD] Keyboard shown without animation")
        
        # Original animacija (comment out for now)
        # self.keyboard.show_animated(parent_pos)
        
    def hide_keyboard(self):
        """Sakriva tastaturu sa delay-om (može se otkazati)"""
        print(f"[KEYBOARD] Hide requested. Active: {self.is_keyboard_active}")
        
        if not self.is_keyboard_active:
            return
            
        # Kreiraj timer za sakrivanje sa 0.3 sekunde delay-a
        self.hide_timer = QTimer()
        self.hide_timer.timeout.connect(self.force_hide_keyboard)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.start(1)  # 0.3 sekunde delay
        print("[KEYBOARD] Hide timer started (0.3s)")
        
    def force_hide_keyboard(self):
        """Forsirano sakriva tastaturu odmah"""
        print("[KEYBOARD] Force hide keyboard called")
        
        self.is_keyboard_active = False
        self.current_input_widget = None
        if self.hide_timer:
            self.hide_timer.stop()
            self.hide_timer = None
            
        # TEMP: Bez animacije
        self.keyboard.hide()
        print("[KEYBOARD] Keyboard hidden without animation")
        
    def cancel_hide(self):
        """Otkazuje sakrivanje tastature"""
        if self.hide_timer:
            print("[KEYBOARD] Hide canceled")
            self.hide_timer.stop()
            self.hide_timer = None
            
    def is_point_in_keyboard(self, point):
        """Proverava da li je tačka unutar tastature"""
        if not self.keyboard.isVisible():
            return False
            
        keyboard_contains = self.keyboard.geometry().contains(point)
        print(f"[KEYBOARD] Point {point} in keyboard: {keyboard_contains}")
        return keyboard_contains
        
    def switch_to_widget(self, new_widget):
        """Prebacuje tastaturu na novi widget bez sakrivanja"""
        print(f"[KEYBOARD] Switch to widget: {new_widget}, Active: {self.is_keyboard_active}")
        
        if not self.is_keyboard_active:
            # Ako tastatura nije aktivna, prikaži je
            print("[KEYBOARD] Keyboard not active - showing it")
            self.show_keyboard_for_widget(new_widget)
            return
            
        if new_widget != self.current_input_widget:
            self.cancel_hide()  # Otkaži bilo koji postojeći timer
            self.current_input_widget = new_widget
            self.keyboard.set_target_widget(new_widget)
            print("[KEYBOARD] Widget switched successfully")
            # Tastatura ostaje na istoj poziciji - samo menja target
        
    def on_key_pressed(self, key):
        """Obrađuje pritisak tastera"""
        # Otkaži sakrivanje jer korisnik interaguje sa tastaturom
        self.cancel_hide()
        
        if self.current_input_widget and hasattr(self.current_input_widget, 'insert'):
            self.current_input_widget.insert(key)
        elif self.current_input_widget and hasattr(self.current_input_widget, 'setText'):
            current_text = self.current_input_widget.text()
            cursor_pos = getattr(self.current_input_widget, 'cursorPosition', lambda: len(current_text))()
            new_text = current_text[:cursor_pos] + key + current_text[cursor_pos:]
            self.current_input_widget.setText(new_text)
            if hasattr(self.current_input_widget, 'setCursorPosition'):
                self.current_input_widget.setCursorPosition(cursor_pos + 1)
                
    def on_backspace(self):
        """Obrađuje backspace"""
        # Otkaži sakrivanje jer korisnik interaguje sa tastaturom
        self.cancel_hide()
        
        if self.current_input_widget and hasattr(self.current_input_widget, 'backspace'):
            self.current_input_widget.backspace()
        elif self.current_input_widget and hasattr(self.current_input_widget, 'setText'):
            current_text = self.current_input_widget.text()
            cursor_pos = getattr(self.current_input_widget, 'cursorPosition', lambda: len(current_text))()
            if cursor_pos > 0:
                new_text = current_text[:cursor_pos-1] + current_text[cursor_pos:]
                self.current_input_widget.setText(new_text)
                if hasattr(self.current_input_widget, 'setCursorPosition'):
                    self.current_input_widget.setCursorPosition(cursor_pos - 1)
                    
    def on_enter(self):
        """Obrađuje enter - sakriva tastaturu i završava unos"""
        print("[KEYBOARD] Enter pressed - hiding keyboard")
        
        # Ako je trenutni widget email, prebaci focus na password
        if (hasattr(self, 'parent_widget') and 
            self.current_input_widget and 
            hasattr(self.current_input_widget, 'objectName')):
            
            # Pokušaj da nađeš sledeći input field
            parent = self.parent_widget
            if hasattr(parent, 'focusNextChild'):
                parent.focusNextChild()
                return
        
        # Inače, samo sakrij tastaturu
        self.force_hide_keyboard()
    
    def is_global_point_in_keyboard(self, gpos):
        """Da li je globalna tačka unutar tastature?"""
        if not self.keyboard.isVisible():
            return False
        # pretvori tastaturin rect u globalne koordinate
        geom = self.keyboard.geometry()
        top_left = self.keyboard.mapToGlobal(geom.topLeft())
        global_rect = QRect(top_left, geom.size())
        return global_rect.contains(gpos)

# Demo kod za testiranje
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QLineEdit, QLabel
    
    app = QApplication(sys.argv)
    
    # Test window
    window = QMainWindow()
    window.setWindowTitle("Virtual Keyboard Demo")
    window.setGeometry(200, 200, 1000, 600)
    
    central_widget = QWidget()
    window.setCentralWidget(central_widget)
    
    layout = QVBoxLayout(central_widget)
    
    # Test input fields
    layout.addWidget(QLabel("Email:"))
    email_input = QLineEdit()
    layout.addWidget(email_input)
    
    layout.addWidget(QLabel("Password:"))
    password_input = QLineEdit()
    password_input.setEchoMode(QLineEdit.Password)
    layout.addWidget(password_input)
    
    # Keyboard manager
    keyboard_manager = KeyboardManager(central_widget)
    
    # Connect focus events - UPROŠĆENO I ISPRAVNO
    def on_email_focus_in(event):
        print("Email focus IN")
        keyboard_manager.show_keyboard_for_widget(email_input)
        # Pozovi originalni focus event
        QLineEdit.focusInEvent(email_input, event)
        
    def on_email_focus_out(event):
        print("Email focus OUT")
        # NE sakrivaj tastaturu - samo pozovi originalni event
        QLineEdit.focusOutEvent(email_input, event)
        
    def on_password_focus_in(event):
        print("Password focus IN")
        keyboard_manager.show_keyboard_for_widget(password_input)
        QLineEdit.focusInEvent(password_input, event)
        
    def on_password_focus_out(event):
        print("Password focus OUT") 
        QLineEdit.focusOutEvent(password_input, event)
    
    # VAŽNO: Postavi custom event handlere
    email_input.focusInEvent = on_email_focus_in
    email_input.focusOutEvent = on_email_focus_out
    password_input.focusInEvent = on_password_focus_in
    password_input.focusOutEvent = on_password_focus_out
    
    # Poboljšano sakrivanje tastature
    def mousePressEvent(event):
        """Sakrij tastaturu samo ako klik nije na tastaturi ili input fieldu"""
        click_pos = event.globalPos()

        print(f"Mouse click at: {click_pos}")
        
        # Proveri da li je klik na input fieldu
        email_rect = email_input.geometry()
        password_rect = password_input.geometry()
        
        if (email_rect.contains(click_pos) or 
            password_rect.contains(click_pos) or
            keyboard_manager.is_point_in_keyboard(click_pos)):
            # Ne sakrivaj tastaturu
            print("Click on input or keyboard - keeping keyboard open")
            keyboard_manager.cancel_hide()
            return
            
        # Klik je van svih relevantnih elemenata - sakrij sa delay-om
        print("Click outside - hiding keyboard with delay")
        keyboard_manager.hide_keyboard()
        
    central_widget.mousePressEvent = mousePressEvent
    
    window.show()
    sys.exit(app.exec_())