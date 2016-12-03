from flask import Flask, request
import os
import sys
import json
import requests

app = Flask(__name__)

@app.route('/')
def hello_world():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world", 200

# route to respond to receive incoming messages
@app.route('/', methods=['POST'])
def webhook():
    data = request.get_json()
    # log the data
    log(data)

    if data['object'] == 'page':
        for entry in data['entry']:
            for messaging_event in entry['messaging']:
                # if someone sent a message
                if messaging_event.get('message'):
                    # get the message information
                    sender_id = messaging_event['sender']['id']
                    recipient_id = messaging_event['recipient']['id']
                    message_text = messaging_event['message']['text']
                    # send the same message back to the user
                    send_message(recipient_id, message_text)
    return 'ok', 200


def send_message(recipient_id, message_text):
    log('sending message to {recipient}: {text}'.format(recipient=recipient_id, text=message_text))

    # access token and other parameters
    params = {
        'access_token': os.environ['PAGE_ACCESS_TOKEN']
    }

    headers = {
        'Content-Type': 'application/json'
    }

    # the data to be sent
    data = json.dumps({
        'recipient': {
            'id': recipient_id
        },
        'message': {
            'text': message_text
        }
    })

    # make the request
    r = requests.post('https://graph.facebook.com/v2.6/me/messages', params=params, headers=headers, data=data)

    if r.status_code != 200:
        log(r.status_code)
        log(r.text)


def log(message):
    print str(message)
    sys.stdout.flush()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
