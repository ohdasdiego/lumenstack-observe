from peewee import *
from config import DB_PATH

db = SqliteDatabase(DB_PATH)

class BaseModel(Model):
    class Meta:
        database = db

class LLMCall(BaseModel):
    id = AutoField()
    timestamp = DateTimeField()
    model = CharField()
    prompt = TextField()
    response = TextField()
    input_tokens = IntegerField()
    output_tokens = IntegerField()
    latency_ms = FloatField()
    cost_usd = FloatField()
    status = CharField(default="success")  # success | error
    source = CharField(default="manual")   # which tool/service made the call
    error_message = TextField(null=True)

    class Meta:
        table_name = "llm_calls"

def init_db():
    db.connect(reuse_if_open=True)
    db.create_tables([LLMCall], safe=True)
