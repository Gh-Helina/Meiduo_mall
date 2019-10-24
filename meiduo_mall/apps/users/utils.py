#'http://www.meiduo.site:8000/emailsactive/?token=%s'%token
from itsdangerous import BadData
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from meiduo_mall import settings
def generic_active_email_url(id,email):
    #加密
    # 1.创建实例
    s=Serializer(secret_key=settings.SECRET_KEY,expires_in=3600)
    # 2.组织数据
    data={
        'id':id,
        'email':email,
    }
    # 3.加密数据
    new_data=s.dumps(data)
    # 4.返回加密数据
    return 'http://www.meiduo.site:8000/emailsactive/?token=%s'%new_data.decode()
#b'eyJhbGciOiJIUzUxMiIsImlhdCI6MTU3MTYzMTAyMSwiZXhwIjoxNTcxNjM0NjIxfQ.eyJlbWFpbCI6ImhsbjEzNjk0NzFAMTYzLmNvbSIsImlkIjo2fQ.VO8JWHzXtimyaiSybpVVa_VVZvpMpREPIRFrWUBsrjF-9hpy-B8cMlbCJPnTzL_9H89hQu5iVXl-3wdDKlXSWw'

#解密
def check_active_token(token):
    # 1.创建实例
    s = Serializer(secret_key=settings.SECRET_KEY, expires_in=3600)
    # 2.解密数据
    try:
        new_data=s.loads(token)
    except BadData:
        return None
    return new_data

