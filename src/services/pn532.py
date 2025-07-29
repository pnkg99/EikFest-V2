# services/pn532.py
# services/pn532.py
import sys
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from PyQt5.QtWidgets import QWidget
import base64


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


import hashlib
from cryptography.fernet import Fernet


class NFCReader(QObject):
    """PN532 NFC Reader klasa za čitanje i pisanje NFC kartica"""
    
    card_detected = pyqtSignal(str)  # uid_bytes, uid_hex
    card_removed = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self, parent: QWidget = None, callback=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.callback = callback
        self.pn532 = None
        self.is_running = False
        self.reader_thread = None
        self.last_card_uid = None
        self.card_present = False
        
        # Timer za periodično čitanje
        self.read_timer = QTimer()
        self.read_timer.timeout.connect(self._check_for_card)
        
        self._initialize_reader()
    
    def _initialize_reader(self):
        """Inicijalizuje PN532 čitač"""
        if not PN532_AVAILABLE:
            self.error_occurred.emit("PN532 biblioteke nisu dostupne")
            return False
            
        try:
            # Pokušaj inicijalizacije preko I2C
            i2c = busio.I2C(board.SCL, board.SDA)
            self.pn532 = PN532_I2C(i2c, debug=False)
            
            # Konfiguriši čitač
            ic, ver, rev, support = self.pn532.firmware_version
            print(f'PN532 firmware version: {ver}.{rev}')
            
            # Konfiguriši za čitanje MIFARE kartica
            self.pn532.SAM_configuration()
            
            print("PN532 inicijalizovan uspešno")
            return True
            
        except Exception as e:
            print(f"Greška pri inicijalizaciji PN532: {e}")
            self.error_occurred.emit(f"Greška pri inicijalizaciji: {e}")
            return False
    
    def start(self):
        """Pokreće čitanje kartica"""
        if not self.pn532:
            self.error_occurred.emit("PN532 čitač nije inicijalizovan")
            return
            
        self.is_running = True
        self.read_timer.start(500)  # Proveri svake 500ms
        print("NFC čitač pokrenut")
    
    def stop(self):
        """Zaustavlja čitanje kartica"""
        self.is_running = False
        self.read_timer.stop()
        self.last_card_uid = None
        self.card_present = False
        print("NFC čitač zaustavljen")
    
    def _check_for_card(self):
        """Proverava da li je kartica prisutna"""
        if not self.is_running or not self.pn532:
            return
            
        try:
            # Pokušaj čitanja kartice
            uid = self.pn532.read_passive_target(timeout=0.1)
            
            if uid is not None:
                uid_hex = uid.hex().upper()
                
                # Ako je nova kartica
                if not self.card_present or self.last_card_uid != uid_hex:
                    self.card_present = True
                    self.last_card_uid = uid_hex
                    
                    print(f"Kartica detektovana: {uid_hex}")
                    
                    # Emituj signal
                    self.card_detected.emit(uid_hex)
                    
                    # Pozovi callback ako postoji
                    if self.callback:
                        self.callback(uid, uid_hex)
                        
            else:
                # Nema kartice
                if self.card_present:
                    self.card_present = False
                    self.last_card_uid = None
                    self.card_removed.emit()
                    print("Kartica uklonjena")
                    
        except Exception as e:
            print(f"Greška pri čitanju kartice: {e}")
            # Ne emituj error za svaku grešku čitanja
    
    def write_card_number_block(self, uid: bytes, card_number: str, block_number: int = 8):
        """Upisuje broj kartice u specifičan blok"""
        if not self.pn532:
            return False
            
        try:
            # Konvertuj card_number u 16-byte podatak
            data = card_number.encode('utf-8')
            
            # Dopuni ili skrati na 16 bajtova
            if len(data) < 16:
                data = data + b'\x00' * (16 - len(data))
            else:
                data = data[:16]
            
            # Autentifikuj se sa default ključem
            key = b'\xFF\xFF\xFF\xFF\xFF\xFF'
            
            if self.pn532.mifare_classic_authenticate_block(uid, block_number, 0x60, key):
                # Upiši podatke
                success = self.pn532.mifare_classic_write_block(block_number, data)
                if success:
                    print(f"Card number uspešno upisan u blok {block_number}")
                    return True
                else:
                    print(f"Greška pri upisu u blok {block_number}")
                    return False
            else:
                print(f"Autentifikacija neuspešna za blok {block_number}")
                return False
                
        except Exception as e:
            print(f"Greška pri upisu card_number: {e}")
            return False
    
    def write_cvc_code_block(self, uid: bytes, cvc_code: str, pin: str, block_number: int = 9):
        """Upisuje šifrovani CVC kod u specifičan blok"""
        if not self.pn532:
            return False
            
        try:
            # Šifruj CVC kod pomoću PIN-a
            encrypted_cvc = self._encrypt_data(cvc_code, pin)
            
            # Konvertuj u bytes
            data = encrypted_cvc.encode('utf-8')
            
            # Dopuni ili skrati na 16 bajtova
            if len(data) < 16:
                data = data + b'\x00' * (16 - len(data))
            else:
                data = data[:16]
            
            # Autentifikuj se sa default ključem
            key = b'\xFF\xFF\xFF\xFF\xFF\xFF'
            
            if self.pn532.mifare_classic_authenticate_block(uid, block_number, 0x60, key):
                # Upiši podatke
                success = self.pn532.mifare_classic_write_block(block_number, data)
                if success:
                    print(f"CVC code uspešno upisan u blok {block_number}")
                    return True
                else:
                    print(f"Greška pri upisu u blok {block_number}")
                    return False
            else:
                print(f"Autentifikacija neuspešna za blok {block_number}")
                return False
                
        except Exception as e:
            print(f"Greška pri upisu cvc_code: {e}")
            return False
    
    def read_card_number_block(self, uid: bytes, block_number: int = 8):
        """Čita broj kartice iz specifičnog bloka"""
        if not self.pn532:
            return ""
            
        try:
            # Autentifikuj se sa default ključem
            key = b'\xFF\xFF\xFF\xFF\xFF\xFF'
            
            if self.pn532.mifare_classic_authenticate_block(uid, block_number, 0x60, key):
                # Čitaj podatke
                data = self.pn532.mifare_classic_read_block(block_number)
                if data:
                    # Ukloni padding nule
                    card_number = data.decode('utf-8').rstrip('\x00')
                    print(f"Card number pročitan iz bloka {block_number}: {card_number}")
                    return card_number
                else:
                    print(f"Greška pri čitanju bloka {block_number}")
                    return ""
            else:
                print(f"Autentifikacija neuspešna za blok {block_number}")
                return ""
                
        except Exception as e:
            print(f"Greška pri čitanju card_number: {e}")
            return ""
    
    def read_cvc_code_block(self, uid: bytes, pin: str, block_number: int = 9):
        """Čita i dešifruje CVC kod iz specifičnog bloka"""
        if not self.pn532:
            return ""
            
        try:
            # Autentifikuj se sa default ključem
            key = b'\xFF\xFF\xFF\xFF\xFF\xFF'
            
            if self.pn532.mifare_classic_authenticate_block(uid, block_number, 0x60, key):
                # Čitaj podatke
                data = self.pn532.mifare_classic_read_block(block_number)
                if data:
                    # Ukloni padding nule
                    encrypted_cvc = data.decode('utf-8').rstrip('\x00')
                    # Dešifruj CVC kod
                    cvc_code = self._decrypt_data(encrypted_cvc, pin)
                    print(f"CVC code pročitan iz bloka {block_number}")
                    return cvc_code
                else:
                    print(f"Greška pri čitanju bloka {block_number}")
                    return ""
            else:
                print(f"Autentifikacija neuspešna za blok {block_number}")
                return ""
                
        except Exception as e:
            print(f"Greška pri čitanju cvc_code: {e}")
            return ""
    
    def _encrypt_data(self, data: str, key: str) -> str:
        """Šifruje podatke pomoću ključa"""
        try:
            # Generiši ključ od PIN-a
            key_bytes = hashlib.sha256(key.encode()).digest()
            key_b64 = base64.urlsafe_b64encode(key_bytes)
            
            cipher = Fernet(key_b64)
            encrypted = cipher.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
            
        except Exception as e:
            print(f"Greška pri šifrovanju: {e}")
            return data  # Vrati originalni podatak ako šifrovanje ne uspe
    
    def _decrypt_data(self, encrypted_data: str, key: str) -> str:
        """Dešifruje podatke pomoću ključa"""
        try:
            # Generiši ključ od PIN-a
            key_bytes = hashlib.sha256(key.encode()).digest()
            key_b64 = base64.urlsafe_b64encode(key_bytes)
            
            cipher = Fernet(key_b64)
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = cipher.decrypt(encrypted_bytes)
            return decrypted.decode()
            
        except Exception as e:
            print(f"Greška pri dešifrovanju: {e}")
            return encrypted_data  # Vrati šifrovani podatak ako dešifrovanje ne uspe
    
    def is_card_present(self) -> bool:
        """Proverava da li je kartica trenutno prisutna"""
        return self.card_present
    
    def get_last_card_uid(self) -> str:
        """Vraća UID poslednje pročitane kartice"""
        return self.last_card_uid or ""


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