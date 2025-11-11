"""
Script para poblar la base de datos con datos de prueba
Ejecutar: python populate_data.py
"""
import os
import sys
import django
from django.db import transaction

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.categorias.models import Categoria
from apps.productos.models import Producto
from apps.producto_variante.models import VarianteProducto
from decimal import Decimal
import random

def limpiar_datos():
    """Eliminar todos los datos existentes"""
    print("🗑️  Limpiando datos existentes...")
    try:
        VarianteProducto.objects.all().delete()
        Producto.objects.all().delete()
        Categoria.objects.all().delete()
        print("✅ Datos limpiados\n")
    except Exception as e:
        print(f"⚠️  Error limpiando datos: {e}\n")
        raise

def crear_categorias():
    """Crear categorías"""
    print("📁 Creando categorías...")

    categorias = [
        {
            'nombre': 'Pantalones',
            'descripcion': 'Pantalones de diversos estilos para hombre y mujer'
        },
        {
            'nombre': 'Camisas',
            'descripcion': 'Camisas casuales y formales'
        },
        {
            'nombre': 'Vestidos',
            'descripcion': 'Vestidos elegantes y casuales para mujer'
        },
        {
            'nombre': 'Zapatos',
            'descripcion': 'Calzado deportivo y casual'
        },
        {
            'nombre': 'Accesorios',
            'descripcion': 'Bolsos, carteras y complementos'
        }
    ]

    categorias_creadas = []
    for cat_data in categorias:
        try:
            categoria = Categoria.objects.create(**cat_data)
            categorias_creadas.append(categoria)
            print(f"  ✓ {categoria.nombre}")
        except Exception as e:
            print(f"  ✗ Error creando {cat_data['nombre']}: {e}")

    print(f"✅ {len(categorias_creadas)} categorías creadas\n")
    return categorias_creadas

def crear_productos(categorias):
    """Crear productos"""
    print("👕 Creando productos...")

    # Obtener categorías
    cat_pantalones = categorias[0]
    cat_camisas = categorias[1]
    cat_vestidos = categorias[2]
    cat_zapatos = categorias[3]
    cat_accesorios = categorias[4]

    productos_data = [
        # PANTALONES
        {
            'nombre': 'Jean Azul Clásico',
            'descripcion': 'Jean de mezclilla azul, corte recto, ideal para uso diario',
            'genero': 'Unisex',
            'marca': 'Levi\'s',
            'categoria': cat_pantalones,
            'image': 'productos/producto.jpeg'
        },
        {
            'nombre': 'Pantalón Negro Formal',
            'descripcion': 'Pantalón de vestir negro, tela de alta calidad',
            'genero': 'Hombre',
            'marca': 'Zara',
            'categoria': cat_pantalones,
            'image': 'productos/producto.jpeg'
        },
        {
            'nombre': 'Jogger Deportivo',
            'descripcion': 'Pantalón deportivo con puños, cómodo y moderno',
            'genero': 'Unisex',
            'marca': 'Nike',
            'categoria': cat_pantalones,
            'image': 'productos/producto.jpeg'
        },

        # CAMISAS
        {
            'nombre': 'Camisa Blanca Formal',
            'descripcion': 'Camisa de vestir blanca, manga larga',
            'genero': 'Hombre',
            'marca': 'Arrow',
            'categoria': cat_camisas,
            'image': 'productos/producto.jpeg'
        },
        {
            'nombre': 'Blusa Floreada',
            'descripcion': 'Blusa casual con estampado de flores',
            'genero': 'Mujer',
            'marca': 'H&M',
            'categoria': cat_camisas,
            'image': 'productos/producto.jpeg'
        },
        {
            'nombre': 'Polo Deportivo',
            'descripcion': 'Polo de algodón para uso deportivo',
            'genero': 'Unisex',
            'marca': 'Adidas',
            'categoria': cat_camisas,
            'image': 'productos/producto.jpeg'
        },

        # VESTIDOS
        {
            'nombre': 'Vestido Negro Elegante',
            'descripcion': 'Vestido negro de noche, corte elegante',
            'genero': 'Mujer',
            'marca': 'Mango',
            'categoria': cat_vestidos,
            'image': 'productos/producto.jpeg'
        },
        {
            'nombre': 'Vestido Floral Verano',
            'descripcion': 'Vestido ligero con estampado floral',
            'genero': 'Mujer',
            'marca': 'Zara',
            'categoria': cat_vestidos,
            'image': 'productos/producto.jpeg'
        },

        # ZAPATOS
        {
            'nombre': 'Zapatillas Running',
            'descripcion': 'Zapatillas deportivas para correr',
            'genero': 'Unisex',
            'marca': 'Nike',
            'categoria': cat_zapatos,
            'image': 'productos/producto.jpeg'
        },
        {
            'nombre': 'Botas de Cuero',
            'descripcion': 'Botas casual de cuero genuino',
            'genero': 'Hombre',
            'marca': 'Timberland',
            'categoria': cat_zapatos,
            'image': 'productos/producto.jpeg'
        },
        {
            'nombre': 'Tacones Negros',
            'descripcion': 'Tacones de fiesta color negro',
            'genero': 'Mujer',
            'marca': 'Aldo',
            'categoria': cat_zapatos,
            'image': 'productos/producto.jpeg'
        },

        # ACCESORIOS
        {
            'nombre': 'Bolso de Mano',
            'descripcion': 'Bolso pequeño para ocasiones especiales',
            'genero': 'Mujer',
            'marca': 'Michael Kors',
            'categoria': cat_accesorios,
            'image': 'productos/producto.jpeg'
        },
        {
            'nombre': 'Mochila Urbana',
            'descripcion': 'Mochila resistente para uso diario',
            'genero': 'Unisex',
            'marca': 'Eastpak',
            'categoria': cat_accesorios,
            'image': 'productos/producto.jpeg'
        }
    ]

    productos_creados = []
    for prod_data in productos_data:
        try:
            producto = Producto.objects.create(**prod_data)
            productos_creados.append(producto)
            print(f"  ✓ {producto.nombre} ({producto.marca})")
        except Exception as e:
            print(f"  ✗ Error creando {prod_data['nombre']}: {e}")

    print(f"✅ {len(productos_creados)} productos creados\n")
    return productos_creados

