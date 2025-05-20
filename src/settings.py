from src.models import db, dbs, Setting

class Settings:

    @classmethod
    def init(cls):
        settings = dbs.execute(db.select(Setting).limit(1)).one_or_none()

        if not settings:
            dbs.add(Setting())
            dbs.commit()
    
    @classmethod
    def get(cls, key):
        return getattr(dbs.execute(db.select(Setting).limit(1)).scalar_one(), key)