from classes import Assistant

carl = Assistant()

frame_count = 0
try:
    while True:
        if carl.detect_word() == True:
            # play one of the audio responses
            carl.react()
            context = carl.default_context
            context.append({
                "role":"user",
                "content":"why are you the way that you are?"
            })
            response = carl.generate_response(context)
            print(response)
            carl.speak(response)
                # record the audio
                 
                # play umm or uhh
                # translate the audio
                # generate a response
                # analyze response
                # say response
                # do desired functions

             
             

except KeyboardInterrupt:
    carl.shutdown()
         