def crear_variantes(productos):
    """Crear variantes de productos"""
    print("🔢 Creando variantes...")

    # Tallas comunes
    tallas_ropa = ['XS', 'S', 'M', 'L', 'XL', 'XXL']
    tallas_zapatos = ['36', '37', '38', '39', '40', '41', '42', '43', '44']

    variantes_creadas = []

    for producto in productos:
        # Determinar qué tallas usar
        if producto.categoria.nombre == 'Zapatos':
            tallas = tallas_zapatos
        else:
            tallas = tallas_ropa

        # Determinar rango de precios según categoría
        if producto.categoria.nombre == 'Pantalones':
            precio_base = 150
        elif producto.categoria.nombre == 'Camisas':
            precio_base = 100
        elif producto.categoria.nombre == 'Vestidos':
            precio_base = 200
        elif producto.categoria.nombre == 'Zapatos':
            precio_base = 250
        else:  # Accesorios
            precio_base = 80

        # Crear variantes para algunas tallas (no todas)
        tallas_seleccionadas = tallas[1:5]  # Tomar 4 tallas del medio

        for i, talla in enumerate(tallas_seleccionadas):
            try:
                # Variar precio ligeramente
                precio = Decimal(str(precio_base + (i * 10)))

                # Variar stock aleatoriamente
                stock = random.randint(10, 50)

                variante = VarianteProducto.objects.create(
                    producto=producto,
                    talla=talla,
                    precio=precio,
                    stock=stock,
                    stock_minimo=5
                )
                variantes_creadas.append(variante)
            except Exception as e:
                print(f"  ✗ Error creando variante {talla} de {producto.nombre}: {e}")
                raise

    print(f"✅ {len(variantes_creadas)} variantes creadas\n")
    return variantes_creadas

def main():
    """Función principal con transacción atómica"""
    print("\n" + "="*60)
    print("🚀 INICIANDO POBLACIÓN DE DATOS")
    print("="*60 + "\n")

    try:
        # Usar transacción atómica: todo o nada
        with transaction.atomic():
            print("🔒 Transacción iniciada (Rollback automático si falla)\n")

            # Limpiar datos anteriores
            limpiar_datos()

            # Crear datos
            categorias = crear_categorias()
            if not categorias:
                raise Exception("No se pudieron crear categorías")

            productos = crear_productos(categorias)
            if not productos:
                raise Exception("No se pudieron crear productos")

            variantes = crear_variantes(productos)
            if not variantes:
                raise Exception("No se pudieron crear variantes")

            # Si llegamos aquí, todo salió bien
            print("="*60)
            print("✅ POBLACIÓN COMPLETADA EXITOSAMENTE")
            print("="*60)
            print(f"📁 Categorías: {len(categorias)}")
            print(f"👕 Productos: {len(productos)}")
            print(f"🔢 Variantes: {len(variantes)}")
            print("="*60 + "\n")

    except Exception as e:
        print("\n" + "="*60)
        print("❌ ERROR - ROLLBACK EJECUTADO")
        print("="*60)
        print(f"Error: {e}")
        print("🔄 Todos los cambios fueron revertidos")
        print("="*60 + "\n")
        sys.exit(1)

if __name__ == '__main__':
    main()
