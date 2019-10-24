from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import JsonResponse
from django.shortcuts import render

# Create your views here.
# 1.获取前端提交的uuid
# 2.生成图片验证码(内容,二进制)
# 3.将uuid和内容保存在数据库
# 4.返回响应
from django.views import View

###############图片验证#########################
from apps.verifications.constants import SMS_CODE_EXPIRES_SECONDS, SMS_FLAG_CODE_EXPIRES_SECONDS
from libs.yuntongxun.sms import CCP
from utils.response_code import RETCODE


class ImageView(View):
    # uuid是  ?P<>里的
    def get(self, request, uuid):
        # 1.获取前端提交的uuid
        from libs.captcha.captcha import captcha
        # 2.生成图片验证码(内容,二进制)
        text, image = captcha.generate_captcha()
        # 连接redis
        from django_redis import get_redis_connection
        # 'code'setting里配置redis数据库里面的,数据库使用的是2
        redis_con = get_redis_connection('code')
        # image_s%加了前缀
        # redis_con.setex(key, seconds, value)
        # 3.将uuid和内容保存在数据库
        # 设置过期时间
        # SMS_CODE_EXPIRES_SECONDS定义的变量在constants.py里，代表过期时间
        redis_con.setex('image_%s' % uuid, SMS_CODE_EXPIRES_SECONDS, text)
        # 4.返回图片
        # content-type=image/jpeg是告诉浏览器是图片类型
        return HttpResponse(image, content_type='image/jpeg')


################短信发送功能##########################
# image_codes/mobile/?image_code=xxx&image_code_id=xxx
class SmsCodeView(View):
    def get(self, request, mobile):
        # 1.获取数据
        # 1.1 uuid
        # 1.2 用户自己输入的
        image_code = request.GET.get('image_code')
        image_code_id = request.GET.get('image_code_id')
        # 2.验证数据
        if not all([image_code, image_code_id]):
            return HttpResponseBadRequest('参数不全')
        # 3.比对数据和redis里的
        #     3.1 连接数据库
        from django_redis import get_redis_connection
        # 'code'setting里配置redis数据库里面的,数据库使用的是2
        redis_con = get_redis_connection('code')
        #     3.2 获取数据库的image_code_id
        redis_text = redis_con.get('image_%s' % image_code_id)
        # 判断时效
        if redis_text is None:
            return HttpResponseBadRequest('图片验证码已过期')
        # 比对数据
        # 用户用小写
        if redis_text.decode().lower() != image_code.lower():
            return HttpResponseBadRequest('图片验证码不一致')


        send_flag=redis_con.get('send_flag_%s'%mobile)
        if send_flag:
            return JsonResponse({'errmsg':'发送太频繁，稍后重试','code':'4002'})

        # 4.生成随机短信验证码  本次6位就行
        from random import randint
        sms_code = '%06d' % randint(0, 999999)
        # redis_con.setex(key,seconds,value)
        # 保存到redis
        # SMS_CODE_EXPIRES_SECONDS定义的变量在constants.py里，代表过期时间
        redis_con.setex('sms_%s' % mobile, SMS_CODE_EXPIRES_SECONDS, sms_code)

        # 添加一个标记
        redis_con.setex('send_flag_%s' % mobile, SMS_FLAG_CODE_EXPIRES_SECONDS, 1)


        # 5.发送验证码
        # CCP().send_template_sms(mobile, [sms_code, 5], 1)

        #将celery添加到中间中
        from  celery_tasks.sms.tasks import send_sms_code
        #任务.delay()#将celery添加到中间中
        send_sms_code.delay(mobile,sms_code)
        # 返回json，里面是字典形式
        # RETCODE在utils中response_code中错误代码定义的类
        return JsonResponse({'image': 'ok', 'code': RETCODE.OK})
