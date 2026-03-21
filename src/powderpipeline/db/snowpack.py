from sqlmodel import Field, SQLModel
import uuid


from django.db import models

# Create your models here.


class Station(models.Model):
    name = models.CharField(max_length=100)
    nwcc_id = models.CharField(max_length=50, unique=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    elevation = models.FloatField()


class SnowfallRecord(models.Model):
    station = models.ForeignKey(Station, on_delete=models.CASCADE)
    date = models.DateField()
    snowfall_amount = models.FloatField(null=True, blank=True)  # in inches
    snow_depth = models.FloatField(null=True, blank=True)  # in inches
    temperature = models.FloatField(null=True, blank=True)  # in Fahrenheit
    precipitation = models.FloatField(null=True, blank=True)  # in inches

    class Meta:
        unique_together = (
            "station",
            "date",
        )

    def __str__(self):
        return f"{self.station.name} : {self.date}"
