from rest import closing_machine
import time
while True:
    print("Scanning for trades to close")
    closing_machine()
    print("Sleeping for 5 seconds")
    time.sleep(5)