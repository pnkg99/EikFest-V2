# src/catalog_page.py
from PyQt6 import QtWidgets, QtCore, QtGui 
from PyQt6.QtWidgets import QButtonGroup, QButtonGroup
from src.image_cache import get_cached_image
# Boje
ACCENT_COLOR = "#E1B10D"
GRAY_COLOR = "#808080"
RED_COLOR = "#f44336"
BORDER_COLOR = "#474747"

class ProductWidget(QtWidgets.QFrame):
    """Widget za prikaz jednog proizvoda"""
    add_to_cart = QtCore.pyqtSignal(dict)

    def __init__(self, product_data: dict, parent=None):
        super().__init__(parent)
        self.product = product_data
        self.setObjectName("productItemFrame")
        self.setup_ui()

    def setup_ui(self):
        # Stil
        self.setStyleSheet(f"""
        QFrame#productItemFrame {{
            background-color: transparent;
            border: none;
            border-bottom: 1px solid {BORDER_COLOR};
            padding: 8px;
        }}
        """)
        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(20)

        # Levi deo: slika, naziv, opis
        left_layout = QtWidgets.QVBoxLayout()
        left_layout.setSpacing(4)
        self.img_label = QtWidgets.QLabel()
        self.img_label.setFixedSize(180, 120)
        self.img_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.img_label.setStyleSheet(f"""
        QLabel {{
            background-color: white;
            border-radius: 8px;
        }}
        """)

        pm = get_cached_image(str(self.product.get("id", "")),
                              self.product.get("image_url", ""),
                              QtCore.QSize(180, 120))
        if not pm.isNull():
            self.img_label.setPixmap(pm)
        else:
            self.img_label.setText("📦")
        name_label = QtWidgets.QLabel(self.product.get('name', 'Nepoznat proizvod'))
        name_label.setFont(QtGui.QFont("Inter", 14, QtGui.QFont.Weight.Bold))
        name_label.setStyleSheet("color: black;")

        # Bolja provera opisa
        raw_desc = self.product.get('description')
        desc_text = str(raw_desc).strip() if raw_desc else ''
        if not desc_text or desc_text == "None":
            desc_text = 'Nema opisa'
        elif len(desc_text) > 60:
            desc_text = desc_text[:57] + '...'
        desc_label = QtWidgets.QLabel(desc_text)
        desc_label.setFont(QtGui.QFont("Inter", 10))
        desc_label.setStyleSheet(f"color: {GRAY_COLOR};")
        desc_label.setWordWrap(True)

        left_layout.addWidget(self.img_label)
        left_layout.addWidget(name_label)
        left_layout.addWidget(desc_label)
        main_layout.addLayout(left_layout)

        # Desni deo: cena, dugmad poravnati uz levu ivicu i vertikalno centrirani
        right_layout = QtWidgets.QVBoxLayout()
        right_layout.setContentsMargins(0, 20, 0, 0)
        # PORAVNANJE na LEVO + vertikalno centrirano
        right_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)

        # --- Price layout (bez stretch) ---
        price = self.product.get('price', 0)
        price_value = QtWidgets.QLabel(f"{price:.2f}")
        price_value.setFont(QtGui.QFont("Inter", 14, QtGui.QFont.Weight.Bold))
        price_value.setStyleSheet(f"color: black;")

        currency = QtWidgets.QLabel("rsd")
        currency.setFont(QtGui.QFont("Inter", 10))
        currency.setStyleSheet("color: #A1A1A6;")

        price_layout = QtWidgets.QHBoxLayout()
        price_layout.setContentsMargins(0, 0, 0, 0)
        price_layout.setSpacing(4)
        price_layout.addWidget(price_value)
        price_layout.addWidget(currency)
        # ne dodaj stretch – želimo da stoji gusto levo

        right_layout.addLayout(price_layout)
        # --- Add button ---
        add_btn = QtWidgets.QPushButton("Dodaj")
        add_btn.setFont(QtGui.QFont("Inter", 14, QtGui.QFont.Weight.Bold))
        add_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        add_btn.setStyleSheet(f"""
        QPushButton {{
            background-color: #E1B10D;
            color: white;
            padding: 8px;
            border-radius: 6px;
        }}
        """)
        add_btn.clicked.connect(self.add_clicked)
        right_layout.addWidget(add_btn)

        # Veći razmak pre “Više”
        right_layout.addSpacing(12)

        # --- More button ---
        more_btn = QtWidgets.QPushButton("Više")
        more_btn.setFont(QtGui.QFont("Inter", 9,  QtGui.QFont.Weight.Bold))
        more_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        more_btn.setStyleSheet(f"""
        QPushButton {{
            background: transparent;
            border: none;
            text-decoration: underline;
            color:black;
            padding: 12px 6px;
        }}
        """)
        more_btn.clicked.connect(self.view_details)
        right_layout.addWidget(more_btn)

        # Popuni ostatak prostora da se celokupno poravnanje ne pomera
        right_layout.addStretch()

        main_layout.addLayout(right_layout) 
    
    def add_clicked(self):
        self.add_to_cart.emit(self.product)

    def view_details(self):
        modal = ProductModal(self.product, self)
        modal.add_to_cart.connect(self.add_to_cart.emit)
        modal.exec()

