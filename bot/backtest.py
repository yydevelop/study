import requests
from datetime import datetime
import time
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import pickle
import lightgbm as lgb
import talib
import joblib

#--------設定項目--------

chart_sec = 60 * 15        #  15分足を使用
buy_term =  30             #  買いエントリーのブレイク期間の設定
sell_term = 30             #  売りエントリーのブレイク期間の設定

judge_price={
  "BUY" : "high_price",    #  ブレイク判断　高値（high_price)か終値（close_price）を使用
  "SELL": "low_price"      #  ブレイク判断　安値 (low_price)か終値（close_price）を使用
}

TEST_MODE_LOT = "fixed"    # fixed なら常に1BTC固定 / adjustable なら可変ロット

volatility_term = 30       # 平均ボラティリティの計算に使う期間
stop_range = 2             # 何レンジ幅にストップを入れるか
trade_risk = 0.03          # 1トレードあたり口座の何％まで損失を許容するか
levarage = 3               # レバレッジ倍率の設定
start_funds = 1000000      # シミュレーション時の初期資金

entry_times = 2            # 何回に分けて追加ポジションを取るか
entry_range = 1            # 何レンジごとに追加ポジションを取るか

stop_config = "OFF"        # ON / OFF / TRAILING の３つが設定可
stop_AF = 0.02             # 加速係数
stop_AF_add = 0.02         # 加速係数を増やす度合
stop_AF_max = 0.2          # 加速係数の上限

filter_VER = "A"           # OFFで無効


wait = 0                   #  ループの待機時間
slippage = 0.001           #  手数料・スリッページ


#-------------------------------------------------------------------------------

def calc_features(df):
	open = df['open_price']
	high = df['high_price']
	low = df['low_price']
	close = df['close_price']
	volume = df['volume']

	orig_columns = df.columns

	hilo = (df['high_price'] + df['low_price']) / 2
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

def backtest(cl=None, hi=None, lo=None, pips=None,
              buy_entry=None, sell_entry=None,
              buy_cost=None, sell_cost=None
            ):
    n = cl.size
    y = cl.copy() * 0.0
    poss = cl.copy() * 0.0
    ret = 0.0
    pos = 0.0
    for i in range(n):
        prev_pos = pos
        
        # exit
        if buy_cost[i]:
            vol = np.maximum(0, -prev_pos)
            ret -= buy_cost[i] * vol
            pos += vol

        if sell_cost[i]:
            vol = np.maximum(0, prev_pos)
            ret -= sell_cost[i] * vol
            pos -= vol

        # entry
        if buy_entry[i] and buy_cost[i]:
            vol = np.minimum(1.0, 1 - prev_pos) * buy_entry[i]
            ret -= buy_cost[i] * vol
            pos += vol

        if sell_entry[i] and sell_cost[i]:
            vol = np.minimum(1.0, prev_pos + 1) * sell_entry[i]
            ret -= sell_cost[i] * vol
            pos -= vol
        
        if i + 1 < n:
            ret += pos * (cl[i + 1] / cl[i] - 1)
            
        y[i] = ret
        poss[i] = pos
        
    return y, poss

model_y_buy = joblib.load("./bot/model_y_buy.xz")
model_y_sell = joblib.load("./bot/model_y_sell.xz")
#-------------------------------------------------------------------------------


#-------------補助ツールの関数--------------

# CryptowatchのAPIを使用する関数
def get_price(min, before=0, after=0):
	price = []
	params = {"periods" : min }
	if before != 0:
		params["before"] = before
	if after != 0:
		params["after"] = after

	response = requests.get("https://api.cryptowat.ch/markets/bitflyer/btcfxjpy/ohlc",params)
	data = response.json()
	
	if data["result"][str(min)] is not None:
		for i in data["result"][str(min)]:
			if i[1] != 0 and i[2] != 0 and i[3] != 0 and i[4] != 0:
				price.append({ "close_time" : i[0],
					"close_time_dt" : datetime.fromtimestamp(i[0]).strftime('%Y/%m/%d %H:%M'),
					"open_price" : i[1],
					"high_price" : i[2],
					"low_price" : i[3],
					"close_price": i[4],
					"volume": i[5] })
		return price
		
	else:
		flag["records"]["log"].append("データが存在しません")
		return None


# 時間と高値・安値をログに記録する関数
def log_price( data,flag ):
	log =  "時間： " + datetime.fromtimestamp(data["close_time"]).strftime('%Y/%m/%d %H:%M') + " 高値： " + str(data["high_price"]) + " 安値： " + str(data["low_price"]) + " 終値： " + str(data["close_price"]) + "\n"
	flag["records"]["log"].append(log)
	return flag



# 平均ボラティリティを計算する関数
def calculate_volatility( last_data ):

	high_sum = sum(i["high_price"] for i in last_data[-1 * volatility_term :])
	low_sum  = sum(i["low_price"]  for i in last_data[-1 * volatility_term :])
	volatility = round((high_sum - low_sum) / volatility_term)
	flag["records"]["log"].append("現在の{0}期間の平均ボラティリティは{1}円です\n".format( volatility_term, volatility ))
	return volatility


