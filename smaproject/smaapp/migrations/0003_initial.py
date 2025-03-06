# Generated by Django 5.1.6 on 2025-03-01 12:10

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('smaapp', '0002_delete_failedsubject_delete_student'),
    ]

    operations = [
        migrations.CreateModel(
            name='Student',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('sgpa', models.FloatField()),
                ('result', models.CharField(max_length=10)),
            ],
        ),
        migrations.CreateModel(
            name='FailedSubject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject_name', models.CharField(max_length=255)),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='failed_subjects', to='smaapp.student')),
            ],
        ),
    ]
