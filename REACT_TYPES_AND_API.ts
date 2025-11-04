/**
 * ============================================
 * TIPOS TYPESCRIPT PARA SISTEMA DE REPORTES
 * Backend Boutique - API de Reportes
 * ============================================
 * 
 * Base URL: http://localhost:8000/api/v1/reports/
 * 
 * Endpoints disponibles:
 * - POST /query/              -> Reporte con lenguaje natural
 * - POST /generate/           -> Reporte por tipo directo
 * - GET  /dashboard/          -> Dashboard administrativo
 * - GET  /cierre-dia/         -> Cierre de caja diario
 * - GET  /alertas-inventario/ -> Alertas de stock
 */

// ============================================
// TIPOS BASE
// ============================================

export interface ReportMeta {
  [key: string]: any;
}

export interface ReportColumn {
  name: string;
  label?: string;
}

export interface ReportResponse<T = any> {
  summary: string;
  columns: string[];
  rows: T[];
  meta?: ReportMeta;
}

// ============================================
// TIPOS PARA LENGUAJE NATURAL
// ============================================

export interface NaturalLanguageQueryRequest {
  query: string;
}

export interface ParsedQuery {
  intent: string;
  filters: {
    fecha_inicio?: string;
    fecha_fin?: string;
    monto_min?: number;
    monto_max?: number;
    cantidad_min?: number;
    cantidad_max?: number;
    cliente?: string;
    categoria?: string;
    periodo?: string;
    [key: string]: any;
  };
  limit?: number;
}

export interface NaturalLanguageQueryResponse {
  query_original: string;
  parsed_query: ParsedQuery;
  report: ReportResponse;
}

// ============================================
// TIPOS PARA REPORTES DIRECTOS
// ============================================

export type ReportType =
  // Ventas
  | 'ventas'
  | 'ventas_cliente'
  | 'ventas_periodo'
  | 'ventas_ultimos_dias'
  | 'ventas_mayores_a'
  | 'ventas_menores_a'
  | 'ventas_entre_montos'
  // Productos
  | 'productos'
  | 'stock_bajo'
  | 'mas_vendidos'
  | 'menos_vendidos'
  | 'sin_ventas'
  | 'rentabilidad'
  | 'productos_mas_ingresos'
  | 'productos_menos_ingresos'
  // Pagos
  | 'pagos'
  | 'cuotas'
  | 'morosidad'
  | 'flujo_caja';

export interface ReportByTypeRequest {
  report_type: ReportType;
  filters?: {
    fecha_inicio?: string;
    fecha_fin?: string;
    cliente?: string | number;
    periodo?: 'dia' | 'semana' | 'mes' | 'año';
    dias?: number;
    monto?: number;
    monto_min?: number;
    monto_max?: number;
    limite?: number;
    categoria?: string | number;
    stock_bajo?: boolean;
    mas_vendidos?: boolean;
    orden?: 'fecha' | 'total' | '-fecha' | '-total';
    tipo_pago?: 'contado' | 'credito';
    estado_pago?: 'pendiente' | 'parcial' | 'pagado';
    [key: string]: any;
  };
}

export interface ReportByTypeResponse {
  report_type: string;
  filters: Record<string, any>;
  report: ReportResponse;
}

// ============================================
// TIPOS ESPECÍFICOS DE REPORTES DE VENTAS
// ============================================

export interface VentaRow {
  producto: string;
  talla: string;
  color: string;
  cantidad_vendida: number;
  total_bs: number;
}

export interface VentaMeta {
  total_ventas: number;
  total_con_interes: number;
  cantidad_ventas: number;
  promedio_venta: number;
  venta_maxima: number;
  venta_minima: number;
  por_tipo_pago: {
    tipo: 'contado' | 'credito';
    cantidad: number;
    monto: number;
  }[];
  por_estado: {
    estado: 'pendiente' | 'parcial' | 'pagado';
    cantidad: number;
    monto: number;
  }[];
}

