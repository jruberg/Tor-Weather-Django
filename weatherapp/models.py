"""
The models module handles the bulk of Tor Weather. The module contains three
models that correspond to database tables (L{Subscriber}, L{Subscription}, and 
L{Router}) as well as two form classes (L{SubscribeForm} and
L{PreferencesForm}), which specify the fields to appear on the sign-up
and change preferences pages.
"""

from django.db import models
from django import forms
import emails
from datetime import datetime
import base64
import os
from weather.config.web_directory import Urls

class Router(models.Model):
    """A model that stores information about every router on the Tor network.
    If a router hasn't been seen on the network for at least one year, it is
    removed from the database.
    
    @type fingerprint: str
    @ivar fingerprint: The router's fingerprint.
    @type name: str
    @ivar name: The name associated with the router.
    @type welcomed: bool
    @ivar welcomed: true if the router operater has received a welcome email,
                    false if they haven't. Default value is C{False}.
    @type last_seen: datetime
    @ivar last_seen: The most recent time the router was listed on a consensus 
                     document. Default value is C{datetime.now()}.
    @type up: bool
    @ivar up: C{True} if this router was up last time a new network consensus
              was published, false otherwise. Default value is C{True}.
    @type exit: bool
    @ivar exit: C{True} if this router accepts exits to port 80, C{False} if
        not.
    """

    fingerprint = models.CharField(max_length=40, unique=True)
    name = models.CharField(max_length=100)
    welcomed = models.BooleanField(default=False)
    last_seen = models.DateTimeField('date last seen', default=datetime.now)
    up = models.BooleanField(default=True)
    exit = models.BooleanField()

    def __unicode__(self):
        return self.fingerprint


class SubscriberManager(models.Manager):
    """In Django, each model class has at least one Manager (by default,
    there is one named 'objects' for each model). The Manager acts as the
    interface through which database query operations are provided to the 
    models. The SubscriberManager class is a custom Manager for the Subscriber
    model, which contains the method get_rand_string to generate a random
    string for user authentication keys."""

    @staticmethod
    def get_rand_string():
        """Returns a random, url-safe string of 24 characters (no '+' or '/'
        characters). The generated string does not end in '-'.
        
        @rtype: str
        @return: A randomly generated, 24 character string (url-safe).
        """

        r = base64.urlsafe_b64encode(os.urandom(18))

        # some email clients don't like URLs ending in -
        if r.endswith("-"):
            r = r.replace("-", "x")
        return r

          
class Subscriber(models.Model):
    """
    A model to store information about Tor Weather subscribers, including their
    authorization keys.

    @ivar email: The subscriber's email.
    @ivar router: A foreign key link to the router model corresponding to the
        node this subscriber is watching.
    @type confirmed: bool
    @ivar confirmed: True if the subscriber has confirmed the subscription by
        following the link in their confirmation email and False otherwise. 
        Default value upon creation is C{False}.
    @type confirm_auth: str
    @ivar confirm_auth: This user's confirmation key, which is incorporated into
        the confirmation url.
    @type unsubs_auth: str
    @ivar unsubs_auth: This user's unsubscribe key, which is incorporated into 
        the unsubscribe url.
    @type pref_auth: str
    @ivar pref_auth: The key for this user's Tor Weather preferences page.
    @type sub_date: datetime.datetime
    @ivar sub_date: The date this user subscribed to Tor Weather. Default value
                    upon creation is datetime.now().
    """
    email = models.EmailField(max_length=75)
    router = models.ForeignKey(Router)
    confirmed = models.BooleanField(default = False)
    confirm_auth = models.CharField(max_length=250, 
                    default=SubscriberManager.get_rand_string) 
    unsubs_auth = models.CharField(max_length=250, 
                    default=SubscriberManager.get_rand_string)
    pref_auth = models.CharField(max_length=250, 
                    default=SubscriberManager.get_rand_string)

    sub_date = models.DateTimeField(default=datetime.now())

    objects = SubscriberManager()

    def __unicode__(self):
        return self.email


