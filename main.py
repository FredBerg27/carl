from classes import Assistant
import threading
import copy

carl = Assistant()

frame_count = 0
try:
    while True:
        
        carl.detect_word()

        if carl.responding == True:
            carl.react()
            carl.context = {}
            carl.context = copy.deepcopy(carl.default_context)
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
         
