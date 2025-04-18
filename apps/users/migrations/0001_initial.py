# Generated by Django 5.2 on 2025-04-17 23:35

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Cliente',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('telefono', models.CharField(blank=True, max_length=15, null=True)),
                ('fecha_nacimiento', models.DateField(blank=True, null=True)),
                ('imagen_perfil', models.ImageField(blank=True, null=True, upload_to='usuarios/perfiles/')),
                ('es_administrador', models.BooleanField(default=False)),
                ('fecha_registro', models.DateTimeField(auto_now_add=True)),
                ('ultima_actualizacion', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='cliente', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Cliente',
                'verbose_name_plural': 'Clientes',
                'ordering': ['-fecha_registro'],
            },
        ),
        migrations.CreateModel(
            name='DireccionEnvio',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre_completo', models.CharField(max_length=100)),
                ('calle', models.CharField(max_length=100)),
                ('numero_exterior', models.CharField(max_length=10)),
                ('numero_interior', models.CharField(blank=True, max_length=10, null=True)),
                ('colonia', models.CharField(max_length=100)),
                ('ciudad', models.CharField(max_length=100)),
                ('estado', models.CharField(max_length=100)),
                ('codigo_postal', models.CharField(max_length=10)),
                ('pais', models.CharField(default='México', max_length=100)),
                ('telefono_contacto', models.CharField(max_length=15)),
                ('es_principal', models.BooleanField(default=False)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
                ('cliente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='direcciones', to='users.cliente')),
            ],
            options={
                'verbose_name': 'Dirección de Envío',
                'verbose_name_plural': 'Direcciones de Envío',
                'ordering': ['-es_principal', '-fecha_actualizacion'],
            },
        ),
    ]
