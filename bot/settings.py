import configparser

inifile = configparser.SafeConfigParser()
inifile.read('settings.ini')

apiKey = inifile.get('BITFLYER', 'apiKey')
secret = inifile.get('BITFLYER', 'secret')

token = inifile.get('LINE', 'token')