export type VentasReportResponse = ReportResponse<VentaRow> & {
  meta: VentaMeta;
};

export interface VentaClienteRow {
  cliente: string;
  username: string;
  email: string;
  total_compras: number;
  monto_total: number;
  monto_pendiente: number;
}

export type VentasClienteReportResponse = ReportResponse<VentaClienteRow>;

export interface VentaPeriodoRow {
  periodo: string;
  fecha: string;
  cantidad_ventas: number;
  monto_total: number;
  monto_promedio: number;
}

export type VentasPeriodoReportResponse = ReportResponse<VentaPeriodoRow>;

export interface VentaDetalleRow {
  id: number;
  codigo: string;
  fecha: string;
  cliente: string;
  total: string;
  total_con_interes: string;
  tipo_venta: string;
  cantidad_total_productos?: number;
}

export interface VentasConProductoResponse {
  ventas: VentaDetalleRow[];
  total_ventas: number;
  monto_total: string;
  producto_mas_vendido: {
    nombre: string;
    sku: string;
    cantidad_vendida: number;
  } | null;
  stats?: {
    promedio_venta: string;
  };
  mensaje?: string;
}

// ============================================
// TIPOS ESPECÍFICOS DE REPORTES DE PRODUCTOS
// ============================================

export interface ProductoRow {
  id: number;
  producto: string;
  categoria: string;
  talla: string;
  color: string;
  stock: number;
  stock_minimo?: number;
  stock_critico?: boolean;
  vendidos: number;
  precio_venta: number;
  precio_costo?: number;
  ingresos: number;
  margen?: number;
  margen_porcentaje: number;
}

export interface ProductoMeta {
  total_variantes: number;
  total_stock: number;
  total_vendidos: number;
  total_ingresos: number;
  productos_criticos: number;
}

export type ProductosReportResponse = ReportResponse<ProductoRow> & {
  meta: ProductoMeta;
};

export interface StockBajoRow {
  producto: string;
  categoria: string;
  talla: string;
  color: string;
  stock_actual: number;
  stock_minimo: number;
  deficit: number;
  estado: 'CRÍTICO' | 'BAJO';
}

export interface StockBajoMeta {
  total_productos_criticos: number;
  sin_stock: number;
}

export type StockBajoReportResponse = ReportResponse<StockBajoRow> & {
  meta: StockBajoMeta;
};

export interface ProductoMasVendidoRow {
  producto: string;
  talla: string;
  color: string;
  cantidad_vendida: number;
  num_ventas: number;
  ingresos: number;
  stock_actual: number;
}

export type ProductosMasVendidosReportResponse = ReportResponse<ProductoMasVendidoRow>;

export interface ProductoConFechasRow {
  id: number;
  nombre: string;
  sku: string;
  color: string;
  talla: string;
  cantidad_vendida: number;
  ingresos_generados: string;
}

export interface ProductosConFechasResponse {
  productos: ProductoConFechasRow[];
  periodo: {
    fecha_inicio?: string;
    fecha_fin?: string;
  };
}

export interface ProductoSinVentasRow {
  producto: string;
  categoria: string;
  talla: string;
  color: string;
  stock: number;
  dias_sin_venta: number;
  precio_venta: number;
}

export interface ProductoSinVentasMeta {
  total_productos: number;
  valor_total_inventario: number;
  promedio_dias_sin_movimiento: number;
}

export type ProductosSinVentasReportResponse = ReportResponse<ProductoSinVentasRow> & {
  meta: ProductoSinVentasMeta;
};

export interface RentabilidadRow {
  producto: string;
  categoria: string;
  talla: string;
  color: string;
  cantidad_vendida: number;
  ingresos: number;
  costos: number;
  ganancia: number;
  margen_porcentaje: number;
  roi_porcentaje: number;
}

export interface RentabilidadMeta {
  ingresos_totales: number;
  costos_totales: number;
  ganancia_total: number;
  margen_promedio: number;
  roi_promedio: number;
}

