from django.db import models
import datetime.date
from django.core.mail import send_mail

class Subscription(models.Model):
    subscriber_id = models.ForeignKey(Subscriber)
    name = models.CharField(max_length=200)
    threshold = models.CharField(max_length=200)
    grace_pd = models.IntegerField()
    emailed = models.BooleanField()
    triggered = models.BooleanField()
    last_changed = models.DateTimeField('date of last change')

    def __unicode__(self):
        return self.name

class Router(models.Model):
    fingerprint = models.CharField(max_length=200)
    welcomed = models.BooleanField()
    last_seen = models.DateTimeField('date last seen')

class Subscriber(models.Model)
    email = models.EmailField(max_length=75)
    router_id = models.ForeignKey(Router)

    #change this when more is known
    subs_auth = models.CharField(max_length=250) 
    unsubs_auth = models.CharField(max_length=250)
    pref_auth = models.CharField(max_length=250)

    sub_date = models.DateField()

class Emailer(models.Model):
    """A class for sending email messages"""
    def sendEmail(sender, recipient, messageText, subject):
        """
        Send an email with message messageText and subject subject to
        recipient from sender
        
        @type sender: string
        @param sender: The sender of this email.
        @type recipient: string
        @param recipient: The recipient of this email.
        @type messageText: string
        @param messageText: The contents of this email.
        @type subject: string
        @param subject: The subject of this email.
        """
        to = [recipient] #send_mail takes a list of recipients
        send_mail(subject, messageText, sender, recipient, fail_silently=True)

