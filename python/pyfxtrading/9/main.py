import logging
import sys

import settings


logging.basicConfig(level=logging.INFO, stream=sys.stdout)


if __name__ == "__main__":
    print(settings.account_id)
    print(settings.access_token)
    print(settings.product_code)
    print(settings.db_name)
    print(settings.db_driver)
    print(settings.web_port)
    print(settings.trade_duration)
    print(settings.back_test)
    print(settings.use_percent)
    print(settings.past_period)
    print(settings.stop_limit_percent)
    print(settings.num_ranking)
