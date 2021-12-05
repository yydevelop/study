import logging

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import Integer
from sqlalchemy.exc import IntegrityError

from app.models.base import Base
from app.models.base import session_scope


logger = logging.getLogger(__name__)


class BaseCandleMixin(object):
    time = Column(DateTime, primary_key=True, nullable=False)
    open = Column(Float)
    close = Column(Float)
    high = Column(Float)
    low = Column(Float)
    volume = Column(Integer)

    @classmethod
    def create(cls, time, open, close, high, low, volume):
        candle = cls(time=time,
                     open=open,
                     close=close,
                     high=high,
                     low=low,
                     volume=volume)
        try:
            with session_scope() as session:
                session.add(candle)
            return candle
        except IntegrityError:
            return False

    @classmethod
    def get(cls, time):
        with session_scope() as session:
            candle = session.query(cls).filter(
                cls.time == time).first()
        if candle is None:
            return None
        return candle

    def save(self):
        with session_scope() as session:
            session.add(self)


class UsdJpyBaseCandle1H(BaseCandleMixin, Base):
    __tablename__ = 'USD_JPY_1H'


class UsdJpyBaseCandle1M(BaseCandleMixin, Base):
    __tablename__ = 'USD_JPY_1M'


class UsdJpyBaseCandle5S(BaseCandleMixin, Base):
    __tablename__ = 'USD_JPY_5S'