class SubscriptionManager(models.Manager):
    """The custom Manager for the Subscription class. The Manager contains
    a method to get the number of hours since the time stored in the
    'last_changed' field in a Subscription object.
    """

    @staticmethod
    def get_hours_since_changed(last_changed):
        """Returns the time that has passed since the datetime parameter
        last_changed in hours.

        @type last_changed: datetime.datetime
        @param last_changed: The date and time of the most recent change
            for some flag.
        @rtype: int
        @return: The number of hours since last_changed.
        """
        time_since_changed = datetime.now() - last_changed
        hours_since_changed = time_since_changed.seconds / 3600
        return hours_since_changed
    

class Subscription(models.Model):
    """The model storing information about a specific subscription. Each type
    of email notification that a user selects generates a new subscription. 
    For instance, each subscriber who elects to be notified about low bandwidth
    will have a low_bandwidth subscription.
    
    @ivar subscriber: A link to the subscriber model representing the owner
        of this subscription.
    @type emailed: bool
    @ivar emailed: True if the user has been emailed about the subscription
        (trigger must also be True), False if the user has not been emailed. 
        Default upon creation is C{False}.
    @type triggered: bool
    @ivar triggered: True if the threshold has been passed for this 
        subscription/the conditions to send a notification are met, False
        if not. Default upon creation is C{False}.
    @type last_changed: datetime.datetime
    @ivar last_changed: The most recent datetime when the trigger field 
        was changed. Default upon creation is C{datetime.now()}.
    """
    subscriber = models.ForeignKey(Subscriber)
    emailed = models.BooleanField(default=False)
    triggered = models.BooleanField(default=False)
    last_changed = models.DateTimeField('date of last change', 
                                        default=datetime.now())

    # In Django, Manager objects handle table-wide methods (i.e filtering)
    objects = SubscriptionManager()
    
    #def __unicode__(self):
    #    return self.subscriber.email + " - Generic Sub"


class NodeDownSub(Subscription):
    """

    @type grace_pd: int
    @ivar grace_pd: The amount of time (hours) before a notification is sent
        after a node is seen down.
    """
    grace_pd = models.IntegerField()

    def __unicode__(self):
        return self.subscriber.email + ": Node Down Sub"

    def should_email():
        """Returns a bool representing whether or not the Subscriber should
        be emailed about their node being down.

        @rtype: bool
        @return: True if the Subscriber should be emailed because their node
            is down and the grace period has passed, False otherwise.
        """
        hours_since_changed = \
            SubscriptionManager.get_hours_since_changed(last_changed)
        if triggered and not emailed and \
                     (hours_since_changed > grace_pd):
            return True
        else:
            return False

class VersionSub(Subscription):
    """

    @type threshold: str
    @ivar threshold: The threshold for sending a notification (i.e. send a 
        notification if the version is obsolete vs. out of date)
    """
# -----------------------------------------------------------------------
# FILL IN LATER, FIX DOCUMENTATION
# -----------------------------------------------------------------------
    threshold = models.CharField(max_length=250)

    def __unicode__(self):
        return self.subscriber.email + " - Version Sub"

    def should_email():
        """
        """


class LowBandwidthSub(Subscription):    
    """
    """
    threshold = models.IntegerField(default = 0)
    grace_pd = models.IntegerField(default = 1)

    def __unicode__(self):
        return self.subscriber.email + " - Low Bandwidth Sub"

    #def should_email():
        #"""
        #"""
        #time_since_changed


class TShirtSub(Subscription):
    """"""
    avg_bandwidth = models.IntegerField(default = 0)
    hours_since_triggered = models.IntegerField(default = 0)

    def __unicode__(self):
        return self.subscriber.email + " - T-Shirt Sub"

    def should_email():
        """Returns true if the router being watched has been up for 1464 hours
        (61 days, or approx 2 months). If it's an exit node, the avg bandwidth
        must be above 100 KB/s. If not, it must be > 500 KB/s.
        
        @rtype: bool
        @return: C{True} if the user earned a T-shirt, C{False} if not."""
        if triggered and hours_since_triggered > 1464:
            if subscriber.router.exit:
                if avg_bandwidth > 100000:
                    return True
            else:
                if avg_bandwidth > 500000:
                    return True
        return False

class SubscriberAlreadyExistsError(Exception):
    def __init__(self, url):
        self.url = url
    def __str__(self):
        return repr(self.url)

