//共通ライブラリ
#include "LibEA.mqh"

input ENUM_TIMEFRAMES TF = 0; //タイム フレーム
input int SLpips = 100; //損切り値幅(pips) 
//input int TPpips = 300; //利食い値幅(pips)
sinput double Lots = 0.1; //売買ロット数
input int EXIT_TIME_H = 24;
input int MACD2_PLUS = 4;
input int BEFORE_ICOUNT = 10;

//ティック時実行関数
void Tick()
{
   if(MyOrderProfitPips() <= -SLpips) MyOrderClose();
   if( TimeCurrent() >= MyOrderOpenTime() + EXIT_TIME_H * 60 * 60 ) {
      MyOrderClose();
   }
   if(DayOfWeek() == FRIDAY && Hour() >= 22){
      MyOrderClose();
      return;
   }
//   if( MyOrderProfitPips() >= TPpips || MyOrderProfitPips() <= -SLpips) MyOrderClose();
//   if( isNewBar(_ Symbol, PERIOD_ M 1) //１ 分 足 の 始値 で 判別 
//      && (MyOrderProfitPips() >= TPpips || MyOrderProfitPips() <= -SLpips) 
//   ) MyOrderClose();

   int sig_entry = EntrySignal(); //仕掛けシグナル

   int myPosType = MyOrderType();
   if(myPosType == OP_BUY && sig_entry == -1) MyOrderClose();
   if(myPosType == OP_SELL && sig_entry == 1) MyOrderClose();

   //成行売買
   MyOrderSendMarket(sig_entry, sig_entry, Lots);

}

//仕掛けシグナル関数
int EntrySignal()
{
   double macd_hist = iOsMA(
                           _Symbol,           // 通貨ペア
                           TF,              // 時間軸
                           12,             // ファーストEMA期間
                           26,             // スローEMA期間
                           9,              // シグナルライン期間
                           PRICE_CLOSE,  // 適用価格
                           1 // シフト
   );

   double macd2_hist  = iOsMA(
                           _Symbol,           // 通貨ペア
                           TF,              // 時間軸
                           12*MACD2_PLUS,             // ファーストEMA期間
                           26*MACD2_PLUS,             // スローEMA期間
                           9*MACD2_PLUS,              // シグナルライン期間
                           PRICE_CLOSE,  // 適用価格
                           1 // シフト
   );

   double macd_local = 0.0;
   double macd_hist_local = 0.0;
   double macd_hist_max = -999;
   double macd_hist_min = 999;
   int icount;
   for ( icount = 1; icount <= BEFORE_ICOUNT; icount++ ) { 
      macd_hist_local = iOsMA(
                           _Symbol,           // 通貨ペア
                           TF,              // 時間軸
                           12,             // ファーストEMA期間
                           26,             // スローEMA期間
                           9,              // シグナルライン期間
                           PRICE_CLOSE,  // 適用価格
                           icount // シフト
      );
      if (macd_hist_max < macd_hist_local){
         macd_hist_max = macd_hist_local;
      }
      if (macd_hist_min > macd_hist_local){
         macd_hist_min = macd_hist_local;
      }
   }

   MqlTick last_tick;
   SymbolInfoTick(_Symbol,last_tick);
   double close = iClose(
         _Symbol,           // 通貨ペア
         TF,              // 時間軸
         1
   );
   double Ask=last_tick.ask;
   double Bid=last_tick.bid;

   int ret = 0; //シグナルの初期化

   //買いシグナル
   if(macd_hist>0 && macd2_hist>0 && macd_hist>=macd_hist_max && Bid >= close) ret = 1;
   //売りシグナル
   if(macd_hist<0 && macd2_hist<0 && macd_hist<=macd_hist_min && Ask <= close) ret = -1;

   return ret; //シグナルの出力
}

