from django.db import models



class School(models.Model):
    name = models.CharField("Nom",max_length=200)
    code = models.CharField("Code",max_length=20,unique=True)
    address = models.CharField("Adresse",max_length=255,blank=True)
    phone = models.CharField("Téléphone",max_length=30,blank=True)
    email = models.EmailField("Email",blank=True)
    created_at = models.DateTimeField(auto_now_add=True)



    class Meta:
        verbose_name = "Ecole"
        verbose_name_plural = "Ecoles"
        ordering = ["name"]



    def __str__(self):
          return self.name