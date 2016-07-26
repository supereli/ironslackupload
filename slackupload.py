import sys
sys.path.append("packages")
import time
import os
import requests
from bs4 import BeautifulSoup
import urllib2
import json
from PIL import Image
from resizeimage import resizeimage


#This creates a proper Python dictionary from the payload file (which should contain typically 1 name and 1 image) for later use
def createPayloadDict():
   payload = os.getenv('PAYLOAD_FILE')
   payloadfile = open(payload)
   payloadstring = payloadfile.read()
   print(payloadstring)
   jsondict = json.loads(payloadstring)
   return jsondict

payloaddict = createPayloadDict()
print("SLACK COOKIE= " + payloaddict['SLACK_COOKIE'])
print("SLACK API TOKEN = " + payloaddict['SLACK_API_TOKEN'])
print("EMOTICON APPEND VALUE = " + payloaddict['EMOTICON_APPEND_VALUE'])
print("IMAGE NAME = " + payloaddict['IMAGE_NAME'])
print("IMAGE URL = " + payloaddict['IMAGE_URL'])

#This will hit the Slack API and return a dictionary of the current Emojees that live there
def pullCurrentSlackEmojees():
   url = "https://slack.com/api/emoji.list"
   querystring = {"token":payloaddict['SLACK_API_TOKEN']}
   headers = {
      'cache-control': "no-cache"
#     'postman-token': "31c4fa00-1914-c056-8788-9c5beb8a4240"
    }
   response = requests.request("GET", url, headers=headers, params=querystring)
   slackDict = json.loads(response.text)
   emojeeDict = slackDict['emoji']
   print(type(emojeeDict))
   return emojeeDict

#This verifies the image is small enough to upload into Slack, if not it downsizes it
def downsizeImage(imageName):
   with open(imageName, 'r+b') as f:
      with Image.open(f) as image:
         imageSize = image.size
         if(imageSize[0] > 128 or imageSize[1] > 128):
            print('Image is too large, downsizing')
            cover = resizeimage.resize_thumbnail(image, [128, 128])
            cover.save (imageName, image.format)
         else:
            print('Image is small enough')

#This actually loads new Emojees directly into Slack via HTTP Post and not using the API
def loadIntoSlack(slackName,slackUrl):
   cookie = payloaddict['SLACK_COOKIE']
   url = 'https://iron.slack.com/customize/emoji'
   headers = {
   'Cookie': cookie
   }
   response = requests.request("GET", url, headers=headers)
   response.raise_for_status()
   soup = BeautifulSoup(response.text, "html.parser")
   crumb = soup.find("input", attrs={"name": "crumb"})["value"]
   imageget = urllib2.urlopen(slackUrl)
   with open('./images/' + slackName,'wb') as output:
      output.write(imageget.read())
   downsizeImage('./images/' + slackName)

   data = {
     'add': 1,
     'crumb': crumb,
     'name': slackName,
     'mode': 'data',
   }

   files = {'img': open('./images/' + slackName, 'rb')}
   r = requests.post(url, headers=headers, data=data, files=files, allow_redirects=False)
#   print(r.text)
   print(r.status_code)

imagename = payloaddict['IMAGE_NAME']
imageurl = payloaddict['IMAGE_URL']

#Print the name and url for diagnostics/troubleshooting
#print('Image name: ' + imagename)
#print('Image URL: ' + imageurl)


try:
  #Check to see if the Emojee being loaded already exists. If it does, append hip to the front of the name 
 print(pullCurrentSlackEmojees()[imagename])
#  imagename = payloaddict['EMOTICON_APPEND_VALUE'] + imagename
 try:
    #Check to see if the new appended version also exists. If it does, abort
  print(pullCurrentSlackEmojees()[imagename])
  print('Image already exists, aborting')
 except:
    #If the appended imagename with the hip prefix does not exist, load into Slack
  print('Loading into Slack with hip appended')
  loadIntoSlack(imagename,imageurl)
except:
  #Cannot find the imagename in Slack, so load it in
 print(imagename + ' not found')
 print('Loading into Slack with original name')
 print('Image URL = ' + imageurl)
 loadIntoSlack(imagename,imageurl)
