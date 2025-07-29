# services/pn532.py
# services/pn532.py
import sys
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from PyQt5.QtWidgets import QWidget
import base64
from adafruit_pn532.adafruit_pn532 import MIFARE_CMD_AUTH_B


IS_WINDOWS = sys.platform.startswith("win")

if not IS_WINDOWS:
    try:
        import board
        import busio
        from digitalio import DigitalInOut
        from adafruit_pn532.i2c import PN532_I2C
        from adafruit_pn532.uart import PN532_UART
        from adafruit_pn532.spi import PN532_SPI
        PN532_AVAILABLE = True
    except Exception:
        PN532_AVAILABLE = False
else:
    PN532_AVAILABLE = False

import board
import busio
from adafruit_pn532.i2c import PN532_I2C
from adafruit_pn532.adafruit_pn532 import MIFARE_CMD_AUTH_B
import time

class NFCReader:
    """
    NFC čitač preko PN532 (I2C) fokusiran na rad sa blokom 8 i blokom 9 MIFARE Classic kartice.
    U blok 8 se upisuje card_number (nešifrovan, uz default ključ), a u blok 9 se upisuje cvc_code
    koji se šifrira pomoću PIN-a.
    """
    def __init__(self, root, on_card_read):
        """
        :param root: Widget koji pokreće/zaustavlja čitanje (koristi se samo za kompatibilnost, ne za scheduling)
        :param on_card_read: Callback funkcija sa potpisom on_card_read(uid, uid_hex)
        """
        self.root = root
        self.on_card_read = on_card_read

        i2c = busio.I2C(board.SCL, board.SDA)
        self.pn532 = PN532_I2C(i2c, debug=False)
        self.pn532.SAM_configuration()

        ic, ver, rev, support = self.pn532.firmware_version
        #print(f"[NFCReader] PN532 Firmware Version: {ver}.{rev}")

        self.check_interval_ms = 200
        self.is_running = False
        self.last_uid = None  # Sprečava višestruku obradu iste kartice

        self.default_key = [0xFF] * 6

    def start(self):
        if not self.is_running:
            self.is_running = True
            self._schedule_next_check()
            #print("[NFCReader] Startovan polling.")

    def stop(self):
        self.is_running = False
        #print("[NFCReader] Zaustavljen.")

    def _schedule_next_check(self):
        if self.is_running:
            QTimer.singleShot(self.check_interval_ms, self._read_card_once)

    def _read_card_once(self):
        if not self.is_running:
            return

        uid = self.pn532.read_passive_target(timeout=0.1)
        if uid:
            uid_hex = ''.join(f"{b:02X}" for b in uid)
            if self.last_uid == uid_hex:
                # Ako je ista kartica već obrađena, ne pozivamo callback
                pass
            else:
                self.last_uid = uid_hex
                #print(f"[NFCReader] Kartica detektovana! UID={uid_hex}")
                # Umesto self.root.after, koristimo QTimer.singleShot za zakazivanje callbacka
		
                QTimer.singleShot(0, lambda: self.on_card_read(uid, uid_hex))
        else:
            # Resetujemo ako kartica nije prisutna
            self.last_uid = None

        self._schedule_next_check()

    def write_card_number_block(self, uid, card_number):
        """Upisuje card_number u blok 8 (16 bajtova, popunjava se nulama ako je potrebno)."""
        block = 8
        card_bytes = [ord(ch) for ch in card_number]
        if len(card_bytes) < 16:
            card_bytes += [0x00] * (16 - len(card_bytes))
        elif len(card_bytes) > 16:
            card_bytes = card_bytes[:16]
        if not self.pn532.mifare_classic_authenticate_block(uid, block, MIFARE_CMD_AUTH_B, self.default_key):
            #print("Autentifikacija za blok 8 nije uspela.")
            return False
        if not self.pn532.mifare_classic_write_block(block, card_bytes):
            #print("Upis card_number u blok 8 nije uspeo.")
            return False
        #print("Card number upisan u blok 8.")
        return True

    def write_cvc_code_block(self, uid, cvc_code, pin):
        """
        Šifrira cvc_code pomoću PIN-a i upisuje ga u blok 9.
        """
        block = 9
        encrypted = self._encrypt_with_pin(cvc_code, pin)
        enc_bytes = list(encrypted)
        if len(enc_bytes) < 16:
            enc_bytes += [0x00] * (16 - len(enc_bytes))
        elif len(enc_bytes) > 16:
            enc_bytes = enc_bytes[:16]
        if not self.pn532.mifare_classic_authenticate_block(uid, block, MIFARE_CMD_AUTH_B, self.default_key):
            #print("Autentifikacija za blok 9 nije uspela.")
            return False
        if not self.pn532.mifare_classic_write_block(block, enc_bytes):
            #print("Upis cvc_code u blok 9 nije uspeo.")
            return False
        #print("CVC code (šifrovan) upisan u blok 9.")
        return True

    def read_card_number_block(self, uid):
        """Čita podatke iz bloka 8 i vraća ih kao string."""
        block = 8
        if not self.pn532.mifare_classic_authenticate_block(uid, block, MIFARE_CMD_AUTH_B, self.default_key):
            #print("Autentifikacija za blok 8 nije uspela pri čitanju.")
            return None
        data = self.pn532.mifare_classic_read_block(block)
        if data:
            return ''.join(chr(b) for b in data if 32 <= b <= 126)
        return None

    def read_cvc_code_block(self, uid, pin):
        """Čita podatke iz bloka 9, dešifruje ih pomoću PIN-a i vraća cvc_code kao string."""
        block = 9
        if not self.pn532.mifare_classic_authenticate_block(uid, block, MIFARE_CMD_AUTH_B, self.default_key):
            #print("Autentifikacija za blok 9 nije uspela pri čitanju.")
            return None
        data = self.pn532.mifare_classic_read_block(block)
        if data:
            return self._decrypt_with_pin(data, pin)
        return None

    def _encrypt_with_pin(self, text, pin):
        """Jednostavna XOR šifra – šifrira text koristeći PIN."""
        text_bytes = text.encode('utf-8')
        pin_bytes = pin.encode('utf-8')
        encrypted = bytearray()
        for i, b in enumerate(text_bytes):
            encrypted.append(b ^ pin_bytes[i % len(pin_bytes)])
        return encrypted

    def _decrypt_with_pin(self, data, pin):
        """Dešifruje podatke korišćenjem PIN-a (XOR dešifrovanje)."""
        pin_bytes = pin.encode('utf-8')
        decrypted = bytearray()
        for i, b in enumerate(data):
            decrypted.append(b ^ pin_bytes[i % len(pin_bytes)])
        return decrypted.decode('utf-8', errors='ignore').rstrip('\x00')

