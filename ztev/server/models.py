from dataclasses import dataclass
from sqlalchemy import Table, Column, Integer, String, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.orm.attributes import QueryableAttribute
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import func
from json import JSONEncoder

def _default(self, obj):
    return getattr(obj.__class__, "to_dict", _default.default)(obj)

_default.default = JSONEncoder().default
JSONEncoder.default = _default


Base = declarative_base()



class MyBase(Base):
    __abstract__ = True
   
    @classmethod
    def get_default_fields(cls):
        default = ['id']
        default_fields = cls._default_fields if hasattr(cls, "_default_fields") else [] 
        default.extend(default_fields)
        default.extend(['updated_on', 'created_on'])
        return default
    
    @classmethod
    def get_form_fields(cls):
        default = cls._default_fields if hasattr(cls, "_default_fields") else []
        hidden = cls.get_hidden_fields()
        form = [ item for item in default if item not in hidden ]
        return form
    
    @classmethod
    def get_readonly_fields(cls):
        readonly = cls._readonly_fields if hasattr(cls, "_readonly_fields") else []
        readonly.extend(['id', 'updated_on', 'created_on'])
        return readonly
    
    @classmethod
    def get_hidden_fields(cls):
        hidden = cls._hidden_fields if hasattr(cls, "_hidden_fields") else []
        return hidden
    
    @classmethod
    def get_editable_fields(cls):
        default = cls.get_default_fields()
        hidden = cls.get_hidden_fields()
        readonly = cls.get_readonly_fields()
        editable = [ item for item in default if item not in readonly and item not in hidden]
        return editable

    def to_dict(self, show=None, _hide=[], _path=None):
        """Return a dictionary representation of this model."""

        show = show or []
        
        default = self.get_default_fields()
        hidden = self.get_hidden_fields()
        readonly = self.get_readonly_fields()

        if not _path:
            _path = self.__tablename__.lower()

            def prepend_path(item):
                item = item.lower()
                if item.split(".", 1)[0] == _path:
                    return item
                if len(item) == 0:
                    return item
                if item[0] != ".":
                    item = ".%s" % item
                item = "%s%s" % (_path, item)
                return item

            _hide[:] = [prepend_path(x) for x in _hide]
            show[:] = [prepend_path(x) for x in show]

        columns = self.__table__.columns.keys()
        relationships = self.__mapper__.relationships.keys()
        properties = dir(self)

        ret_data = {}

        for key in columns:
            if key.startswith("_"):
                continue
            check = "%s.%s" % (_path, key)
            if check in _hide or key in hidden:
                continue
            if check in show or key in default:
                ret_data[key] = getattr(self, key)

        for key in relationships:
            if key.startswith("_"):
                continue
            check = "%s.%s" % (_path, key)
            if check in _hide or key in hidden:
                continue
            if check in show or key in default:
                _hide.append(check)
                is_list = self.__mapper__.relationships[key].uselist
                if is_list:
                    items = getattr(self, key)
                    if self.__mapper__.relationships[key].query_class is not None:
                        if hasattr(items, "all"):
                            items = items.all()
                    ret_data[key] = []
                    for item in items:
                        ret_data[key].append(
                            item.to_dict(
                                show=list(show),
                                _hide=list(_hide),
                                _path=("%s.%s" % (_path, key.lower())),
                            )
                        )
                else:
                    if (
                        self.__mapper__.relationships[key].query_class is not None
                        or self.__mapper__.relationships[key].instrument_class
                        is not None
                    ):
                        item = getattr(self, key)
                        if item is not None:
                            ret_data[key] = item.to_dict(
                                show=list(show),
                                _hide=list(_hide),
                                _path=("%s.%s" % (_path, key.lower())),
                            )
                        else:
                            ret_data[key] = None
                    else:
                        ret_data[key] = getattr(self, key)

        for key in list(set(properties) - set(columns) - set(relationships)):
            if key.startswith("_"):
                continue
            if not hasattr(self.__class__, key):
                continue
            attr = getattr(self.__class__, key)
            if not (isinstance(attr, property) or isinstance(attr, QueryableAttribute)):
                continue
            check = "%s.%s" % (_path, key)
            if check in _hide or key in hidden:
                continue
            if check in show or key in default:
                val = getattr(self, key)
                if hasattr(val, "to_dict"):
                    ret_data[key] = val.to_dict(
                        show=list(show),
                        _hide=list(_hide), 
                        _path=("%s.%s" % (_path, key.lower()))
                    )
                else:
                    try:
                        ret_data[key] = json.loads(json.dumps(val))
                    except:
                        pass
        return ret_data



