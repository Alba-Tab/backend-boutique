# 📊 Guía de Integración - Sistema de Reportes para React/Next.js

## 📁 Archivo de Tipos y API

El archivo **`REACT_TYPES_AND_API.ts`** contiene:
- ✅ **Todos los tipos TypeScript** para cada reporte
- ✅ **Funciones wrapper** para todas las llamadas a la API
- ✅ **Ejemplos de uso** con componentes React
- ✅ **Utilidades** para manejo de fechas

---

## 🚀 Instalación en tu proyecto Next.js

### 1. Copia el archivo

```bash
# Copia el archivo a tu proyecto Next.js
cp REACT_TYPES_AND_API.ts ./src/lib/api/reports.ts
```

### 2. Instala dependencias de TypeScript (si es necesario)

```bash
npm install --save-dev @types/node
```

### 3. Configura la URL base en `.env.local`

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## 📡 Endpoints Disponibles

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/reports/query/` | Reporte con lenguaje natural |
| POST | `/reports/generate/` | Reporte por tipo directo |
| GET | `/reports/dashboard/` | Dashboard administrativo |
| GET | `/reports/cierre-dia/` | Cierre de caja diario |
| GET | `/reports/alertas-inventario/` | Alertas de stock |

---

## 🔥 Ejemplos de Uso

### 1️⃣ Lenguaje Natural (Query con texto)

```tsx
'use client';

import { useState } from 'react';
import { generateNaturalLanguageReport, NaturalLanguageQueryResponse } from '@/lib/api/reports';

