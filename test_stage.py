from classes import Assistant
import os

fred = Assistant()

fred.context = fred.default_context

responding = True
while responding == True:
    new_query = input("$:")
    fred.load_context(new_query)
    response = fred.generate_response(fred.context)
    text = ""
    i = 0
    while response[i] != "#":
        text = text + response[i]
        i += 1
    fred.speak(text)
    command = "" 
    i += 1
    while i < len(response):
        command = command + response[i]
        i += 1
    
    if command == "deactivate()":
        responding = False

    else:
        pass