class Topic(MyBase):
  __tablename__ = 'topics'
  id = Column(Integer, primary_key=True)
  name = Column(String, unique=True, nullable=False)
  desc = Column(String, nullable=False)
  user = Column(String, nullable=False)
  start_time = Column(DateTime, nullable=False)
  end_time = Column(DateTime, nullable=False)
  created_on = Column(DateTime, server_default=func.now())
  updated_on = Column(DateTime, server_default=func.now(), server_onupdate=func.now())
  _default_fields = [ 
        'name',
        'desc',
        'user',
        'start_time',
        'end_time',
   ]
  _readonly_fields = [
        'user',
   ]
  _hidden_fields = [
        'user',
   ]

 
class TopicOption(MyBase):
  __tablename__ = 'topic_options'
  id = Column(Integer, primary_key=True)
  topic_id = Column(Integer, ForeignKey('topics.id', ondelete='CASCADE'))
  topic = relationship("Topic", backref="topic_options")
  desc = Column(String, nullable=False)
  created_on = Column(DateTime, server_default=func.now())
  updated_on = Column(DateTime, server_default=func.now(), server_onupdate=func.now())
  _default_fields = [ 
        'topic_id',
        'desc',
   ]
  _readonly_fields = [
       'topic_id'
   ]
  _hidden_fields = [
       'topic_id'
   ]



class RoleGrant(MyBase):
  __tablename__ = 'role_grants'
  id = Column(Integer, primary_key=True)
  topic_id = Column(Integer, ForeignKey('topics.id', ondelete='CASCADE'))
  topic = relationship("Topic", backref="role_grants")
  role = Column(String, nullable=False)
  created_on = Column(DateTime, server_default=func.now())
  updated_on = Column(DateTime, server_default=func.now(), server_onupdate=func.now())
  __table_args__ = (UniqueConstraint('topic_id', 'role', name='topicrolegrant'),)
  _default_fields = [ 
        'topic_id',
        'role',
   ]
  _readonly_fields = [
        'topic_id',
   ]
  _hidden_fields = [
   ]


class Invite(MyBase):
  __tablename__ = 'vote_invites'
  id = Column(Integer, primary_key=True)
  topic_id = Column(Integer, ForeignKey('topics.id', ondelete='CASCADE'))
  topic = relationship("Topic", backref="vote_invites")
  role = Column(String, nullable=False)
  __table_args__ = (UniqueConstraint('topic_id', 'role', name='topicinvites'),)
  created_on = Column(DateTime, server_default=func.now())
  updated_on = Column(DateTime, server_default=func.now(), server_onupdate=func.now())
  _default_fields = [ 
        'topic_id',
        'role',
   ]
  _readonly_fields = [
        'topic_id',
   ]
  _hidden_fields = [
        'topic_id'
   ]


class Vote(MyBase):
  __tablename__ = "votes"
  id = Column(Integer, primary_key=True)
  topic_id = Column(Integer, ForeignKey('topics.id', ondelete='CASCADE'))
  topic = relationship("Topic", backref="votes")
  option_id = Column(Integer, ForeignKey('topic_options.id', ondelete='CASCADE'))
  option = relationship("TopicOption", backref="votes")
  token = Column(String, unique=True, nullable=False)
  created_on = Column(DateTime, server_default=func.now())
  updated_on = Column(DateTime, server_default=func.now(), server_onupdate=func.now())
  _default_fields = [ 
        'topic_id',
        'option_id',
        'token'
   ]
  _readonly_fields = [
        'topic_id',
        'option_id'
   ]
  _hidden_fields = [
   ]



class Mapper(MyBase):
  __tablename__ = "mapper"
  id = Column(Integer, primary_key=True)
  topic_id = Column(Integer, ForeignKey('topics.id', ondelete='CASCADE'))
  topic = relationship("Topic", backref="mapper")
  user = Column(String, nullable=False)
  created_on = Column(DateTime, server_default=func.now())
  updated_on = Column(DateTime, server_default=func.now(), server_onupdate=func.now())
  _default_fields = [ 
        'topic_id',
        'user',
   ]
  _readonly_fields = [
       'topic_id',
       'user'
   ]
  _hidden_fields = [
   ]