export type RentabilidadReportResponse = ReportResponse<RentabilidadRow> & {
  meta: RentabilidadMeta;
};

// ============================================
// TIPOS ESPECÍFICOS DE REPORTES DE PAGOS
// ============================================

export interface PagoRow {
  método_pago: 'efectivo' | 'tarjeta' | 'qr';
  cantidad_pagos: number;
  monto_total: number;
  monto_promedio: number;
}

export interface PagoMeta {
  total_pagos: number;
  monto_total_efectivo: number;
  monto_total_tarjeta: number;
  monto_total_qr: number;
}

export type PagosReportResponse = ReportResponse<PagoRow> & {
  meta: PagoMeta;
};

export interface CuotaRow {
  venta_codigo: string;
  cliente: string;
  cuota_numero: number;
  monto: number;
  fecha_vencimiento: string;
  estado: 'pendiente' | 'pagada' | 'vencida';
  dias_vencidos?: number;
}

export interface CuotaMeta {
  total_cuotas: number;
  cuotas_pendientes: number;
  cuotas_vencidas: number;
  monto_pendiente: number;
  monto_vencido: number;
}

export type CuotasReportResponse = ReportResponse<CuotaRow> & {
  meta: CuotaMeta;
};

export interface MorosidadRow {
  cliente: string;
  email: string;
  telefono: string;
  deuda_total: number;
  cuotas_vencidas: number;
  dias_mora_promedio: number;
  ultima_venta: string;
}

export interface MorosidadMeta {
  total_clientes_morosos: number;
  deuda_total: number;
  cuotas_vencidas_total: number;
  promedio_dias_mora: number;
}

export type MorosidadReportResponse = ReportResponse<MorosidadRow> & {
  meta: MorosidadMeta;
};

export interface FlujoCajaRow {
  fecha: string;
  ingresos: number;
  egresos: number;
  neto: number;
  saldo_acumulado: number;
}

export interface FlujoCajaMeta {
  total_ingresos: number;
  total_egresos: number;
  neto_periodo: number;
  saldo_final: number;
}

export type FlujoCajaReportResponse = ReportResponse<FlujoCajaRow> & {
  meta: FlujoCajaMeta;
};

// ============================================
// TIPOS PARA DASHBOARD
// ============================================

export interface DashboardData {
  ventas_mes: VentasReportResponse;
  top_productos: ProductosMasVendidosReportResponse;
  stock_critico: StockBajoReportResponse;
  morosidad: MorosidadReportResponse;
  flujo_caja: FlujoCajaReportResponse;
}

// ============================================
// TIPOS PARA CIERRE DE DÍA
// ============================================

export interface CierreDiaData {
  fecha: string;
  ventas: {
    cantidad: number;
    total: number;
    promedio: number;
  };
  ingresos: {
    efectivo: number;
    tarjeta: number;
    qr: number;
    total: number;
  };
  detalle_ventas: VentaDetalleRow[];
  detalle_pagos: PagoRow[];
}

// ============================================
// TIPOS PARA ALERTAS DE INVENTARIO
// ============================================

export interface AlertasInventarioData {
  urgente: StockBajoRow[];
  bajo_stock: StockBajoRow[];
  sin_movimiento: ProductoSinVentasRow[];
  resumen: {
    productos_criticos: number;
    productos_bajo_stock: number;
    productos_sin_ventas: number;
  };
}

// ============================================
// SERVICIO API - FUNCIONES PARA REACT/NEXT.JS
// ============================================

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
const REPORTS_URL = `${API_BASE_URL}/reports`;

/**
 * Configuración base para fetch
 */
const fetchConfig = (method: 'GET' | 'POST' = 'GET', body?: any): RequestInit => ({
  method,
  headers: {
    'Content-Type': 'application/json',
    // Agregar token de autenticación si existe
    // 'Authorization': `Bearer ${token}`,
  },
  body: body ? JSON.stringify(body) : undefined,
});

