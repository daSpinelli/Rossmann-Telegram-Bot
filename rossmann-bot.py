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
    url = 'https://api.telegram.org/bot{}/'.format( TOKEN ) 
    url = url + 'sendMessage?parse_mode=MarkdownV2&chat_id={}'.format( chat_id ) 

    r = requests.post( url, json={'text': text } )
    print( 'Status Code {}'.format( r.status_code ) )

    return None
        
def load_dataset(store_id):
    # loading test dataset
    df_test_raw = pd.read_csv('test.csv')
    df_store_raw = pd.read_csv('store.csv')

    # merge test dataset with Store
    df_test = pd.merge(df_test_raw, df_store_raw, how='left', on='Store')

    # choose store for prediction
    df_test = df_test[df_test['Store'].isin(store_id)]
    
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

def get_help():
    hour = pd.datetime.now().hour
    msg_help  = 'Good morning!' if hour < 12 else 'Good afternoon!' if hour < 18 else 'Good evening!%0A%0A'
    msg_help += 'Welcome to Rossmann Stores Sales Prediction. A project developd by Denny de Almeida Spinelli.%0A'
    msg_help += 'For full info go to the [project github](https://github.com/daSpinelli/dsEmProd).%0A'
    msg_help += 'Well, in this telegram bot you access to preditions about Rossmann Stores.%0A%0A'
    msg_help += 'Here are you options:%0A%0A'
    msg_help += 'help -> shows the commands%0A'
    msg_help += 'top predictions ->: shows a bar graph with the top 5 predictions%0A'
    msg_help += 'top sales -> shows a bar graph with the top sales + predictions%0A'
    msg_help += 'n -> shows the prediction for a single store, where n is the id of a store%0A'
    msg_help += 'n,n,n,n -> shows the predictions for a list of stores, where n is the id of a store%0A%0A'
    msg_help += 'Make good use of these data! With great powers comes great responsabilities!'
    
    return msg_help

# API initialize
app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])

def index():
    if request.method == 'POST':
        message = request.get_json()
        
        chat_id, command = parse_message(message)
        
        # filtered prediction
        if (command.find(',') >= 0) | type(command) == int:
            store_id = command.split(',')
            store_id = [store_id for x in store_id if type(x) == int]
            
            # loading data
            data = load_dataset(store_id)
            
            if data != 'error':
                
                # prediction
                d1 = predict(data)
                
                # calculation
                d2 = d1[['store', 'prediction']].groupby('store').sum().reset_index()

                # send message
                msg = 'Store Number {} will sell R${:,.2f} in the next 6 weeks'.format(
                    d2['store'].values[0],
                    d2['prediction'].values[0]
                )
                send_message( chat_id, msg )
                return Response('Ok', status=200)
                
            else:
                send_message(chat_id, 'Store ID do not exist')
                return Response('Ok', status=200)

        # start & help
        elif (command == 'start') | (command == 'help'):
            msg_help = get_help()
            
            send_message(chat_id, msg_help)
            return Response('Ok', status=200)

        # top prediction
        elif command == 'top5predictions':
            send_message(chat_id, 'top5prediction')
            return Response('Ok', status=200)

        # top sales
        elif command == 'top5sales':
            send_message(chat_id, 'top5sales')
            return Response('Ok', status=200)            
            
        else:
            msg_help = get_help()
            send_message(chat_id, 'Invalid Command')
            send_message(chat_id, msg_help)
            return Response('Ok', status=200)
        
    else:
        return '<h1> Rossmann Telegram BOT</h1>'

if __name__ == '__main__':
    port = os.environ.get('PORT', 5000)
    app.run(host='0.0.0.0', port=port)
