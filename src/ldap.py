import ldap

from src.settings import Settings
from src.models import db, dbs, User

def ldap_retrieve_users():
    server = Settings.get("ldap_server")
    base = Settings.get("ldap_base")
    l = ldap.initialize(server)
    l.simple_bind_s("","")
    res = l.search_s(base, ldap.SCOPE_SUBTREE, attrlist=["mail", "cn", "uid"])
    users = [{
        "uid": user["uid"][0].decode(),
        "name": user["cn"][0].decode(),
        "email": user["mail"][0].decode()
    } for _, user in res if "mail" in user]
    
    dbs.execute(db.update(User).where(User.from_ldap == True).values(is_active=False))
    dbs.commit()

    for user in users:
        if not dbs.execute(db.select(User).where(User.uid == user["uid"])).scalar_one_or_none():
            dbs.add(User(uid=user["uid"], name=user["name"], email=user["email"], from_ldap=True))
        else:
            dbs.execute(db.update(User).where(User.uid == user["uid"]).values(is_active=True))

    dbs.commit()

def ldap_is_admin(email):
    server = Settings.get("ldap_server")
    base = Settings.get("ldap_base")
    admin_filter = Settings.get("ldap_admin_filter")
    l = ldap.initialize(server)
    l.simple_bind_s("","")
    res = l.search_s(base, ldap.SCOPE_SUBTREE, admin_filter % email, attrlist=["uid"])
    return len(res) > 0