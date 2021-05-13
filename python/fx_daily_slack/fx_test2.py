# import関連
import sys
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pylab as plt
import seaborn as sns
import slackweb
import warnings
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
import urllib.request
import linecache
#import datetime
from datetime import datetime,date, timedelta

def calcFxSend(save_dir,save_file):
    warnings.filterwarnings('ignore') # 実行上問題ない注意は非表示にする

    slack = slackweb.Slack(url="https://hooks.slack.com/services/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")
    url = 'https://kabutan.jp/info/accessranking/3_2'

    # dataフォルダの場所を各自指定してください
    data_dir = save_dir
    data = pd.read_csv(data_dir + "\\" + save_file) # FXデータの読み込み（データは同じリポジトリのdataフォルダに入っています）
    #data = data.drop(range(1,6563))
    data=data.query("Date>='1997-01-02'")
    
    # pandasのDataFrameのままでは、扱いにくい+実行速度が遅いので、numpyに変換して処理します
    data2 = np.array(data)

    # 5日移動平均線を追加します
    data2 = np.c_[data2, np.zeros((len(data2),1))] # 列の追加
    ave_day = 5
    for i in range(ave_day, len(data2)):
        tmp =data2[i-ave_day+1:i+1,4].astype(np.float) # pythonは0番目からindexが始まります
        data2[i,5] = np.mean(tmp)

    # 25日移動平均線を追加します
    data2 = np.c_[data2, np.zeros((len(data2),1))]
    ave_day = 25
    for i in range(ave_day, len(data2)):
        tmp =data2[i-ave_day+1:i+1,4].astype(np.float)
        data2[i,6] = np.mean(tmp)

    # 75日移動平均線を追加します
    data2 = np.c_[data2, np.zeros((len(data2),1))] # 列の追加
    ave_day = 75
    for i in range(ave_day, len(data2)):
        tmp =data2[i-ave_day+1:i+1,4].astype(np.float)
        data2[i,7] = np.mean(tmp)
        
    # 200日移動平均線を追加します
    data2 = np.c_[data2, np.zeros((len(data2),1))] # 列の追加
    ave_day = 200
    for i in range(ave_day, len(data2)):
        tmp =data2[i-ave_day+1:i+1,4].astype(np.float)
        data2[i,8] = np.mean(tmp)

    # 一目均衡表を追加します (9,26,52) 
    para1 =9
    para2 = 26
    para3 = 52

    # 転換線 = （過去(para1)日間の高値 + 安値） ÷ 2
    data2 = np.c_[data2, np.zeros((len(data2),1))] # 列の追加
    for i in range(para1, len(data2)):
        tmp_high =data2[i-para1+1:i+1,2].astype(np.float)
        tmp_low =data2[i-para1+1:i+1,3].astype(np.float)
        data2[i,9] = (np.max(tmp_high) + np.min(tmp_low)) / 2 
        
    # 基準線 = （過去(para2)日間の高値 + 安値） ÷ 2
    data2 = np.c_[data2, np.zeros((len(data2),1))]
    for i in range(para2, len(data2)):
        tmp_high =data2[i-para2+1:i+1,2].astype(np.float)
        tmp_low =data2[i-para2+1:i+1,3].astype(np.float)
        data2[i,10] = (np.max(tmp_high) + np.min(tmp_low)) / 2 

    # 先行スパン1 = ｛ （転換値+基準値） ÷ 2 ｝を(para2)日先にずらしたもの
    data2 = np.c_[data2, np.zeros((len(data2),1))]
    for i in range(0, len(data2)-para2):
        tmp =(data2[i,9] + data2[i,10]) / 2 
        data2[i+para2,11] = tmp


    # 先行スパン2 = ｛ （過去(para3)日間の高値+安値） ÷ 2 ｝を(para2)日先にずらしたもの
    data2 = np.c_[data2, np.zeros((len(data2),1))]
    for i in range(para3, len(data2)-para2):
        tmp_high =data2[i-para3+1:i+1,2].astype(np.float)
        tmp_low =data2[i-para3+1:i+1,3].astype(np.float)
        data2[i+para2,12] = (np.max(tmp_high) + np.min(tmp_low)) / 2 

    # 25日ボリンジャーバンド（±1, 2シグマ）を追加します
    parab = 25
    data2 = np.c_[data2, np.zeros((len(data2),4))] # 列の追加
    for i in range(parab, len(data2)):
        tmp = data2[i-parab+1:i+1,4].astype(np.float)
        data2[i,13] = np.mean(tmp) + 1.0* np.std(tmp) 
        data2[i,14] = np.mean(tmp) - 1.0* np.std(tmp) 
        data2[i,15] = np.mean(tmp) + 2.0* np.std(tmp) 
        data2[i,16] = np.mean(tmp) - 2.0* np.std(tmp) 


    # 説明変数となる行列Xを作成します
    day_ago = 25 # 何日前までのデータを使用するのかを設定
    num_sihyou = 1 + 4 + 4 +4 # 終値1本、MVave4本、itimoku4本、ボリンジャー4本

    X = np.zeros((len(data2), day_ago*num_sihyou)) 

    for s in range(0, num_sihyou): # 日にちごとに横向きに並べる
        for i in range(0, day_ago):
            X[i:len(data2),day_ago*s+i] = data2[0:len(data2)-i,s+4]

    # 被説明変数となる Y = pre_day後の終値-当日終値 を作成します
    Y = np.zeros(len(data2))

    # 何日後を値段の差を予測するのか決めます
    pre_day = 1
    Y[0:len(Y)-pre_day] = X[pre_day:len(X),0] - X[0:len(X)-pre_day,0]

    # 【重要】X, Yを正規化します
    original_X = np.copy(X) # コピーするときは、そのままイコールではダメ
    tmp_mean = np.zeros(len(X))

    for i in range(day_ago,len(X)):
        tmp_mean[i] = np.mean(original_X[i-day_ago+1:i+1,0]) # 25日分の平均値
        for j in range(0, X.shape[1]): 
            X[i,j] = (X[i,j] - tmp_mean[i]) # Xを正規化
        Y[i] =  Y[i] # X同士の引き算しているので、Yはそのまま

    # # XとYを学習データとテストデータ(2017年～)に分ける
    # X_train = X[200:5713,:] # 200日平均を使うので、それ以降を学習データに使用します
    # Y_train = Y[200:5713] 

    # X_test = X[5713:len(X)-pre_day,:] 
    # Y_test = Y[5713:len(Y)-pre_day]
    from sklearn.model_selection import train_test_split
    X=X[200:len(X)-pre_day,]
    Y=Y[200:len(Y)-pre_day]
    X_train,X_test,Y_train,Y_test = train_test_split(X, Y,train_size=0.8,shuffle=False)

    # 学習データを使用して、線形回帰モデルを作成します
    from sklearn.linear_model import Ridge
    ridge = Ridge().fit(X_train, Y_train)


    Y_pred = ridge.predict(X_test) # 予測する

    result = pd.DataFrame(Y_pred) # 予測
    result.columns = ['Y_pred']
    result['Y_test'] = Y_test


    sns.set_style('darkgrid') 
    sns.regplot(x='Y_pred', y='Y_test', data=result) #plotする


    # 正答率を計算
    success_num = 0
    success_sum = 0
    for i in range(len(Y_pred)):
        if Y_pred[i] * Y_test[i] >=0:
            success_num+=1
        if Y_pred[i] > 0.05:
            success_sum += Y_test[i]
        elif Y_pred[i] <= -0.05:
            success_sum -= Y_test[i]
    

    slack.notify(text="--------------------------------")
    print("予測日数："+ str(len(Y_pred))+"、正解日数："+str(success_num)+"、正解率："+str(success_num/len(Y_pred)*100)+"、利益合計："+str(success_sum))
    slack.notify(text="予測日数："+ str(len(Y_pred))+"、正解日数："+str(success_num)+"、正解率："+str(success_num/len(Y_pred)*100)+"、利益合計："+str(success_sum))
    slack.notify(text=" ")

    ## 前々日終値に比べて前日終値が高い場合は、買いとする
    slack.notify(text=" ")
    slack.notify(text=data2[len(data2)-2][0]+"の値")
    slack.notify(text=str(data2[len(data2)-1][4]))
    slack.notify(text=" ")
    print(data2[len(data2)-1][0])
    print(str(Y_pred[len(Y_pred)-1]))
    print(str(Y_pred[len(Y_pred)-1]+data2[len(data2)-1][4]))
    slack.notify(text=data2[len(data2)-1][0]+"の予想")
    if Y_pred[len(Y_pred)-1] > 0.05:
        tmpStr = "買い："
    elif Y_pred[len(Y_pred)-1] <= -0.05:
        tmpStr = "売り："
    else:
        tmpStr = "様子見："
    slack.notify(text=tmpStr+"前日から"+str(Y_pred[len(Y_pred)-1]))
    slack.notify(text=str(Y_pred[len(Y_pred)-1]+data2[len(data2)-1][4]))

def getCSV(save_dir,save_file):
    urllib.request.urlretrieve("https://stooq.com/q/d/l/?s=usdjpy&i=d","{0}".format(save_file))

    today = datetime.today()
    yesterday = today - timedelta(days=1)

    lastrow = sum(1 for i in open(save_dir+"\\"+save_file)) # ファイル内の最終行の行番号を取得
    lastrow_sen = linecache.getline(save_dir+"\\"+save_file, lastrow) # ファイル内の最終行の一行を取得
    with open(save_dir+"\\"+save_file, mode='a') as f:
        f.write(lastrow_sen.replace(datetime.strftime(yesterday, '%Y-%m-%d'),datetime.strftime(today, '%Y-%m-%d')))
        
if __name__ == '__main__':
    import os
    today = datetime.today()
    args = sys.argv
    if 2 <= len(args):
        file_name=args[1]
    else:
        file_name="USDJPY_"+today.strftime('%Y%m%d')+".csv"
        getCSV(os.getcwd(),file_name)
    calcFxSend(os.getcwd(),file_name)
