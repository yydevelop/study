import numpy as np
import pandas as pd
from datetime import datetime


# 設定値
winning_percentage = 0.387     # 勝率
payoff_ratio = 2.97            # 損益レシオ
funds = 200000                # 初期資金
funds2 = 700000                # 途中経過時点での資金

drawdown_rate_list = np.arange(10,100,10) # ドローダウン率 10～90％
risk_rate_list = np.arange(0.5,10,0.5)    # 口座のリスク率 0.5～9.5％


# 特性方程式の関数
def equation(x):

	k = payoff_ratio
	p = winning_percentage
	return p * x**(k+1) + (1-p) - x


# 特定方程式の解を探す
def solve_equation():
	
	R = 0
	while equation(R) > 0:
		R += 1e-4
	if R>=1:
		R=1
	return R


# 破産確率を計算する公式
def calculate_ruin_rate( R, risk_rate, bankrupt_line ):
	
	risk_rate = risk_rate / 100
	unit = (np.log(funds2) - np.log(bankrupt_line)) / abs(np.log( 1-risk_rate ))
	unit = int(np.floor(unit))
	return R ** unit


# メイン処理

result = []

bankrupt_line_list = []
for drawdown_rate in drawdown_rate_list:
	bankrupt_line_list.append(int(round(funds * (1 - drawdown_rate / 100))))

for risk_rate in risk_rate_list:
	temp = []
	for bankrupt_line in bankrupt_line_list:
		R = solve_equation()
		ruin_rate = calculate_ruin_rate(R,risk_rate,bankrupt_line)
		ruin_rate = round(ruin_rate * 100,2)
		if ruin_rate > 100:
			ruin_rate = 100.0
		temp.append(ruin_rate)
	result.append(temp)

df = pd.DataFrame(result)
df.index = [str(i)+"％" for i in risk_rate_list]
df.columns = [str(i)+"％" for i in drawdown_rate_list]
print("初期資金{}円からのドローダウン確率を、{}円の時点で再計算した表\n".format(funds,funds2))
print(df)

# 最終結果をcsvファイルに出力
df.to_csv("RuinTable-{}.csv".format(datetime.now().strftime("%Y-%m-%d-%H-%M")) )