import requests

BASE_URL = "https://fest.eik.rs/api/"
API_TOKEN = "8f7a19b60359e6d69a258d38276cc333"

def login(email, password):
    url = f"{BASE_URL}login"
    headers = {
        "X-API-Key": API_TOKEN,
        "Content-Type": "application/json"
    }
    payload = {
        "email": email,
        "password": password
    }

    try:
        # Šaljemo POST zahtev
        response = requests.post(url, json=payload, headers=headers, timeout=5)

        # Provera HTTP status koda
        if response.status_code == 200:
            # Preuzimamo JSON iz tela odgovora
            data = response.json()

            # Ako je status "success", vraćamo ceo odgovor da ga GUI deo obrađuje
            if data.get("status") == "success":
                return data["data"]
            else:
                # U slučaju da nije "success", vrati šta god treba za obradu greške
                # Može biti poruka ili None, zavisi kako želite da hendlujete
                ##print("API je vratio status:", data.get("status"))
                return data

        else:
            # Ako nije 200, odštampa i vrati None ili kreira posebnu grešku
            #print(f"Greška: {response.status_code} - {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        # Kod mrežnih grešaka, time-outa i sl.
        #print("Došlo je do greške prilikom povezivanja na API:", e)
        return None

def logout(bearer_token):
    url = f"{BASE_URL}account/logout" 
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, headers=headers, timeout=5)

        if response.status_code == 200:
            #print(response.json())
            return response.json()
        else:
            #print(f"Greška prilikom poziva POST {url}: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        #print(f"Došlo je do mrežne greške ili time-outa: {e}")
        return None

def get_products(bearer_token):
    url = f"{BASE_URL}account" 
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, timeout=5)

        if response.status_code == 200:
            #print(response.json())
            return response.json()["data"]
        else:
            #print(f"Greška prilikom poziva GET {url}: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        #print(f"Došlo je do mrežne greške ili time-outa: {e}")
        return None

def pay_card_info(bearer_token, uid_hex):
    url=f"{BASE_URL}pay-card/info/{uid_hex}"
    print("pay_card_url: ", url)

    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, timeout=5)
        print(response.json())
        if response.status_code == 200:
            #print(response.json())
            return response.json()["data"]
        else:
            #print(f"Greška prilikom poziva GET {url}: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Došlo je do mrežne greške ili time-outa: {e}")
        return None

def read_nfc_card(bearer_token, card_number, cvc_code):
    # pay-card/read/1701-2025-1202-1111/11-AA-BB-CC
    url=f"{BASE_URL}pay-card/read/{card_number}/{cvc_code}"
    #url=f"{BASE_URL}pay-card/read/1701-2025-1202-1111/11-AA-BB-CC"

    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, timeout=5)

        if response.status_code == 200:
            #print(response.json())
            return response.json()["data"]
        else:
            #print(f"Greška prilikom poziva GET {url}: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        #print(f"Došlo je do mrežne greške ili time-outa: {e}")
        return None
    
def checkout_service(bearer_token, slug, total_price, cart_dict):
    url=f"{BASE_URL}pay-card/checkout"

    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "slug": slug ,
        "totalAmount": total_price,
        "cart": cart_dict
    }
    print("checkout_payload: ", payload)
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        if response.status_code == 201:
            return response.json()
        else:
            try :
                return response.json()
            except :
                return None
    except requests.exceptions.RequestException as e:
        #print(f"Došlo je do mrežne greške ili time-outa: {e}")
        print(e, " eeee")
        return None

def write_nfc_card(bearer_token, uid_hex):

    url=f"{BASE_URL}pay-card/write"
    payload = {
    "uuid" : uid_hex
    }
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.put(url, json=payload, headers=headers, timeout=5)

        if response.status_code == 200:
            #print(response.json())
            return response.json()
        else:
            #print(f"Greška prilikom poziva PUT {url}: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        #print(f"Došlo je do mrežne greške ili time-outa: {e}")
        return None


def change_balance(bearer_token, slug, action, amount):
    url=f"{BASE_URL}pay-card/change-balance"

    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json"
    }
    # action 2 - increase 1 - decrease
    payload = {
    "slug" : slug,
    "account_operations" : action,
    "value" : amount
    }

    try:
        response = requests.put(url, json=payload, headers=headers, timeout=5)

        if response.status_code == 200:
            #print(response.json())
            return response.json()
        else:
            print(f"Greška prilikom poziva PUT {url}: {response.status_code} - {response.text}")
            return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Došlo je do mrežne greške ili time-outa: {e}")
        return None