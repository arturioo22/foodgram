# import base64
# import uuid
 
# from django.core.files.base import ContentFile
# from drf_extra_fields.fields import Base64ImageField as DrfBase64ImageField


# class Base64ImageField(DrfBase64ImageField):
#     """Поле для обработки base64 изображений."""

#     def to_internal_value(self, data):
#         if isinstance(data, str) and data.startswith('data:image'):
#             format, imgstr = data.split(';base64,')
#             ext = format.split('/')[-1]
#             data = ContentFile(
#                 base64.b64decode(imgstr),
#                 name=f'{uuid.uuid4()}.{ext}'
#             )
#         return super().to_internal_value(data)
