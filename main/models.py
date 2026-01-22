from django.db import models
from django.contrib.auth.models import User

class Person(models.Model):
    ari8mosEisagoghs = models.IntegerField(unique=True, primary_key=True, blank=True)
    hmeromhnia_eis = models.CharField(max_length=200, null=True, blank=True)
    syggrafeas = models.CharField(max_length=200, null=True, blank=True)
    koha = models.CharField(max_length=200, null=True, blank=True)
    titlos = models.CharField(max_length=200, null=True, blank=True)
    ekdoths = models.CharField(max_length=200, null=True, blank=True)
    ekdosh = models.CharField(max_length=200, null=True, blank=True)
    etosEkdoshs = models.CharField(max_length=20, null=True, blank=True)
    toposEkdoshs = models.CharField(max_length=200, null=True, blank=True)
    sxhma = models.CharField(max_length=200, null=True, blank=True)
    selides = models.CharField(max_length=50, null=True, blank=True)
    tomos = models.CharField(max_length=50, null=True, blank=True)
    troposPromPar = models.CharField(max_length=200, null=True, blank=True)
    ISBN = models.CharField(max_length=50, null=True, blank=True)
    sthlh1 = models.CharField(max_length=200, null=True, blank=True)
    sthlh2 = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return self.ari8mosEisagoghs
    
class UploadLog(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="uploads"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    filename = models.CharField(max_length=255)
    rows_added = models.PositiveIntegerField(default=0)
    rows_updated = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.filename} by {self.user.username} on {self.uploaded_at}"