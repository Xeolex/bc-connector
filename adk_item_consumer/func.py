import json
from django.core.serializers.json import DjangoJSONEncoder
from django.core.files.uploadedfile import InMemoryUploadedFile

class MyJsonEncoder(DjangoJSONEncoder):
    def default(self, o):
        if isinstance(o, InMemoryUploadedFile):
           return o.read()
        return str(o)


