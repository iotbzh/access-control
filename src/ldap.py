import ldap

from src.models import db, dbs, User

def ldap_retrieve_users(server, default_role):
    l = ldap.initialize(server)
    l.simple_bind_s("","")
    res = l.search_s("ou=people, dc=lorient, dc=iot", ldap.SCOPE_SUBTREE, attrlist=["mail", "cn", "uid"]) # TODO: Add to the config
    users = [{
        "uid": user["uid"][0].decode(),
        "name": user["cn"][0].decode(),
        "email": user["mail"][0].decode()
    } for _, user in res if "mail" in user]

    for user in users:
        if not dbs.execute(db.select(User).where(User.uid == user["uid"])).scalar_one_or_none():
            dbs.add(User(uid=user["uid"], name=user["name"], email=user["email"], role=default_role))
    
    dbs.commit()