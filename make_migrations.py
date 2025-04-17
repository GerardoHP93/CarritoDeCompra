"""
Script para ejecutar las migraciones iniciales.
Ejecutar con: python make_migrations.py
"""
import os
import sys
import django

# Configurar el entorno Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'market_project.settings')
django.setup()

def main():
    """
    Ejecuta las migraciones iniciales para todas las aplicaciones.
    """
    from django.core.management import call_command
    
    print("Creando migraciones iniciales...")
    
    # Crear migraciones para todas las apps
    call_command('makemigrations', 'users')
    call_command('makemigrations', 'products')
    call_command('makemigrations', 'cart')
    call_command('makemigrations', 'orders')
    call_command('makemigrations')
    
    print("Aplicando migraciones...")
    call_command('migrate')
    
    print("Migraciones completadas exitosamente.")
    
    # Preguntar si se desea crear un superusuario
    create_superuser = input("¿Deseas crear un superusuario? (s/n): ").lower()
    if create_superuser == 's':
        call_command('createsuperuser')

if __name__ == "__main__":
    main()