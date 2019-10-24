# 1.启动celery启动文件
from celery import Celery, app

# 2.为celery使用django配置文件进行设计
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "meiduo_mall.settings")

# 3.创建celery实例
celery_app = Celery('celery_tasks')

# # 加载celety配置中间人
celery_app.config_from_object('celery_tasks.config')


# 自动检测celery任务
celery_app.autodiscover_tasks(['celery_tasks.sms','celery_tasks.email'])

#celery -A celery_tasks.main worker -l info