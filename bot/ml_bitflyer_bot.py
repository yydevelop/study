import requests
from datetime import datetime
import ccxt
import pandas as pd
import numpy as np
import talib
import settings
import time
import joblib
from logging import getLogger,Formatter,StreamHandler,FileHandler,INFO

# モデルの読み込み
model_y_buy = joblib.load('./model_y_buy.xz')
model_y_sell = joblib.load('./model_y_sell.xz')

# ccxtのパラメータ
symbol = 'BTC/JPY'	  # 購入予定のシンボル
product_code = 'FX_BTC_JPY'
bitflyer = ccxt.bitflyer()		 # 使用する取引所を記入
bitflyer.apiKey = settings.apiKey
bitflyer.secret = settings.secret
#lot = 100				# 購入する数量
lot = 10				# 購入する数量
#max_lot = 1000		   # 最大ロット
max_lot = 100		   # 最大ロット

# 特徴量作成
def calc_features(df):
	open = df['op']
	high = df['hi']
	low = df['lo']
	close = df['cl']
	volume = df['volume']
	
	orig_columns = df.columns

	hilo = (df['hi'] + df['lo']) / 2
	df['BBANDS_upperband'], df['BBANDS_middleband'], df['BBANDS_lowerband'] = talib.BBANDS(close, timeperiod=5, nbdevup=2, nbdevdn=2, matype=0)
	df['BBANDS_upperband'] -= hilo
	df['BBANDS_middleband'] -= hilo
	df['BBANDS_lowerband'] -= hilo
	df['DEMA'] = talib.DEMA(close, timeperiod=30) - hilo
	df['EMA'] = talib.EMA(close, timeperiod=30) - hilo
	df['HT_TRENDLINE'] = talib.HT_TRENDLINE(close) - hilo
	df['KAMA'] = talib.KAMA(close, timeperiod=30) - hilo
	df['MA'] = talib.MA(close, timeperiod=30, matype=0) - hilo
	df['MIDPOINT'] = talib.MIDPOINT(close, timeperiod=14) - hilo
	df['SMA'] = talib.SMA(close, timeperiod=30) - hilo
	df['T3'] = talib.T3(close, timeperiod=5, vfactor=0) - hilo
	df['TEMA'] = talib.TEMA(close, timeperiod=30) - hilo
	df['TRIMA'] = talib.TRIMA(close, timeperiod=30) - hilo
	df['WMA'] = talib.WMA(close, timeperiod=30) - hilo

	df['ADX'] = talib.ADX(high, low, close, timeperiod=14)
	df['ADXR'] = talib.ADXR(high, low, close, timeperiod=14)
	df['APO'] = talib.APO(close, fastperiod=12, slowperiod=26, matype=0)
	df['AROON_aroondown'], df['AROON_aroonup'] = talib.AROON(high, low, timeperiod=14)
	df['AROONOSC'] = talib.AROONOSC(high, low, timeperiod=14)
	df['BOP'] = talib.BOP(open, high, low, close)
	df['CCI'] = talib.CCI(high, low, close, timeperiod=14)
	df['DX'] = talib.DX(high, low, close, timeperiod=14)
	df['MACD_macd'], df['MACD_macdsignal'], df['MACD_macdhist'] = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
	# skip MACDEXT MACDFIX たぶん同じなので
	df['MFI'] = talib.MFI(high, low, close, volume, timeperiod=14)
	df['MINUS_DI'] = talib.MINUS_DI(high, low, close, timeperiod=14)
	df['MINUS_DM'] = talib.MINUS_DM(high, low, timeperiod=14)
	df['MOM'] = talib.MOM(close, timeperiod=10)
	df['PLUS_DI'] = talib.PLUS_DI(high, low, close, timeperiod=14)
	df['PLUS_DM'] = talib.PLUS_DM(high, low, timeperiod=14)
	df['RSI'] = talib.RSI(close, timeperiod=14)
	df['STOCH_slowk'], df['STOCH_slowd'] = talib.STOCH(high, low, close, fastk_period=5, slowk_period=3, slowk_matype=0, slowd_period=3, slowd_matype=0)
	df['STOCHF_fastk'], df['STOCHF_fastd'] = talib.STOCHF(high, low, close, fastk_period=5, fastd_period=3, fastd_matype=0)
	df['STOCHRSI_fastk'], df['STOCHRSI_fastd'] = talib.STOCHRSI(close, timeperiod=14, fastk_period=5, fastd_period=3, fastd_matype=0)
	df['TRIX'] = talib.TRIX(close, timeperiod=30)
	df['ULTOSC'] = talib.ULTOSC(high, low, close, timeperiod1=7, timeperiod2=14, timeperiod3=28)
	df['WILLR'] = talib.WILLR(high, low, close, timeperiod=14)

	df['AD'] = talib.AD(high, low, close, volume)
	df['ADOSC'] = talib.ADOSC(high, low, close, volume, fastperiod=3, slowperiod=10)
	df['OBV'] = talib.OBV(close, volume)

	df['ATR'] = talib.ATR(high, low, close, timeperiod=14)
	df['NATR'] = talib.NATR(high, low, close, timeperiod=14)
	df['TRANGE'] = talib.TRANGE(high, low, close)

	df['HT_DCPERIOD'] = talib.HT_DCPERIOD(close)
	df['HT_DCPHASE'] = talib.HT_DCPHASE(close)
	df['HT_PHASOR_inphase'], df['HT_PHASOR_quadrature'] = talib.HT_PHASOR(close)
	df['HT_SINE_sine'], df['HT_SINE_leadsine'] = talib.HT_SINE(close)
	df['HT_TRENDMODE'] = talib.HT_TRENDMODE(close)

	df['BETA'] = talib.BETA(high, low, timeperiod=5)
	df['CORREL'] = talib.CORREL(high, low, timeperiod=30)
	df['LINEARREG'] = talib.LINEARREG(close, timeperiod=14) - close
	df['LINEARREG_ANGLE'] = talib.LINEARREG_ANGLE(close, timeperiod=14)
	df['LINEARREG_INTERCEPT'] = talib.LINEARREG_INTERCEPT(close, timeperiod=14) - close
	df['LINEARREG_SLOPE'] = talib.LINEARREG_SLOPE(close, timeperiod=14)
	df['STDDEV'] = talib.STDDEV(close, timeperiod=5, nbdev=1)

	return df

