
# from django.contrib.auth import authenticate

from apps.users.models import User

"""
authenticate 默认是调用的 ModelBackend的认证方法
他默认是 用户名登陆

我们的需求是 不仅是用户名 还需要 手机号
所以我们要重写

"""

from django.contrib.auth.backends import ModelBackend
import re
import logging
logger=logging.getLogger('django')

"""
封装/抽取

为什么要封装/抽取
    1.降低代码的耦合度
    2.降低代码量

如何封装/抽取
    1.将要封装/抽取的代码复制到一个函数中
    2.哪里有问题,该哪里,没有的变量以参数的形式传递
        注意是否需要有返回值
    3.验证代码(先注释原有代码,最后没问题,再删除)

什么时候封装/抽取
    1. 只要完成了某一个功能,就可以抽取
    2. 只要第二次使用到的重复代码,就封装/抽取

"""

def get_user_by_usernamemobile(username):
    try:
        if re.match(r'1[3-9]\d{9}', username):
            # 手机号登陆
            user = User.objects.get(mobile=username)
        else:
            # 用户名登陆
            user = User.objects.get(username=username)
    except Exception as e:
        logger.error(e)
        return None
    else:
        return user


class UsernameMobileModelBackend(ModelBackend):

    def authenticate(self, request, username=None, password=None, **kwargs):
        # 1. 区分 手机号 和 用户名
        # try:
        #     if re.match(r'1[3-9]\d{9}',username):
        #         # 手机号登陆
        #         user = User.objects.get(mobile=username)
        #     else:
        #         # 用户名登陆
        #         user=User.objects.get(username=username)
        # except Exception as e:
        #     logger.error(e)
        #     return None
        # else:

        #1.就要一个用户名
        user = get_user_by_usernamemobile(username)
        #2.检查密码
        if user is not None and user.check_password(password):
            return user

