# screen_manager.py
from PyQt5 import QtWidgets
from PyQt5.QtCore import QObject, pyqtSignal
from typing import Dict, Any, Optional
from src.config import ScreenType
from src.helpers import wire_virtual_keyboard_for_login


class ScreenManager(QObject):
    screen_changed    = pyqtSignal(str, dict)
    login_requested   = pyqtSignal(str, str)
    logout_requested  = pyqtSignal()
    card_scanned      = pyqtSignal(str)
    category_selected = pyqtSignal(str)
    order_action      = pyqtSignal(str, dict)
    
    decrease_credit_requested = pyqtSignal(float)  # (card_id, amount)
    increase_credit_requested = pyqtSignal(float)  # (card_id, amount)
    charge_back_requested = pyqtSignal()  # Umesto back_requested(str)
    
    def __init__(self, stacked_widget: QtWidgets.QStackedWidget, keyboard_manager=None):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.keyboard_manager = keyboard_manager
        self.screens: Dict[str, QtWidgets.QWidget] = {}
        self.current_screen: Optional[str] = None
        self.screen_data: Dict[str, Any] = {}

        # map screen names to their indices in the QStackedWidget
        self.screen_indices = {
            ScreenType.WELCOME.value:  0,
            ScreenType.LOGIN.value:    1,
            ScreenType.CARD.value:     2,
            ScreenType.CATALOG.value:  3,
            ScreenType.CHARGE.value:   4,
        }

        self._register_screens()

    def _register_screens(self):
        for i in range(self.stacked_widget.count()):
            w = self.stacked_widget.widget(i)
            # assign by order; adjust if your widget order differs
            if i == 0:
                self.screens[ScreenType.WELCOME.value] = w
            elif i == 1:
                self.screens[ScreenType.LOGIN.value] = w
            elif i == 2:
                self.screens[ScreenType.CARD.value] = w
            elif i == 3:
                self.screens[ScreenType.CATALOG.value] = w
            elif i == 4:
                self.screens[ScreenType.CHARGE.value] = w
    
    def get_screen(self, screen_name: str):
        """Vraća screen widget po imenu."""
        return self.screens.get(screen_name)
    
    def switch_to_screen(self, screen_name: str, data: Optional[Dict[str, Any]] = None):
        """Prebacuje na zadati screen i prosleđuje mu eventualne podatke."""
        if screen_name not in self.screen_indices:
            print(f"Screen '{screen_name}' nije registrovan.")
            return

        # Sačuvaj podatke za taj screen, ukoliko ih ima
        if data is not None:
            self.screen_data[screen_name] = data

        # Postavi odgovarajući indeks u QStackedWidget
        index = self.screen_indices[screen_name]
        self.stacked_widget.setCurrentIndex(index)
        self.current_screen = screen_name

        if self.keyboard_manager and screen_name != ScreenType.LOGIN.value:
            self.keyboard_manager.hide_keyboard()

        # Obavesti sve koji slušaju da je ekran promenjen
        self.screen_changed.emit(screen_name, data or {})

        # Postavi specifične event listenere za novi screen, ako ih ima
        self._setup_screen_events(screen_name)

    def _setup_screen_events(self, screen_name: str):
        """Povezuje event listenere za dati screen."""
        if screen_name == ScreenType.LOGIN.value:
            self._setup_login_events()
        elif screen_name == ScreenType.CARD.value:
            self._setup_card_events()
        elif screen_name == ScreenType.CATALOG.value:
            self._setup_catalog_events()
        elif screen_name == ScreenType.CHARGE.value:
            self._setup_charge_events()  # NOVO: Setup za ChargePage

    def _setup_catalog_events(self):
        catalog_widget = self.screens.get(ScreenType.CATALOG.value)
        if not catalog_widget:
            return

        # 1) Category buttons…
        for i in range(1, 9):
            btn = catalog_widget.findChild(QtWidgets.QPushButton, f"btnCategory{i}")
            if not btn: continue
            try: btn.clicked.disconnect()
            except TypeError: pass
            btn.clicked.connect(lambda _, name=btn.text(): self._handle_category_click(name))

        # 2) Order actions (finish / cancel):
        page = getattr(catalog_widget, 'catalog_page', None)
        if page:
            try:
                page.order_action.disconnect()
            except TypeError:
                pass
            page.order_action.connect(self._handle_order_action)
    def _setup_login_events(self):
        login_widget = self.screens.get(ScreenType.LOGIN.value)
        if not login_widget:
            return

        login_button = login_widget.findChild(QtWidgets.QPushButton, "LoginButton")
        if login_button:
            try:
                login_button.clicked.disconnect()
            except TypeError:
                pass
            login_button.clicked.connect(self._handle_login_click)

        # Poveži tastaturu sa login poljima
        if hasattr(self, 'keyboard_manager') and self.keyboard_manager:
            wire_virtual_keyboard_for_login(login_widget, self.keyboard_manager)
            
    def _setup_card_events(self):
        """Povezuje event listener za Card screen (npr. dugme za skeniranje)."""
        card_widget = self.screens.get(ScreenType.CARD.value)
        if not card_widget:
            return

        # Pretpostavimo da je objectName dugmeta za skeniranje "btnScanCard"
        scan_btn = card_widget.findChild(QtWidgets.QPushButton, "btnScanCard")
        if scan_btn:
            try:
                scan_btn.clicked.disconnect()
            except TypeError:
                pass
            scan_btn.clicked.connect(self._handle_card_scan)

        # NOVO: Setup za ChargePage
    def _setup_charge_events(self):
        """Povezuje event listenere za Charge screen."""
        charge_widget = self.screens.get(ScreenType.CHARGE.value)
        if not charge_widget:
            return

        # Poveži back dugme
        back_btn = charge_widget.findChild(QtWidgets.QPushButton, "btnChargeBack") or \
                charge_widget.findChild(QtWidgets.QToolButton, "btnChargeBack")
        if back_btn:
            try:
                back_btn.clicked.disconnect()
            except TypeError:
                pass
            back_btn.clicked.connect(self._handle_charge_back)

        # Poveži decrease dugme
        decrease_btn = charge_widget.findChild(QtWidgets.QPushButton, "btnDecreaseCredit") or \
                    charge_widget.findChild(QtWidgets.QToolButton, "btnDecreaseCredit")
        if decrease_btn:
            try:
                decrease_btn.clicked.disconnect()
            except TypeError:
                pass
            decrease_btn.clicked.connect(self._handle_decrease_credit_click)

        # Poveži increase dugme
        increase_btn = charge_widget.findChild(QtWidgets.QPushButton, "btnIncreaseCredit") or \
                    charge_widget.findChild(QtWidgets.QToolButton, "btnIncreaseCredit")
        if increase_btn:
            try:
                increase_btn.clicked.disconnect()
            except TypeError:
                pass
            increase_btn.clicked.connect(self._handle_increase_credit_click)


    def _handle_decrease_credit_click(self):
        """Rukuje klikom na dugme za umanjenje kredita."""
        charge_widget = self.screens.get(ScreenType.CHARGE.value)
        if not charge_widget:
            return

        amount = charge_widget.get_current_amount()
        self.decrease_credit_requested.emit(amount)

    def _handle_increase_credit_click(self):
        """Rukuje klikom na dugme za uvećanje kredita."""
        charge_widget = self.screens.get(ScreenType.CHARGE.value)
        if not charge_widget:
            return

        amount = charge_widget.get_current_amount()
        self.increase_credit_requested.emit( amount)

    def _handle_charge_back(self):
        """Prosleđuje signal za povratak sa ChargePage."""
        self.charge_back_requested.emit()

    # Event handlers
    def _handle_card_scan(self):
        """Simulira ili čita unos ID-ja kartice i emituje signal."""
        card_widget = self.screens.get(ScreenType.CARD.value)
        if not card_widget:
            return

        id_input = "323232323232"
        self.card_scanned.emit(id_input)

    def _handle_category_click(self, category_name: str):
        """Emituje koji je category dugme pritisnuto."""
        self.category_selected.emit(category_name)
        
    def _handle_order_action(self, action: str, items: dict):
        """Rukuje order akcijama iz catalog screen-a."""
        #print(f"[Screen manager] emitujem signal sa vrednostima action : {action}, items {str(items)}")
        self.order_action.emit(action, items)

    def _handle_login_click(self):
        """Rukuje klikom na dugme za prijavu – čita email i lozinku i emituje signal."""
        login_widget = self.screens.get(ScreenType.LOGIN.value)
        if not login_widget:
            return

        # Pronađi polja za unos email-a i lozinke
        email_input = login_widget.findChild(QtWidgets.QLineEdit, "EmailInput")
        password_input = login_widget.findChild(QtWidgets.QLineEdit, "PswInput")

        if not email_input or not password_input:
            return

        # Preuzmi tekst iz polja
        email = email_input.text().strip()
        password = password_input.text()

        # Emituj signal za kontroler
        self.login_requested.emit(email, password)

    # NOVO: Handler metode za ChargePage signale
    def _handle_decrease_credit(self, card_id: str, amount: float):
        """Prosleđuje signal za umanjenje kredita."""
        self.decrease_credit_requested.emit(amount)

    def _handle_increase_credit(self, card_id: str, amount: float):
        """Prosleđuje signal za uvećanje kredita."""
        self.increase_credit_requested.emit(amount)

    def _handle_charge_back(self):
        """Prosleđuje signal za povratak sa ChargePage."""
        self.charge_back_requested.emit()