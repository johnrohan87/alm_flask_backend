# -*- coding: utf-8 -*-
"""User models."""
import datetime as dt

from flask_login import UserMixin
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.hybrid import hybrid_method

from alm_flask_backend.database import Column, PkModel, db, reference_col, relationship
from alm_flask_backend.extensions import bcrypt


class Role(PkModel):
    """A role for a user."""

    __tablename__ = "roles"
    name = Column(db.String(80), unique=True, nullable=False)
    user_id = reference_col("users", nullable=True)
    user = relationship("User", backref="roles")

    def __init__(self, name, **kwargs):
        """Create instance."""
        super().__init__(name=name, **kwargs)

    def __repr__(self):
        """Represent instance as a unique string."""
        return f"<Role({self.name})>"


class User(UserMixin, PkModel):
    """A user of the app."""

    __tablename__ = "users"
    username = Column(db.String(80), unique=True, nullable=False)
    email = Column(db.String(80), unique=True, nullable=False)
    _password = Column("password", db.LargeBinary(128), nullable=True)
    created_at = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    first_name = Column(db.String(30), nullable=True)
    last_name = Column(db.String(30), nullable=True)
    active = Column(db.Boolean(), default=False)
    is_admin = Column(db.Boolean(), default=False)
    rss_feeds = relationship("RssFeed", back_populates="user", cascade="all, delete-orphan")


    @hybrid_property
    def password(self):
        """Hashed password."""
        return self._password
    
    def rss_feeds_count(self):
        """Return the number of RSS feeds for the user."""
        return len(self.rss_feeds)

    @password.setter
    def password(self, value):
        """Set password."""
        self._password = bcrypt.generate_password_hash(value)

    def check_password(self, value):
        """Check password."""
        return bcrypt.check_password_hash(self._password, value)
    
    def rss_feeds(self):
        """A user's RSS feeds."""
        return RssFeed.query.filter_by(user_id=self.id).all()

    @rss_feeds
    def rss_feeds(self, feeds):
        for feed in feeds:
            feed.user_id = self.id
            db.session.add(feed)
        db.session.commit()

    @hybrid_method
    def get_rss_feeds(self, *feed_ids):
        """Return a list of RSS feeds for the user, filtered by feed IDs if provided."""
        query = self.rss_feeds.filter(RssFeed.id.in_(feed_ids)) if feed_ids else self.rss_feeds
        return query.all()

    @property
    def full_name(self):
        """Full user name."""
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        """Represent instance as a unique string."""
        return f"<User({self.username!r})>"

#create a flask class consisting of rss feeds and their children stories
class FlaskFeeds:
    def __init__(self, feed_urls):
        self.feeds = [feedparser.parse(url) for url in feed_urls]

    def get_stories(self):
        stories = []
        for feed in self.feeds:
            stories.extend(feed['items'])
        return stories

    def get_stories_by_tag(self, tag):
        return list(filter(lambda item: tag in item['tags'], [item for feed in self.feeds for item in feed['items']]))
    
#create a flask class consisting of Stories from the parent class FlaskFeeds 