from classes import Assistant

carl = Assistant()

frame_count = 0
try:
    while True:
        if carl.detect_word() == True:
            carl.react()
            carl.context = carl.default_context
            carl.responding = True
            while carl.responding == True:
                speech = carl.listen()
                print(speech)
                carl.load_context(speech, "user")
                response = carl.generate_response()
                print(response)
                carl.parse_response(response)

             
except KeyboardInterrupt:
    exit()
         