# 単純移動平均を計算する関数
def calculate_MA( value,before=None ):
	if before is None:
		MA = sum(i["close_price"] for i in last_data[-1*value:]) / value
	else:
		MA = sum(i["close_price"] for i in last_data[-1*value + before: before]) / value
	return round(MA)


# 指数移動平均を計算する関数
def calculate_EMA( value,before=None ):
	if before is not None:
		MA = sum(i["close_price"] for i in last_data[-2*value + before : -1*value + before]) / value
		EMA = (last_data[-1*value + before]["close_price"] * 2 / (value+1)) + (MA * (value-1) / (value+1))
		for i in range(value-1):
			EMA = (last_data[-1*value+before+1 + i]["close_price"] * 2 /(value+1)) + (EMA * (value-1) / (value+1))
	else:
		MA = sum(i["close_price"] for i in last_data[-2*value: -1*value]) / value
		EMA = (last_data[-1*value]["close_price"] * 2 / (value+1)) + (MA * (value-1) / (value+1))
		for i in range(value-1):
			EMA = (last_data[-1*value+1 + i]["close_price"] * 2 /(value+1)) + (EMA * (value-1) / (value+1))
	return round(EMA)



#-------------エントリーフィルターの関数--------------

# エントリーフィルターの関数
def filter( signal ):
	
	if filter_VER == "OFF":
		return True
	
	if filter_VER == "A":
		if len(last_data) < 200:
			return True
		if data["close_price"] > last_data[-200]["close_price"] and signal["side"] == "BUY":
			return True
		if data["close_price"] < last_data[-200]["close_price"] and signal["side"] == "SELL":
			return True
	
	if filter_VER == "B":
		if len(last_data) < 200:
			return True
		if data["close_price"] > calculate_MA(200) and signal["side"] == "BUY":
			return True
		if data["close_price"] < calculate_MA(200) and signal["side"] == "SELL":
			return True
		
	if filter_VER == "C":
		if len(last_data) < 20:
			return True
		if calculate_MA(20) > calculate_MA(20,-1) and signal["side"] == "BUY":
			return True
		if calculate_MA(20) < calculate_MA(20,-1) and signal["side"] == "SELL":
			return True
		
	if filter_VER == "D":
		if len(last_data) < 400:
			return True
		if calculate_EMA(200) < calculate_EMA(14) and signal["side"] == "BUY":
			return True
		if calculate_EMA(200) > calculate_EMA(14) and signal["side"] == "SELL":
			return True
		
	return False


#-------------資金管理の関数--------------

# 注文ロットを計算する関数
def calculate_lot( last_data,data,flag ):
	
	# 固定ロットでのテスト時
	if TEST_MODE_LOT == "fixed":
		flag["records"]["log"].append("固定ロット(1枚)でテスト中のため、1BTCを注文します\n")
		lot = 1
		volatility = calculate_volatility( last_data )
		stop = stop_range * volatility
		flag["position"]["ATR"] = round( volatility )
		return lot,stop,flag
	
	
	# 口座残高を取得する
	balance = flag["records"]["funds"]

	# 最初のエントリーの場合
	if flag["add-position"]["count"] == 0:
		
		# １回の注文単位（ロット数）と、追加ポジの基準レンジを計算する
		volatility = calculate_volatility( last_data )
		stop = stop_range * volatility
		calc_lot = np.floor( balance * trade_risk / stop * 100 ) / 100
		
		flag["add-position"]["unit-size"] = np.floor( calc_lot / entry_times * 100 ) / 100
		flag["add-position"]["unit-range"] = round( volatility * entry_range )
		flag["add-position"]["stop"] = stop
		flag["position"]["ATR"] = round( volatility )
		
		flag["records"]["log"].append("\n現在のアカウント残高は{}円です\n".format( balance ))
		flag["records"]["log"].append("許容リスクから購入できる枚数は最大{}BTCまでです\n".format( calc_lot ))
		flag["records"]["log"].append("{0}回に分けて{1}BTCずつ注文します\n".format( entry_times, flag["add-position"]["unit-size"] ))
		
	# ２回目以降のエントリーの場合
	else:
		balance = round( balance - flag["position"]["price"] * flag["position"]["lot"] / levarage )
	
	# ストップ幅には、最初のエントリー時に計算したボラティリティを使う
	stop = flag["add-position"]["stop"]
	
	# 実際に購入可能な枚数を計算する
	able_lot = np.floor( balance * levarage / data["close_price"] * 100 ) / 100
	lot = min(able_lot, flag["add-position"]["unit-size"])
	flag["records"]["log"].append("証拠金から購入できる枚数は最大{}BTCまでです\n".format( able_lot ))
	
	return lot,stop,flag



