from django.db import models


class Theme(models.Model):
    name = models.CharField(max_length=80)
    short_name = models.CharField(max_length=10, default="")
    number_of_pictures = models.IntegerField(default=0)


class LinkToPicture(models.Model):
    theme = models.ForeignKey(Theme, on_delete=models.SET_NULL, null=True)
    link = models.CharField(max_length=500)


class User(models.Model):
    telegram_id = models.CharField(max_length=20)
    is_logged = models.BooleanField(default=False)


class Schedule(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    day_of_week = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    start_time = models.CharField(max_length=10)
    end_time = models.CharField(max_length=10)
    place = models.CharField(max_length=40)
    professor = models.CharField(max_length=40)


class CSV(models.Model):
    number = models.IntegerField(default=0)


class FavLocation(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    longitude = models.FloatField()
    latitude = models.FloatField()
    name = models.CharField(max_length=100)


