import webbrowser
import pyautogui
import pandas as pd
from time import sleep
import os

# Load contacts Excel
contacts_df = pd.read_excel("contacts.xlsx", dtype=str)

# Clean spaces and duplicates in phone numbers
def clean_phone_numbers(phone_str):
    phones = [p.strip() for p in phone_str.split(',')]
    seen = set()
    unique_phones = []
    for p in phones:
        if p not in seen:
            seen.add(p)
            unique_phones.append(p)
    return unique_phones

contacts_df['clean_phone_list'] = contacts_df['cell_phone'].apply(clean_phone_numbers)

# Lookup phone list by name
def get_phone_numbers_by_name(name):
    filtered = contacts_df[contacts_df['name_user'].str.lower() == name.lower()]
    if filtered.empty:
        raise ValueError(f"Contact '{name}' not found in contacts.")
    all_numbers = []
    for phones in filtered['clean_phone_list']:
        all_numbers.extend(phones)
    return list(dict.fromkeys(all_numbers))  # Unique preserve order

# Send message to one phone number (pass custom message param)
def send_message(name_or_number, phone_number, message, country_code="91"):
    url = f"https://api.whatsapp.com/send?phone={country_code}{phone_number}"
    print(f"Opening WhatsApp Web for {name_or_number} ({phone_number})...")
    webbrowser.open(url)
    sleep(7)
    pyautogui.typewrite(message, interval=0.05)
    sleep(2)
    pyautogui.press('enter')
    print(f"Message sent to {phone_number} ({name_or_number})!")
    sleep(3)
    os.system('taskkill /F /IM chrome.exe')
    sleep(2)

# Main function to accept name or phone and custom message
def send_whatsapp_message(name_or_number, message, country_code="91"):
    if all(c.isdigit() or c == ',' or c == ' ' for c in name_or_number):
        # direct phone or list: separate
        numbers = clean_phone_numbers(name_or_number)
        for num in numbers:
            send_message(num, num, message, country_code)
    else:
        # lookup by name and send to all linked numbers
        phones = get_phone_numbers_by_name(name_or_number)
        for p in phones:
            send_message(name_or_number, p, message, country_code)

# Example usage
if __name__ == "__main__":
    input_value = "Bhupendra Rajput"             # Can be name or phone number string
    custom_message = "Hello! Automation working perfectly."
    send_whatsapp_message(input_value, custom_message)