features = sorted([
	'ADX',
	'ADXR',
	'APO',
	'AROON_aroondown',
	'AROON_aroonup',
	'AROONOSC',
	'CCI',
	'DX',
	'MACD_macd',
	'MACD_macdsignal',
	'MACD_macdhist',
	'MFI',
#	 'MINUS_DI',
#	 'MINUS_DM',
	'MOM',
#	 'PLUS_DI',
#	 'PLUS_DM',
	'RSI',
	'STOCH_slowk',
	'STOCH_slowd',
	'STOCHF_fastk',
#	 'STOCHRSI_fastd',
	'ULTOSC',
	'WILLR',
#	 'ADOSC',
#	 'NATR',
	'HT_DCPERIOD',
	'HT_DCPHASE',
	'HT_PHASOR_inphase',
	'HT_PHASOR_quadrature',
	'HT_TRENDMODE',
	'BETA',
	'LINEARREG',
	'LINEARREG_ANGLE',
	'LINEARREG_INTERCEPT',
	'LINEARREG_SLOPE',
	'STDDEV',
	'BBANDS_upperband',
	'BBANDS_middleband',
	'BBANDS_lowerband',
	'DEMA',
	'EMA',
	'HT_TRENDLINE',
	'KAMA',
	'MA',
	'MIDPOINT',
	'T3',
	'TEMA',
	'TRIMA',
	'WMA',
])


#----------------------------------------------------------------------------------------
# while True:
# 	# 現在の時刻を取得
# 	now = datetime.datetime.now() + datetime.timedelta(hours=9)
# 	count=0
# 	pos = 0
# 	# 15分ごとにローソク足を取得して特徴量を作成し、モデルで予測します
# 	if now.minute % 15 == 0 or count==0:
# 		count+=1
# 		# 現在のポジションを取得します。
# 		#pos = list(filter(lambda x: x['product_code'] == symbol, ftx.fetch_positions()))

# 		# 15分足のローソク足を100本取得し、pandasへ変換
# 		candle = bitflyer.fetch_ohlcv(symbol, timeframe='15m', limit=100)
# 		df = pd.DataFrame(candle, columns=['datetime','op','hi','lo','cl','volume'])

