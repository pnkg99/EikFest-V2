import sys
from PyQt6 import QtWidgets, uic, QtCore
from PyQt6.QtGui import QGuiApplication

from src.config import ScreenType
from src.screen_manager import ScreenManager
from src.app_controll import AppController      # ← fixed typo here
from src.catalog_page import CatalogPage
from src.charge_page import ChargePage
from src.virtual_keyboard import KeyboardManager



class MainWindow(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("./eik.ui", self)

        # 1) set up screen manager
        self._init_screen_manager()

        # 2) enable touch‑scroll on your two scroll areas
        self._init_scrollers()

        # 3) wire up category list once it’s loaded
        self.app_controller.categories_loaded.connect(
            self.catalog_page.update_categories
        )

        self.CardHelpFooter.mousePressEvent = lambda event: self.app_controller._on_logout_requested()


    def _init_screen_manager(self):
        self.keyboard_manager = KeyboardManager(self)  # Kreiraj tastaturu

        self.screen_manager = ScreenManager(
            self.stackedWidget,
            keyboard_manager=self.keyboard_manager
        )
        idx = self.screen_manager.screen_indices[ScreenType.CATALOG.value]
        placeholder = self.stackedWidget.widget(idx)
        self.catalog_page = CatalogPage(placeholder)
        self.charge_page = ChargePage()
        self.stackedWidget.addWidget(self.charge_page)
        self.screen_manager.screens[ScreenType.CHARGE.value] = self.charge_page
        self.screen_manager.screen_indices[ScreenType.CHARGE.value] = self.stackedWidget.indexOf(self.charge_page)

        self.app_controller = AppController(
            parent=self,
            screen_manager=self.screen_manager
        )

    def _init_scrollers(self):
        for scroll in (
            self.catalog_page.scroll_prod,
            self.catalog_page.scroll_basket
        ):
            scroll.setHorizontalScrollBarPolicy(
                QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
            )
            scroll.setVerticalScrollBarPolicy(
                QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
            )
            scroll.setWidgetResizable(True)
            vp = scroll.viewport()
            vp.setAttribute(QtCore.Qt.WidgetAttribute.WA_AcceptTouchEvents, True)

            # enable touch and mouse‑drag
            for gesture in (
                QtWidgets.QScroller.ScrollerGestureType.TouchGesture,
                QtWidgets.QScroller.ScrollerGestureType.LeftMouseButtonGesture
            ):
                QtWidgets.QScroller.grabGesture(vp, gesture)

            sc = QtWidgets.QScroller.scroller(vp)
            props = sc.scrollerProperties()
            props.setScrollMetric(
                QtWidgets.QScrollerProperties.ScrollMetric.AxisLockThreshold,
                1.0
            )
            sc.setScrollerProperties(props)
            
            


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()

    # show window then kick off the first screen
    window.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)
    window.showFullScreen()
    window.app_controller.start_app()

    sys.exit(app.exec())