class ProductModal(QtWidgets.QDialog):
    """Modal dialog za prikaz detalja proizvoda, sa slikom i modernim stilom."""
    add_to_cart = QtCore.pyqtSignal(dict)
    
    def __init__(self, product_data: dict, parent=None):
        super().__init__(parent)
        self.product = product_data
        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint | QtCore.Qt.WindowType.Dialog)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)

        # Dimenzije modala
        screen_geom = QtGui.QGuiApplication.primaryScreen().availableGeometry()
        w = int(screen_geom.width() * 0.5)
        h = int(screen_geom.height() * 0.5)
        if w > 600:
            w = 600
        self.resize(w, h)
        self.move(
            (screen_geom.width() - w) // 2,
            (screen_geom.height() - h) // 2
        )

        self._setup_ui()

    def _setup_ui(self):
        # Glavni container sa senkom
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        container = QtWidgets.QFrame(self)
        container.setObjectName("container")
        container.setStyleSheet("""
            QFrame#container {
                background-color: white;
                border-radius: 12px;
            }
        """)
        shadow = QtWidgets.QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QtGui.QColor(0, 0, 0, 60))
        shadow.setOffset(0, 5)
        container.setGraphicsEffect(shadow)
        main_layout.addWidget(container)

        # Vertikalni layout unutra
        vbox = QtWidgets.QVBoxLayout(container)
        vbox.setContentsMargins(20, 20, 20, 20)
        vbox.setSpacing(15)

        self.img_label = QtWidgets.QLabel()
        self.img_label.setFixedHeight(200)
        self.img_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.img_label.setStyleSheet(f"border-radius: 8px;")

        pm = get_cached_image(str(self.product.get("id", "")),
                              self.product.get("image_url", ""),
                              QtCore.QSize(300, 200))
        if not pm.isNull():
            self.img_label.setPixmap(pm)
        else:
            self.img_label.setText("📦")
        vbox.addWidget(self.img_label)

        # --- Naziv ---
        title = QtWidgets.QLabel(self.product.get('name', 'Nepoznat proizvod'))
        title.setFont(QtGui.QFont('Inter', 20, QtGui.QFont.Weight.Bold))
        title.setStyleSheet("color: black;")
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(title)

        # --- Opis ---
        desc_label = QtWidgets.QLabel(self.product.get('description', 'Nema opisa'))
        desc_label.setWordWrap(True)
        desc_label.setFont(QtGui.QFont('Inter', 14))
        desc_label.setStyleSheet('color: #909090;')
        vbox.addWidget(desc_label)

        # --- Cena ---
        price_lbl = QtWidgets.QLabel(f"{self.product.get('price', 0):.2f} rsd")
        price_lbl.setFont(QtGui.QFont('Inter', 18, QtGui.QFont.Weight.Bold))
        price_lbl.setStyleSheet("color: black;")
        price_lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        vbox.addWidget(price_lbl)

        # --- Dugmad ---
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.setSpacing(10)

        back_btn = QtWidgets.QPushButton('Nazad')
        back_btn.setFont(QtGui.QFont('Inter', 14))
        back_btn.setFixedHeight(36)
        back_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        back_btn.setStyleSheet("""
            QPushButton {
                background: #f44336;
                color: white;
                border-radius: 6px;
            }
        """)
        back_btn.clicked.connect(self.reject)
        btn_layout.addWidget(back_btn)

        add_btn = QtWidgets.QPushButton('Dodaj u korpu')
        add_btn.setFont(QtGui.QFont('Inter', 14, QtGui.QFont.Weight.Bold))
        add_btn.setFixedHeight(36)
        add_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        add_btn.setStyleSheet("""
            QPushButton {
                background: #E1B10D;
                color: white;
                border-radius: 6px;
            }
        """)
        add_btn.clicked.connect(self.add_and_close)
        btn_layout.addWidget(add_btn)

        vbox.addLayout(btn_layout)
        
    def add_and_close(self):
        self.add_to_cart.emit(self.product)
        self.accept()

