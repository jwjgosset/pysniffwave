'''
..  codeauthor:: Charles Blais
'''

from sqlalchemy import Column, Integer, Float, String, DateTime

from .database import Base


class Channel(Base):  # type: ignore
    __tablename__ = 'Channel'

    recorded_at = Column(DateTime, nullable=False, primary_key=True)
    network = Column(String(2), nullable=False, primary_key=True)
    station = Column(String(5), nullable=False, primary_key=True)
    location = Column(String(2), nullable=False, primary_key=True)
    channel = Column(String(3), nullable=False, primary_key=True)
    n_samples = Column(Integer, nullable=False)
    sample_rate = Column(Float, nullable=False)
    start_time = Column(DateTime, nullable=False)
    n_bytes = Column(Integer, nullable=False)
    data_latency = Column(Float, nullable=False)
    feeding_latency = Column(Float, nullable=False)


class ChannelError(Base):  # type: ignore
    __tablename__ = 'ChannelError'

    recorded_at = Column(DateTime, nullable=False, primary_key=True)
    network = Column(String(2), nullable=False, primary_key=True)
    station = Column(String(5), nullable=False, primary_key=True)
    location = Column(String(2), nullable=False, primary_key=True)
    channel = Column(String(3), nullable=False, primary_key=True)
    error = Column(String(20), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
