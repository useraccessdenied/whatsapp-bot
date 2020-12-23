from openwa import WhatsAPIDriver
import time
from pprint import pprint as pp

driver = WhatsAPIDriver()
print("Waiting for QR")
while not driver.wait_for_login():
    time.sleep(3)

print("Bot started")

while True:
    time.sleep(3)
    for contact in driver.get_unread():
        for message in contact.messages:
            print(message)
            pp(vars(contact))
            pp(vars(message))
            contact.chat.send_message(message.content)
