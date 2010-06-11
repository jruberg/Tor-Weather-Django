from django.db import models
from django.core.mail import send_mail
import datetime
import TorCtl.TorCtl
import socket
#import weather.config

class Router(models.Model):
    fingerprint = models.CharField(max_length=200)
    name = models.CharField(max_length=100)
    welcomed = models.BooleanField()
    last_seen = models.DateTimeField('date last seen')
    
    def __unicode__(self):
        return self.fingerprint

class Subscriber(models.Model):
    email = models.EmailField(max_length=75)
    router = models.ForeignKey(Router)
    confirmed = models.BooleanField()

    #change this when more is known?
    confirm_auth = models.CharField(max_length=250) 
    unsubs_auth = models.CharField(max_length=250)
    pref_auth = models.CharField(max_length=250)

    sub_date = models.DateField()

    def __unicode__(self):
        return self.email

class Subscription(models.Model):
    subscriber = models.ForeignKey(Subscriber)
    name = models.CharField(max_length=200)
    threshold = models.CharField(max_length=200)
    grace_pd = models.IntegerField()
    emailed = models.BooleanField()
    triggered = models.BooleanField()
    last_changed = models.DateTimeField('date of last change')

    def __unicode__(self):
        return self.name

#class Emailer(models.Model):
#    """A class for sending email messages"""
#    def sendEmail(sender, recipient, messageText, subject):
#        """
#        Send an email with message messageText and subject subject to
#        recipient from sender
#        
#        @type sender: string
#        @param sender: The sender of this email.
#        @type recipient: string
#        @param recipient: The recipient of this email.
#        @type messageText: string
#        @param messageText: The contents of this email.
#        @type subject: string
#        @param subject: The subject of this email.
#        """
#        to = [recipient] #send_mail takes a list of recipients
#        send_mail(subject, messageText, sender, recipient, fail_silently=True)

class Poller:
    def __init__(self):
        ctrl_host = '127.0.0.1'        
        ctrl_port = 9051
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((ctrl_host, ctrl_port))
        self.ctrl = TorCtl.Connection(sock)
        self.ctrl.authenticate(config.authenticator)
        