# 複数回に分けて追加ポジションを取る関数
def add_position( data,flag ):
	
	# ポジションがない場合は何もしない
	if flag["position"]["exist"] == False:
		return flag
	
	# 固定ロット（1BTC）でのテスト時は何もしない
	if TEST_MODE_LOT == "fixed":
		return flag
	
	# 最初（１回目）のエントリー価格を記録
	if flag["add-position"]["count"] == 0:
		flag["add-position"]["first-entry-price"] = flag["position"]["price"]
		flag["add-position"]["last-entry-price"] = flag["position"]["price"]
		flag["add-position"]["count"] += 1
	
	while True:
		
		# 以下の場合は、追加ポジションを取らない
		if flag["add-position"]["count"] >= entry_times:
			return flag
		
		# この関数の中で使う変数を用意
		first_entry_price = flag["add-position"]["first-entry-price"]
		last_entry_price = flag["add-position"]["last-entry-price"]
		unit_range = flag["add-position"]["unit-range"]
		current_price = data["close_price"]
		
		
		# 価格がエントリー方向に基準レンジ分だけ進んだか判定する
		should_add_position = False
		if flag["position"]["side"] == "BUY" and (current_price - last_entry_price) > unit_range:
			should_add_position = True
		elif flag["position"]["side"] == "SELL" and (last_entry_price - current_price) > unit_range:
			should_add_position = True
		else:
			break
		
		# 基準レンジ分進んでいれば追加注文を出す
		if should_add_position == True:
			flag["records"]["log"].append("\n前回のエントリー価格{0}円からブレイクアウトの方向に{1}ATR（{2}円）以上動きました\n".format( last_entry_price, entry_range, round( unit_range ) ))
			flag["records"]["log"].append("{0}/{1}回目の追加注文を出します\n".format(flag["add-position"]["count"] + 1, entry_times))
			
			# 注文サイズを計算
			lot,stop,flag = calculate_lot( last_data,data,flag )
			if lot < 0.01:
				flag["records"]["log"].append("注文可能枚数{}が、最低注文単位に満たなかったので注文を見送ります\n".format(lot))
				flag["add-position"]["count"] += 1
				return flag
			
			# 追加注文を出す
			if flag["position"]["side"] == "BUY":
				entry_price = first_entry_price + (flag["add-position"]["count"] * unit_range)
				#entry_price = round((1 + slippage) * entry_price)
				
				flag["records"]["log"].append("現在のポジションに追加して、{0}円で{1}BTCの買い注文を出します\n".format(entry_price,lot))
				
				# ここに買い注文のコードを入れる
				
				
			if flag["position"]["side"] == "SELL":
				entry_price = first_entry_price - (flag["add-position"]["count"] * unit_range)
				#entry_price = round((1 - slippage) * entry_price)
				
				flag["records"]["log"].append("現在のポジションに追加して、{0}円で{1}BTCの売り注文を出します\n".format(entry_price,lot))
				
				# ここに売り注文のコードを入れる
				
				
			# ポジション全体の情報を更新する
			flag["position"]["stop"] = stop
			flag["position"]["price"] = int(round(( flag["position"]["price"] * flag["position"]["lot"] + entry_price * lot ) / ( flag["position"]["lot"] + lot )))
			flag["position"]["lot"] = np.round( (flag["position"]["lot"] + lot) * 100 ) / 100
			
			if flag["position"]["side"] == "BUY":
				flag["records"]["log"].append("{0}円の位置にストップを更新します\n".format(flag["position"]["price"] - stop))
			elif flag["position"]["side"] == "SELL":
				flag["records"]["log"].append("{0}円の位置にストップを更新します\n".format(flag["position"]["price"] + stop))
			flag["records"]["log"].append("現在のポジションの取得単価は{}円です\n".format(flag["position"]["price"]))
			flag["records"]["log"].append("現在のポジションサイズは{}BTCです\n\n".format(flag["position"]["lot"]))
			
			flag["add-position"]["count"] += 1
			flag["add-position"]["last-entry-price"] = entry_price
	
	return flag


# トレイリングストップの関数
def trail_stop( data,flag ):

	# まだ追加ポジションの取得中であれば何もしない
	if flag["add-position"]["count"] < entry_times and TEST_MODE_LOT != "fixed":
		return flag
	
	# 高値／安値がエントリー価格からいくら離れたか計算
	if flag["position"]["side"] == "BUY":
		moved_range = round( data["high_price"] - flag["position"]["price"] )
	if flag["position"]["side"] == "SELL":
		moved_range = round( flag["position"]["price"] - data["low_price"] )
	
	# 最高値・最安値を更新したか調べる
	if moved_range < 0 or flag["position"]["stop-EP"] >= moved_range:
		return flag
	else:
		flag["position"]["stop-EP"] = moved_range
	
	# 加速係数に応じて損切りラインを動かす
	flag["position"]["stop"] = round(flag["position"]["stop"] - ( moved_range + flag["position"]["stop"] ) * flag["position"]["stop-AF"])
	
	
	# 加速係数を更新
	flag["position"]["stop-AF"] = round( flag["position"]["stop-AF"] + stop_AF_add ,2 )
	if flag["position"]["stop-AF"] >= stop_AF_max:
		flag["position"]["stop-AF"] = stop_AF_max
	
	# ログ出力
	if flag["position"]["side"] == "BUY":
		flag["records"]["log"].append("トレイリングストップの発動：ストップ位置を{}円に動かして、加速係数を{}に更新します\n".format( round(flag["position"]["price"] - flag["position"]["stop"]) , flag["position"]["stop-AF"] ))
	else:
		flag["records"]["log"].append("トレイリングストップの発動：ストップ位置を{}円に動かして、加速係数を{}に更新します\n".format( round(flag["position"]["price"] + flag["position"]["stop"]) , flag["position"]["stop-AF"] ))
	
	return flag
	


