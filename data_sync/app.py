import threading, time

def process():
    while True:
        print("Sleeping for one second")
        time.sleep(1)

def main():
    # Start background thread
    thread = threading.Thread(target=process)
    thread.daemon = True
    thread.start()

    while True:
        text = input("Please write a message\n")
        print("You wrote", text)

main()
