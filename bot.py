from openwa import WhatsAPIDriver
import time

driver = WhatsAPIDriver()
print("Waiting for QR")
while not driver.wait_for_login():
    time.sleep(3)

print("Bot started")
