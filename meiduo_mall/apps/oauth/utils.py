from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from meiduo_mall import settings

def serect_openid(openid):

    # return openid
    #1.创建实例对象
    s = Serializer(secret_key=settings.SECRET_KEY,expires_in=3600)
    #2.组织数据
    data={
        'openid':openid
    }
    # 3.加密
    new_data = s.dumps(data)
    # 4.返回加密数据
    return new_data.decode()
#解密
def check_openid(serect_openid):
    # 1.导入
    from itsdangerous import BadSignature, BadTimeSignature, BadData
    # 2.创建实例对象
    s = Serializer(secret_key=settings.SECRET_KEY, expires_in=3600)
    # 3.解密数据
    try:
        data = s.loads(serect_openid)
    # except Exception :
    except BadData:
        return None
    else:
        return data.get('openid')