class BasketItemWidget(QtWidgets.QFrame):
    quantity_changed = QtCore.pyqtSignal(int, int)
    remove_item      = QtCore.pyqtSignal(int)
    add_to_cart      = QtCore.pyqtSignal(dict)

    def __init__(self, product_data: dict, quantity: int, parent=None):
        super().__init__(parent)
        self.product = product_data
        self.quantity = quantity
        self._setup_ui()

    def _setup_ui(self):
        # Stil widgeta: donja linija i vertikalni padding
        self.setObjectName("basketItem")
        self.setStyleSheet(f"""
        QFrame#basketItem {{
            background-color: transparent;
            border: none;
            border-bottom: 1px solid {GRAY_COLOR};
            padding: 8px;
        }}
        """)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(8)

        # --- Gornji red: naziv | količina | ukupna cena ---
        top_layout = QtWidgets.QHBoxLayout()
        raw_name = self.product.get('name', 'Nepoznat proizvod')
        name = (raw_name[:12] + "..." + raw_name[-5:]) if len(raw_name)>20 else raw_name

        name_label = QtWidgets.QLabel(name)
        name_label.setFont(QtGui.QFont("Inter", 10, QtGui.QFont.Weight.Bold))
        name_label.setStyleSheet("color: black;")
        top_layout.addWidget(name_label)

        top_layout.addStretch()

        self.qty_label = QtWidgets.QLabel(f"x{self.quantity}")
        self.qty_label.setFont(QtGui.QFont("Inter", 10))
        self.qty_label.setStyleSheet(f"color: {GRAY_COLOR};")
        self.qty_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        top_layout.addWidget(self.qty_label)

        self.price_label = QtWidgets.QLabel(f"{self.product.get('price',0)*self.quantity:.2f} rsd")
        self.price_label.setFont(QtGui.QFont("Inter", 10, QtGui.QFont.Weight.Bold))
        self.price_label.setStyleSheet(f"color: black;")
        self.price_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        top_layout.addWidget(self.price_label)

        main_layout.addLayout(top_layout)

        # --- Donji red: dugmići ---
        bottom_layout = QtWidgets.QHBoxLayout()
        bottom_layout.setContentsMargins(0,0,0,0)

        # 1) Dugme za brisanje (X)
        btn_remove = QtWidgets.QToolButton()
        btn_remove.setIcon(QtGui.QIcon("icons/remove.svg"))
        btn_remove.setIconSize(QtCore.QSize(32,32))
        btn_remove.setAutoRaise(True)
        btn_remove.clicked.connect(lambda: self.remove_item.emit(self.product['id']))
        bottom_layout.addWidget(btn_remove)

        bottom_layout.addStretch()

        # 2) Dugme za smanjenje količine (-)
        btn_minus = QtWidgets.QToolButton()
        btn_minus.setIcon(QtGui.QIcon("icons/minus.svg"))
        btn_minus.setIconSize(QtCore.QSize(32,32))
        btn_minus.setAutoRaise(True)
        btn_minus.clicked.connect(lambda: self._change_quantity(-1))
        bottom_layout.addWidget(btn_minus)

        bottom_layout.addStretch()

        # 3) Dugme za povećanje količine (+)
        btn_plus = QtWidgets.QToolButton()
        btn_plus.setIcon(QtGui.QIcon("icons/plus.svg"))
        btn_plus.setIconSize(QtCore.QSize(32,32))
        btn_plus.setAutoRaise(True)
        btn_plus.clicked.connect(lambda: self.add_to_cart.emit(self.product))

        bottom_layout.addWidget(btn_plus)

        main_layout.addLayout(bottom_layout)

    def _change_quantity(self, delta: int):
        new_qty = max(0, self.quantity + delta)
        if new_qty != self.quantity:
            self.quantity = new_qty
            # Emituj signal ka spoljnom kontroleru
            self.quantity_changed.emit(self.product['id'], new_qty)
            # Ažuriraj UI
            self.qty_label.setText(f"x{new_qty}")
            total = self.product.get('price',0) * new_qty
            self.price_label.setText(f"{total:.2f} rsd")


