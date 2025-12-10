#!/usr/bin/env python3
"""
Script para verificar usuarios en PostgreSQL
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.postgres_manager import PostgresManager

def main():
    print("="*60)
    print(" VERIFICACIÓN DE USUARIOS ".center(60))
    print("="*60)
    
    db = PostgresManager()
    
    # Lista de usuarios esperados
    usuarios = ['alcalde', 'director', 'admin', 'usuario']
    
    print("\nUsuarios en la base de datos:")
    print("-"*60)
    
    for username in usuarios:
        user = db.get_user_by_username(username)
        
        if user:
            print(f"\n✓ Usuario: {username}")
            print(f"  Nombre completo: {user['full_name']}")
            print(f"  Email: {user['email']}")
            print(f"  Rol: {user['role']}")
            print(f"  Activo: {user['is_active']}")
            print(f"  Último login: {user['last_login']}")
            
            # Verificar contraseña
            password = f"{username}123"
            if db.verify_password(password, user['password_hash']):
                print(f"  ✓ Contraseña correcta: {password}")
            else:
                print(f"  ✗ Contraseña incorrecta")
        else:
            print(f"\n✗ Usuario NO encontrado: {username}")
    
    print("\n" + "="*60)
    print("\nCredenciales correctas:")
    print("-"*60)
    for username in usuarios:
        print(f"  {username} / {username}123")
    
    db.close()

if __name__ == '__main__':
    main()