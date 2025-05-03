# En apps/orders/migrations/0002_orden_recibido_orden_fecha_recepcion.py

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0001_initial'),  # Asegúrate de que este nombre sea correcto para tu proyecto
    ]

    operations = [
        migrations.AddField(
            model_name='orden',
            name='recibido',
            field=models.BooleanField(default=False, help_text='Indica si el cliente ha confirmado la recepción del pedido'),
        ),
        migrations.AddField(
            model_name='orden',
            name='fecha_recepcion',
            field=models.DateTimeField(blank=True, help_text='Fecha en que el cliente confirmó la recepción', null=True),
        ),
    ]