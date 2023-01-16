# Generated by Django 4.1.4 on 2023-01-16 09:12

from django.db import migrations, models
import django.utils.timezone
import model_utils.fields
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('search_service', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Context',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('id', model_utils.fields.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('urn', models.CharField(max_length=512, unique=True)),
                ('type', models.CharField(default='', max_length=64)),
            ],
            options={
                'ordering': ['-modified'],
            },
        ),
        migrations.AddField(
            model_name='indexable',
            name='contexts',
            field=models.ManyToManyField(to='search_service.context'),
        ),
        migrations.AddField(
            model_name='jsonresource',
            name='contexts',
            field=models.ManyToManyField(to='search_service.context'),
        ),
    ]
