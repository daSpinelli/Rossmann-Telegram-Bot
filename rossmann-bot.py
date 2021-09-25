import pandas as pd
import json
import requests
from flask import Flask, request, Response
import os

# constants
TOKEN = '1964746514:AAGmnUoclbp8R1NczhX38vt8_4Da10u4uW4'

# # Info about the Bot
# https://api.telegram.org/bot1964746514:AAGmnUoclbp8R1NczhX38vt8_4Da10u4uW4/getMe
        
# # get updates
# https://api.telegram.org/bot1964746514:AAGmnUoclbp8R1NczhX38vt8_4Da10u4uW4/getUpdates

# # webhook Heroku
# https://api.telegram.org/bot1964746514:AAGmnUoclbp8R1NczhX38vt8_4Da10u4uW4/setWebhook?url=https://rossmann-predict-bot.herokuapp.com
        
# # send messages
# https://api.telegram.org/bot1964746514:AAGmnUoclbp8R1NczhX38vt8_4Da10u4uW4/sendMessage?chat_id=1105720401&text=Hi!

def send_message(chat_id, text):
    parse = 'HTML'
    url = 'https://api.telegram.org/bot{}/sendMessage'.format( TOKEN )
    
    message = {
        'text': text,
        'parse_mode': 'HTML',
        'disable_web_page_preview': True,
        'chat_id': chat_id
    }
    
    header = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    print('text: {}'.format( text))
    r = requests.post(url, json=message, headers=header)
    print('Status Code {}'.format( r.status_code ))
    print(chat_id)

    return None
        
def load_dataset(store_id):
    # loading test dataset
    df_test_raw = pd.read_csv('test.csv')
    df_store_raw = pd.read_csv('store.csv')

    # merge test dataset with Store
    df_test = pd.merge(df_test_raw, df_store_raw, how='left', on='Store')
    
    # choose store for prediction
    df_test = df_test[df_test['Store'].isin(store_id)]
    print('df_test = df_test[df_test["Store"].isin({})]\n\n{}'.format(store_id, df_test))
    if not df_test.empty:
        # remove closed days
        df_test = df_test[df_test['Open'] != 0]
        df_test = df_test[~df_test['Open'].isnull()]
        df_test = df_test.drop('Id', axis=1)

        # convert DataFrame to JSON
        data = json.dumps(df_test.to_dict(orient='records'))
        
    else:
        data = 'error'
    
    return data

def predict(data):
    # API Call
    url = 'https://das-rossmann-prediction.herokuapp.com/rossmann/predict'
    header = {'Content-type': 'application/json'}
    data = data

    r = requests.post(url, data=data, headers=header)
    print( 'Status Code {}'.format( r.status_code ) )

    d1 = pd.DataFrame(r.json(), columns=r.json()[0].keys())

    return d1

def parse_message(message):
    chat_id = message['message']['chat']['id']
    store_id = message['message']['text']
    
    command = store_id.replace('/', '')
    command = store_id.replace(' ', '')
            
    return chat_id, command

def get_help(greeting=True):
    msg_help_g = ''
    if greeting:

        github_link = 'https://github.com/daSpinelli/dsEmProd'
        linkedin_link = 'https://linkedin.com/in/dennydaspinelli'

        msg_help_g  = '''Hello!

Welcome to Rossmann Stores Sales Prediction!
A project developd by <a hred="{}">Denny de Almeida Spinelli</a>.
For full info, go to the <a href="{}">project github</a>.

Through this telegram bot you will access sales preditions of Rossmann Stores.


'''.format(greeting, github_link, linkedin_link)
        
    msg_help = msg_help_g + '''<b><u>Here are you options</u></b>

<b><i>start</i></b> : project info
<b><i>help</i></b> : available commands
<b><i>top predictions</i></b> : a bar graph with the top 5 predictions
<b><i>top sales</i></b> : a bar graph with the top sales + predictions
<b><i>n</i></b> : prediction for a single store, where n is the id of a store
<b><i>n,n,n,n</i></b> : predictions for a list of stores, where n is the id of a store

Make good use of these data! With great powers comes great responsabilities!'
   '''
    
    return msg_help

# API initialize
app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])

def index():
    if request.method == 'POST':
        message = request.get_json()
        
        chat_id, command = parse_message(message)
        
        try:
            command = command.lower()
        except ValueError:
            command = command
        
        try:
            command = int(command)
        except ValueError:
            command = command
        
        if type(command) != int:
            command = command.split(',') if command.find(',') >= 0 else command
        
        # filtered prediction
        if (type(command) == list) | (type(command) == int):
            # reshape if there is only one store_id
            store_id = command if type(command) == list else [command,]
            # loading data
            data = load_dataset(store_id)
            print(data[:13])
            if data != 'error':
                
                # prediction
                d1 = predict(data)
                
                # calculation
                d2 = d1[['store', 'prediction']].groupby('store').sum().reset_index()
                print('itens da predição: {}'.format(len(d2)))
                for i in range(len(d2)):
                # send message
                    msg = 'Store Number {} will sell R${:,.2f} in the next 6 weeks'.format(
                        d2.loc[i, 'store'],
                        d2.loc[i, 'prediction']
                    )
                    send_message( chat_id, msg )
                    print('return message: {}'.format(msg))
                    #return Response('Ok', status=200)
                
            else:
                send_message(chat_id, 'Store ID do not exist')
                #return Response('Ok', status=200)

        # start
        elif (command == 'start'):
            msg_help = get_help()
            send_message(chat_id, msg_help)
            #return Response('Ok', status=200)
            
        # help
        elif (command == 'help'):
            msg_help = get_help(False)
            send_message(chat_id, msg_help)
            #return Response('Ok', status=200)

        # top prediction
        elif command == 'toppredictions':
            print('top predictions')
            send_message(chat_id, 'top 5 prediction')
            #return Response('Ok', status=200)

        # top sales
        elif command.lower() == 'topsales':
            print('top sales')
            send_message(chat_id, 'top 5 sales')
            #return Response('Ok', status=200)            
            
        else:
            msg_help = get_help(greeting = False)
            send_message(chat_id, 'This is an invalid command!')
            send_message(chat_id, msg_help)
            #return Response('Ok', status=200)
            
        return Response('Ok', status=200)
        
    else:
        return '<h1> Rossmann Telegram BOT</h1>'

if __name__ == '__main__':
    port = os.environ.get('PORT', 5000)
    app.run(host='0.0.0.0', port=port)
