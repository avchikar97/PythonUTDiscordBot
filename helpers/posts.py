from datetime import datetime
from sqlalchemy import Column, String, Integer, DeclarativeMeta

class posts(DeclarativeMeta):
    __tablename__ = datetime.now().strftime("%m-%y")

    #Column for name, posts, how many mentions, how many times mentioned, how many posts in anime
    name = Column(String, primary_key=True)
    posts = Column(Integer)
    mentions = Column(Integer)
    mentioned = Column(Integer)
    animePosts = Column(Integer)