import configparser


conf = configparser.ConfigParser()
conf.read('settings.ini')

account_id = conf['oanda']['account_id']
access_token = conf['oanda']['access_token']