class SubscribeForm(forms.Form):
    """For full feature list. """

    _MAX_NODE_DOWN_GRACE_PD = 4500
    _MIN_NODE_DOWN_GRACE_PD = 1
    #_MAX_OUT_OF_DATE_GRACE_PD = 200
    #_MIN_OUT_OF_DATE_GRACE_PD = 1
    _MAX_BAND_LOW_THRESHOLD = 5000
    _MIN_BAND_LOW_THRESHOLD = 1
    _MAX_BAND_LOW_GRACE_PD = 4500
    _MIN_BAND_LOW_GRACE_PD = 1

    email_1 = forms.EmailField(label='Enter Email:',
            max_length=75)
    email_2 = forms.EmailField(label='Re-enter Email:',
            max_length=75)
    fingerprint = forms.CharField(label='Node Fingerprint:',
            max_length=50)

    get_node_down = forms.BooleanField(initial=True, required=False,
            label='Receive notifications when node is down')
    node_down_grace_pd = forms.IntegerField(required=False,
            max_value=_MAX_NODE_DOWN_GRACE_PD,
            min_value=_MIN_NODE_DOWN_GRACE_PD,
            label='How many hours of downtime before \
                       we send a notifcation?',
            help_text='Enter a value between 1 and 4500 (roughly six months)')
    
    get_out_of_date = forms.BooleanField(initial=False, required=False,
            label='Receive notifications when node is out of date')
    out_of_date_threshold = forms.ChoiceField(required=False,
            choices=((u'c1', u'out of date lvl 1'),
                     (u'c2', u'out of date lvl 2'),
                     (u'c3', u'out of date lvl 3'),
                     (u'c4', u'out of date lvl 4')),
                label='How current would you like your version of Tor?')
    #out_of_date_grace_pd = forms.IntegerField(required=False,
    #        max_value=_MAX_OUT_OF_DATE_GRACE_PD,
    #        min_value=_MIN_OUT_OF_DATE_GRACE_PD, 
    #        label='How quickly, in days, would you like to be notified?',
    #        help_text='Enter a value between 1 and 200 (roughly six months)')
    
    get_band_low = forms.BooleanField(initial=False, required=False,
            label='Receive notifications when node has low bandwidth')
    band_low_threshold = forms.IntegerField(required=False,
            max_value=_MAX_BAND_LOW_THRESHOLD,
            min_value=_MIN_BAND_LOW_THRESHOLD,
            label='Critical bandwidth measured in kilobits per second:',
            help_text='Default value is 50 kbps.')
    band_low_grace_pd = forms.IntegerField(required=False,
            max_value=_MAX_BAND_LOW_GRACE_PD,
            min_value=_MIN_BAND_LOW_GRACE_PD,
            label='How many hours of low bandwidth before \
                       we send a notification?',
            help_text='Enter a value between 1 and 4500 (roughly six \
                       months); default value is 1 hour.')
    
    get_t_shirt = forms.BooleanField(initial=False, required=False,
            label='Receive notification when node has earned a t-shirt')

    def clean(self):
        required_msg = "This field is required."

        # Only creates validation errors for required fields if their
        # 'parent' checkbox is checked. That is, a validation error for
        # fields pertinent to get_node_down are only thrown if get_node_down
        # is checked. By default, all non-subscriber fields are not required.
        # The reason for all this complication is that it doesn't seem possible
        # to actually dynamically change Django's built-in required field
        # functionality.

        # If the node down subscription box is checked.
        if self.cleaned_data['get_node_down']:
            # If there are no other errors for the node_down_grace_pd field and
            # it is empty (either not in cleaned_data or in it as None).
            if 'node_down_grace_pd' not in self._errors \
            and ('node_down_grace_pd' not in self.cleaned_data
            or self.cleaned_data['node_down_grace_pd'] == None):
                # Create an error saying that the field is required.
                self._errors['node_down_grace_pd'] = self.error_class(
                                                            [required_msg])
        # If the node down subscription box isn't checked, and there are
        # errors for node_down_grace_pd, then ignore them.
        elif 'node_down_grace_pd' in self._errors:
            # Deletes the error since it should be ignored.
            del self._errors['node_down_grace_pd']

        # If the out of date subscription box is checked.
        if self.cleaned_data['get_out_of_date']:
            # If there are no other errors for the out_of_date_threshold field
            # and it is empty (either not in cleaned data or in it as None).
            if 'out_of_date_threshold' not in self._errors \
            and ('out_of_date_threshold' not in self.cleaned_data
            or self.cleaned_data['out_of_date_threshold'] == None):
                # Create an error saying that the field is required.
                self._errors['out_of_date_threshold'] = self.error_class(
                                                            [required_msg])
            # If there are no other errrors for the out_of_date_grace_pd field
            # and it is empty (either not in clenaed data or in it as None).
            #if 'out_of_date_grace_pd' not in self._errors \
            #and ('out_of_date_grace_pd' not in self.cleaned_data
            #or self.cleaned_data['out_of_date_grace_pd'] == None):
            #    # Create an error saying that the field is required.
            #    self._errors['out_of_date_grace_pd'] = self.error_class(
            #                                                [required_msg])
        # If the out of date subscription box isn't checked.
        else:
            # If there are errors for out_of_date_trheshold, then ignore them.
            if 'out_of_date_threshold' in self._errors:     
                del self._errors['out_of_date_threshold']
            # If there are errors for out_of_date_grace_pd, then ignore them.
            #if 'out_of_date_grace_pd' in self._errors:
            #    del self._errors['out_of_date_grace_pd']

        # If the band low subscription is checked.
        if self.cleaned_data['get_band_low']:
            # If there are no errors for the band_low_threshold field and it is
            # empty (either not in cleaned_data or in it as None).
            if 'band_low_threshold' not in self._errors \
            and ('band_low_threshold' not in self.cleaned_data
            or self.cleaned_data['band_low_threshold'] == None):
                # Create an error saying that the field is required.
                self._errors['band_low_threshold'] = self.error_class(
                                                            [required_msg])
            # If there are no errors for the band_low_grace_pd field and it is
            # empty (either not in cleaned_data or in it as None).
            if 'band_low_grace_pd' not in self._errors \
            and ('band_low_grace_pd' not in self.cleaned_data
            or self.cleaned_data['band_low_grace_pd'] == None):
                # Create an error saying that the field is required.
                self._errors['band_low_grace_pd'] = self.error_class(
                                                            [required_msg])
        # If the band low subscription box isn't checked.
        else:
            # If there are errors for band_low_threshold, then ignore them.
            if 'band_low_threshold' in self._errors:
                del self._errors['band_low_threshold']
            # If there are errors for band_low_grace_pd, then ignore them.
            if 'band_low_grace_pd' in self._errors:
                del self._errors['band_low_grace_pd']


        # Makes sure email_1 and email_2 match and creates error messages
        # if they don't as well as deleting the cleaned data so that it isn't
        # erroneously used.
        if 'email_1' in self.cleaned_data and 'email_2' in self.cleaned_data:
            email_1 = self.cleaned_data['email_1']
            email_2 = self.cleaned_data['email_2']

            if not email_1 == email_2:
                msg = 'Email addresses must match.'
                self._errors['email_1'] = self.error_class([msg])
                self._errors['email_2'] = self.error_class([msg])
                
                del self.cleaned_data['email_1']
                del self.cleaned_data['email_2']

        # Ensures that at least one subscription must be checked.
        if not (self.cleaned_data['get_node_down'] or
                self.cleaned_data['get_out_of_date'] or
                self.cleaned_data['get_band_low'] or
                self.cleaned_data['get_t_shirt']):
            raise forms.ValidationError('You must choose at least one \
                                         type of subscription!')

        return self.cleaned_data

    def clean_fingerprint(self):
        """Uses Django's built-in 'clean' form processing functionality to
        test whether the fingerprint entered is a router we have in the
        current database, and presents an appropriate error message if it
        isn't (along with helpful information).
        """
        fingerprint = self.cleaned_data.get('fingerprint')
        fingerprint.replace(' ', '')

        if self.is_valid_router(fingerprint):
            return fingerprint
        else:
            info_extension = Urls.get_fingerprint_info_ext(fingerprint)
            msg = 'We could not locate a Tor node with that fingerprint. \
                   (<a href=%s>More info</a>)' % info_extension
            raise forms.ValidationError(msg)

    def is_valid_router(self, fingerprint):
        """Helper function to check if a router exists in the database.
        """
        router_query_set = Router.objects.filter(fingerprint=fingerprint)

        if router_query_set.count() == 0:
            return False
        else:
            return True

    def save_subscriber(self):
        """Attempts to save the new subscriber, but throws a catchable error
        if a subscriber already exists with the given email and fingerprint.
        PRE-CONDITION: fingerprint is a valid fingerprint for a 
        router in the Router database.
        """

        email = self.cleaned_data['email_1']
        fingerprint = self.cleaned_data['fingerprint']
        router = Router.objects.get(fingerprint=fingerprint)

        # Get all subscribers that have both the email and fingerprint
        # entered in the form. 
        subscriber_query_set = Subscriber.objects.filter(email=email, 
                                        router__fingerprint=fingerprint)
        
        # Redirect the user if such a subscriber exists, else create one.
        if subscriber_query_set.count() > 0:
            subscriber = subscriber_query_set[0]
            url_extension = Urls.get_error_ext('already_subscribed', 
                                               subscriber.pref_auth)
            raise Exception(url_extension)
            #raise UserAlreadyExistsError(url_extension)
        else:
            subscriber = Subscriber(email=email, router=router)
            subscriber.save()
            return subscriber
            
    def save_subscriptions(self, subscriber):
        # Create the various subscriptions if they are specified.
        if self.cleaned_data['get_node_down']:
            node_down_sub = NodeDownSub(subscriber=subscriber,
                    grace_pd=self.cleaned_data['node_down_grace_pd'])
            node_down_sub.save()
        if self.cleaned_data['get_out_of_date']:
            out_of_date_sub = VersionSub(subscriber=subscriber,
                    threshold=self.cleaned_data['out_of_date_threshold'],
                    #grace_pd=self.cleaned_data['out_of_date_grace_pd']
                    )
            out_of_date_sub.save()
        if self.cleaned_data['get_band_low']:
            band_low_sub = LowBandwidthSub(subscriber=subscriber,
                    threshold=self.cleaned_data['band_low_threshold'],
                    grace_pd=self.cleaned_data['band_low_grace_pd'])
            band_low_sub.save()
        if self.cleaned_data['get_t_shirt']:
            t_shirt_sub = TShirtSub(subscriber=subscriber)
            t_shirt_sub.save()

