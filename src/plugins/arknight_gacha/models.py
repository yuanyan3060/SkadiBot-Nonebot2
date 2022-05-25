from tortoise.models import Model
from tortoise.fields.data import CharField, DatetimeField, BigIntField, IntField, DatetimeField, BooleanField, JSONField
from tortoise.fields import ReverseRelation, ForeignKeyRelation, ForeignKeyField


class OperatorModel(Model):
    code = CharField(max_length=32)
    nums = IntField()
    gain_time = DatetimeField(auto_now=True)
    user: ForeignKeyRelation["UserBoxModel"] = ForeignKeyField(
        "models.UserBoxModel", related_name="operators", to_field="qq"
    )


class PoolModel(Model):
    name = CharField(max_length=150)
    pickup_6 = JSONField()
    pickup_5 = JSONField()
    pickup_4 = JSONField()


class UserBoxModel(Model):
    qq = BigIntField(pk=True)
    operators: ReverseRelation[OperatorModel]
    ten_gacha_tickets = IntField()
    last_checkin_time = DatetimeField()
    favor = IntField()
    no6_times = IntField()
