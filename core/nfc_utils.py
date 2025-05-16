# filepath: core/nfc_utils.py

import nfc

def scan_nfc_card():
    
    try:
        clf = nfc.ContactlessFrontend('usb')  # Connect to the NFC reader
        if not clf:
            raise Exception("No NFC reader found. Please connect an NFC reader.")

        # Define a callback to handle the NFC tag
        def on_connect(tag):
            if tag.ndef:
                return tag.ndef.message[0].text  # Extract the student ID from the NFC tag
            else:
                raise Exception("No NDEF data found on the NFC card.")

        # Wait for an NFC card to be scanned
        student_id = clf.connect(rdwr={'on-connect': on_connect})
        clf.close()
        return student_id

    except Exception as e:
        raise Exception(f"Error during NFC scanning: {e}")