from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    username = models.CharField(max_length=20)
    password = models.CharField(max_length=20)
    email = models.EmailField()

    def _str_(self):
        return self.user.username
    

class SearchHistory(models.Model):
    # id = models.AutoField()
    username= models.CharField( default="J",null=False, max_length=100)
    data = models.JSONField(null=True)
    # user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    type = models.CharField(null=True, max_length=10)

    def _str_(self):
        return self.query