/**
 * Manejo de errores de API
 */
const handleApiError = async (response: Response) => {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Error desconocido' }));
    throw new Error(error.error || `HTTP Error: ${response.status}`);
  }
  return response.json();
};

// ============================================
// 1. LENGUAJE NATURAL
// ============================================

/**
 * Genera un reporte usando lenguaje natural
 * 
 * @example
 * ```typescript
 * const resultado = await generateNaturalLanguageReport({
 *   query: "ventas del mes pasado mayores a 1000"
 * });
 * ```
 */
export async function generateNaturalLanguageReport(
  data: NaturalLanguageQueryRequest
): Promise<NaturalLanguageQueryResponse> {
  const response = await fetch(
    `${REPORTS_URL}/query/`,
    fetchConfig('POST', data)
  );
  return handleApiError(response);
}

// ============================================
// 2. REPORTES DIRECTOS POR TIPO
// ============================================

/**
 * Genera un reporte por tipo específico
 * 
 * @example
 * ```typescript
 * const ventas = await generateReportByType({
 *   report_type: 'ventas',
 *   filters: {
 *     fecha_inicio: '2025-01-01',
 *     fecha_fin: '2025-01-31'
 *   }
 * });
 * ```
 */
export async function generateReportByType(
  data: ReportByTypeRequest
): Promise<ReportByTypeResponse> {
  const response = await fetch(
    `${REPORTS_URL}/generate/`,
    fetchConfig('POST', data)
  );
  return handleApiError(response);
}

// ============================================
// 3. REPORTES DE VENTAS (ESPECÍFICOS)
// ============================================

/**
 * Obtiene reporte de ventas con filtros
 */
export async function getVentasReport(
  filters?: ReportByTypeRequest['filters']
): Promise<VentasReportResponse> {
  const result = await generateReportByType({ report_type: 'ventas', filters });
  return result.report as VentasReportResponse;
}

/**
 * Obtiene reporte de ventas por cliente
 */
export async function getVentasPorCliente(
  clienteId?: string | number
): Promise<VentasClienteReportResponse> {
  const result = await generateReportByType({
    report_type: 'ventas_cliente',
    filters: { cliente: clienteId }
  });
  return result.report as VentasClienteReportResponse;
}

/**
 * Obtiene reporte de ventas por período
 */
export async function getVentasPorPeriodo(
  periodo: 'dia' | 'semana' | 'mes' | 'año' = 'mes'
): Promise<VentasPeriodoReportResponse> {
  const result = await generateReportByType({
    report_type: 'ventas_periodo',
    filters: { periodo }
  });
  return result.report as VentasPeriodoReportResponse;
}

/**
 * Obtiene ventas de los últimos N días
 */
export async function getVentasUltimosDias(
  dias: number = 30
): Promise<VentasReportResponse> {
  const result = await generateReportByType({
    report_type: 'ventas_ultimos_dias',
    filters: { dias }
  });
  return result.report as VentasReportResponse;
}

/**
 * Obtiene ventas mayores a un monto
 */
export async function getVentasMayoresA(
  monto: number
): Promise<VentasReportResponse> {
  const result = await generateReportByType({
    report_type: 'ventas_mayores_a',
    filters: { monto }
  });
  return result.report as VentasReportResponse;
}

/**
 * Obtiene ventas menores a un monto
 */
export async function getVentasMenoresA(
  monto: number
): Promise<VentasReportResponse> {
  const result = await generateReportByType({
    report_type: 'ventas_menores_a',
    filters: { monto }
  });
  return result.report as VentasReportResponse;
}

/**
 * Obtiene ventas entre dos montos
 */
export async function getVentasEntremontos(
  montoMin: number,
  montoMax: number
): Promise<VentasReportResponse> {
  const result = await generateReportByType({
    report_type: 'ventas_entre_montos',
    filters: { monto_min: montoMin, monto_max: montoMax }
  });
  return result.report as VentasReportResponse;
}

