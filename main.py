from classes import Assistant
import threading

carl = Assistant()

frame_count = 0
try:
    while True:
        thread1a = threading.Thread(target = carl.detect_word)
        thread2a = threading.Thread(target = carl.maintain_bluetooth, daemon = True)

        thread1a.start()
        thread2a.start()

        thread1a.join()

        if carl.responding == True:
            carl.react()
            carl.context = carl.default_context
            while carl.responding == True:
                speech = carl.listen()
                print(speech)
                carl.load_context(speech, "user")
                result = {}
                thread1b = threading.Thread(target = carl.generate_response, args = (result, "text"))
                thread2b = threading.Thread(target = carl.pause)

                thread1b.start()
                thread2b.start()

                thread1b.join()
                thread2b.join()
                
                response = result["text"]
                print(response)
                carl.parse_response(response)

             
except KeyboardInterrupt:
    exit()
         
