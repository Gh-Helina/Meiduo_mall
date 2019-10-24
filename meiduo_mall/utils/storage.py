from django.core.files.storage import Storage


class MyStorage(Storage):
    def _open(self,name,mode='rb'):
        pass
    def _save(self, name, content, max_length=None):
        pass
    def url(self, name):
        return 'http://192.168.221.135:8888/' +name