# 		# 検証時に見やすいように日本時間に変換、indexに日時をセット。売買には関係ありませんのでコメントアウトしてます。
# 		df['datetime'] = pd.to_datetime(df['datetime'], unit='ms') + datetime.timedelta(hours=9)
# 		df = df.set_index('datetime')

# 		# 特徴量作成
# 		df_features = calc_features(df)

# 		# 予測
# 		df_features['y_pred_buy'] = model_y_buy.predict(df_features[features])
# 		df_features['y_pred_sell'] = model_y_sell.predict(df_features[features])

# 		# 予測結果
# 		pred_buy = df_features['y_pred_buy'].iloc[-1]
# 		pred_sell = df_features['y_pred_sell'].iloc[-1]
		
# 		df_now = df_features.iloc[-1]

# 		# 呼び値 (取引所、取引ペアごとに異なるので、適切に設定してください)
# 		pips = 1

# 		# ATRで指値距離を計算します
# 		limit_price_dist = df['ATR'] * 0.5
# 		limit_price_dist = np.maximum(1, (limit_price_dist / pips).round().fillna(1)) * pips

# 		# 終値から両側にlimit_price_distだけ離れたところに、買い指値と売り指値を出します
# 		buy_price = df['cl'] - limit_price_dist
# 		sell_price = df['cl'] + limit_price_dist

# 		print(df_now['y_pred_buy'],df_now['y_pred_sell'],df_now['cl'])

# 		# # ポジションが０以外ならドテン用にロット２倍
# 		# if pos == 0:
# 		# 	order_lot = lot
# 		# else:
# 		# 	order_lot = lot * 2

# 		# 予測結果による売買
# 		if pred_buy > 0:
# 			if pos < max_lot:  # 現在のポジションが最大ロット未満の場合に発注する
# 				if pos >= 0:
# 					pos+=1
# 					print(now,symbol, 'market', 'buy', order_lot,df_features['y_pred_buy'])
# 					#ftx.create_order(symbol, 'market', 'buy', order_lot)
# 				elif pos < 0:
# 					pos+=2
# 					order_lot = abs(pos) * 2
# 					print(now,symbol, 'market', 'buy', order_lot,df_features['y_pred_buy'])
# 					#ftx.create_order(symbol, 'market', 'buy', order_lot)
# 		if pred_sell > 0:
# 			if pos > -max_lot:
# 				if pos >= 0:
# 					pos-=1
# 					print(now,symbol, 'market', 'sell', order_lot,df_features['y_pred_buy'])
# 					#ftx.create_order(symbol, 'market', 'sell', order_lot)
# 				elif pos < 0:
# 					pos-=2
# 					order_lot = abs(pos) * 2
# 					print(now,symbol, 'market', 'sell', order_lot,df_features['y_pred_buy'])
		
# 		# 14分スリープ
# 		time.sleep(840)

#----------------------------------------------------------------------------------------



# ログの設定
logger = getLogger(__name__)
handlerSh = StreamHandler()
handlerFile = FileHandler("./crypt_bot.log")
handlerSh.setLevel(INFO)
handlerFile.setLevel(INFO)
logger.setLevel(INFO)
logger.addHandler(handlerSh)
logger.addHandler(handlerFile)

# LINEの設定
line_token = settings.token

bitflyer = ccxt.bitflyer()
bitflyer.apiKey = settings.apiKey
bitflyer.secret = settings.secret

# print文のかわりに使用
def print_log( text ):
	
	# コマンドラインへの出力とファイル保存
	logger.info( text )
	
	# LINEへの通知
	url = "https://notify-api.line.me/api/notify"
	data = {"message" : text}
	headers = {"Authorization": "Bearer " + line_token} 
	requests.post(url, data=data, headers=headers)

# Cryptowatchから価格を取得する関数
def get_price(min,i):
	while True:
		try:
			response = requests.get("https://api.cryptowat.ch/markets/bitflyer/btcfxjpy/ohlc", params = { "periods" : 60 }, timeout = 5)
			response.raise_for_status()
			data = response.json()
			return { "close_time" : data["result"][str(min)][i][0],
				"open_price" : data["result"][str(min)][i][1],
				"high_price" : data["result"][str(min)][i][2],
				"low_price" : data["result"][str(min)][i][3],
				"close_price": data["result"][str(min)][i][4] }
		except requests.exceptions.RequestException as e:
			print("Cryptowatchの価格取得でエラー発生 : ",e)
			print("10秒待機してやり直します")
			time.sleep(10)