# Mock klasa za testiranje bez fizičkog čitača
class MockNFCReader(NFCReader):
    """Mock implementacija za testiranje"""
    
    def __init__(self, parent: QWidget = None, callback=None):
        QObject.__init__(self, parent)
        self.parent_widget = parent
        self.callback = callback
        self.is_running = False
        self.read_timer = QTimer()
        self.read_timer.timeout.connect(self._simulate_card_read)
        
    def _initialize_reader(self):
        #print("Mock NFC Reader inicijalizovan")
        return True
    
    def start(self):
        self.is_running = True
        self.read_timer.start(3000)  # Simuliraj kartu svake 3 sekunde
        #print("Mock NFC čitač pokrenut")
    
    def stop(self):
        self.is_running = False
        self.read_timer.stop()
        #print("Mock NFC čitač zaustavljen")
    
    def _simulate_card_read(self):
        """Simulira čitanje kartice"""
        if not self.is_running:
            return
            
        # Simuliraj random UID
        #import random
        #uid_hex = f"{''.join([f'{random.randint(0,255):02X}' for _ in range(4)])}"
        uid_hex = "63627ECE"
        uid_bytes = bytes.fromhex(uid_hex)
        
        print(f"Mock kartica: {uid_hex}")
        
        if self.callback:
            self.callback(uid_bytes, uid_hex)
    
    def write_card_number_block(self, uid: bytes, card_number: str, block_number: int = 8):
        print(f"Mock: Upisivanje card_number '{card_number}' u blok {block_number}")
        return True
    
    def write_cvc_code_block(self, uid: bytes, cvc_code: str, pin: str, block_number: int = 9):
        print(f"Mock: Upisivanje CVC '{cvc_code}' u blok {block_number}")
        return True
    
    def read_card_number_block(self, uid: bytes, block_number: int = 8):
        print(f"Mock: Čitanje card_number iz bloka {block_number}")
        return "1306202515449568"
    
    def read_cvc_code_block(self, uid: bytes, pin: str, block_number: int = 9):
        print(f"Mock: Čitanje CVC iz bloka {block_number}")
        return "4379970468652445"


def create_nfc_reader(parent: QWidget = None, callback=None, force_mock: bool = False):
    """Factory funkcija za kreiranje NFC čitača.
    Ako smo na Windows‑u, ili je eksplicitno zatražen mock, vraća MockNFCReader.
    Inače vraća pravi NFCReader."""
    is_windows = sys.platform.startswith("win")
    if force_mock or is_windows:
        return MockNFCReader(parent, callback)
    else:
        return NFCReader(parent, callback)