class PreferencesForm(forms.Form):
    """The form for a new subscriber. The form includes an email field, 
    a node fingerprint field, and a field to specify the hours of downtime 
    before receiving a notification.

    @ivar email: A field for the user's email address
    @ivar fingerprint: A field for the fingerprint (node ID) corresponding 
        to the node the user wants to monitor
    @ivar grace_pd: A field for the hours of downtime the user specifies
        before being notified via email"""

    # widget attributes are modified here to customize the form
    email = forms.EmailField(widget=forms.TextInput(attrs={'size':'50', 
        'value' : 'Enter a valid email address', 'onClick' : 'if (this.value'+\
        '=="Enter a valid email address") {this.value=""}'}))
    fingerprint = forms.CharField(widget=forms.TextInput(attrs={'size':'50',
        'value' : 'Enter one Tor node ID', 'onClick' : 'if (this.value' +\
        '=="Enter one Tor node ID") {this.value=""}'}))
    grace_pd = forms.IntegerField(widget=forms.TextInput(attrs={'size':'50',
        'value' : 'Default is 1 hour, enter up to 8760 (1 year)', 'onClick' :
        'if (this.value=="Default is 1 hour, enter up to 8760 (1 year)") '+\
        '{this.value=""}'}))

    def clean_grace_pd(self):
        """Django lets you specify how to 'clean' form data for specific
        fields by adding clean methods to the form classes. The grace 
        period for downtime must be between 1 and 8760, and this method
        ensures that an error message is displayed to the user if they
        try to submit a value outside that range.
        """ 
        grace_pd = self.cleaned_data.get('grace_pd')
        if grace_pd < 1 or grace_pd > 8760:
            raise forms.ValidationError("You must enter a number between " 
                                        + "1 and 8760")
        return grace_pd

    def clean_fingerprint(self):
        """Raises a validation error if the fingerprint the user entered
        wasn't found in the database. The error message contains a link
        to a page listing possible problems.
        """
        fingerprint = self.cleaned_data.get('fingerprint')
        fingerprint.replace(' ','')
        fingerprint_set = Router.objects.filter(fingerprint=fingerprint)
        if len(fingerprint_set) == 0:
            info_ext = Urls.get_fingerprint_info_ext(fingerprint)
            message = "We could not locate a Tor node with that fingerprint. "+\
                      "(<a href=%s>More info</a>)" % info_ext
            raise forms.ValidationError(message)
        return fingerprint