# 時間と始値・終値を表示する関数
def print_price( data ):
	print( "時間： " + datetime.fromtimestamp(data["close_time"]).strftime('%Y/%m/%d %H:%M') + " 始値： " + str(data["open_price"]) + " 終値： " + str(data["close_price"]) )


# 各ローソク足が陽線・陰線の基準を満たしているか確認する関数
def check_candle( data,side ):
	realbody_rate = abs(data["close_price"] - data["open_price"]) / (data["high_price"]-data["low_price"]) 
	increase_rate = data["close_price"] / data["open_price"] - 1
	
	if side == "buy":
		if data["close_price"] < data["open_price"] : return False
		elif increase_rate < 0.0003 : return False
		elif realbody_rate < 0.5 : return False
		else : return True
		
	if side == "sell":
		if data["close_price"] > data["open_price"] : return False
		elif increase_rate > -0.0003 : return False
		elif realbody_rate < 0.5 : return False
		else : return True


# ローソク足が連続で上昇しているか確認する関数
def check_ascend( data,last_data ):
	if data["open_price"] > last_data["open_price"] and data["close_price"] > last_data["close_price"]:
		return True
	else:
		return False

# ローソク足が連続で下落しているか確認する関数
def check_descend( data,last_data ):
	if data["open_price"] < last_data["open_price"] and data["close_price"] < last_data["close_price"]:
		return True
	else:
		return False


# 買いシグナルが出たら指値で買い注文を出す関数
def buy_signal( data,last_data,flag ):
	if flag["buy_signal"] == 0 and check_candle( data,"buy" ):
		flag["buy_signal"] = 1

	elif flag["buy_signal"] == 1 and check_candle( data,"buy" )  and check_ascend( data,last_data ):
		flag["buy_signal"] = 2

	elif flag["buy_signal"] == 2 and check_candle( data,"buy" )  and check_ascend( data,last_data ):
		print("３本連続で陽線 なので" + str(data["close_price"]) + "で買い指値を入れます")
		flag["buy_signal"] = 3
		
		try:
			order = bitflyer.create_order(
				symbol = 'BTC/JPY',
				type='limit',
				side='buy',
				price= data["close_price"],
				amount='0.01',
				params = { "product_code" : "FX_BTC_JPY" })
			flag["order"]["exist"] = True
			flag["order"]["side"] = "BUY"
			time.sleep(30)
		except ccxt.BaseError as e:
			print("Bitflyerの注文APIでエラー発生",e)
			print("注文が失敗しました")
			
	else:
		flag["buy_signal"] = 0
	return flag


# 売りシグナルが出たら指値で売り注文を出す関数
def sell_signal( data,last_data,flag ):
	if flag["sell_signal"] == 0 and check_candle( data,"sell" ):
		flag["sell_signal"] = 1

	elif flag["sell_signal"] == 1 and check_candle( data,"sell" )  and check_descend( data,last_data ):
		flag["sell_signal"] = 2

	elif flag["sell_signal"] == 2 and check_candle( data,"sell" )  and check_descend( data,last_data ):
		print("３本連続で陰線 なので" + str(data["close_price"]) + "で売り指値を入れます")
		flag["sell_signal"] = 3
		
		try:
			order = bitflyer.create_order(
				symbol = 'BTC/JPY',
				type='limit',
				side='sell',
				price= data["close_price"],
				amount='0.01',
				params = { "product_code" : "FX_BTC_JPY" })
			flag["order"]["exist"] = True
			flag["order"]["side"] = "SELL"
			time.sleep(30)
		except ccxt.BaseError as e:
			print("BitflyerのAPIでエラー発生",e)
			print("注文が失敗しました")

	else:
		flag["sell_signal"] = 0
	return flag