#-------------売買ロジックの部分の関数--------------

# # ドンチャンブレイクを判定する関数
# def donchian( data,last_data ):
	
# 	highest = max(i["high_price"] for i in last_data[ (-1* buy_term): ])
# 	if data[ judge_price["BUY"] ] > highest:
# 		return {"side":"BUY","price":highest}
	
# 	lowest = min(i["low_price"] for i in last_data[ (-1* sell_term): ])
# 	if data[ judge_price["SELL"] ] < lowest:
# 		return {"side":"SELL","price":lowest}
	
# 	return {"side" : None , "price":0}


def mlpredict(data):
	df_i = pd.DataFrame(data,index=[0])
	# 予測
	df_i['y_pred_buy'] = model_y_buy.predict(df_i[features])
	df_i['y_pred_sell'] = model_y_sell.predict(df_i[features])

	# 呼び値 (取引所、取引ペアごとに異なるので、適切に設定してください)
	pips = 1

	# ATRで指値距離を計算します
	limit_price_dist = df_i['ATR'] * 0.5
	limit_price_dist = np.maximum(1, (limit_price_dist / pips).round().fillna(1)) * pips

	# 終値から両側にlimit_price_distだけ離れたところに、買い指値と売り指値を出します
	buy_price = df_i['close_price'] - limit_price_dist
	sell_price = df_i['close_price'] + limit_price_dist

	# 予測結果
	pred_buy = df_i['y_pred_buy'].iloc[-1]
	pred_sell = df_i['y_pred_sell'].iloc[-1]
	print(pred_buy,pred_sell)

	if pred_buy > 0 and pred_buy>=pred_sell:
		return {"side":"BUY","price":buy_price}
	
	if pred_sell > 0 and pred_sell>=pred_buy:
		return {"side":"SELL","price":sell_price}
	
	return {"side" : None , "price":0}

# エントリー注文を出す関数
def entry_signal( data,flag ):
	signal = mlpredict(data)
	
	if signal["side"] == "BUY":
		# flag["records"]["log"].append("過去{0}足の最高値{1}円を、直近の価格が{2}円でブレイクしました\n".format(buy_term,signal["price"],data[judge_price["BUY"]]))
		
		# # フィルター条件を確認
		# if filter( signal ) == False:
		# 	flag["records"]["log"].append("フィルターのエントリー条件を満たさなかったため、エントリーしません\n")
		# 	return flag
		
		lot,stop,flag = calculate_lot( last_data,data,flag )
		if lot > 0.01:
			flag["records"]["log"].append("{0}円で{1}BTCの買い注文を出します\n".format(data["close_price"],lot))
			
			# ここに買い注文のコードを入れる
			
			flag["records"]["log"].append("{0}円にストップを入れます\n".format(data["close_price"] - stop))
			flag["position"]["lot"],flag["position"]["stop"] = lot,stop
			flag["position"]["exist"] = True
			flag["position"]["side"] = "BUY"
			flag["position"]["price"] = data["close_price"]
		else:
			flag["records"]["log"].append("注文可能枚数{}が、最低注文単位に満たなかったので注文を見送ります\n".format(lot))

	if signal["side"] == "SELL":
		# flag["records"]["log"].append("過去{0}足の最安値{1}円を、直近の価格が{2}円でブレイクしました\n".format(sell_term,signal["price"],data[judge_price["SELL"]]))
		
		# # フィルター条件を確認
		# if filter( signal ) == False:
		# 	flag["records"]["log"].append("フィルターのエントリー条件を満たさなかったため、エントリーしません\n")
		# 	return flag
		
		lot,stop,flag = calculate_lot( last_data,data,flag )
		if lot > 0.01:
			flag["records"]["log"].append("{0}円で{1}BTCの売り注文を出します\n".format(data["close_price"],lot))
			
			# ここに売り注文のコードを入れる
			
			flag["records"]["log"].append("{0}円にストップを入れます\n".format(data["close_price"] + stop))
			flag["position"]["lot"],flag["position"]["stop"] = lot,stop
			flag["position"]["exist"] = True
			flag["position"]["side"] = "SELL"
			flag["position"]["price"] = data["close_price"]
		else:
			flag["records"]["log"].append("注文可能枚数{}が、最低注文単位に満たなかったので注文を見送ります\n".format(lot))

	return flag