class CatalogPage(QtCore.QObject):
    # Signali
    order_action = QtCore.pyqtSignal(str, dict)  # emituje "finish" ili "cancel"

    def __init__(self, widget: QtWidgets.QWidget):
        super().__init__(parent=widget)
        self.widget = widget
        self.widget.setObjectName('CatalogPage')
        self.basket_items = {}
        self.categories = []
        self.widget.basket_items = self.basket_items
        self.widget.catalog_page = self

        self._setup_ui_elements()
        self._setup_total_label()
        self._setup_action_buttons()

        # Layout spacing fix
        vl = self.widget.layout()
        if vl:
            vl.insertSpacing(1, 10)
            vl.setStretch(0, 0)
            vl.setStretch(1, 0)
            vl.setStretch(2, 0)
            vl.setStretch(3, 10)
            vl.setStretch(4, 2)

        root = self.widget.window().layout()
        if isinstance(root, QtWidgets.QVBoxLayout):
            root.setStretch(0, 0)
            root.setStretch(1, 1)
            root.setStretch(2, 0)

    # -------------------------
    # Dugmad
    # -------------------------
    def _setup_action_buttons(self):
        finish_btn = self.widget.findChild(QtWidgets.QPushButton, "finishOrderButton")
        cancel_btn = self.widget.findChild(QtWidgets.QPushButton, "cancelOrderButton")

        if finish_btn:
            try:
                finish_btn.clicked.disconnect()
            except TypeError:
                pass
            finish_btn.clicked.connect(lambda: self._emit_finish())
            print("[CatalogPage] Finish button connected")

        if cancel_btn:
            try:
                cancel_btn.clicked.disconnect()
            except TypeError:
                pass
            cancel_btn.clicked.connect(lambda: self._emit_cancel())
            print("[CatalogPage] Cancel button connected")

    def _emit_finish(self):
        print("[DEBUG] CatalogPage _emit_finish called")
        self.order_action.emit("finish", self.get_basket_items())

    def _emit_cancel(self):
        print("[DEBUG] CatalogPage _emit_cancel called")
        self.order_action.emit("cancel", {})

    # -------------------------
    # Korpa
    # -------------------------
    def clear_basket(self):
        self.basket_items.clear()
        self.update_basket_display()

    def update_basket_display(self):
        for i in reversed(range(self.basket_layout.count())):
            item = self.basket_layout.itemAt(i)
            widget = item.widget()
            if widget and widget is not self.total_label:
                self.basket_layout.takeAt(i)
                widget.deleteLater()

        for product_id, item in self.basket_items.items():
            w = BasketItemWidget(item["product"], item["quantity"], parent=self.basket_contents)
            w.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
            w.quantity_changed.connect(self.update_item_quantity)
            w.remove_item.connect(self.remove_from_basket)
            w.add_to_cart.connect(self.add_to_basket)
            self.basket_layout.insertWidget(self.basket_layout.count() - 1, w)

        self.update_total()

    def add_to_basket(self, product: dict):
        product_id = product.get('id', product.get('name', ''))
        if product_id in self.basket_items:
            self.basket_items[product_id]["quantity"] += 1
        else:
            self.basket_items[product_id] = {"product": product, "quantity": 1}
        self.update_basket_display()

    def update_item_quantity(self, product_id: str, new_quantity: int):
        if new_quantity <= 0:
            self.remove_from_basket(product_id)
        else:
            if product_id in self.basket_items:
                self.basket_items[product_id]["quantity"] = new_quantity
                self.update_basket_display()

    def remove_from_basket(self, product_id: str):
        if product_id in self.basket_items:
            del self.basket_items[product_id]
            self.update_basket_display()

    def update_total(self):
        total = sum(item["product"].get('price', 0) * item["quantity"]
                    for item in self.basket_items.values())
        self.total_label.setText(f"{total:.2f} rsd")

    def get_basket_items(self):
        return self.basket_items.copy()

    def get_basket_total(self):
        return sum(item["product"].get('price', 0) * item["quantity"]
                   for item in self.basket_items.values())

    def is_basket_empty(self):
        return len(self.basket_items) == 0

    # -------------------------
    # UI Setup
    # -------------------------
    def _setup_ui_elements(self):
        scroll_cat = self.widget.findChild(QtWidgets.QScrollArea, "categoryScrollArea")
        if not scroll_cat:
            raise RuntimeError("categoryScrollArea nije pronađen")
        self.cat_contents = scroll_cat.widget()
        self.cat_layout = self.cat_contents.layout()
        self.cat_layout.setSpacing(12)  # ili veći broj ako želiš više prostora


        scroll_prod = self.widget.findChild(QtWidgets.QScrollArea, "productScrollArea")
        if not scroll_prod:
            raise RuntimeError("productScrollArea nije pronađen")
        self.prod_contents = scroll_prod.widget()

        scroll_prod.setStyleSheet("""
            QScrollArea#productScrollArea {
                border-right: 2px solid #474747;
                border-radius : 2px;
                background-color: white;
            }
        """)
        scroll_prod.viewport().setStyleSheet("background-color: white;")

        self.prod_layout = self.prod_contents.layout()
        self.prod_layout.setContentsMargins(10, 10, 10, 10)
        self.prod_layout.setSpacing(10)
        self.prod_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)

        scroll_basket = self.widget.findChild(QtWidgets.QScrollArea, "BasketScrollArea")
        if not scroll_basket:
            raise RuntimeError("BasketScrollArea nije pronađen")
        self.basket_contents = scroll_basket.widget()
        self.basket_layout = self.basket_contents.layout()
        self.basket_layout.setContentsMargins(0, 0, 0, 0)
        self.basket_layout.setSpacing(4)

        self.scroll_prod = scroll_prod
        self.scroll_prod.setWidgetResizable(True)
        self.scroll_prod.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.scroll_basket = scroll_basket
        self.scroll_basket.setWidgetResizable(True)
        self.scroll_basket.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        vsb_width = self.scroll_basket.verticalScrollBar().sizeHint().width()
        self.basket_layout.setContentsMargins(vsb_width, 10, vsb_width, 10)

        first_item = self.prod_layout.itemAt(0)
        if first_item and first_item.spacerItem():
            self.prod_layout.takeAt(0)

    def _setup_total_label(self):
        self.total_label = QtWidgets.QLabel("0.00 rsd")
        self.total_label.setFont(QtGui.QFont("Inter", 18, QtGui.QFont.Weight.Bold))
        self.total_label.setStyleSheet("padding: 10px; color: #999090;")
        self.total_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignBottom)
        self.basket_layout.addWidget(self.total_label)

    def update_categories(self, categories: list[dict]):
        self.categories = categories
        for i in reversed(range(self.cat_layout.count())):
            w = self.cat_layout.itemAt(i).widget()
            if isinstance(w, QtWidgets.QPushButton):
                w.deleteLater()

        button_group = QButtonGroup(self.cat_contents)
        button_group.setExclusive(True)

        for cat in categories:
            btn = QtWidgets.QPushButton("#" + cat["name"], parent=self.cat_contents)
            btn.setMinimumSize(QtCore.QSize(80, 0))
            btn.setFont(QtGui.QFont("Inter", 12, QtGui.QFont.Weight.Bold))
            btn.setCheckable(True)
            button_group.addButton(btn)
            btn.setStyleSheet("""
                QPushButton {
                    border: 1px solid #474747;
                    padding: 8px 14px;  /* veći vertikalni i horizontalni padding */
                    border-radius: 14px;  /* dovoljno veliki broj da krajevi budu potpuno zaobljeni */
                    color: #808080;
                    font-weight: 500;
                    background: white;
                }
                QPushButton:checked {
                    background-color: #808080;
                    color: white;
                }
            """)
            btn.clicked.connect(lambda _, prods=cat["products"]: self.update_products(prods))
            self.cat_layout.insertWidget(self.cat_layout.count() - 1, btn)

    def update_products(self, products: list[dict]):
        for i in reversed(range(self.prod_layout.count())):
            w = self.prod_layout.itemAt(i).widget()
            if w:
                w.deleteLater()

        for prod in products:
            w = ProductWidget(prod, parent=self.prod_contents)
            w.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
            w.add_to_cart.connect(self.add_to_basket)
            self.prod_layout.addWidget(w)