# 手仕舞いのシグナルが出たら決済の成行注文を出す関数
def close_position( data,last_data,flag ):
	if flag["position"]["side"] == "BUY":
		if data["close_price"] < last_data["close_price"]:
			print("前回の終値を下回ったので" + str(data["close_price"]) + "あたりで成行で決済します")
			while True:
				try:
					order = bitflyer.create_order(
						symbol = 'BTC/JPY',
						type='market',
						side='sell',
						amount='0.01',
						params = { "product_code" : "FX_BTC_JPY" })
					flag["position"]["exist"] = False
					time.sleep(30)
					break
				except ccxt.BaseError as e:
					print("BitflyerのAPIでエラー発生",e)
					print("注文の通信が失敗しました。30秒後に再トライします")
					time.sleep(30)
			
	if flag["position"]["side"] == "SELL":
		if data["close_price"] > last_data["close_price"]:
			print("前回の終値を上回ったので" + str(data["close_price"]) + "あたりで成行で決済します")
			while True:
				try:
					order = bitflyer.create_order(
						symbol = 'BTC/JPY',
						type='market',
						side='buy',
						amount='0.01',
						params = { "product_code" : "FX_BTC_JPY" })
					flag["position"]["exist"] = False
					time.sleep(30)
					break
				except ccxt.BaseError as e:
					print("BitflyerのAPIでエラー発生",e)
					print("注文の通信が失敗しました。30秒後に再トライします")
					time.sleep(30)
	return flag


# サーバーに出した注文が約定したかどうかチェックする関数
def check_order( flag ):
	try:
		position = bitflyer.private_get_getpositions( params = { "product_code" : "FX_BTC_JPY" })
		orders = bitflyer.fetch_open_orders(
			symbol = "BTC/JPY",
			params = { "product_code" : "FX_BTC_JPY" })
	except ccxt.BaseError as e:
		print("BitflyerのAPIで問題発生 : ",e)
	else:
		if position:
			print("注文が約定しました！")
			flag["order"]["exist"] = False
			flag["order"]["count"] = 0
			flag["position"]["exist"] = True
			flag["position"]["side"] = flag["order"]["side"]
		else:
			if orders:
				print("まだ未約定の注文があります")
				for o in orders:
					print( o["id"] )
				flag["order"]["count"] += 1
				
				if flag["order"]["count"] > 6:
					flag = cancel_order( orders,flag )
			else:
				print("注文が遅延しているようです")
	return flag



# 注文をキャンセルする関数
def cancel_order( orders,flag ):
	try:
		for o in orders:
			bitflyer.cancel_order(
				symbol = "BTC/JPY",
				id = o["id"],
				params = { "product_code" : "FX_BTC_JPY" })
		print("約定していない注文をキャンセルしました")
		flag["order"]["count"] = 0
		flag["order"]["exist"] = False
		
		time.sleep(20)
		position = bitflyer.private_get_getpositions( params = { "product_code" : "FX_BTC_JPY" })
		if not position:
			print("現在、未決済の建玉はありません")
		else:
			print("現在、まだ未決済の建玉があります")
			flag["position"]["exist"] = True
			flag["position"]["side"] = position[0]["side"]
	except ccxt.BaseError as e:
		print("BitflyerのAPIで問題発生 ： ", e)
	finally:
		return flag



# ここからメイン
last_data = get_price(60,-2)
print_price( last_data )
time.sleep(10)

flag = {
	"buy_signal":0,
	"sell_signal":0,
	"order":{
		"exist" : False,
		"side" : "",
		"count" : 0
	},
	"position":{
		"exist" : False,
		"side" : ""
	}
}

while True:
	now = datetime.datetime.now() + datetime.timedelta(hours=9)
	firstFlg = True
	# 15分ごとにローソク足を取得して特徴量を作成し、モデルで予測します
	if now.minute % 15 == 0 or firstFlg:
		firstFlg = False
		print("aaa")

	# if flag["order"]["exist"]:
	# 	flag = check_order( flag )
	
	# data = get_price(60,-2)
	# if data["close_time"] != last_data["close_time"]:
	# 	print_price( data )
	# 	if flag["position"]["exist"]:
	# 		flag = close_position( data,last_data,flag )
	# 	else:
	# 		flag = buy_signal( data,last_data,flag )
	# 		flag = sell_signal( data,last_data,flag )
	# 	last_data["close_time"] = data["close_time"]
	# 	last_data["open_price"] = data["open_price"]
	# 	last_data["close_price"] = data["close_price"]
		
	time.sleep(10)