# 手仕舞いのシグナルが出たら決済の成行注文 + ドテン注文 を出す関数
def close_position( data,last_data,flag ):
	
	if flag["position"]["exist"] == False:
		return flag
	
	flag["position"]["count"] += 1
	signal = mlpredict( data,last_data )
	
	if flag["position"]["side"] == "BUY":
		if signal["side"] == "SELL":
			#flag["records"]["log"].append("過去{0}足の最安値{1}円を、直近の価格が{2}円でブレイクしました\n".format(sell_term,signal["price"],data[judge_price["SELL"]]))
			flag["records"]["log"].append(str(data["close_price"]) + "円あたりで成行注文を出してポジションを決済します\n")
			
			# 決済の成行注文コードを入れる
			
			records( flag,data,data["close_price"] )
			flag["position"]["exist"] = False
			flag["position"]["count"] = 0
			flag["position"]["stop-AF"] = stop_AF
			flag["position"]["stop-EP"] = 0
			flag["add-position"]["count"] = 0
			
			
			# ドテン注文の箇所
			if filter( signal ) == False:
				flag["records"]["log"].append("フィルターのエントリー条件を満たさなかったため、ドテンエントリーはしません\n")
				return flag
			
			lot,stop,flag = calculate_lot( last_data,data,flag )
			if lot > 0.01:
				flag["records"]["log"].append("\n{0}円で{1}BTCの売りの注文を入れてドテンします\n".format(data["close_price"],lot))
				
				# ここに売り注文のコードを入れる
				
				flag["records"]["log"].append("{0}円にストップを入れます\n".format(data["close_price"] + stop))
				flag["position"]["lot"],flag["position"]["stop"] = lot,stop
				flag["position"]["exist"] = True
				flag["position"]["side"] = "SELL"
				flag["position"]["price"] = data["close_price"]
			


	if flag["position"]["side"] == "SELL":
		if signal["side"] == "BUY":
			flag["records"]["log"].append("過去{0}足の最高値{1}円を、直近の価格が{2}円でブレイクしました\n".format(buy_term,signal["price"],data[judge_price["BUY"]]))
			flag["records"]["log"].append(str(data["close_price"]) + "円あたりで成行注文を出してポジションを決済します\n")
			
			# 決済の成行注文コードを入れる
			
			records( flag,data,data["close_price"] )
			flag["position"]["exist"] = False
			flag["position"]["count"] = 0
			flag["position"]["stop-AF"] = stop_AF
			flag["position"]["stop-EP"] = 0
			flag["add-position"]["count"] = 0
			
			
			# ドテン注文の箇所
			if filter( signal ) == False:
				flag["records"]["log"].append("フィルターのエントリー条件を満たさなかったため、ドテンエントリーはしません\n")
				return flag
			
			lot,stop,flag = calculate_lot( last_data,data,flag )
			if lot > 0.01:
				flag["records"]["log"].append("\n{0}円で{1}BTCの買いの注文を入れてドテンします\n".format(data["close_price"],lot))
				
				# ここに買い注文のコードを入れる
				
				flag["records"]["log"].append("{0}円にストップを入れます\n".format(data["close_price"] - stop))
				flag["position"]["lot"],flag["position"]["stop"] = lot,stop
				flag["position"]["exist"] = True
				flag["position"]["side"] = "BUY"
				flag["position"]["price"] = data["close_price"]
			
	return flag



# 損切ラインにかかったら成行注文で決済する関数
def stop_position( data,flag ):
	
	# トレイリングストップを実行
	if stop_config == "TRAILING":
		flag = trail_stop( data,flag )

	if flag["position"]["side"] == "BUY":
		stop_price = flag["position"]["price"] - flag["position"]["stop"]
		if data["low_price"] < stop_price:
			flag["records"]["log"].append("{0}円の損切ラインに引っかかりました。\n".format( stop_price ))
			stop_price = round( stop_price - 2 * calculate_volatility(last_data) / ( chart_sec / 60) )
			flag["records"]["log"].append(str(stop_price) + "円あたりで成行注文を出してポジションを決済します\n")
			
			# 決済の成行注文コードを入れる
			
			records( flag,data,stop_price,"STOP" )
			flag["position"]["exist"] = False
			flag["position"]["count"] = 0
			flag["position"]["stop-AF"] = stop_AF
			flag["position"]["stop-EP"] = 0
			flag["add-position"]["count"] = 0
	
	
	if flag["position"]["side"] == "SELL":
		stop_price = flag["position"]["price"] + flag["position"]["stop"]
		if data["high_price"] > stop_price:
			flag["records"]["log"].append("{0}円の損切ラインに引っかかりました。\n".format( stop_price ))
			stop_price = round( stop_price + 2 * calculate_volatility(last_data) / (chart_sec / 60) )
			flag["records"]["log"].append(str(stop_price) + "円あたりで成行注文を出してポジションを決済します\n")
			
			# 決済の成行注文コードを入れる
			
			records( flag,data,stop_price,"STOP" )
			flag["position"]["exist"] = False
			flag["position"]["count"] = 0
			flag["position"]["stop-AF"] = stop_AF
			flag["position"]["stop-EP"] = 0
			flag["add-position"]["count"] = 0
			
	return flag


