# Generated by Django 5.2 on 2025-04-17 23:35

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('products', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Carrito',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
                ('usuario', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='carrito', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Carrito',
                'verbose_name_plural': 'Carritos',
            },
        ),
        migrations.CreateModel(
            name='ItemCarrito',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cantidad', models.PositiveIntegerField(default=1)),
                ('fecha_agregado', models.DateTimeField(auto_now_add=True)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
                ('carrito', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='cart.carrito')),
                ('producto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.producto')),
            ],
            options={
                'verbose_name': 'Ítem de Carrito',
                'verbose_name_plural': 'Ítems de Carrito',
                'ordering': ['-fecha_agregado'],
                'unique_together': {('carrito', 'producto')},
            },
        ),
    ]
