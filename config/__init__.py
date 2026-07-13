import sys

# Compatibility note: Django's template BaseContext changed in newer versions.
# The previous custom patch caused rendering failures for admin templates.
# No patch is currently required for Django 6.x.

# if sys.version_info >= (3, 14):
#     import django.template.context as django_context
# 
#     if not hasattr(django_context.BaseContext, '_kisiitv_patch_applied'):
#         _orig_basecontext_copy = django_context.BaseContext.__copy__
# 
#         def _patched_basecontext_copy(self):
#             duplicate = copy.copy(super(django_context.BaseContext, self))
#             duplicate.dicts = self.dicts[:]
#             return duplicate
# 
#         django_context.BaseContext.__copy__ = _patched_basecontext_copy
#         django_context.BaseContext._kisiitv_patch_applied = True
