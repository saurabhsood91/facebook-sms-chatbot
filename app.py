from flask import Flask, request
import os
import sys
import json
import requests
import re

from twilio import TwilioRestException
from twilio.rest import TwilioRestClient

app = Flask(__name__)

TWILIO_ACCOUNT_SID = os.environ['TWILIO_ACCOUNT_SID']
TWILIO_AUTH_TOKEN = os.environ['TWILIO_AUTH_TOKEN']

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
                    # # send the same message back to the user
                    # send_message(sender_id, message_text)
                    # send an SMS if the message is valid
                    is_message_sent, reason = _send_message_if_valid_message_request(message_text)

                    if not is_message_sent:
                        # send an error message
                        response_message_text = 'Invalid Request. {reason}'.format(reason=reason)

                        _send_message(sender_id, response_message_text)
                    else:
                        # send a response message
                        _send_message(sender_id, reason)

    return 'ok', 200

def _send_message_if_valid_message_request(message):
    if not message:
        return (False, 'Empty Message')
    message = message.split(':')
    if len(message) == 0:
        return (False, 'Incorrect Format for sending a message')
    phone_number = message[0]

    match = re.search('^(\+[0-9]{1,3})?[0-9]{10}$', phone_number)
    if not match:
        return (False, 'Phone Number is not valid')
    message_body = ''.join(message[1:])

    log('Phone Number: {phone_number}, Message Text: {message_body}'.format(phone_number=phone_number, message_body=message_body))

    _send_sms(phone_number, message_body)
    return (True, 'Message sent to {phone_number}'.format(phone_number=phone_number))

def _send_sms(phone_number, message):
    log('sending sms to {phone_number}'.format(phone_number=phone_number))
    if message:
        client = TwilioRestClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

        try:
            message = client.messages.create(body=message, to=phone_number, from_='+14694402744')
        except TwilioRestException as e:
            log(e)


def _send_message(recipient_id, message_text):
    log('sending message to {recipient}: {text}'.format(recipient=recipient_id, text=message_text))

    # access token and other parameters
    # log('access token: {access_token}'.format(access_token=os.environ['PAGE_ACCESS_TOKEN']))
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
