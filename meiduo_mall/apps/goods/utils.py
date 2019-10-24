
def get_breadcrumb(category):
    # 分类为三级
    # 返回字典记录三个分类
    breadcrumb={
        'cat1':'',
        'cat2' : '',
        'cat3' : ''
    }
    # 根据当前传递过来的分类进行判断
    if category.parent is None:
        #一级标题
        breadcrumb['cat1']=category
    elif category.subs.count()==0:
        # 说明下边没有分类,是三级
        breadcrumb['cat3']=category
        breadcrumb['cat2']=category.parent
        breadcrumb['cat1']= category.parent.parent
    else:
        # 二级
        breadcrumb['cat2']=category
        breadcrumb['cat1']=category.parent
    return breadcrumb
