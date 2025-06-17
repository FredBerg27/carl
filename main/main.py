from test_stage import *

carl = Ai()

frame_count = 0
try:
     while True:
         if carl.detect_word() == True:
             print("hello")
             
             

except KeyboardInterrupt:
    carl.shutdown()
         
