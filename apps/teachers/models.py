from django.conf import settings
from django.db import models


class Teacher(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="teacher_profile",
        verbose_name="Compte utilisateur",
      )
    school = models.ForeignKey(
        "schools.School",
        on_delete=models.CASCADE,
        related_name="teachers",
        verbose_name="Ecole",
      )
    subjects = models.ManyToManyField(
       "subjects.Subject",
       blank=True,
       related_name="teachers",
       verbose_name="Matières",
      )
    classes = models.ManyToManyField(
       "classes.SchoolClass",
        blank=True,
        related_name="teachers",
        verbose_name="Classes",
      )
    employee_number = models.CharField("Matricule",max_length=30,blank=True)
    hire_date = models.DateField("Date d'embauche",null=True,blank=True)
    is_active = models.BooleanField("Actif",default=True)

    class Meta:
        verbose_name = "Enseignant"
        verbose_name_plural = "Enseignants"
        ordering = ["school","user__last_name"]

    def __str__(self):
        return self.user.get_full_name() or str(self.user)





