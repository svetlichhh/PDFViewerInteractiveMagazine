from django.db import models
from users.models import User
import random

# заглушка
class Issue(models.Model):
    pass
class NonExistentUser(models.Model):
    pass

class User(models.Model):

    annot_color = models.CharField(max_length=7, null=True)

    def save(self, *args, **kwargs):
        if not self.annot_color:
            self.annot_color = random_hex_color()
        super().save(*args, **kwargs)

    def get_anon_user():
        pass

class PDFDocument(models.Model):

    pdf = models.FileField(upload_to='pdfs/', null=True)
    #issue = models.ForeignKey(Issue, null=True, on_delete=models.CASCADE)
    author = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_DEFAULT, default=User.get_anon_user(),)
    uploaded_at = models.DateField(auto_now_add=True, null=True)
    name = models.CharField(max_length=228, null=True)
    is_annotated = models.BooleanField(default=False)

    def __str__(self):
        return self.name
    
class Annotation(models.Model):
    xref = models.IntegerField(null=True)
    author = models.ForeignKey(User, null=True, default=User.get_anon_user(), on_delete=models.SET_DEFAULT)
    pdf = models.ForeignKey(PDFDocument, on_delete=models.CASCADE, null=True)
    color = models.CharField(null=True, max_length=15)

class Comment(models.Model):

    author = models.ForeignKey(User, null=True, default=User.get_anon_user(), on_delete=models.SET_DEFAULT)
    parent_com = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL) # check on on_delete
    parent_annot = models.ForeignKey(Annotation, null=True, on_delete=models.CASCADE)

    comment_text = models.TextField(max_length=14888, blank=True)
    created_at = models.DateField(auto_now_add=True, null=True)
    updated_at = models.DateField(auto_now=True, null=True)
    
    page = models.PositiveIntegerField(null=True)
    position = models.JSONField(null=True)  # {x: 100, y: 200, width: 50, height: 30}
    length = models.PositiveIntegerField(null=True, blank=True)
    
    def __str__(self):
        return f"Comment by {self.author} on {self.pdf.name}"

    # автор, документ, текст, даты, реф на комментируемое место, парент комментария 

def random_hex_color():
    decimal = random.randrange(220**3) # можно степ ебануть \ решил ограничить (220, 220, 220)
    r = (decimal >> 16) & 255
    g = (decimal >> 8) & 255
    b = decimal & 255
    return f"#{r:02X}{g:02X}{b:02X}"