export default function ReportesNaturalesPage() {
  const [query, setQuery] = useState('');
  const [result, setResult] = useState<NaturalLanguageQueryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  
  const handleSearch = async () => {
    setLoading(true);
    try {
      const response = await generateNaturalLanguageReport({ query });
      setResult(response);
    } catch (error) {
      console.error('Error:', error);
      alert('Error al generar reporte');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Búsqueda con Lenguaje Natural</h1>
      
      <div className="flex gap-2 mb-4">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="ej: ventas del mes pasado mayores a 1000"
          className="flex-1 px-4 py-2 border rounded"
        />
        <button
          onClick={handleSearch}
          disabled={loading}
          className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          {loading ? 'Buscando...' : 'Buscar'}
        </button>
      </div>
      
      {result && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-2">{result.report.summary}</h2>
          <p className="text-sm text-gray-600 mb-4">
            Intent detectado: <strong>{result.parsed_query.intent}</strong>
          </p>
          
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  {result.report.columns.map(col => (
                    <th key={col} className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {result.report.rows.map((row, i) => (
                  <tr key={i}>
                    {result.report.columns.map(col => (
                      <td key={col} className="px-4 py-2 text-sm text-gray-900">
                        {row[col]}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          {result.report.meta && (
            <div className="mt-4 p-4 bg-gray-50 rounded">
              <pre className="text-xs">
                {JSON.stringify(result.report.meta, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
```

**Ejemplos de queries:**
- `"ventas del mes pasado mayores a 1000"`
- `"los 10 productos más vendidos de este mes"`
- `"productos con stock bajo"`
- `"morosidad de clientes"`

---

### 2️⃣ Dashboard Administrativo

```tsx
'use client';

import { useEffect, useState } from 'react';
import { getDashboard, DashboardData } from '@/lib/api/reports';

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    getDashboard()
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);
  
  if (loading) return <div>Cargando dashboard...</div>;
  if (!data) return <div>Error al cargar datos</div>;
  
  return (
    <div className="p-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {/* Ventas del Mes */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-2">Ventas del Mes</h3>
        <p className="text-3xl font-bold text-blue-600">
          {data.ventas_mes.meta.total_ventas.toFixed(2)} Bs
        </p>
        <p className="text-sm text-gray-600">
          {data.ventas_mes.meta.cantidad_ventas} ventas realizadas
        </p>
        <p className="text-sm text-gray-600">
          Promedio: {data.ventas_mes.meta.promedio_venta.toFixed(2)} Bs
        </p>
      </div>
      
      {/* Top Productos */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-2">Top 5 Productos</h3>
        <ul className="space-y-2">
          {data.top_productos.rows.slice(0, 5).map((producto, i) => (
            <li key={i} className="flex justify-between text-sm">
              <span>{producto.producto}</span>
              <span className="font-semibold">{producto.cantidad_vendida}</span>
            </li>
          ))}
        </ul>
      </div>
      
      {/* Stock Crítico */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-2">Alertas de Stock</h3>
        <p className="text-3xl font-bold text-red-600">
          {data.stock_critico.meta.sin_stock}
        </p>
        <p className="text-sm text-gray-600">Productos sin stock</p>
        <p className="text-sm text-gray-600 mt-2">
          {data.stock_critico.meta.total_productos_criticos} productos críticos en total
        </p>
      </div>
      
      {/* Morosidad */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-2">Morosidad</h3>
        <p className="text-3xl font-bold text-yellow-600">
          {data.morosidad.meta.total_clientes_morosos}
        </p>
        <p className="text-sm text-gray-600">Clientes morosos</p>
        <p className="text-sm text-gray-600 mt-2">
          Deuda total: {data.morosidad.meta.deuda_total.toFixed(2)} Bs
        </p>
      </div>
      
      {/* Flujo de Caja */}
      <div className="bg-white rounded-lg shadow p-6 md:col-span-2">
        <h3 className="text-lg font-semibold mb-2">Flujo de Caja del Mes</h3>
        <div className="grid grid-cols-3 gap-4 mt-4">
          <div>
            <p className="text-sm text-gray-600">Ingresos</p>
            <p className="text-xl font-bold text-green-600">
              {data.flujo_caja.meta.total_ingresos.toFixed(2)} Bs
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Egresos</p>
            <p className="text-xl font-bold text-red-600">
              {data.flujo_caja.meta.total_egresos.toFixed(2)} Bs
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Neto</p>
            <p className="text-xl font-bold text-blue-600">
              {data.flujo_caja.meta.neto_periodo.toFixed(2)} Bs
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
```

---

### 3️⃣ Ventas con Filtros de Fecha

```tsx
'use client';

import { useState, useEffect } from 'react';
import { 
  getVentasReport, 
  VentasReportResponse, 
  getCurrentMonthRange,
  getLastMonthRange 
} from '@/lib/api/reports';

export default function VentasPage() {
  const [ventas, setVentas] = useState<VentasReportResponse | null>(null);
  const [periodo, setPeriodo] = useState<'mes_actual' | 'mes_pasado'>('mes_actual');
  const [loading, setLoading] = useState(false);
  
  const cargarVentas = async () => {
    setLoading(true);
    try {
      const filters = periodo === 'mes_actual' 
        ? getCurrentMonthRange() 
        : getLastMonthRange();
      
      const data = await getVentasReport(filters);
      setVentas(data);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };
  
  useEffect(() => {
    cargarVentas();
  }, [periodo]);
  
  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Reporte de Ventas</h1>
        
        <div className="flex gap-2">
          <button
            onClick={() => setPeriodo('mes_actual')}
            className={`px-4 py-2 rounded ${
              periodo === 'mes_actual' 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-200'
            }`}
          >
            Mes Actual
          </button>
          <button
            onClick={() => setPeriodo('mes_pasado')}
            className={`px-4 py-2 rounded ${
              periodo === 'mes_pasado' 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-200'
            }`}
          >
            Mes Pasado
          </button>
        </div>
      </div>
      
      {loading && <div>Cargando...</div>}
      
      {ventas && (
        <>
          {/* Resumen */}
          <div className="grid grid-cols-4 gap-4 mb-6">
            <div className="bg-white p-4 rounded shadow">
              <p className="text-sm text-gray-600">Total Ventas</p>
              <p className="text-2xl font-bold">{ventas.meta.total_ventas.toFixed(2)} Bs</p>
            </div>
            <div className="bg-white p-4 rounded shadow">
              <p className="text-sm text-gray-600">Cantidad</p>
              <p className="text-2xl font-bold">{ventas.meta.cantidad_ventas}</p>
            </div>
            <div className="bg-white p-4 rounded shadow">
              <p className="text-sm text-gray-600">Promedio</p>
              <p className="text-2xl font-bold">{ventas.meta.promedio_venta.toFixed(2)} Bs</p>
            </div>
            <div className="bg-white p-4 rounded shadow">
              <p className="text-sm text-gray-600">Venta Máxima</p>
              <p className="text-2xl font-bold">{ventas.meta.venta_maxima.toFixed(2)} Bs</p>
            </div>
          </div>
          
          {/* Tabla de detalles */}
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  {ventas.columns.map(col => (
                    <th key={col} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {ventas.rows.map((row, i) => (
                  <tr key={i}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">{row.producto}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">{row.talla}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">{row.color}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">{row.cantidad_vendida}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold">
                      {row.total_bs.toFixed(2)} Bs
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
```

---

### 4️⃣ Stock Bajo (Alertas)

```tsx
'use client';

import { useEffect, useState } from 'react';
import { getStockBajo, StockBajoReportResponse } from '@/lib/api/reports';

export default function StockBajoPage() {
  const [stock, setStock] = useState<StockBajoReportResponse | null>(null);
  
  useEffect(() => {
    getStockBajo()
      .then(setStock)
      .catch(console.error);
  }, []);
  
  if (!stock) return <div>Cargando...</div>;
  
  const productosUrgentes = stock.rows.filter(p => p.estado === 'CRÍTICO');
  const productosBajos = stock.rows.filter(p => p.estado === 'BAJO');
  
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Alertas de Inventario</h1>
      
      {/* Resumen */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-red-50 border border-red-200 p-4 rounded">
          <p className="text-sm text-red-600">URGENTE - Sin Stock</p>
          <p className="text-3xl font-bold text-red-600">
            {stock.meta.sin_stock}
          </p>
        </div>
        <div className="bg-yellow-50 border border-yellow-200 p-4 rounded">
          <p className="text-sm text-yellow-600">Stock Bajo</p>
          <p className="text-3xl font-bold text-yellow-600">
            {stock.meta.total_productos_criticos - stock.meta.sin_stock}
          </p>
        </div>
      </div>
      
      {/* Productos urgentes */}
      {productosUrgentes.length > 0 && (
        <div className="mb-6">
          <h2 className="text-xl font-semibold text-red-600 mb-3">
            🚨 URGENTE - Sin Stock
          </h2>
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full">
              <thead className="bg-red-50">
                <tr>
                  <th className="px-4 py-2 text-left">Producto</th>
                  <th className="px-4 py-2 text-left">Categoría</th>
                  <th className="px-4 py-2 text-left">Talla/Color</th>
                  <th className="px-4 py-2 text-right">Stock</th>
                  <th className="px-4 py-2 text-right">Necesario</th>
                </tr>
              </thead>
              <tbody>
                {productosUrgentes.map((producto, i) => (
                  <tr key={i} className="border-t">
                    <td className="px-4 py-2">{producto.producto}</td>
                    <td className="px-4 py-2">{producto.categoria}</td>
                    <td className="px-4 py-2">{producto.talla} / {producto.color}</td>
                    <td className="px-4 py-2 text-right font-bold text-red-600">
                      {producto.stock_actual}
                    </td>
                    <td className="px-4 py-2 text-right">
                      {producto.deficit}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
      
      {/* Productos con stock bajo */}
      {productosBajos.length > 0 && (
        <div>
          <h2 className="text-xl font-semibold text-yellow-600 mb-3">
            ⚠️ Stock Bajo
          </h2>
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full">
              <thead className="bg-yellow-50">
                <tr>
                  <th className="px-4 py-2 text-left">Producto</th>
                  <th className="px-4 py-2 text-left">Categoría</th>
                  <th className="px-4 py-2 text-left">Talla/Color</th>
                  <th className="px-4 py-2 text-right">Stock</th>
                  <th className="px-4 py-2 text-right">Mínimo</th>
                  <th className="px-4 py-2 text-right">Necesario</th>
                </tr>
              </thead>
              <tbody>
                {productosBajos.map((producto, i) => (
                  <tr key={i} className="border-t">
                    <td className="px-4 py-2">{producto.producto}</td>
                    <td className="px-4 py-2">{producto.categoria}</td>
                    <td className="px-4 py-2">{producto.talla} / {producto.color}</td>
                    <td className="px-4 py-2 text-right font-semibold">
                      {producto.stock_actual}
                    </td>
                    <td className="px-4 py-2 text-right text-gray-600">
                      {producto.stock_minimo}
                    </td>
                    <td className="px-4 py-2 text-right text-yellow-600">
                      {producto.deficit}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
```

---

### 5️⃣ Cierre de Día (Caja)

```tsx
'use client';

import { useEffect, useState } from 'react';
import { getCierreDia, CierreDiaData } from '@/lib/api/reports';

export default function CierreDiaPage() {
  const [cierre, setCierre] = useState<CierreDiaData | null>(null);
  
  useEffect(() => {
    getCierreDia()
      .then(setCierre)
      .catch(console.error);
  }, []);
  
  if (!cierre) return <div>Cargando cierre de día...</div>;
  
  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Cierre de Caja - {cierre.fecha}</h1>
      
      {/* Resumen de Ventas */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Resumen de Ventas</h2>
        <div className="grid grid-cols-3 gap-4">
          <div>
            <p className="text-sm text-gray-600">Cantidad de Ventas</p>
            <p className="text-2xl font-bold">{cierre.ventas.cantidad}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Total Vendido</p>
            <p className="text-2xl font-bold text-green-600">
              {cierre.ventas.total.toFixed(2)} Bs
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Promedio por Venta</p>
            <p className="text-2xl font-bold">
              {cierre.ventas.promedio.toFixed(2)} Bs
            </p>
          </div>
        </div>
      </div>
      
      {/* Ingresos por Método de Pago */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Ingresos por Método de Pago</h2>
        <div className="space-y-3">
          <div className="flex justify-between items-center p-3 bg-green-50 rounded">
            <span className="font-medium">💵 Efectivo</span>
            <span className="text-lg font-bold text-green-600">
              {cierre.ingresos.efectivo.toFixed(2)} Bs
            </span>
          </div>
          <div className="flex justify-between items-center p-3 bg-blue-50 rounded">
            <span className="font-medium">💳 Tarjeta</span>
            <span className="text-lg font-bold text-blue-600">
              {cierre.ingresos.tarjeta.toFixed(2)} Bs
            </span>
          </div>
          <div className="flex justify-between items-center p-3 bg-purple-50 rounded">
            <span className="font-medium">📱 QR</span>
            <span className="text-lg font-bold text-purple-600">
              {cierre.ingresos.qr.toFixed(2)} Bs
            </span>
          </div>
          <div className="flex justify-between items-center p-3 bg-gray-100 rounded border-2 border-gray-300">
            <span className="font-bold text-lg">TOTAL</span>
            <span className="text-2xl font-bold">
              {cierre.ingresos.total.toFixed(2)} Bs
            </span>
          </div>
        </div>
      </div>
      
      {/* Botón de Impresión */}
      <button
        onClick={() => window.print()}
        className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700"
      >
        🖨️ Imprimir Cierre
      </button>
    </div>
  );
}
```

---

## 🎯 Tipos de Reportes Disponibles

### 📈 Ventas
- `ventas` - Reporte general de ventas
- `ventas_cliente` - Ventas por cliente
- `ventas_periodo` - Ventas agrupadas por período
- `ventas_ultimos_dias` - Ventas de últimos N días
- `ventas_mayores_a` - Ventas mayores a un monto
- `ventas_menores_a` - Ventas menores a un monto
- `ventas_entre_montos` - Ventas entre dos montos

### 📦 Productos
- `productos` - Reporte general de productos
- `stock_bajo` - Productos con stock bajo/crítico
- `mas_vendidos` - Top N productos más vendidos
- `menos_vendidos` - Top N productos menos vendidos
- `sin_ventas` - Productos sin movimiento
- `rentabilidad` - Análisis de rentabilidad
- `productos_mas_ingresos` - Productos que generan más ingresos
- `productos_menos_ingresos` - Productos que generan menos ingresos

### 💰 Pagos y Cuotas
- `pagos` - Reporte de pagos recibidos
- `cuotas` - Estado de cuotas
- `morosidad` - Clientes morosos
- `flujo_caja` - Flujo de caja (ingresos vs egresos)

---

## 🔧 Utilidades Incluidas

```typescript
// Formatear fecha para backend
formatDateForBackend(new Date()) // "2025-11-04"

// Rango del mes actual
getCurrentMonthRange() // { fecha_inicio: "2025-11-01", fecha_fin: "2025-11-30" }

// Rango del mes pasado
getLastMonthRange() // { fecha_inicio: "2025-10-01", fecha_fin: "2025-10-31" }

// Últimos N días
getLastNDaysRange(7) // { fecha_inicio: "2025-10-28", fecha_fin: "2025-11-04" }
```

---

## 🎨 Integración con librerías de estado

### Con SWR

```typescript
import useSWR from 'swr';
import { getDashboard } from '@/lib/api/reports';

export function useDashboard() {
  return useSWR('/dashboard', getDashboard, {
    refreshInterval: 60000, // Refrescar cada minuto
  });
}

// Uso en componente
function Dashboard() {
  const { data, error, isLoading } = useDashboard();
  
  if (isLoading) return <div>Cargando...</div>;
  if (error) return <div>Error: {error.message}</div>;
  
  return <div>Dashboard con {data.ventas_mes.meta.cantidad_ventas} ventas</div>;
}
```

### Con React Query

```typescript
import { useQuery } from '@tanstack/react-query';
import { getVentasReport } from '@/lib/api/reports';

export function useVentas(filters?: any) {
  return useQuery({
    queryKey: ['ventas', filters],
    queryFn: () => getVentasReport(filters),
    staleTime: 30000, // Cache por 30 segundos
  });
}

// Uso en componente
function Ventas() {
  const filters = getCurrentMonthRange();
  const { data, isLoading } = useVentas(filters);
  
  if (isLoading) return <div>Cargando ventas...</div>;
  
  return <div>Total: {data?.meta.total_ventas} Bs</div>;
}
```

---

## 📱 Ejemplo Completo: App de Reportes

```tsx
// app/reportes/page.tsx
'use client';

import { useState } from 'react';
import { generateNaturalLanguageReport, generateReportByType } from '@/lib/api/reports';

export default function ReportesPage() {
  const [modo, setModo] = useState<'natural' | 'directo'>('natural');
  
  return (
    <div className="p-6">
      <div className="flex gap-4 mb-6">
        <button
          onClick={() => setModo('natural')}
          className={`px-6 py-2 rounded ${modo === 'natural' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
        >
          Lenguaje Natural
        </button>
        <button
          onClick={() => setModo('directo')}
          className={`px-6 py-2 rounded ${modo === 'directo' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
        >
          Reporte Directo
        </button>
      </div>
      
      {modo === 'natural' ? <BusquedaNatural /> : <ReporteDirecto />}
    </div>
  );
}
```

---

## 🚀 Próximos Pasos

1. **Copia el archivo** `REACT_TYPES_AND_API.ts` a tu proyecto Next.js
2. **Configura la URL** del backend en `.env.local`
3. **Importa los tipos y funciones** donde los necesites
4. **Opcional**: Agrega autenticación con tokens JWT
5. **Opcional**: Integra con SWR o React Query para caché

---

## 📚 Documentación Adicional

- **Backend**: Django REST Framework en `http://localhost:8000/api/v1/reports/`
- **Swagger/OpenAPI**: (si está configurado) en `http://localhost:8000/api/docs/`
- **Queries de lenguaje natural**: Ver `base_parser.py` y `ventas_parser.py`

---

## ✅ Checklist de Integración

- [ ] Copiar `REACT_TYPES_AND_API.ts` a tu proyecto
- [ ] Instalar `@types/node` (si usas Next.js)
- [ ] Configurar `NEXT_PUBLIC_API_URL` en `.env.local`
- [ ] Probar llamada a `/reports/dashboard/` desde tu app
- [ ] Implementar manejo de autenticación (si aplica)
- [ ] Agregar manejo de errores personalizado
- [ ] Configurar SWR o React Query (opcional)
- [ ] Crear componentes reutilizables para tablas de reportes

---

¡Listo! Ahora tienes todo lo necesario para integrar el sistema de reportes en tu aplicación React/Next.js 🎉
