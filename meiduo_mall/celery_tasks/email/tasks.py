from celery_tasks.main import celery_app
from django.core.mail import send_mail

from apps.users.utils import generic_active_email_url

@celery_app.task
def send_active_email(user_id,email):
    subject = '美多商城激活邮件'
    # message,       内容
    message = ''
    # from_email,  谁发的
    from_email = '美多商城<hln1369471@163.com>'
    # recipient_list,  收件人列表
    recipient_list = [email]
    # 用户点击链接，，跳转到激成功页面，同时修改用户邮件状态

    # 对用户加密
    active_url = generic_active_email_url(user_id,email)
    # html_mesage = "<a href='http://www.meiduo.site:8000/emailactive/'>戳我有惊喜</a>"
    # html_mesage = "<a href='%s'>戳我有惊喜</a>" % active_url
    html_message = '<p>尊敬的用户您好！</p>' \
                   '<p>感谢您使用美多商城。</p>' \
                   '<p>您的邮箱为：%s 。请点击此链接激活您的邮箱：</p>' \
                   '<p><a href="%s">%s<a></p>' % (email, active_url, active_url)
    send_mail(subject=subject, message=message, from_email=from_email, recipient_list=recipient_list,
              html_message=html_message)

