from django.contrib.gis.db import models

class IncidentLocation(models.Model):
    location = models.PointField(null=True)
    description = models.CharField(max_length=256, null=True)

class Incident(models.Model):
    incnum = models.BigIntegerField(primary_key=True)
    type = models.CharField(max_length=256, null=True)
    location = models.CharField(max_length=256, null=True)
    num = models.CharField(max_length=256, null=True)
    street = models.CharField(max_length=256, null=True)
    status = models.CharField(max_length=256, null=True)
    cname = models.CharField(max_length=256, null=True)
    cadrs = models.CharField(max_length=256, null=True)
    capt = models.CharField(max_length=256, null=True)
    cphone = models.CharField(max_length=256, null=True)
    pu = models.CharField(max_length=256, null=True)
    timestamp = models.DateTimeField(null=True)
    beat = models.CharField(max_length=256, null=True)
    casen = models.BigIntegerField(null=True)
    rcvtime = models.TimeField(null=True)
    disptime = models.TimeField(null=True)
    enrttime = models.TimeField(null=True)
    ostime = models.TimeField(null=True)
    cleartime = models.TimeField(null=True)
    cmt1 = models.TextField(null=True)
    incident_location = models.ForeignKey(IncidentLocation, null=True, default=None)

class Incunit(models.Model):
    incident = models.ForeignKey(Incident)
    unitid = models.CharField(max_length=256, null=True)
    ofcrnum = models.CharField(max_length=256, null=True)
    dispdatetime = models.DateTimeField(null=True)
    enrtdatetime = models.DateTimeField(null=True)
    osdatetime = models.DateTimeField(null=True)
    cleardatetime = models.DateTimeField(null=True)
    primaryunit = models.BooleanField(default=None)

class GPSLog(models.Model):
    unitid = models.CharField(max_length=256, null=True)
    location = models.PointField(null=True)
    timestamp = models.DateTimeField(null=True)
    heading = models.IntegerField(null=True)
    speed = models.IntegerField(null=True)
    status = models.CharField(max_length=256, null=True)
    objects = models.GeoManager()

class CaseAudit(models.Model):
    caseid = models.BigIntegerField(null=True)
    timestamp = models.DateTimeField(null=True)
    description = models.CharField(max_length=256, null=True)
    userid = models.CharField(max_length=256, null=True)
    logcode = models.CharField(max_length=256, null=True)
    termid = models.IntegerField(null=True)

class Terminal(models.Model):
    termid = models.IntegerField(primary_key=True)
    description = models.CharField(max_length=256, null=True)
    userid = models.CharField(max_length=256, null=True)