// ============================================
// 4. REPORTES DE PRODUCTOS (ESPECÍFICOS)
// ============================================

/**
 * Obtiene reporte de productos con filtros
 */
export async function getProductosReport(
  filters?: ReportByTypeRequest['filters']
): Promise<ProductosReportResponse> {
  const result = await generateReportByType({ report_type: 'productos', filters });
  return result.report as ProductosReportResponse;
}

/**
 * Obtiene productos con stock bajo
 */
export async function getStockBajo(): Promise<StockBajoReportResponse> {
  const result = await generateReportByType({ report_type: 'stock_bajo' });
  return result.report as StockBajoReportResponse;
}

/**
 * Obtiene los productos más vendidos
 */
export async function getProductosMasVendidos(
  limite: number = 10
): Promise<ProductosMasVendidosReportResponse> {
  const result = await generateReportByType({
    report_type: 'mas_vendidos',
    filters: { limite }
  });
  return result.report as ProductosMasVendidosReportResponse;
}

/**
 * Obtiene los productos menos vendidos
 */
export async function getProductosMenosVendidos(
  limite: number = 10
): Promise<ProductosMasVendidosReportResponse> {
  const result = await generateReportByType({
    report_type: 'menos_vendidos',
    filters: { limite }
  });
  return result.report as ProductosMasVendidosReportResponse;
}

/**
 * Obtiene productos sin ventas
 */
export async function getProductosSinVentas(): Promise<ProductosSinVentasReportResponse> {
  const result = await generateReportByType({ report_type: 'sin_ventas' });
  return result.report as ProductosSinVentasReportResponse;
}

/**
 * Obtiene reporte de rentabilidad de productos
 */
export async function getRentabilidadProductos(): Promise<RentabilidadReportResponse> {
  const result = await generateReportByType({ report_type: 'rentabilidad' });
  return result.report as RentabilidadReportResponse;
}

/**
 * Obtiene productos que generaron más ingresos
 */
export async function getProductosMasIngresos(
  limite: number = 10
): Promise<ProductosMasVendidosReportResponse> {
  const result = await generateReportByType({
    report_type: 'productos_mas_ingresos',
    filters: { limite }
  });
  return result.report as ProductosMasVendidosReportResponse;
}

/**
 * Obtiene productos que generaron menos ingresos
 */
export async function getProductosMenosIngresos(
  limite: number = 10
): Promise<ProductosMasVendidosReportResponse> {
  const result = await generateReportByType({
    report_type: 'productos_menos_ingresos',
    filters: { limite }
  });
  return result.report as ProductosMasVendidosReportResponse;
}

// ============================================
// 5. REPORTES DE PAGOS Y CUOTAS (ESPECÍFICOS)
// ============================================

/**
 * Obtiene reporte de pagos con filtros
 */
export async function getPagosReport(
  filters?: ReportByTypeRequest['filters']
): Promise<PagosReportResponse> {
  const result = await generateReportByType({ report_type: 'pagos', filters });
  return result.report as PagosReportResponse;
}

/**
 * Obtiene reporte de cuotas
 */
export async function getCuotasReport(
  filters?: ReportByTypeRequest['filters']
): Promise<CuotasReportResponse> {
  const result = await generateReportByType({ report_type: 'cuotas', filters });
  return result.report as CuotasReportResponse;
}

/**
 * Obtiene reporte de morosidad
 */
export async function getMorosidadReport(): Promise<MorosidadReportResponse> {
  const result = await generateReportByType({ report_type: 'morosidad' });
  return result.report as MorosidadReportResponse;
}

/**
 * Obtiene reporte de flujo de caja
 */
export async function getFlujoCajaReport(
  filters?: ReportByTypeRequest['filters']
): Promise<FlujoCajaReportResponse> {
  const result = await generateReportByType({ report_type: 'flujo_caja', filters });
  return result.report as FlujoCajaReportResponse;
}