#------------バックテストの部分の関数--------------


# 各トレードのパフォーマンスを記録する関数
def records(flag,data,close_price,close_type=None):
	
	# 取引手数料等の計算
	entry_price = int(round(flag["position"]["price"] * flag["position"]["lot"]))
	exit_price = int(round(close_price * flag["position"]["lot"]))
	trade_cost = round( exit_price * slippage )
	
	log = "スリッページ・手数料として " + str(trade_cost) + "円を考慮します\n"
	flag["records"]["log"].append(log)
	flag["records"]["slippage"].append(trade_cost)
	
	# 手仕舞った日時と保有期間を記録
	flag["records"]["date"].append(data["close_time_dt"])
	flag["records"]["holding-periods"].append( flag["position"]["count"] )
	
	# 損切りにかかった回数をカウント
	if close_type == "STOP":
		flag["records"]["stop-count"].append(1)
	else:
		flag["records"]["stop-count"].append(0)
	
	# 値幅の計算
	buy_profit = exit_price - entry_price - trade_cost
	sell_profit = entry_price - exit_price - trade_cost
	
	# 利益が出てるかの計算
	if flag["position"]["side"] == "BUY":
		flag["records"]["side"].append( "BUY" )
		flag["records"]["profit"].append( buy_profit )
		flag["records"]["return"].append( round( buy_profit / entry_price * 100, 4 ))
		flag["records"]["funds"] = flag["records"]["funds"] + buy_profit
		if buy_profit  > 0:
			log = str(buy_profit) + "円の利益です\n\n"
			flag["records"]["log"].append(log)
		else:
			log = str(buy_profit) + "円の損失です\n\n"
			flag["records"]["log"].append(log)
	
	if flag["position"]["side"] == "SELL":
		flag["records"]["side"].append( "SELL" )
		flag["records"]["profit"].append( sell_profit )
		flag["records"]["return"].append( round( sell_profit / entry_price * 100, 4 ))
		flag["records"]["funds"] = flag["records"]["funds"] + sell_profit
		if sell_profit > 0:
			log = str(sell_profit) + "円の利益です\n\n"
			flag["records"]["log"].append(log)
		else:
			log = str(sell_profit) + "円の損失です\n\n"
			flag["records"]["log"].append(log)
	
	return flag



