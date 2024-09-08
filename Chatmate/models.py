import random
from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from Auth.models import User
    
def generate_random_id():
    return str(random.randint(100000, 999999))

class Rooms(models.Model):
    id = models.CharField(max_length=255, primary_key=True, default=generate_random_id, editable=False)
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE, to_field='id', related_name='Users')

    def __str__(self):
        return self.name

class Documents(models.Model):
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents/', null=True, blank=True)
    link = models.URLField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    room = models.ForeignKey(Rooms, on_delete=models.CASCADE, to_field='name', related_name='documents')

    def __str__(self):
        return self.title

class Query(models.Model):
    query_text = models.TextField()
    response_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    room = models.ForeignKey(Rooms, on_delete=models.CASCADE, to_field='name', related_name='queries')

    def save(self, *args, **kwargs):
        if not Query.objects.filter(query_text=self.query_text).exists():
            super().save(*args, **kwargs)

    def __str__(self):
        return self.query_text

class CombinedChunk(models.Model):
    chunks = models.JSONField(default=list)  
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    room = models.ForeignKey(Rooms, on_delete=models.CASCADE, to_field='name', related_name='combined_chunks')