// ============================================
// 6. ENDPOINTS ESPECIALES
// ============================================

/**
 * Obtiene datos del dashboard administrativo
 */
export async function getDashboard(): Promise<DashboardData> {
  const response = await fetch(`${REPORTS_URL}/dashboard/`, fetchConfig());
  return handleApiError(response);
}

/**
 * Obtiene el cierre de día actual
 */
export async function getCierreDia(): Promise<CierreDiaData> {
  const response = await fetch(`${REPORTS_URL}/cierre-dia/`, fetchConfig());
  return handleApiError(response);
}

/**
 * Obtiene alertas de inventario
 */
export async function getAlertasInventario(): Promise<AlertasInventarioData> {
  const response = await fetch(`${REPORTS_URL}/alertas-inventario/`, fetchConfig());
  return handleApiError(response);
}

// ============================================
// 7. HOOKS DE REACT (OPCIONAL - USAR CON SWR O REACT-QUERY)
// ============================================

/**
 * Ejemplo de uso con SWR (opcional)
 * 
 * ```typescript
 * import useSWR from 'swr';
 * 
 * export function useDashboard() {
 *   return useSWR('/dashboard', getDashboard);
 * }
 * 
 * export function useVentas(filters?: ReportByTypeRequest['filters']) {
 *   return useSWR(
 *     filters ? ['/ventas', JSON.stringify(filters)] : '/ventas',
 *     () => getVentasReport(filters)
 *   );
 * }
 * ```
 */

/**
 * Ejemplo de uso con React Query (opcional)
 * 
 * ```typescript
 * import { useQuery } from '@tanstack/react-query';
 * 
 * export function useDashboard() {
 *   return useQuery({
 *     queryKey: ['dashboard'],
 *     queryFn: getDashboard
 *   });
 * }
 * 
 * export function useVentas(filters?: ReportByTypeRequest['filters']) {
 *   return useQuery({
 *     queryKey: ['ventas', filters],
 *     queryFn: () => getVentasReport(filters)
 *   });
 * }
 * ```
 */

// ============================================
// 8. UTILIDADES
// ============================================

/**
 * Formatea una fecha para el backend (YYYY-MM-DD)
 */
export function formatDateForBackend(date: Date): string {
  return date.toISOString().split('T')[0];
}

/**
 * Obtiene el rango de fechas del mes actual
 */
export function getCurrentMonthRange(): { fecha_inicio: string; fecha_fin: string } {
  const now = new Date();
  const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);
  const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0);
  
  return {
    fecha_inicio: formatDateForBackend(firstDay),
    fecha_fin: formatDateForBackend(lastDay)
  };
}

/**
 * Obtiene el rango de fechas del mes pasado
 */
export function getLastMonthRange(): { fecha_inicio: string; fecha_fin: string } {
  const now = new Date();
  const firstDay = new Date(now.getFullYear(), now.getMonth() - 1, 1);
  const lastDay = new Date(now.getFullYear(), now.getMonth(), 0);
  
  return {
    fecha_inicio: formatDateForBackend(firstDay),
    fecha_fin: formatDateForBackend(lastDay)
  };
}

/**
 * Obtiene el rango de los últimos N días
 */
export function getLastNDaysRange(days: number): { fecha_inicio: string; fecha_fin: string } {
  const now = new Date();
  const pastDate = new Date(now);
  pastDate.setDate(pastDate.getDate() - days);
  
  return {
    fecha_inicio: formatDateForBackend(pastDate),
    fecha_fin: formatDateForBackend(now)
  };
}

// ============================================
// EJEMPLOS DE USO
// ============================================

