from django.db import models
import re, bcrypt, time
class UserManager(models.Manager):
    def basic_validator(self, data):
        errors = {}
        EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
        if not EMAIL_REGEX.match(data['email']):
            errors['email'] = "Invalid email address!"
        #check to see if the email address is unique
        users = User.objects.all()
        for user in users:
            if user.email == data['email']:
                errors['email_unique'] = 'This email has already been registered'
        if len(data['password']) < 8:
            errors['pass_len'] = 'Password must be at least 8 characters'
        #password = confirmation password
        if data['password'] != data['password2']:
            errors['pass_con'] = 'The password confirmation does not match the password'
        return errors
    def login_validator(self, request, data):
        errors = {}
        eMatch = User.objects.filter(email = data['email'])
        if not eMatch:
            errors['eMatch'] = "This does not match any email in our database"
            return errors
        else:
            user = User.objects.get(email = eMatch[0].email)
            if user.spotify_id != request.session['curr_user_sid']:
                errors['spotify_id'] = "This email doesn't match your spotify id"
            if bcrypt.checkpw(data['password'].encode(), user.password.encode()):
                return errors
            else:
                errors['pass_match'] = 'Your password does not match your email'
        return errors


class User(models.Model):
    email = models.CharField(max_length= 50)
    aka = models.CharField(max_length= 50)
    spotify_id = models.CharField(max_length= 255)
    password = models.CharField(max_length= 255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = UserManager()

class MixTape(models.Model):
    name = models.CharField(max_length= 255)
    images = models.CharField(max_length = 255)
    desc = models.TextField(default = '')
    created_by = models.ForeignKey(User, related_name = 'mixtape', on_delete= models.CASCADE)
    burned_by = models.ManyToManyField(User, related_name = 'mixtapes_burned')
    shared_with = models.ManyToManyField(User, related_name= 'mixtapes_shared')
    spotify_id = models.CharField(max_length= 255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
# Create your models here.