# バックテストの集計用の関数
def backtest_count(flag):
	
	# 成績を記録したpandas DataFrameを作成
	records = pd.DataFrame({
		"Date"     :  pd.to_datetime(flag["records"]["date"]),
		"Profit"   :  flag["records"]["profit"],
		"Side"     :  flag["records"]["side"],
		"Rate"     :  flag["records"]["return"],
		"Stop"     :  flag["records"]["stop-count"],
		"Periods"  :  flag["records"]["holding-periods"],
		"Slippage" :  flag["records"]["slippage"]
	})
	
	# 連敗回数をカウントする
	consecutive_defeats = []
	defeats = 0
	for p in flag["records"]["profit"]:
		if p < 0:
			defeats += 1
		else:
			consecutive_defeats.append( defeats )
			defeats = 0
	
	# テスト日数を集計
	time_period = datetime.fromtimestamp(last_data[-1]["close_time"]) - datetime.fromtimestamp(last_data[0]["close_time"])
	time_period = int(time_period.days)
	
	# 総損益の列を追加する
	records["Gross"] = records.Profit.cumsum()
	
	# 資産推移の列を追加する
	records["Funds"] = records.Gross + start_funds
	
	# 最大ドローダウンの列を追加する
	records["Drawdown"] = records.Funds.cummax().subtract(records.Funds)
	records["DrawdownRate"] = round(records.Drawdown / records.Funds.cummax() * 100,1)
	
	# 買いエントリーと売りエントリーだけをそれぞれ抽出する
	buy_records = records[records.Side.isin(["BUY"])]
	sell_records = records[records.Side.isin(["SELL"])]
	
	# 月別のデータを集計する
	records["月別集計"] = pd.to_datetime( records.Date.apply(lambda x: x.strftime('%Y/%m')))
	grouped = records.groupby("月別集計")
	
	month_records = pd.DataFrame({
		"Number"   :  grouped.Profit.count(),
		"Gross"    :  grouped.Profit.sum(),
		"Funds"    :  grouped.Funds.last(),
		"Rate"     :  round(grouped.Rate.mean(),2),
		"Drawdown" :  grouped.Drawdown.max(),
		"Periods"  :  grouped.Periods.mean()
		})
	
	print("バックテストの結果")
	print("-----------------------------------")
	print("買いエントリの成績")
	print("-----------------------------------")
	print("トレード回数       :  {}回".format( len(buy_records) ))
	print("勝率               :  {}％".format(round(len(buy_records[buy_records.Profit>0]) / len(buy_records) * 100,1)))
	print("平均リターン       :  {}％".format(round(buy_records.Rate.mean(),2)))
	print("総損益             :  {}円".format( buy_records.Profit.sum() ))
	print("平均保有期間       :  {}足分".format( round(buy_records.Periods.mean(),1) ))
	print("損切りの回数       :  {}回".format( buy_records.Stop.sum() ))
	
	print("-----------------------------------")
	print("売りエントリの成績")
	print("-----------------------------------")
	print("トレード回数       :  {}回".format( len(sell_records) ))
	print("勝率               :  {}％".format(round(len(sell_records[sell_records.Profit>0]) / len(sell_records) * 100,1)))
	print("平均リターン       :  {}％".format(round(sell_records.Rate.mean(),2)))
	print("総損益             :  {}円".format( sell_records.Profit.sum() ))
	print("平均保有期間       :  {}足分".format( round(sell_records.Periods.mean(),1) ))
	print("損切りの回数       :  {}回".format( sell_records.Stop.sum() ))
	
	print("-----------------------------------")
	print("総合の成績")
	print("-----------------------------------")
	print("全トレード数       :  {}回".format(len(records) ))
	print("勝率               :  {}％".format(round(len(records[records.Profit>0]) / len(records) * 100,1)))
	print("平均リターン       :  {}％".format(round(records.Rate.mean(),2)))
	print("標準偏差           :  {}％".format(round(records.Rate.std(),2)))
	print("平均利益率         :  {}％".format(round(records[records.Profit>0].Rate.mean(),2) ))
	print("平均損失率         :  {}％".format(round(records[records.Profit<0].Rate.mean(),2) ))
	print("平均保有期間       :  {}足分".format( round(records.Periods.mean(),1) ))
	print("損切りの回数       :  {}回".format( records.Stop.sum() ))
	print("")
	print("最大の勝ちトレード :  {}円".format(records.Profit.max()))
	print("最大の負けトレード :  {}円".format(records.Profit.min()))
	print("最大連敗回数       :  {}回".format( max(consecutive_defeats) ))
	print("最大ドローダウン   :  {0}円 / {1}％".format(-1 * records.Drawdown.max(), -1 * records.DrawdownRate.loc[records.Drawdown.idxmax()]  ))
	print("利益合計           :  {}円".format( records[records.Profit>0].Profit.sum() ))
	print("損失合計           :  {}円".format( records[records.Profit<0].Profit.sum() ))
	print("最終損益           :  {}円".format( records.Profit.sum() ))
	print("")
	print("初期資金           :  {}円".format( start_funds ))
	print("最終資金           :  {}円".format( records.Funds.iloc[-1] )) 
	print("運用成績           :  {}％".format( round(records.Funds.iloc[-1] / start_funds * 100),2 ))
	print("手数料合計         :  {}円".format( -1 * records.Slippage.sum() ))
	
	print("-----------------------------------")
	print("各成績指標")
	print("-----------------------------------")
	print("CAGR(年間成長率)         :  {}％".format( round((records.Funds.iloc[-1] / start_funds)**(  365 / time_period ) * 100 - 100,2)   ))
	print("MARレシオ                :  {}".format(round( (records.Funds.iloc[-1] / start_funds -1)*100 / records.DrawdownRate.max(),2 )))
	print("シャープレシオ           :  {}".format( round(records.Rate.mean()/records.Rate.std(),2) ))
	print("プロフィットファクター   :  {}".format( round(records[records.Profit>0].Profit.sum()/abs(records[records.Profit<0].Profit.sum()),2) ))
	print("損益レシオ               :  {}".format(round( records[records.Profit>0].Rate.mean()/abs(records[records.Profit<0].Rate.mean()) ,2)))
	
	print("-----------------------------------")
	print("月別の成績")
	
	for index , row in month_records.iterrows():
		print("-----------------------------------")
		print( "{0}年{1}月の成績".format( index.year, index.month ) )
		print("-----------------------------------")
		print("トレード数         :  {}回".format( row.Number.astype(int) ))
		print("月間損益           :  {}円".format( row.Gross.astype(int) ))
		print("平均リターン       :  {}％".format( row.Rate ))
		print("継続ドローダウン   :  {}円".format( -1 * row.Drawdown.astype(int) ))
		print("月末資金           :  {}円".format( row.Funds.astype(int) ))
	
	
	# 際立った損益を表示
	n = 10
	print("------------------------------------------")
	print("＋{}%を超えるトレードの回数  :  {}回".format(n,len(records[records.Rate>n]) ))
	print("------------------------------------------")
	for index,row in records[records.Rate>n].iterrows():
		print( "{0}  |  {1}％  |  {2}".format(row.Date,round(row.Rate,2),row.Side ))
	print("------------------------------------------")
	print("－{}%を下回るトレードの回数  :  {}回".format(n,len(records[records.Rate< n*-1]) ))
	print("------------------------------------------")
	for index,row in records[records.Rate < n*-1].iterrows():
		print( "{0}  |  {1}％  |  {2}".format(row.Date,round(row.Rate,2),row.Side  ))
	
	
	# ログファイルの出力
	file =  open("./{0}-log.txt".format(datetime.now().strftime("%Y-%m-%d-%H-%M")),'wt',encoding='utf-8')
	file.writelines(flag["records"]["log"])
	
	
	# 損益曲線をプロット
	plt.subplot(1,2,1)
	plt.plot( records.Date, records.Funds )
	plt.xlabel("Date")
	plt.ylabel("Balance")
	plt.xticks(rotation=50) # X軸の目盛りを50度回転
	
	
	# リターン分布の相対度数表を作る
	plt.subplot(1,2,2)
	plt.hist( records.Rate,50,rwidth=0.9)
	plt.axvline( x=0,linestyle="dashed",label="Return = 0" )
	plt.axvline( records.Rate.mean(), color="orange", label="AverageReturn" )
	plt.legend() # 凡例を表示
	plt.show()
	


