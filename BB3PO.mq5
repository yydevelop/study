//共通ライブラリ
#include "LibEA.mqh"

input ENUM_TIMEFRAMES TF = 0; //タイム フレーム
input int SLpips = 1000; //損切り値幅(pips) 
//input int TPpips = 100; //利食い値幅(pips)
sinput double Lots = 0.1; //売買ロット数
input int ShortMAPeriod = 12*5; //短期移動平均の期間
input int MidMAPeriod = 12*11; //長期移動平均の期間
input int LongMAPeriod = 12*22; //長期移動平均の期間
input double Deviation = 3.0;

//ティック時実行関数
void Tick()
{
   if(MyOrderProfitPips() <= -SLpips) MyOrderClose();
//   if( MyOrderProfitPips() >= TPpips || MyOrderProfitPips() <= -SLpips) MyOrderClose();
//   if( isNewBar(_ Symbol, PERIOD_ M 1) //１ 分 足 の 始値 で 判別 
//      && (MyOrderProfitPips() >= TPpips || MyOrderProfitPips() <= -SLpips) 
//   ) MyOrderClose();

   int sig_entry = EntrySignal(); //仕掛けシグナル
   int sig_filter = FilterSignal(sig_entry); //トレンドフィルタ

   int myPosType = MyOrderType();
   if(myPosType == OP_BUY && sig_entry == -1) MyOrderClose();
   if(myPosType == OP_SELL && sig_entry == 1) MyOrderClose();

   //成行売買
   MyOrderSendMarket(sig_filter, sig_entry, Lots);

}

//仕掛けシグナル関数
int EntrySignal()
{
   double upperBand = iBands(_Symbol, TF, 20, Deviation, 0, PRICE_CLOSE, MODE_UPPER, 1);
   double lowerBand = iBands(_Symbol, TF, 20, Deviation, 0, PRICE_CLOSE, MODE_LOWER, 1);

   MqlTick last_tick;
   SymbolInfoTick(_Symbol,last_tick);
   
   double Ask=last_tick.ask;
   double Bid=last_tick.bid;

   int ret = 0; //シグナルの初期化

   //買いシグナル
   if(Ask <= lowerBand) ret = 1;
   //売りシグナル
   if(Bid >= upperBand) ret = -1;

   return ret; //シグナルの出力
}

//フィルタ関数
int FilterSignal(int signal)
{
   //１本前と２本前の移動平均
   double ShortMA = iMA(_Symbol, TF, ShortMAPeriod, 0, MODE_SMA, PRICE_CLOSE, 1);
   double MidMA = iMA(_Symbol, TF, MidMAPeriod, 0, MODE_SMA, PRICE_CLOSE, 1);
   double LongMA = iMA(_Symbol, TF, LongMAPeriod, 0, MODE_SMA, PRICE_CLOSE, 1);

   int ret = 0; //シグナルの初期化

   //買いシグナルのフィルタ
   if(ShortMA > MidMA && MidMA > LongMA && signal==1) ret = signal;

   //売りシグナルのフィルタ
   if(ShortMA < MidMA && MidMA < LongMA && signal==-1) ret = signal;

   return ret; //シグナルの出力
}
