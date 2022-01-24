# Generated by Django 4.0.1 on 2022-01-24 15:20

import django.contrib.postgres.indexes
import django.contrib.postgres.search
from django.db import migrations, models
import django.db.models.deletion
import django.db.models.functions.text
import django.utils.timezone
import django_extensions.db.fields
import model_utils.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Context',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('id', models.CharField(max_length=512, primary_key=True, serialize=False, verbose_name='Identifier (Context)')),
                ('type', models.CharField(max_length=30)),
                ('slug', django_extensions.db.fields.AutoSlugField(blank=True, editable=False, max_length=512, populate_from='id')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='IIIFResource',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('madoc_id', models.CharField(max_length=512, primary_key=True, serialize=False, verbose_name='Identifier (Madoc)')),
                ('madoc_thumbnail', models.URLField(blank=True, null=True)),
                ('id', models.URLField(verbose_name='IIIF id')),
                ('slug', django_extensions.db.fields.AutoSlugField(blank=True, editable=False, max_length=512, populate_from='madoc_id')),
                ('type', models.CharField(max_length=30)),
                ('label', models.JSONField(blank=True, null=True)),
                ('thumbnail', models.JSONField(blank=True, null=True)),
                ('summary', models.JSONField(blank=True, null=True)),
                ('metadata', models.JSONField(blank=True, null=True)),
                ('navDate', models.DateTimeField(blank=True, null=True)),
                ('rights', models.URLField(blank=True, null=True)),
                ('requiredStatement', models.JSONField(blank=True, null=True)),
                ('provider', models.JSONField(blank=True, null=True)),
                ('first_canvas_id', models.URLField(blank=True, null=True, verbose_name='First canvas IIIF id')),
                ('first_canvas_json', models.JSONField(blank=True, null=True)),
                ('contexts', models.ManyToManyField(blank=True, related_name='associated_iiif', to='search_service.Context')),
                ('items', models.ManyToManyField(blank=True, related_name='ispartof', to='search_service.IIIFResource')),
            ],
        ),
        migrations.CreateModel(
            name='Indexables',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('resource_id', models.CharField(max_length=512, verbose_name='Identifier (URL/URI/URN) for associated IIIF resource')),
                ('content_id', models.CharField(blank=True, max_length=512, null=True, verbose_name='Identifier (URL/URI/URN) for the content, if it has one')),
                ('indexable', models.TextField()),
                ('indexable_date_range_start', models.DateTimeField(blank=True, null=True)),
                ('indexable_date_range_end', models.DateTimeField(blank=True, null=True)),
                ('indexable_int', models.IntegerField(blank=True, null=True)),
                ('indexable_json', models.JSONField(blank=True, null=True)),
                ('indexable_float', models.FloatField(blank=True, null=True)),
                ('original_content', models.TextField()),
                ('search_vector', django.contrib.postgres.search.SearchVectorField(blank=True, null=True)),
                ('language_iso639_2', models.CharField(blank=True, max_length=3, null=True)),
                ('language_iso639_1', models.CharField(blank=True, max_length=2, null=True)),
                ('language_display', models.CharField(blank=True, max_length=64, null=True)),
                ('language_pg', models.CharField(blank=True, max_length=64, null=True)),
                ('selector', models.JSONField(blank=True, null=True)),
                ('type', models.CharField(max_length=64)),
                ('subtype', models.CharField(max_length=256)),
                ('iiif', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, related_name='indexables', to='search_service.iiifresource')),
            ],
        ),
        migrations.AddIndex(
            model_name='indexables',
            index=django.contrib.postgres.indexes.GinIndex(fields=['search_vector'], name='search_serv_search__d642e8_gin'),
        ),
        migrations.AddIndex(
            model_name='indexables',
            index=models.Index(fields=['content_id'], name='search_serv_content_83f514_idx'),
        ),
        migrations.AddIndex(
            model_name='indexables',
            index=models.Index(fields=['resource_id'], name='search_serv_resourc_794531_idx'),
        ),
        migrations.AddIndex(
            model_name='indexables',
            index=models.Index(fields=['language_iso639_2', 'language_iso639_1', 'language_display'], name='search_serv_languag_985c2a_idx'),
        ),
        migrations.AddIndex(
            model_name='indexables',
            index=models.Index(fields=['type'], name='search_serv_type_abf02f_idx'),
        ),
        migrations.AddIndex(
            model_name='indexables',
            index=models.Index(fields=['subtype'], name='search_serv_subtype_3ca12d_idx'),
        ),
        migrations.AddIndex(
            model_name='indexables',
            index=models.Index(fields=['type', 'subtype'], name='search_serv_type_4d1b70_idx'),
        ),
        migrations.AddIndex(
            model_name='indexables',
            index=models.Index(django.db.models.functions.text.Upper('type'), name='uppercase_type'),
        ),
        migrations.AddIndex(
            model_name='indexables',
            index=models.Index(django.db.models.functions.text.Upper('subtype'), name='uppercase_subtype'),
        ),
        migrations.AddIndex(
            model_name='indexables',
            index=models.Index(django.db.models.functions.text.Upper('type'), django.db.models.functions.text.Upper('subtype'), name='uppercase_type_subtype'),
        ),
        migrations.AddIndex(
            model_name='indexables',
            index=models.Index(django.db.models.functions.text.Upper('type'), django.db.models.functions.text.Upper('subtype'), django.db.models.functions.text.Upper('indexable'), name='uppercase_indexables'),
        ),
        migrations.AddIndex(
            model_name='indexables',
            index=django.contrib.postgres.indexes.HashIndex(fields=['indexable'], name='search_serv_indexab_d3e10c_hash'),
        ),
        migrations.AddIndex(
            model_name='iiifresource',
            index=models.Index(fields=['type'], name='search_serv_type_6c43dd_idx'),
        ),
        migrations.AddIndex(
            model_name='iiifresource',
            index=models.Index(fields=['madoc_id'], name='search_serv_madoc_i_c5a24a_idx'),
        ),
        migrations.AddIndex(
            model_name='iiifresource',
            index=models.Index(fields=['id'], name='search_serv_id_cd669a_idx'),
        ),
        migrations.AddIndex(
            model_name='iiifresource',
            index=models.Index(fields=['label'], name='search_serv_label_551ca1_idx'),
        ),
    ]
