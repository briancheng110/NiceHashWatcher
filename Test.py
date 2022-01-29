import json
import requests
import time


NHPage = ""

def safeHTMLGet(Url):
    while(True):
        try:
            page = requests.get(Url)
        except:
            print("Failed to fetch " + Url + ', retrying...')
        else:
            # sometimes NH sends us back garbage data, need secondary check
            print('no exception, checking html status code...' + str(page.status_code))
            if page.status_code == 200:
                print('passed')
                break
        time.sleep(5) # prevent spamming server with requests
        
    pageVar = json.loads(page.text)
    return pageVar

# main
json = safeHTMLGet('https://stackoverflow.com/asdf')
