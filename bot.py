from openwa import WhatsAPIDriver
from time import sleep
from threading import Thread, Event
from signal import signal, SIGINT, SIGTERM
from queue import Queue
import re
import requests

help_string = """
Group Commands ~

1. /add 91xxxxxxxxxx
2. /kick @Tag Member
3. /promote @Tag Member
4. /Demote @Tag Admin
5. /admin_list
6. /group_owner
7. /group_link
8. /delete (Select Bot Reply)
9. /kick_all
0. /leave

Miscellaneous Commands (1) / Features 

1. /jokes or /joke
 ~ For Jokes
 
2. /pjokes or /pjoke
 ~ For Programming Jokes
 
3. /facts or /fact
 ~ For Random Facts
 
4. /catfacts or /catfact
 ~ For Cat Facts
 
5. /quotes or /quote
 ~ For Random Quotes
 
6. /pquotes or /pquote
 ~ For Programming Quotes
 
7. /cbs ~ For Corporate Bullshit

"""

message_queue = Queue()

options = ["user-data-dir=temp-dir"]
driver = WhatsAPIDriver(client="chrome", chrome_options=options)
print("Waiting for QR")
while not driver.wait_for_login():
  sleep(3)

print("Bot started")


# This class is purely used to trigger end of program
# execution by simulating failure.
class ServiceExit(Exception):
  pass


def shutdown_service(signum, frame):
  print("Interrupt signal received")
  raise ServiceExit


# This thread reads the messages and add them to the
# message queue.
class ReceiveMessageThread(Thread):
  def __init__(self):
    Thread.__init__(self)

    # This is the flag which tracks shutdown event
    # from the main thread
    self.shutdown_flag = Event()

  def run(self) -> None:
    global message_queue

    print("Message thread started.")

    while not self.shutdown_flag.isSet():
      # Appended '_' here to prevent shadowing
      for _contact in driver.get_unread():
        for _message in _contact.messages:
          driver.chat_send_seen(_message.chat_id)
          message_queue.put(_message)
      sleep(0.5)

    print("Message thread stopped")


# This thread fetches data from API and sends it to
# the users.
class APIWorkerThread(Thread):
  def __init__(self):
    Thread.__init__(self)

    # This is the flag which tracks shutdown event
    # from the main thread
    self.shutdown_flag = Event()

  def run(self) -> None:
    global message_queue

    print("API Worker thread started")

    while not self.shutdown_flag.isSet():
      current_message = message_queue.get()
      command = re.compile("^[#!/]([a-z]+)").search(current_message.content)

      if command is not None:
        command = command.group(1)
        remaining_text = re.compile("^[#!/][a-z]+\\s+(.*)").search(current_message.content)

        if remaining_text is not None:
          remaining_text = remaining_text.group(1).strip()
        else:
          remaining_text = ""

        if command == "help":
          driver.chat_send_message(current_message.chat_id, help_string)
        elif command == "math" or command == "cal":
          data = {
            'expr': remaining_text
          }
          headers = {'content-type': 'application/json'}

          response = requests.post("http://api.mathjs.org/v4/",
                                   headers=headers, json=data)
          if response.ok:
            driver.chat_send_message(current_message.chat_id,
                                     response.json()['result'])
        elif command == "catfact" or command == "catfacts":
          response = requests.get("https://cat-fact.herokuapp.com/facts/random")
          if response.ok:
            driver.chat_send_message(current_message.chat_id,
                                     response.json()['text'])
        elif command == "cbs":
          response = requests.get("https://corporatebs-generator.sameerkumar.website/")
          if response.ok:
            driver.chat_send_message(current_message.chat_id,
                                     response.json()['phrase'])
        elif command == "pjokes" or command == "pjoke":
          response = requests.get("https://geek-jokes.sameerkumar.website/api?format=json")
          if response.ok:
            driver.chat_send_message(current_message.chat_id,
                                     response.json()['joke'])
        elif command == "jokes" or command == "joke":
          response = requests.get("https://official-joke-api.appspot.com/random_joke")
          if response.ok:
            joke = response.json()['setup'] + "\n\n" + response.json()['punchline']
            driver.chat_send_message(current_message.chat_id,
                                     joke)
        elif command == "quotes" or command == "quote":
          response = requests.get("https://freequote.herokuapp.com/")
          if response.ok:
            quote = response.json()['quote'] + "\n\n" + response.json()['author']
            driver.chat_send_message(current_message.chat_id,
                                     quote)
        elif command == "pquote" or command == "pquotes":
          response = requests.get("http://quotes.stormconsultancy.co.uk/random.json")
          if response.ok:
            pquote = response.json()['quote'] + "\n\n" + response.json()['author']
            driver.chat_send_message(current_message.chat_id,
                                     pquote)
        elif command == "fact" or command == "facts":
          response = requests.get("https://useless-facts.sameerkumar.website/api")
          if response.ok:
            driver.chat_send_message(current_message.chat_id,
                                     response.json()['data'])
        elif command == "dict":
          if " " not in remaining_text:
            response = requests.get("https://api.dictionaryapi.dev/api/v2/entries/en/"
                                    + remaining_text)
            if response.ok:
              words = response.json()
              res = ""
              for word in words:
                res += word['word']
                res += " - "
                res += word['phonetics'][0]['text']
                res += "\n\n"
                for meaning in word['meanings']:
                  res += "(" + meaning['partOfSpeech'] + ")\n"
                  res += meaning['definitions'][0]['definition']
                  res += "\n\n"
              driver.chat_send_message(current_message.chat_id, res)
            else:
              driver.chat_send_message(current_message.chat_id, "Sorry pal, I couldn't find it!")
        elif command == "meme":
          response = requests.get("https://meme-api.herokuapp.com/gimme")
          if response.ok:
            image_link = response.json()['url']
            title = response.json()['title']
            response = requests.get(image_link)
            if response.ok:
              with open('temp-dir/meme.jpg', 'wb') as file:
                file.write(response.content)
                driver.send_media('temp-dir/meme.jpg', current_message.chat_id, title)


    print("API Worker thread stopped")


def main():
  signal(SIGINT, shutdown_service)
  signal(SIGTERM, shutdown_service)

  message_thread = ReceiveMessageThread()
  api_thread = APIWorkerThread()

  try:
    message_thread.start()
    api_thread.start()

    while True:
      sleep(0.5)

  except ServiceExit:
    message_thread.shutdown_flag.set()
    api_thread.shutdown_flag.set()
    print("Completing pending operations.\nPlease wait.")
    message_thread.join()
    api_thread.join()


if __name__ == '__main__':
  main()
  driver.close()
  print("Bot Stopped!")
