from django.http import JsonResponse
from django.shortcuts import render

# Create your views here.
from django.views import View

from apps.areas.models import Area

##########获取市区县###############

from utils.response_code import RETCODE
from django.core.cache import cache


class AreaView(View):
    def get(self, request):
        # 1.获取area_d
        parent_id = request.GET.get('area_id')
        # 判断
        if parent_id is None:
            # 省
            # 先读取缓存
            # cache_pro是下面设置的cache_pro
            cache_pro = cache.get('cache_pro')

            if cache_pro is None:
                # 说明无缓存
                proviences = Area.objects.filter(parent=None)
                # 将对象列表转换为字典列表
                # JsonResponse默认是可以对字典进行json转换的
                # pro_list=[]
                cache_pro = []
                # for pro in pro_list:
                for pro in proviences:
                    # pro_list.append({
                    cache_pro.append({
                        'id': pro.id,
                        'name': pro.name,
                    })
                # 设置缓存,可以用redis，也可以用系统集成的cache
                cache.set('cache_pro', cache_pro, 24 * 3600)

            # return JsonResponse({'code': RETCODE.OK, 'province_list': pro_list})
            return JsonResponse({'code': RETCODE.OK, 'province_list': cache_pro})
            # return JsonResponse(pro_list,safe=False)

        else:
            # 市/区县
            # 1.根据省的id查询市
            #先读取
            city_list=cache.get('city_%s'%parent_id)
            if city_list is None:
                pro = Area.objects.get(id=parent_id)
                citys = pro.subs.all()
                # 查询结果集
                # 2.遍历
                city_list = []
                for city in citys:
                    city_list.append({
                        'id': city.id,
                        'name': city.name,
                    })
                    cache.set('city_%s'%parent_id,city_list,24*3600)

                # 3.返回响应
            return JsonResponse({'code': RETCODE.OK, 'subs': city_list})

            # return JsonResponse(city_list,safe=False)

            # 响应代码
