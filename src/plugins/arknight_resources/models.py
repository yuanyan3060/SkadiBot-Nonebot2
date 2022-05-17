from tortoise.models import Model
from tortoise.fields.data import TextField, CharField, DatetimeField


class SourceModel(Model):
    name = TextField(pk=True)
    md5 = CharField(max_length=32)

class VersionModel(Model):
    version = TextField(pk=True)
    update_time = DatetimeField(auto_now=True)