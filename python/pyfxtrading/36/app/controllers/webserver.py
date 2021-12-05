from flask import Flask
from flask import jsonify
from flask import render_template
from flask import request

from app.models.dfcandle import DataFrameCandle

import constants
import settings

app = Flask(__name__, template_folder='../views')


@app.teardown_appcontext
def remove_session(ex=None):
    from app.models.base import Session
    Session.remove()


@app.route('/')
def index():
    return render_template('./chart.html')


@app.route('/api/candle/', methods=['GET'])
def api_make_handler():
    product_code = request.args.get('product_code')
    if not product_code:
        return jsonify({'error': 'No product_code params'}), 400

    limit_str = request.args.get('limit')
    limit = 1000
    if limit_str:
        limit = int(limit_str)

    if limit < 0 or limit > 1000:
        limit = 1000

    duration = request.args.get('duration')
    if not duration:
        duration = constants.DURATION_1M
    duration_time = constants.TRADE_MAP[duration]['duration']
    df = DataFrameCandle(product_code, duration_time)
    df.set_all_candles(limit)

    sma = request.args.get('sma')
    if sma:
        str_sma_period_1 = request.args.get('smaPeriod1')
        str_sma_period_2 = request.args.get('smaPeriod2')
        str_sma_period_3 = request.args.get('smaPeriod3')
        if str_sma_period_1:
            period_1 = int(str_sma_period_1)
        if str_sma_period_2:
            period_2 = int(str_sma_period_2)
        if str_sma_period_3:
            period_3 = int(str_sma_period_3)
        if not str_sma_period_1 or period_1 < 0:
            period_1 = 7
        if not str_sma_period_2 or period_2 < 0:
            period_2 = 14
        if not str_sma_period_3 or period_3 < 0:
            period_3 = 50
        df.add_sma(period_1)
        df.add_sma(period_2)
        df.add_sma(period_3)

    return jsonify(df.value), 200



def start():
    # app.run(host='127.0.0.1', port=settings.web_port, threaded=True)
    app.run(host='0.0.0.0', port=settings.web_port, threaded=True)
