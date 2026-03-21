from django.db import models
from datetime import date
from model_utils.models import TimeStampedModel

# Create your models here.


class ForecastZone(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    @property
    def slug(self):
        return self.name.lower().replace(" ", "-")


class Forecast(TimeStampedModel):
    zone = models.ForeignKey(ForecastZone, on_delete=models.CASCADE)
    date = models.DateField(default=date.today)
    author = models.CharField(max_length=100)

    upper_elevation_danger = models.IntegerField()
    mid_elevation_danger = models.IntegerField()
    lower_elevation_danger = models.IntegerField()

    evening_temperature = models.IntegerField()
    overnight_temperature = models.IntegerField()

    evening_snowline = models.IntegerField()
    overnight_snowline = models.IntegerField()

    evening_wind_speed = models.IntegerField()
    overnight_wind_speed = models.IntegerField()

    precipitation = models.IntegerField()

    class Meta:
        unique_together = (
            "zone",
            "date",
        )

    def __str__(self):
        return f"{self.zone.name} : {self.date}"