#------------ここからメイン処理--------------

# 価格チャートを取得
price = get_price(chart_sec,after=1451606400)

flag = {
	"position":{
		"exist" : False,
		"side" : "",
		"price": 0,
		"stop":0,
		"stop-AF": stop_AF,
		"stop-EP":0,
		"ATR":0,
		"lot":0,
		"count":0
	},
	"add-position":{
		"count":0,
		"first-entry-price":0,
		"last-entry-price":0,
		"unit-range":0,
		"unit-size":0,
		"stop":0
	},
	"records":{
		"date":[],
		"profit":[],
		"return":[],
		"side":[],
		"stop-count":[],
		"funds" : start_funds,
		"holding-periods":[],
		"slippage":[],
		"log":[]
	}
}


df = pd.DataFrame(price)
# df=df.rename(columns={
# 		"close_time_dt" : "timestamp",
# 		# "open_price" : "op",
# 		# "high_price" : "hi",
# 		# "low_price" : "lo",
# 		# "close_price": "cl",
# 		# "volume": "volume",
# })
df['close_time_dt'] = pd.to_datetime(df['close_time_dt'])
df['timestamp'] = df['close_time_dt']
# df['cl'] = df['cl'].astype(np.float64)
# df['op'] = df['op'].astype(np.float64)
# df['hi'] = df['hi'].astype(np.float64)
# df['lo'] = df['lo'].astype(np.float64)
# df['cl'] = df['cl'].astype(np.float64)
df["open_price"] = df["open_price"].astype(np.float64)
df["high_price"] = df["high_price"].astype(np.float64)
df["low_price"] = df["low_price"].astype(np.float64)
df["close_price"] = df["close_price"].astype(np.float64)
df['volume'] = df['volume'].astype(np.float64)

# df = df.set_index('timestamp')
# df = df[[
# 		"op",
# 		"hi",
# 		"lo",
# 		"cl",
# 		"volume",
# ]]
df = calc_features(df)

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
#     'MINUS_DI',
#     'MINUS_DM',
    'MOM',
#     'PLUS_DI',
#     'PLUS_DM',
    'RSI',
    'STOCH_slowk',
    'STOCH_slowd',
    'STOCHF_fastk',
#     'STOCHRSI_fastd',
    'ULTOSC',
    'WILLR',
#     'ADOSC',
#     'NATR',
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

price = df.to_dict('records')


last_data = []
need_term = max(buy_term,sell_term,volatility_term)
i = 0
#while i < len(price):
while i < 500:
	data = price[i]
	df_i = pd.DataFrame(data,index=[i])

	# ポジションがある場合
	if flag["position"]["exist"]:
		if stop_config != "OFF":
			flag = stop_position( data,flag )
		flag = close_position( data,flag )
		flag = add_position( data,flag )
	
	# ポジションがない場合
	else:
		#flag = entry_signal( data,last_data,flag )
		flag = entry_signal(data,flag)
	

	last_data.append( data )
	i += 1

	time.sleep(wait)

print(flag)

print("--------------------------")
print("テスト期間：")
print("開始時点 : " + str(price[0]["close_time_dt"]))
print("終了時点 : " + str(price[-1]["close_time_dt"]))
print(str(len(price)) + "件のローソク足データで検証")
print("--------------------------")


backtest_count(flag)


# OOS予測値を計算
def my_cross_val_predict(estimator, X, y=None, cv=None):
    y_pred = y.copy()
    y_pred[:] = np.nan
    for train_idx, val_idx in cv:
        estimator.fit(X[train_idx], y[train_idx])
        y_pred[val_idx] = estimator.predict(X[val_idx])
    return y_pred



# モデルの読み込み
model_y_buy = joblib.load('./bot/model_y_buy.xz')
model_y_sell = joblib.load('./bot/model_y_sell.xz')

df['y_pred_buy'] = model_y_buy.predict(df[features])
df['y_pred_sell'] = model_y_sell.predict(df[features])

print(df[['close_time_dt','y_pred_buy','y_pred_sell']])