/**
 * EJEMPLO 1: Componente de Dashboard
 * 
 * ```tsx
 * import { getDashboard, DashboardData } from '@/lib/api/reports';
 * import { useEffect, useState } from 'react';
 * 
 * export function DashboardPage() {
 *   const [data, setData] = useState<DashboardData | null>(null);
 *   const [loading, setLoading] = useState(true);
 *   
 *   useEffect(() => {
 *     getDashboard()
 *       .then(setData)
 *       .catch(console.error)
 *       .finally(() => setLoading(false));
 *   }, []);
 *   
 *   if (loading) return <div>Cargando...</div>;
 *   if (!data) return <div>Error al cargar datos</div>;
 *   
 *   return (
 *     <div>
 *       <h1>Dashboard</h1>
 *       <div>Ventas del mes: {data.ventas_mes.meta.total_ventas} Bs</div>
 *       <div>Top productos: {data.top_productos.rows.length}</div>
 *       <div>Stock crítico: {data.stock_critico.meta.sin_stock} productos</div>
 *     </div>
 *   );
 * }
 * ```
 */

/**
 * EJEMPLO 2: Reporte con lenguaje natural
 * 
 * ```tsx
 * import { generateNaturalLanguageReport } from '@/lib/api/reports';
 * import { useState } from 'react';
 * 
 * export function NaturalLanguageSearch() {
 *   const [query, setQuery] = useState('');
 *   const [result, setResult] = useState(null);
 *   
 *   const handleSearch = async () => {
 *     try {
 *       const response = await generateNaturalLanguageReport({ query });
 *       setResult(response);
 *     } catch (error) {
 *       console.error(error);
 *     }
 *   };
 *   
 *   return (
 *     <div>
 *       <input
 *         value={query}
 *         onChange={(e) => setQuery(e.target.value)}
 *         placeholder="ventas del mes pasado mayores a 1000"
 *       />
 *       <button onClick={handleSearch}>Buscar</button>
 *       {result && (
 *         <div>
 *           <h3>{result.report.summary}</h3>
 *           <table>
 *             <thead>
 *               <tr>
 *                 {result.report.columns.map(col => (
 *                   <th key={col}>{col}</th>
 *                 ))}
 *               </tr>
 *             </thead>
 *             <tbody>
 *               {result.report.rows.map((row, i) => (
 *                 <tr key={i}>
 *                   {result.report.columns.map(col => (
 *                     <td key={col}>{row[col]}</td>
 *                   ))}
 *                 </tr>
 *               ))}
 *             </tbody>
 *           </table>
 *         </div>
 *       )}
 *     </div>
 *   );
 * }
 * ```
 */

/**
 * EJEMPLO 3: Filtros de fecha con utilidades
 * 
 * ```tsx
 * import { getVentasReport, getCurrentMonthRange } from '@/lib/api/reports';
 * 
 * export async function VentasMesActual() {
 *   const filters = getCurrentMonthRange();
 *   const ventas = await getVentasReport(filters);
 *   
 *   return (
 *     <div>
 *       <h2>Ventas de {filters.fecha_inicio} a {filters.fecha_fin}</h2>
 *       <p>Total: {ventas.meta.total_ventas} Bs</p>
 *       <p>Cantidad: {ventas.meta.cantidad_ventas}</p>
 *     </div>
 *   );
 * }
 * ```
 */

export default {
  // Lenguaje natural
  generateNaturalLanguageReport,
  generateReportByType,
  
  // Ventas
  getVentasReport,
  getVentasPorCliente,
  getVentasPorPeriodo,
  getVentasUltimosDias,
  getVentasMayoresA,
  getVentasMenoresA,
  getVentasEntremontos,
  
  // Productos
  getProductosReport,
  getStockBajo,
  getProductosMasVendidos,
  getProductosMenosVendidos,
  getProductosSinVentas,
  getRentabilidadProductos,
  getProductosMasIngresos,
  getProductosMenosIngresos,
  
  // Pagos
  getPagosReport,
  getCuotasReport,
  getMorosidadReport,
  getFlujoCajaReport,
  
  // Especiales
  getDashboard,
  getCierreDia,
  getAlertasInventario,
  
  // Utilidades
  formatDateForBackend,
  getCurrentMonthRange,
  getLastMonthRange,
  getLastNDaysRange,
};
