# helpers.py
from PyQt6.QtWidgets import QLineEdit

def wire_virtual_keyboard_for_login(login_widget, keyboard_manager):
    email_input = login_widget.findChild(QLineEdit, "EmailInput")
    password_input = login_widget.findChild(QLineEdit, "PswInput")

    if not (email_input and password_input):
        print("[KEYBOARD] Nema EmailInput ili PswInput na login ekranu!")
        return

    # Fokus eventi
    def on_focus_in(widget):
        def handler(event):
            keyboard_manager.show_keyboard_for_widget(widget)
            QLineEdit.focusInEvent(widget, event)
        return handler

    def on_focus_out(widget):
        def handler(event):
            QLineEdit.focusOutEvent(widget, event)
        return handler

    email_input.focusInEvent = on_focus_in(email_input)
    email_input.focusOutEvent = on_focus_out(email_input)

    password_input.focusInEvent = on_focus_in(password_input)
    password_input.focusOutEvent = on_focus_out(password_input)

    # Klik van → sakrij tastaturu
    root = login_widget

    def mousePressEvent(event):
        click_pos = event.pos()
        if (email_input.geometry().contains(click_pos) or
            password_input.geometry().contains(click_pos) or
            keyboard_manager.is_point_in_keyboard(click_pos)):
            keyboard_manager.cancel_hide()
        else:
            keyboard_manager.hide_keyboard()
        return super(type(root), root).mousePressEvent(event) if hasattr(super(type(root), root), 'mousePressEvent') else None

    root.mousePressEvent = mousePressEvent
