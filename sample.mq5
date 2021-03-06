sinput double Lots = 0.1;   //売買ロット数
input int FastMAPeriod = 20;  //短期移動平均の期間
input int SlowMAPeriod = 50;  //長期移動平均の期間

ulong Ticket = 0; //チケット番号

double FastMA[];  //短期移動平均用配列
double SlowMA[];  //長期移動平均用配列
int FastMAHandle; //短期移動平均用ハンドル
int SlowMAHandle; //長期移動平均用ハンドル

//初期化関数
int OnInit()
{
   //テクニカル指標の初期化
   FastMAHandle = iMA(_Symbol, 0, FastMAPeriod, 0, MODE_SMA, PRICE_CLOSE);
   SlowMAHandle = iMA(_Symbol, 0, SlowMAPeriod, 0, MODE_SMA, PRICE_CLOSE);
   ArraySetAsSeries(FastMA, true);
   ArraySetAsSeries(SlowMA, true);
   return 0;
}

//ティック時実行関数
void OnTick()
{
   //テクニカル指標の更新
   CopyBuffer(FastMAHandle, 0, 0, 3, FastMA);
   CopyBuffer(SlowMAHandle, 0, 0, 3, SlowMA);

   int pos = 0; //ポジションの状態
   //未決済ポジションの有無
   if(PositionSelectByTicket(Ticket))
   {
      if(PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY) pos = 1; //買いポジション
      if(PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_SELL) pos = -1; //売りポジション
   }
   
   if(FastMA[2] <= SlowMA[2] && FastMA[1] > SlowMA[1]) //買いシグナル
   {
      //売りポジションがあれば決済注文
      if(pos < 0)
      {
         MqlTradeRequest request = {};
         MqlTradeResult result = {}; 
         request.action = TRADE_ACTION_DEAL;
         request.symbol = _Symbol;
         request.volume = Lots;
         request.price = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
         request.type = ORDER_TYPE_BUY;
         request.position = Ticket;
         bool b = OrderSend(request, result);
         if(result.retcode == TRADE_RETCODE_DONE) pos = 0; //決済成功すればポジションなしに
      }
      //ポジションがなければ買い注文
      if(pos == 0)
      {
         MqlTradeRequest request = {};
         MqlTradeResult result = {}; 
         request.action = TRADE_ACTION_DEAL;
         request.symbol = _Symbol;
         request.volume = Lots;
         request.price = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
         request.type = ORDER_TYPE_BUY;
         bool b = OrderSend(request, result);
         if(result.retcode == TRADE_RETCODE_DONE) Ticket = result.deal;
      }
   }
   if(FastMA[2] >= SlowMA[2] && FastMA[1] < SlowMA[1]) //売りシグナル
   {
      //買いポジションがあれば決済注文
      if(pos > 0)
      {
         MqlTradeRequest request = {};
         MqlTradeResult result = {}; 
         request.action = TRADE_ACTION_DEAL;
         request.symbol = _Symbol;
         request.volume = Lots;
         request.price = SymbolInfoDouble(_Symbol, SYMBOL_BID);
         request.type = ORDER_TYPE_SELL;
         request.position = Ticket;
         bool b = OrderSend(request, result);
         if(result.retcode == TRADE_RETCODE_DONE) pos = 0; //決済成功すればポジションなしに
      }
      //ポジションがなければ売り注文
      if(pos == 0)
      {
         MqlTradeRequest request = {};
         MqlTradeResult result = {}; 
         request.action = TRADE_ACTION_DEAL;
         request.symbol = _Symbol;
         request.volume = Lots;
         request.price = SymbolInfoDouble(_Symbol, SYMBOL_BID);
         request.type = ORDER_TYPE_SELL;
         bool b = OrderSend(request, result);
         if(result.retcode == TRADE_RETCODE_DONE) Ticket = result.deal;
      }
   }
}
