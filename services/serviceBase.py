class ServiceBase(object):
    manager = None

    def all(self, *args, **kwargs):
        return self.manager.all(*args, **kwargs)

    def get(self, *args, **kwargs):
        return self.manager.get(*args,**kwargs)

    def filter(self, *args, **kwargs):
        return self.manager.filter(*args, **kwargs)

    def create(self, *args, **kwargs):
        return self.manager.create(**kwargs)

    def update(self, uuid, *args, **kwargs):
        return self.filter(id=uuid).update(**kwargs)

    def delete(self,uuid):
        return self.filter(id=uuid).delete()

    def exists(self, **kwargs):
        return self.manager.filter(**kwargs).exists()

    def first(self, **kwargs):
        return self.manager.filter(**kwargs).first()