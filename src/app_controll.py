from src.services.pn532 import create_nfc_reader
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from PyQt5.QtWidgets import QMessageBox, QWidget, QDialog

from src.config import ScreenType
from src.services.web_api import (
    login, get_products, checkout_service,
    pay_card_info, write_nfc_card, read_nfc_card, change_balance
)
from src.msg_modal import ModernMessageDialog, ModalService
from src.confirm_modal import PurchaseConfirmationDialog
class AppController(QObject):
    """Main application controller handling business logic and screen transitions."""
    categories_loaded = pyqtSignal(list)

    def __init__(self, parent: QWidget, screen_manager):
        super().__init__(parent)
        self.parent_widget = parent
        self.screen_manager = screen_manager

        # User/session state
        self.bearer_token = None
        self.user_group_id = None
        self.card_id = None
        self.slug = None
        self.balance = 0
        self.pin = "123456"
        self.categories = []
        self.next_screen_after_card = None
        
        # NFC reader setup
        self.nfc_reader = create_nfc_reader(parent, self._on_card_uid)

        self.modal = ModalService()

        # Connect all signals
        self._connect_signals()
        

    def _connect_signals(self):
        """Povezuje sve potrebne signale."""
        sm = self.screen_manager
        signal_mappings = [
            (sm.screen_changed, self._on_screen_changed),
            (sm.login_requested, self._on_login),
            (sm.card_scanned, self._on_card_scanned),
            (sm.category_selected, self._on_category_selected),
            (sm.order_action, self._on_order_action),
            (sm.decrease_credit_requested, lambda amount: self._handle_credit_change(amount, is_increase=False)),
            (sm.increase_credit_requested, lambda amount: self._handle_credit_change(amount, is_increase=True)),
            (sm.charge_back_requested, self._on_charge_back),
            (sm.logout_requested, self._on_logout_requested)
        ]
        
        for signal, handler in signal_mappings:
            signal.connect(handler)

    def _show_confirmation_dialog(self, title: str, text: str, callback_on_yes=None, callback_on_no=None):
        dialog = ModernMessageDialog(
            parent=self.parent_widget,
            title=title,
            message=text,
            dialog_type="question",
            buttons=[
                ("Da", QDialog.Accepted, callback_on_yes),
                ("Ne", QDialog.Rejected, callback_on_no),
            ],
        )

        result = dialog.exec()
        if result == QDialog.Accepted:
            if callback_on_yes:
                callback_on_yes()
        else:
            if callback_on_no:
                callback_on_no()

    def _show_message(self, title: str, text: str, msg_type: str = "info",
                    auto_close: bool = False, timeout: int = 3000):
        dialog = ModernMessageDialog(
            parent=self.parent_widget,
            title=title,
            message=text,
            dialog_type=msg_type,
            auto_close=auto_close,
            timeout=timeout,
            buttons=[
                ("Nazad", QDialog.Rejected, self._handle_back)
            ] if not auto_close else None
        )
        dialog.exec()
    
    def _handle_back(self):
        self.screen_manager.switch_to_screen(ScreenType.CARD.value)

    def _update_charge_page_balance(self):
        """Ažurira stanje na charge stranici."""
        charge_page = self.screen_manager.screens.get(ScreenType.CHARGE.value)
        if charge_page:
            charge_page.refresh_state(self.balance)

    def _switch_to_card_screen(self):
        """Prebacuje na card screen i ažurira charge page."""
        self._update_charge_page_balance()
        self.screen_manager.switch_to_screen(ScreenType.CARD.value)

    def _on_screen_changed(self, screen_name: str, data: dict):
        """Obrađuje promene ekrana."""
        print(f"Screen changed to: {screen_name}")
        if screen_name == ScreenType.WELCOME.value:
            QTimer.singleShot(3000, lambda: self.screen_manager.switch_to_screen(ScreenType.LOGIN.value))
        elif screen_name == ScreenType.CARD.value:
            print("Starting NFC reader...")
            self.nfc_reader.start()
        else:
            self.nfc_reader.stop()

    def start_app(self):
        """Pokretanje aplikacije."""
        self.screen_manager.switch_to_screen(ScreenType.WELCOME.value)

    def _on_login(self, email: str, password: str):
        """Obrađuje zahteve za prijavu."""
        print(f"Login requested: {email}")
        
        if not (email and password):
            self._show_message(
                "Neuspešan login",
                "Nisu uneti kredencijali",
                msg_type="warning",
                auto_close=True,
                timeout=1500
            )
            return

        resp = login(email, password)
        if not resp:
            self._show_message(
            "Neuspešan login",
            "Vaša porudžbina je uspešno otkazana.",
            msg_type="warning",
            auto_close=True,
            timeout=1500
            )
            return

        self.bearer_token = resp.get("token")
        self.user_group_id = resp.get("user_group_id")

        # Mapiranje grupa na sledeće ekrane
        group_screen_mapping = {
            5: ScreenType.CATALOG.value,
            4: ScreenType.CHARGE.value,
            3: ScreenType.CARD.value
        }
        
        self.next_screen_after_card = group_screen_mapping.get(self.user_group_id)

        if self.user_group_id == 5:
            # Za katalog, učitaj proizvode
            if self._load_categories():
                self.screen_manager.switch_to_screen(ScreenType.CARD.value)
        elif self.user_group_id == 4:
            self.screen_manager.switch_to_screen(ScreenType.CARD.value)
        elif self.user_group_id == 3 :
            self.screen_manager.switch_to_screen(ScreenType.CARD.value)

    def _load_categories(self):
        """Učitava kategorije proizvoda."""
        prod_resp = get_products(self.bearer_token)
        if prod_resp:
            self.categories = prod_resp.get("categories", [])
            self.categories_loaded.emit(self.categories)
            
            return True
        else:
            print("Failed to load product categories")
            return False

    def _clear_catalog_basket(self):
        """Čisti korpu u CatalogPage."""
        catalog_widget = self.screen_manager.screens.get(ScreenType.CATALOG.value)
        if catalog_widget and hasattr(catalog_widget, "catalog_page"):
            catalog_widget.catalog_page.clear_basket()

    def _on_card_uid(self, uid_bytes, uid_hex):
        """Callback kada NFC čitač pročita UID kartice."""
        self.nfc_reader.stop()
        print(f"NFC UID read: {uid_hex}")
        self.screen_manager.card_scanned.emit(uid_hex)

    def _on_card_scanned(self, card_id: str):
        """Obrađuje skaniranje NFC kartice."""
        print(f"Card scanned: {card_id}")
        self.card_id = card_id

        # Mapiranje grupa na handler funkcije
        group_handlers = {
            3: self._handle_write_card,
            4: self._handle_read_card,
            5: self._handle_read_card
        }
        
        handler = group_handlers.get(self.user_group_id)
        if handler:
            handler(card_id)

    def _handle_write_card(self, card_id: str):
        """Obrađuje pisanje podataka na karticu (grupa 3)."""
        info = pay_card_info(self.bearer_token, card_id)
        if info:
            print("Info : ", info)
            uid_bytes = bytes.fromhex(card_id)
            if self.nfc_reader.write_card_number_block(uid_bytes, info["card_number"]):
                if self.nfc_reader.write_cvc_code_block(uid_bytes, info["cvc_code"], self.pin):
                    write_nfc_card(self.bearer_token, card_id)
                    self._show_message(
                        "Uspešna registracija kartice",
                        f"Uspesno registrovana nova kartica!\n"
                        f"UID: {card_id}\n"
                        f"CARD NUMBER: {info['card_number']}\n"
                        f"CVC CODE: {info['cvc_code']}",
                        msg_type="success",
                        auto_close=True,
                        timeout=2000
                    )
                else :
                    print("failed to wirte cvc code")
                    self._show_message(
                        "Neuspešna registracija kartice",
                        "Neuspeh pri upisu cvc koda",
                        msg_type="error",
                        auto_close=True,
                        timeout=2000
                    )
            else :
                print("failed to wirte carad number")
                self._show_message(
                    "Neuspešna registracija kartice",
                    "Neuspeh pri upisu card number",
                    msg_type="error",
                    auto_close=True,
                    timeout=2000
                )
        else :
            print("Failed to get pay_card_info for card with id : ", card_id)
            self._show_message(
                "Neuspešna registracija kartice",
                "Neuspeh pri dobijanju dozvole za registraciju kartice",
                msg_type="error",
                auto_close=True,
                timeout=2000
            )
 
     
    def _handle_read_card(self, card_id: str):
        """Obrađuje čitanje podataka sa kartice (grupe 4 i 5)."""
        
        uid_bytes = bytes.fromhex(card_id)
        number = self.nfc_reader.read_card_number_block(uid_bytes)
        cvc = self.nfc_reader.read_cvc_code_block(uid_bytes, self.pin)
        
        if number and cvc:
            resp = read_nfc_card(self.bearer_token, number, cvc)
            if resp:
                self.balance = resp.get("balance", 0)
                self.slug = resp.get("slug")
                
                # Ažuriraj charge page sa podacima o kartici
                charge_page = self.screen_manager.screens.get(ScreenType.CHARGE.value)
                if charge_page:
                    charge_page.update_card_info(self.card_id, self.balance)
                
                # Prebaci na sledeći ekran
                next_screen = self.next_screen_after_card or ScreenType.CARD.value
                self.screen_manager.switch_to_screen(next_screen)
                return

        print("Failed to read card data")
        self.screen_manager.switch_to_screen(ScreenType.CARD.value)

    def _on_category_selected(self, category_name: str):
        """Obrađuje izbor kategorije."""
        print(f"Category selected: {category_name}")
        # TODO: load products for this category

    def _on_order_action(self, action: str, items: dict):
        """Obrađuje završetak/otkazivanje porudžbine."""
        if action == "finish":
            dialog = PurchaseConfirmationDialog(
                parent=self.parent_widget,
                cart_items=items
            )
            dialog.purchase_confirmed.connect(lambda: self._process_order(items))
            dialog.modal_closed.connect(lambda: print("[DEBUG] Purchase modal zatvoren"))
            dialog.exec()

        elif action == "cancel":
            dialog = ModernMessageDialog(
                parent=self.parent_widget,
                title="Otkazivanje porudžbine",
                message="Da li ste sigurni da želite da otkažete porudžbinu?",
                dialog_type="warning",
                buttons=[
                    ("Da", QDialog.Accepted, self._cancel_order),
                    ("Ne", QDialog.Rejected, lambda: print("[DEBUG] Otkazivanje poništeno"))
                ]
            )
            dialog.exec()

    def _cancel_order(self):
        """Izvršava logiku otkazivanja porudžbine."""
        self._show_message(
            "Porudžbina otkazana",
            "Vaša porudžbina je uspešno otkazana.",
            msg_type="warning",
            auto_close=True,
            timeout=1500
        )
        self._clear_catalog_basket()
        self.screen_manager.switch_to_screen(ScreenType.CARD.value)



    def _process_order(self, items: dict):
        """Obrađuje porudžbinu nakon potvrde."""
        total_price, cart_dict = self._calculate_order_total(items)
        resp = checkout_service(self.bearer_token, self.slug, total_price, cart_dict)

        if resp and resp.get("status") == "success":
            self.balance -= total_price
            self._show_message(
                "Porudžbina uspešna!",
                f"Vaša porudžbina je obrađena.\nNovi balans: {self.balance} RSD",
                msg_type="success",
                auto_close=True,
                timeout=3000
            )
        else:
            msg = resp.get("message", "Obrada porudžbine nije uspela.") if resp else "Nepoznata greška"
            self._show_message(
                "Porudžbina neuspešna!",
                msg,
                msg_type="error",
                auto_close=True,
                timeout=3000
            )

        # Nakon poruke, očisti korpu i vrati na ekran kartice
        self._clear_catalog_basket()
        QTimer.singleShot(100, self._handle_back)



    def _calculate_order_total(self, items: dict):
        """Izračunava ukupnu cenu porudžbine."""
        total_price = 0
        cart_dict = {}
        
        for prod_id, entry in items.items():
            product = entry["product"]
            quantity = entry["quantity"]
            price = product.get("price", 0)
            
            total_price += int(price * quantity)
            cart_dict[prod_id] = {
                "name": product.get("name", ""),
                "price": price,
                "quantity": quantity
            }
        
        return total_price, cart_dict

    def _handle_credit_change(self, amount: float, is_increase: bool = True):
        """Jedinstvena funkcija za uvećanje/umanjenje kredita."""
        # Validacija iznosa
        if amount <= 0:
            self._show_message(
                "Greška",
                "Iznos mora biti veći od 0",
                msg_type="error",
                auto_close=True,
                timeout=2000
            )
            return

        # Dodatna validacija za umanjenje
        if not is_increase and amount > self.balance:
            self._show_message(
                "Nedovoljno sredstava",
                f"Trenutno stanje je {self.balance} RSD.\nNe možete umanjiti kredit za {amount} RSD.",
                msg_type="warning",
                timeout=3000
            )
            return

        # Pozovi API (1 = umanjenje, 2 = uvećanje)
        operation_type = 2 if is_increase else 1
        response = change_balance(self.bearer_token, self.slug, operation_type, amount)
        
        if response:
            if is_increase:
                self._handle_increase_response(response, amount)
            else:
                self._handle_decrease_response(amount)
        else:
            action = "uvećanje" if is_increase else "umanjenje"
            self._show_message(
                "Greška",
                f"{action.capitalize()} kredita nije uspelo.\nMolimo pokušajte ponovo.",
                msg_type="error",
                timeout=3000
            )

        self._switch_to_card_screen()

    def _handle_increase_response(self, response: dict, amount: float):
        """Obrađuje odgovor za uvećanje kredita."""
        if response["status"] != "fail":
            self.balance += amount
            self._show_message(
                "Uspešno!",
                f"Kredit je uvećan za {amount} RSD.\nNovo stanje: {self.balance} RSD",
                msg_type="success",
                auto_close=True,
                timeout=4000
            )
        else:
            self._show_message(
                "Transaction Failed",
                str(response["data"]),
                msg_type="error",
                timeout=3000
            )

    def _handle_decrease_response(self, amount: float):
        """Obrađuje odgovor za umanjenje kredita."""
        self.balance -= amount
        self._show_message(
            "Uspešno!",
            f"Kredit je umanjen za {amount} RSD.\nNovo stanje: {self.balance} RSD",
            msg_type="success",
            auto_close=True,
            timeout=2000
        )

    def _reset_session_data(self):
        """Resetuje podatke sesije prilikom odjave."""
        self.bearer_token = None
        self.user_group_id = None
        self.card_id = None
        self.slug = None
        self.balance = 0
        self.categories = []
        self.next_screen_after_card = None

    def _on_logout_requested(self):
        dialog = ModernMessageDialog(
            parent=self.parent_widget,
            title="Logout",
            message="Da li želiš da se izloguješ?",
            dialog_type="question",
            buttons=[
                ("Nazad", QDialog.Rejected, self._handle_back),
                ("OK", QDialog.Accepted, self._handle_logout)
            ]
        )
        dialog.exec()

    def _handle_logout(self):
        self._reset_session_data()
        self.screen_manager.switch_to_screen(ScreenType.LOGIN.value)
        
    def _on_charge_back(self):
        """Obrađuje povratak sa ChargePage."""
        print("Povratak sa charge page")
        self._switch_to_card_screen()