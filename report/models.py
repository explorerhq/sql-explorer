from django.db import models

class Report(models.Model):
    title = models.CharField(max_length=255)
    sql = models.TextField()
    description = models.TextField(null=True, blank=True)
    created_by = models.CharField(max_length=255, null=True, blank=True,)
    
    def __unicode__(self):
        return unicode(self.title)