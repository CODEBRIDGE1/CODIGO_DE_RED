<script lang="ts">
  import { onMount } from 'svelte';
  import { authStore } from '../../stores/auth';

  type Tab = 'cotizaciones' | 'conceptos';

  interface AdminQuoteLine {
    id: number;
    quote_item_id: number | null;
    description: string;
    quantity: number;
    unit_price: number;
    subtotal: number;
  }

  interface AdminQuote {
    id: number;
    quote_number: string;
    title: string;
    status: string;
    total: number;
    iva_percent: number;
    iva_amount: number;
    total_con_iva: number;
    fecha_vigencia: string | null;
    comentarios_admin: string | null;
    numero_transformadores: number | null;
    observaciones: string | null;
    created_at: string;
    updated_at: string;
    company_id: number;
    razon_social: string;
    rfc: string | null;
    direccion: string | null;
    ciudad: string | null;
    estado_empresa: string | null;
    codigo_postal: string | null;
    telefono: string | null;
    email: string | null;
    tenant_id: number;
    cliente_nombre: string;
    lines: AdminQuoteLine[];
  }

  interface QuoteItem {
    id: number;
    code: string;
    name: string;
    description: string | null;
    category: string;
    unit: string;
    base_price: number;
    is_active: boolean;
    created_at: string;
  }

  interface QuoteItemForm {
    code: string;
    name: string;
    description: string;
    category: string;
    unit: string;
    base_price: number;
  }

  const categories = [
    { value: 'INSTALACION', label: 'Instalación' },
    { value: 'MANTENIMIENTO', label: 'Mantenimiento' },
    { value: 'AUDITORIA', label: 'Auditoría' },
    { value: 'CERTIFICACION', label: 'Certificación' },
    { value: 'CONSULTORIA', label: 'Consultoría' },
    { value: 'MATERIALES', label: 'Materiales' },
    { value: 'MANO_OBRA', label: 'Mano de Obra' },
    { value: 'EQUIPO', label: 'Equipo' },
    { value: 'OTRO', label: 'Otro' }
  ];

  const units = [
    { value: 'PIEZA', label: 'Pieza' },
    { value: 'METRO', label: 'Metro' },
    { value: 'METRO_CUADRADO', label: 'Metro Cuadrado' },
    { value: 'METRO_CUBICO', label: 'Metro Cúbico' },
    { value: 'SERVICIO', label: 'Servicio' },
    { value: 'HORA', label: 'Hora' },
    { value: 'DIA', label: 'Día' },
    { value: 'LOTE', label: 'Lote' },
    { value: 'KILOGRAMO', label: 'Kilogramo' },
    { value: 'LITRO', label: 'Litro' }
  ];

  let activeTab = $state<Tab>('cotizaciones');

  // ── Cotizaciones recibidas ──────────────────────────────
  let quotes = $state<AdminQuote[]>([]);
  let quotesLoading = $state(false);
  let quotesTotal = $state(0);
  let quotesPage = $state(1);
  let quotesSearch = $state('');
  let quotesStatus = $state('sent');  // por defecto: enviadas
  let selectedQuote = $state<AdminQuote | null>(null);
  let showQuoteDetail = $state(false);
  let showStatusModal = $state(false);
  let quoteForStatus = $state<AdminQuote | null>(null);
  let newStatus = $state('');
  let editingPrices = $state(false);
  let draftPrices = $state<Record<number, number>>({});
  let savingPrices = $state(false);
  let draftIva = $state(16);
  let draftVigencia = $state('');
  let draftComentarios = $state('');
  let savingDetails = $state(false);
  let hasLoadedQuotes = $state(false);

  // Derived totals used in tfoot and PDF
  const modalSubtotal = $derived(
    editingPrices && selectedQuote
      ? selectedQuote.lines.reduce((s, l) => s + (draftPrices[l.id] || 0) * l.quantity, 0)
      : Number(selectedQuote?.total ?? 0)
  );
  const modalIvaPct = $derived(editingPrices ? draftIva : (selectedQuote?.iva_percent ?? 0));
  const modalIvaAmt = $derived(
    editingPrices ? modalSubtotal * modalIvaPct / 100 : Number(selectedQuote?.iva_amount ?? 0)
  );
  const modalTotal = $derived(
    editingPrices ? modalSubtotal + modalIvaAmt : Number(selectedQuote?.total_con_iva || selectedQuote?.total || 0)
  );

  // ── Catálogo de conceptos ───────────────────────────────
  let items = $state<QuoteItem[]>([]);
  let loading = $state(true);
  let showModal = $state(false);
  let isEditing = $state(false);
  let currentItem = $state<QuoteItem | null>(null);
  let searchTerm = $state('');
  let filterCategory = $state<string>('all');
  let filterActive = $state<'all' | 'active' | 'inactive'>('all');
  let showDeleteModal = $state(false);
  let itemToDelete = $state<QuoteItem | null>(null);
  let errorMessage = $state('');
  let successMessage = $state('');

  let form = $state<QuoteItemForm>({
    code: '',
    name: '',
    description: '',
    category: 'MATERIALES',
    unit: 'PIEZA',
    base_price: 0
  });

  const filteredItems = $derived(
    Array.isArray(items) ? items.filter(item => {
      const matchesSearch = item.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          (item.description?.toLowerCase().includes(searchTerm.toLowerCase()) ?? false);
      const matchesCategory = filterCategory === 'all' || item.category === filterCategory;
      const matchesActive = filterActive === 'all' ? true :
                          filterActive === 'active' ? item.is_active : !item.is_active;
      return matchesSearch && matchesCategory && matchesActive;
    }) : []
  );

  let hasLoadedItems = $state(false);

  onMount(() => {
    // Cargar cotizaciones enviadas al montar
    loadQuotes();
  });

  // ── Funciones de cotizaciones ───────────────────────────

  async function loadQuotes() {
    try {
      quotesLoading = true;
      const params = new URLSearchParams({
        page: String(quotesPage),
        page_size: '50',
        status: quotesStatus,
      });
      if (quotesSearch) params.set('search', quotesSearch);

      const response = await fetch(
        `${import.meta.env.VITE_API_BASE_URL}/api/v1/admin/quotes/?${params}`,
        { headers: { 'Authorization': `Bearer ${$authStore.accessToken}` } }
      );

      if (!response.ok) throw new Error('Error al cargar cotizaciones');
      const data = await response.json();
      quotes = data.quotes || [];
      quotesTotal = data.total || 0;
      hasLoadedQuotes = true;
    } catch (error: any) {
      errorMessage = error.message || 'Error al cargar cotizaciones';
      quotes = [];
    } finally {
      quotesLoading = false;
    }
  }

  function openQuoteDetail(q: AdminQuote) {
    selectedQuote = q;
    draftIva = q.iva_percent ?? 16;
    draftVigencia = q.fecha_vigencia ? q.fecha_vigencia.split('T')[0] : '';
    draftComentarios = q.comentarios_admin ?? '';
    showQuoteDetail = true;
  }

  function openStatusModal(q: AdminQuote, status: string) {
    quoteForStatus = q;
    newStatus = status;
    showStatusModal = true;
  }

  async function confirmStatusChange() {
    if (!quoteForStatus) return;
    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_BASE_URL}/api/v1/admin/quotes/${quoteForStatus.id}/status`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${$authStore.accessToken}`
          },
          body: JSON.stringify({ status: newStatus })
        }
      );
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Error al actualizar estado');
      }
      await loadQuotes();
      showStatusModal = false;
      showQuoteDetail = false;
      quoteForStatus = null;
      successMessage = `Cotización ${newStatus === 'approved' ? 'aprobada' : 'rechazada'} correctamente`;
      setTimeout(() => successMessage = '', 3000);
    } catch (error: any) {
      errorMessage = error.message || 'Error al cambiar estado';
    }
  }

  function startEditPrices() {
    if (!selectedQuote) return;
    draftPrices = {};
    for (const line of selectedQuote.lines) {
      draftPrices[line.id] = line.unit_price;
    }
    editingPrices = true;
  }

  async function savePrices() {
    if (!selectedQuote) return;
    savingPrices = true;
    try {
      const updates = selectedQuote.lines
        .filter(l => draftPrices[l.id] !== undefined && draftPrices[l.id] !== l.unit_price)
        .map(l =>
          fetch(
            `${import.meta.env.VITE_API_BASE_URL}/api/v1/admin/quotes/${selectedQuote!.id}/lines/${l.id}/price`,
            {
              method: 'PUT',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${$authStore.accessToken}`
              },
              body: JSON.stringify({ unit_price: draftPrices[l.id] })
            }
          )
        );
      const results = await Promise.all(updates);
      for (const r of results) {
        if (!r.ok) throw new Error('Error al guardar precio');
      }
      // Reload quote data
      const res = await fetch(
        `${import.meta.env.VITE_API_BASE_URL}/api/v1/admin/quotes/${selectedQuote.id}`,
        { headers: { 'Authorization': `Bearer ${$authStore.accessToken}` } }
      );
      if (res.ok) {
        selectedQuote = await res.json();
        // Update in list too
        quotes = quotes.map(q => q.id === selectedQuote!.id ? selectedQuote! : q);
      }
      editingPrices = false;
      successMessage = 'Precios actualizados correctamente';
      setTimeout(() => successMessage = '', 3000);
    } catch (error: any) {
      errorMessage = error.message || 'Error al guardar precios';
    } finally {
      savingPrices = false;
    }
  }

  async function saveDetails() {
    if (!selectedQuote) return;
    savingDetails = true;
    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_BASE_URL}/api/v1/admin/quotes/${selectedQuote.id}/details`,
        {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${$authStore.accessToken}`
          },
          body: JSON.stringify({
            iva_percent: draftIva,
            fecha_vigencia: draftVigencia || null,
            comentarios_admin: draftComentarios || null
          })
        }
      );
      if (!response.ok) throw new Error('Error al guardar');
      selectedQuote = await response.json();
      quotes = quotes.map(q => q.id === selectedQuote!.id ? selectedQuote! : q);
      successMessage = 'Datos actualizados correctamente';
      setTimeout(() => successMessage = '', 3000);
    } catch (error: any) {
      errorMessage = error.message || 'Error al guardar datos';
    } finally {
      savingDetails = false;
    }
  }

  function printQuotePDF() {
    if (!selectedQuote) return;
    const q = selectedQuote;
    const ivaLabel = q.iva_percent > 0 ? `IVA (${q.iva_percent}%)` : 'IVA';
    const subtotal = q.total;
    const ivaAmt = q.iva_amount;
    const totalFinal = q.total_con_iva > 0 ? q.total_con_iva : subtotal;
    const vigencia = q.fecha_vigencia ? new Date(q.fecha_vigencia + 'T12:00:00').toLocaleDateString('es-MX', { day:'2-digit', month:'long', year:'numeric' }) : 'No especificada';
    const fechaEmision = new Date(q.created_at).toLocaleDateString('es-MX', { day:'2-digit', month:'long', year:'numeric' });

    // Pre-compute badge colors — avoids template expressions inside CSS block
    const badgeBgMap: Record<string, string> = { sent:'#dbeafe', approved:'#dcfce7', rejected:'#fee2e2', draft:'#f3f4f6' };
    const badgeColorMap: Record<string, string> = { sent:'#1d4ed8', approved:'#15803d', rejected:'#b91c1c', draft:'#374151' };
    const badgeBg = badgeBgMap[q.status] || '#f3f4f6';
    const badgeColor = badgeColorMap[q.status] || '#374151';
    // Use variable so Svelte preprocessor doesn't try to parse this as a real <style> block
    const styleTag = 'style';

    const linesRows = q.lines.map((l, i) => `
      <tr>
        <td>${i + 1}</td>
        <td>${l.description}</td>
        <td style="text-align:right">${Number(l.quantity)}</td>
        <td style="text-align:right">${l.unit_price > 0 ? fmtMXN(l.unit_price) : '<em style="color:#999">Por definir</em>'}</td>
        <td style="text-align:right">${l.unit_price > 0 ? fmtMXN(l.subtotal) : '—'}</td>
      </tr>`).join('');

    function fmtMXN(v: number) {
      return new Intl.NumberFormat('es-MX', { style:'currency', currency:'MXN' }).format(v);
    }

    const html = `<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8"/>
  <title>Cotización ${q.quote_number}</title>
  <${styleTag}>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: Arial, sans-serif; font-size: 11pt; color: #1a1a1a; padding: 20mm 18mm; }
    .header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 28px; border-bottom: 3px solid #1d4ed8; padding-bottom: 16px; }
    .logo-area h1 { font-size: 20pt; font-weight: 800; color: #1d4ed8; letter-spacing: -0.5px; }
    .logo-area p { font-size: 9pt; color: #6b7280; margin-top: 2px; }
    .doc-info { text-align: right; }
    .doc-info .quote-num { font-size: 16pt; font-weight: 700; color: #1d4ed8; }
    .doc-info .meta { font-size: 9pt; color: #6b7280; line-height: 1.6; margin-top: 4px; }
    .status-badge { display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 8pt; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;
      background: ${badgeBg};
      color: ${badgeColor};
    }
    .grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px; }
    .card { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 14px; }
    .card h3 { font-size: 8pt; font-weight: 700; text-transform: uppercase; color: #64748b; letter-spacing: 0.8px; margin-bottom: 8px; }
    .card p { font-size: 10pt; line-height: 1.6; color: #1e293b; }
    .card .company-name { font-size: 12pt; font-weight: 700; color: #0f172a; }
    table { width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 10pt; }
    thead tr { background: #1d4ed8; color: white; }
    thead th { padding: 8px 10px; text-align: left; font-weight: 600; font-size: 9pt; }
    thead th:nth-child(3), thead th:nth-child(4), thead th:nth-child(5) { text-align: right; }
    tbody tr:nth-child(even) { background: #f8fafc; }
    tbody td { padding: 7px 10px; border-bottom: 1px solid #e5e7eb; vertical-align: top; }
    tbody td:nth-child(1) { width: 30px; color: #94a3b8; font-size: 9pt; }
    tbody td:nth-child(3), tbody td:nth-child(4), tbody td:nth-child(5) { text-align: right; white-space: nowrap; }
    .totals { margin-left: auto; width: 280px; }
    .totals table { margin-bottom: 0; }
    .totals td { padding: 5px 10px; border-bottom: none; }
    .totals .total-row { background: #1d4ed8; color: white; font-weight: 700; font-size: 11pt; }
    .totals .total-row td { padding: 8px 10px; border-radius: 4px; }
    .comments { margin-top: 20px; background: #fffbeb; border: 1px solid #fde68a; border-radius: 6px; padding: 12px 14px; }
    .comments h3 { font-size: 9pt; font-weight: 700; color: #92400e; margin-bottom: 6px; text-transform: uppercase; }
    .comments p { font-size: 10pt; color: #78350f; white-space: pre-line; line-height: 1.5; }
    .footer { margin-top: 30px; text-align: center; font-size: 8pt; color: #94a3b8; border-top: 1px solid #e5e7eb; padding-top: 10px; }
    @media print { body { padding: 15mm 12mm; } }
  </${styleTag}>
</head>
<body>
  <div class="header">
    <div class="logo-area">
      <h1>CÓDIGO DE RED</h1>
      <p>Soluciones en Energía Eléctrica</p>
    </div>
    <div class="doc-info">
      <div class="quote-num">${q.quote_number}</div>
      <div class="meta">
        Emisión: ${fechaEmision}<br/>
        Vigencia: ${vigencia}<br/>
        <span class="status-badge">${{ sent:'Enviada', approved:'Aprobada', rejected:'Rechazada', draft:'Borrador', accepted:'Aceptada' }[q.status] || q.status}</span>
      </div>
    </div>
  </div>

  <div class="grid2">
    <div class="card">
      <h3>Empresa</h3>
      <p class="company-name">${q.razon_social}</p>
      ${q.rfc ? `<p>RFC: <strong>${q.rfc}</strong></p>` : ''}
      ${q.direccion ? `<p>${q.direccion}${q.ciudad ? ', ' + q.ciudad : ''}${q.estado_empresa ? ', ' + q.estado_empresa : ''}${q.codigo_postal ? ' C.P. ' + q.codigo_postal : ''}</p>` : ''}
      ${q.telefono ? `<p>Tel: ${q.telefono}</p>` : ''}
      ${q.email ? `<p>${q.email}</p>` : ''}
    </div>
    <div class="card">
      <h3>Cotización</h3>
      <p><strong>${q.title}</strong></p>
      <p>Cliente: <strong>${q.cliente_nombre}</strong></p>
      ${q.numero_transformadores ? `<p>Transformadores: ${q.numero_transformadores}</p>` : ''}
      ${q.observaciones ? `<p style="margin-top:6px;font-size:9pt;color:#64748b">${q.observaciones}</p>` : ''}
    </div>
  </div>

  <table>
    <thead>
      <tr>
        <th>#</th>
        <th>Descripción</th>
        <th style="text-align:right">Cant.</th>
        <th style="text-align:right">P. Unitario</th>
        <th style="text-align:right">Subtotal</th>
      </tr>
    </thead>
    <tbody>${linesRows}</tbody>
  </table>

  <div class="totals">
    <table>
      <tr><td>Subtotal</td><td style="text-align:right;font-weight:600">${fmtMXN(subtotal)}</td></tr>
      ${q.iva_percent > 0 ? `<tr><td>${ivaLabel}</td><td style="text-align:right">${fmtMXN(ivaAmt)}</td></tr>` : ''}
      <tr class="total-row"><td>TOTAL</td><td style="text-align:right">${fmtMXN(totalFinal)}</td></tr>
    </table>
  </div>

  ${q.comentarios_admin ? `
  <div class="comments">
    <h3>Notas y Condiciones</h3>
    <p>${q.comentarios_admin}</p>
  </div>` : ''}

  <div class="footer">
    Cotización generada el ${new Date().toLocaleDateString('es-MX', { day:'2-digit', month:'long', year:'numeric' })} — Código de Red
  </div>
</body>
</html>`;

    const win = window.open('', '_blank', 'width=900,height=700');
    if (!win) return;
    win.document.write(html);
    win.document.close();
    win.focus();
    setTimeout(() => win.print(), 600);
  }

  function getStatusColor(status: string) {
    const map: Record<string, string> = {
      draft: 'bg-gray-100 text-gray-700',
      sent: 'bg-blue-100 text-blue-700',
      approved: 'bg-green-100 text-green-700',
      rejected: 'bg-red-100 text-red-700',
      accepted: 'bg-emerald-100 text-emerald-700',
    };
    return map[status] || 'bg-gray-100 text-gray-700';
  }

  function getStatusLabel(status: string) {
    const map: Record<string, string> = {
      draft: 'Borrador',
      sent: 'Enviada',
      approved: 'Aprobada',
      rejected: 'Rechazada',
      accepted: 'Aceptada',
    };
    return map[status] || status;
  }

  function formatCurrency(value: number) {
    return new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(value);
  }

  function formatDate(date: string) {
    return new Date(date).toLocaleDateString('es-MX', { day: '2-digit', month: 'short', year: 'numeric' });
  }

  // ── Funciones de catálogo ───────────────────────────────

  async function loadItems() {
    try {
      loading = true;
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/admin/quote-items/`, {
        headers: {
          'Authorization': `Bearer ${$authStore.accessToken}`
        }
      });

      if (!response.ok) throw new Error('Error al cargar conceptos');
      
      const data = await response.json();
      // El endpoint devuelve {items: [...], total: X, page: Y, page_size: Z}
      items = data.items || [];
      hasLoadedItems = true;
    } catch (error: any) {
      console.error('Error:', error);
      errorMessage = error.message || 'Error al cargar conceptos';
      items = [];
    } finally {
      loading = false;
    }
  }

  function openCreateModal() {
    isEditing = false;
    currentItem = null;
    form = {
      code: '',
      name: '',
      description: '',
      category: 'MATERIALES',
      unit: 'PIEZA',
      base_price: 0
    };
    showModal = true;
  }

  function openEditModal(item: QuoteItem) {
    isEditing = true;
    currentItem = item;
    form = {
      code: item.code,
      name: item.name,
      description: item.description || '',
      category: item.category,
      unit: item.unit,
      base_price: item.base_price
    };
    showModal = true;
  }

  function closeModal() {
    showModal = false;
    currentItem = null;
    errorMessage = '';
  }

  async function handleSubmit() {
    try {
      errorMessage = '';
      const url = isEditing
        ? `${import.meta.env.VITE_API_BASE_URL}/api/v1/admin/quote-items/${currentItem!.id}/`
        : `${import.meta.env.VITE_API_BASE_URL}/api/v1/admin/quote-items/`;
      
      const method = isEditing ? 'PUT' : 'POST';

      const payload = {
        ...form,
        notes: null,
        is_active: true
      };

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${$authStore.accessToken}`
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Error al guardar');
      }

      await loadItems();
      closeModal();
      successMessage = isEditing ? 'Concepto actualizado correctamente' : 'Concepto creado correctamente';
      setTimeout(() => successMessage = '', 3000);
    } catch (error: any) {
      console.error('Error:', error);
      errorMessage = error.message || 'Error al guardar el concepto';
    }
  }

  function confirmDelete(item: QuoteItem) {
    itemToDelete = item;
    showDeleteModal = true;
  }

  async function handleDelete() {
    if (!itemToDelete) return;

    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_BASE_URL}/api/v1/admin/quote-items/${itemToDelete.id}/`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${$authStore.accessToken}`
          }
        }
      );

      if (!response.ok) throw new Error('Error al eliminar');

      await loadItems();
      showDeleteModal = false;
      itemToDelete = null;
      successMessage = 'Concepto desactivado correctamente';
      setTimeout(() => successMessage = '', 3000);
    } catch (error: any) {
      console.error('Error:', error);
      errorMessage = error.message || 'Error al desactivar el concepto';
    }
  }

  function getCategoryLabel(value: string) {
    return categories.find(c => c.value === value)?.label || value;
  }

  function getUnitLabel(value: string) {
    return units.find(u => u.value === value)?.label || value;
  }

  function formatPrice(price: number) {
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency: 'MXN'
    }).format(price);
  }
</script>

<div class="p-6">
  <!-- Header -->
  <div class="mb-6">
    <h1 class="text-2xl font-bold text-gray-900">Gestión de Cotizaciones</h1>
    <p class="text-gray-600 mt-1">Administra las cotizaciones recibidas y configura el catálogo de conceptos</p>
  </div>

  <!-- Tabs -->
  <div class="mb-6">
    <div class="border-b border-gray-200">
      <nav class="-mb-px flex space-x-8">
        <button
          onclick={() => activeTab = 'cotizaciones'}
          class="whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors"
          class:border-blue-600={activeTab === 'cotizaciones'}
          class:text-blue-600={activeTab === 'cotizaciones'}
          class:border-transparent={activeTab !== 'cotizaciones'}
          class:text-gray-500={activeTab !== 'cotizaciones'}
          class:hover:text-gray-700={activeTab !== 'cotizaciones'}
          class:hover:border-gray-300={activeTab !== 'cotizaciones'}
        >
          <div class="flex items-center gap-2">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 14l6-6m-5.5.5h.01m4.99 5h.01M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16l3.5-2 3.5 2 3.5-2 3.5 2z"/>
            </svg>
            Cotizaciones Recibidas
          </div>
        </button>
        <button
          onclick={() => {
            activeTab = 'conceptos';
            if (!hasLoadedItems) {
              loadItems();
              hasLoadedItems = true;
            }
          }}
          class="whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors"
          class:border-blue-600={activeTab === 'conceptos'}
          class:text-blue-600={activeTab === 'conceptos'}
          class:border-transparent={activeTab !== 'conceptos'}
          class:text-gray-500={activeTab !== 'conceptos'}
          class:hover:text-gray-700={activeTab !== 'conceptos'}
          class:hover:border-gray-300={activeTab !== 'conceptos'}
        >
          <div class="flex items-center gap-2">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
            </svg>
            Catálogo de Conceptos
          </div>
        </button>
      </nav>
    </div>
  </div>

  <!-- Messages -->
  {#if errorMessage}
    <div class="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3">
      <svg class="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
      </svg>
      <span class="text-red-800">{errorMessage}</span>
      <button onclick={() => errorMessage = ''} class="ml-auto text-red-600 hover:text-red-800">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
        </svg>
      </button>
    </div>
  {/if}

  {#if successMessage}
    <div class="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg flex items-center gap-3">
      <svg class="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
      </svg>
      <span class="text-green-800">{successMessage}</span>
    </div>
  {/if}

  <!-- Content -->
  {#if activeTab === 'cotizaciones'}
    <!-- Filtros -->
    <div class="bg-white rounded-lg shadow-sm p-4 mb-6">
      <div class="flex gap-4 flex-wrap items-center">
        <div class="flex-1 min-w-[280px]">
          <input
            type="text"
            bind:value={quotesSearch}
            onkeydown={(e) => { if (e.key === 'Enter') { quotesPage = 1; loadQuotes(); } }}
            placeholder="Buscar por folio o título..."
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
        <!-- Tabs de estado -->
        <div class="flex gap-1 bg-gray-100 rounded-lg p-1">
          {#each [['sent','Enviadas'],['approved','Aprobadas'],['accepted','Aceptadas'],['rejected','Rechazadas'],['all','Todas']] as [val, label]}
            <button
              onclick={() => { quotesStatus = val; quotesPage = 1; loadQuotes(); }}
              class="px-3 py-1.5 text-sm rounded-md transition-colors"
              class:bg-white={quotesStatus === val}
              class:shadow={quotesStatus === val}
              class:font-medium={quotesStatus === val}
              class:text-gray-900={quotesStatus === val}
              class:text-gray-500={quotesStatus !== val}
            >
              {label}
            </button>
          {/each}
        </div>
        <button
          onclick={() => { quotesPage = 1; loadQuotes(); }}
          class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
        >
          Buscar
        </button>
      </div>
    </div>

    <!-- Tabla -->
    {#if quotesLoading}
      <div class="text-center py-12">
        <div class="inline-block animate-spin rounded-full h-12 w-12 border-4 border-gray-300 border-t-blue-600"></div>
        <p class="mt-4 text-gray-600">Cargando cotizaciones...</p>
      </div>
    {:else if quotes.length === 0}
      <div class="bg-white rounded-lg shadow-sm p-12 text-center">
        <svg class="w-16 h-16 mx-auto text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
        </svg>
        <h3 class="text-lg font-medium text-gray-900 mb-1">Sin cotizaciones</h3>
        <p class="text-gray-500 text-sm">
          {quotesStatus === 'sent' ? 'No hay cotizaciones enviadas pendientes de revisión.' : 'No se encontraron cotizaciones con este filtro.'}
        </p>
      </div>
    {:else}
      <div class="bg-white rounded-lg shadow-sm overflow-x-auto">
        <div class="px-6 py-3 border-b border-gray-100 flex items-center justify-between">
          <span class="text-sm text-gray-500">{quotesTotal} cotización{quotesTotal !== 1 ? 'es' : ''}</span>
        </div>
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Folio</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Título</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Empresa / Cliente</th>
              <th class="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Conceptos</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fecha</th>
              <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            {#each quotes as q}
              <tr class="hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap">
                  <span class="text-sm font-mono font-medium text-gray-900">{q.quote_number}</span>
                </td>
                <td class="px-6 py-4">
                  <div class="text-sm font-medium text-gray-900 max-w-xs truncate">{q.title}</div>
                  {#if q.numero_transformadores}
                    <div class="text-xs text-gray-500">{q.numero_transformadores} transformadores</div>
                  {/if}
                </td>
                <td class="px-6 py-4">
                  <div class="text-sm font-medium text-gray-900">{q.razon_social}</div>
                  <div class="text-xs text-gray-500">{q.cliente_nombre}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-center">
                  <span class="text-sm font-medium text-gray-700">{q.lines.length}</span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span class="px-2 py-1 text-xs rounded-full {getStatusColor(q.status)}">
                    {getStatusLabel(q.status)}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {formatDate(q.created_at)}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-right">
                  <div class="flex items-center justify-end gap-1">
                    <button
                      onclick={() => openQuoteDetail(q)}
                      class="inline-flex items-center px-3 py-1.5 text-sm font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 rounded-md"
                      title="Ver detalle"
                    >
                      <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                      </svg>
                      Ver
                    </button>
                    {#if q.status === 'sent'}
                      <button
                        onclick={() => openStatusModal(q, 'approved')}
                        class="inline-flex items-center px-3 py-1.5 text-sm font-medium text-green-700 bg-green-50 hover:bg-green-100 rounded-md"
                      >
                        <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                        </svg>
                        Aprobar
                      </button>
                      <button
                        onclick={() => openStatusModal(q, 'rejected')}
                        class="inline-flex items-center px-3 py-1.5 text-sm font-medium text-red-700 bg-red-50 hover:bg-red-100 rounded-md"
                      >
                        <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                        </svg>
                        Rechazar
                      </button>
                    {/if}
                  </div>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}


  {:else if activeTab === 'conceptos'}
    <!-- Catálogo de Conceptos -->
    <div class="flex justify-between items-center mb-6">
      <div>
        <h2 class="text-xl font-bold text-gray-900">Catálogo de Conceptos</h2>
        <p class="text-gray-600 mt-1">Configura los conceptos disponibles para las cotizaciones</p>
      </div>
      <button
        onclick={openCreateModal}
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
        </svg>
        Nuevo Concepto
      </button>
    </div>

    <!-- Filters -->
    <div class="bg-white rounded-lg shadow-sm p-4 mb-6">
      <div class="flex gap-4 flex-wrap">
        <div class="flex-1 min-w-[300px]">
          <input
            type="text"
            bind:value={searchTerm}
            placeholder="Buscar por código, nombre o descripción..."
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
        <select
          bind:value={filterCategory}
          class="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="all">Todas las categorías</option>
          {#each categories as cat}
            <option value={cat.value}>{cat.label}</option>
          {/each}
        </select>
        <div class="flex gap-2">
          <button
            onclick={() => filterActive = 'all'}
            class="px-4 py-2 rounded-lg border"
            class:bg-blue-600={filterActive === 'all'}
            class:text-white={filterActive === 'all'}
            class:border-blue-600={filterActive === 'all'}
            class:bg-white={filterActive !== 'all'}
            class:text-gray-700={filterActive !== 'all'}
          >
            Todos
          </button>
          <button
            onclick={() => filterActive = 'active'}
            class="px-4 py-2 rounded-lg border"
            class:bg-blue-600={filterActive === 'active'}
            class:text-white={filterActive === 'active'}
            class:border-blue-600={filterActive === 'active'}
            class:bg-white={filterActive !== 'active'}
            class:text-gray-700={filterActive !== 'active'}
          >
            Activos
          </button>
          <button
            onclick={() => filterActive = 'inactive'}
            class="px-4 py-2 rounded-lg border"
            class:bg-blue-600={filterActive === 'inactive'}
            class:text-white={filterActive === 'inactive'}
            class:border-blue-600={filterActive === 'inactive'}
            class:bg-white={filterActive !== 'inactive'}
            class:text-gray-700={filterActive !== 'inactive'}
          >
            Inactivos
          </button>
        </div>
      </div>
    </div>

    <!-- Table -->
    {#if loading}
      <div class="text-center py-12">
        <div class="inline-block animate-spin rounded-full h-12 w-12 border-4 border-gray-300 border-t-blue-600"></div>
        <p class="mt-4 text-gray-600">Cargando conceptos...</p>
      </div>
    {:else if filteredItems.length === 0}
      <div class="bg-white rounded-lg shadow-sm p-12 text-center">
        <svg class="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
        </svg>
        <p class="text-gray-600">No se encontraron conceptos</p>
      </div>
    {:else}
      <div class="bg-white rounded-lg shadow-sm overflow-hidden">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Código</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Concepto</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Categoría</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Unidad</th>
              <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Precio Base</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
              <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            {#each filteredItems as item}
              <tr class="hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="text-sm font-mono font-medium text-gray-900">{item.code}</div>
                </td>
                <td class="px-6 py-4">
                  <div class="text-sm font-medium text-gray-900">{item.name}</div>
                  {#if item.description}
                    <div class="text-sm text-gray-500 truncate max-w-xs">{item.description}</div>
                  {/if}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span class="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                    {getCategoryLabel(item.category)}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {getUnitLabel(item.unit)}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right font-medium">
                  {formatPrice(item.base_price)}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span class="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full"
                    class:bg-green-100={item.is_active}
                    class:text-green-800={item.is_active}
                    class:bg-red-100={!item.is_active}
                    class:text-red-800={!item.is_active}
                  >
                    {item.is_active ? 'Activo' : 'Inactivo'}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <div class="flex items-center justify-end gap-2">
                    <button
                      onclick={() => openEditModal(item)}
                      class="p-1.5 text-blue-600 hover:text-blue-900 hover:bg-blue-50 rounded"
                      title="Editar"
                    >
                      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                      </svg>
                    </button>
                    {#if item.is_active}
                      <button
                        onclick={() => confirmDelete(item)}
                        class="p-1.5 text-red-600 hover:text-red-900 hover:bg-red-50 rounded"
                        title="Desactivar"
                      >
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                        </svg>
                      </button>
                    {/if}
                  </div>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}
  {/if}
</div>

<!-- Create/Edit Modal -->
{#if showModal}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
      <div class="p-6">
        <div class="flex justify-between items-center mb-6">
          <h2 class="text-2xl font-bold text-gray-900">
            {isEditing ? 'Editar Concepto' : 'Nuevo Concepto'}
          </h2>
          <button onclick={closeModal} class="text-gray-400 hover:text-gray-600">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>

        {#if errorMessage}
          <div class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-800 text-sm">
            {errorMessage}
          </div>
        {/if}

        <form onsubmit={(e) => { e.preventDefault(); handleSubmit(); }} class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Código *</label>
              <input
                type="text"
                bind:value={form.code}
                required
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono"
                placeholder="Ej: MAT-001"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Categoría *</label>
              <select
                bind:value={form.category}
                required
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                {#each categories as cat}
                  <option value={cat.value}>{cat.label}</option>
                {/each}
              </select>
            </div>

            <div class="col-span-2">
              <label class="block text-sm font-medium text-gray-700 mb-1">Nombre *</label>
              <input
                type="text"
                bind:value={form.name}
                required
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Ej: Cemento Portland"
              />
            </div>

            <div class="col-span-2">
              <label class="block text-sm font-medium text-gray-700 mb-1">Descripción</label>
              <textarea
                bind:value={form.description}
                rows="3"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Descripción detallada del concepto..."
              ></textarea>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Unidad *</label>
              <select
                bind:value={form.unit}
                required
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                {#each units as unit}
                  <option value={unit.value}>{unit.label}</option>
                {/each}
              </select>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Precio Base *</label>
              <div class="relative">
                <span class="absolute left-3 top-2 text-gray-500">$</span>
                <input
                  type="number"
                  bind:value={form.base_price}
                  required
                  min="0"
                  step="0.01"
                  class="w-full pl-7 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="0.00"
                />
              </div>
            </div>
          </div>

          <div class="flex justify-end gap-3 mt-6 pt-6 border-t border-gray-200">
            <button
              type="button"
              onclick={closeModal}
              class="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              {isEditing ? 'Actualizar' : 'Crear'} Concepto
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
{/if}

<!-- Delete Confirmation Modal -->
{#if showDeleteModal && itemToDelete}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
      <h3 class="text-lg font-bold text-gray-900 mb-4">Confirmar Desactivación</h3>
      <p class="text-gray-600 mb-6">
        ¿Estás seguro de que deseas desactivar el concepto <strong>{itemToDelete.code} - {itemToDelete.name}</strong>?
        Este concepto ya no estará disponible para nuevas cotizaciones.
      </p>
      <div class="flex justify-end gap-3">
        <button
          onclick={() => { showDeleteModal = false; itemToDelete = null; }}
          class="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
        >
          Cancelar
        </button>
        <button
          onclick={handleDelete}
          class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
        >
          Desactivar
        </button>
      </div>
    </div>
  </div>
{/if}

<!-- Quote Detail Modal -->
{#if showQuoteDetail && selectedQuote}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
      <div class="p-6">

        <!-- Header -->
        <div class="flex justify-between items-start mb-6">
          <div>
            <h2 class="text-xl font-bold text-gray-900">{selectedQuote.quote_number}</h2>
            <p class="text-gray-600 mt-0.5">{selectedQuote.title}</p>
          </div>
          <div class="flex items-center gap-3">
            <span class="px-3 py-1 text-sm rounded-full {getStatusColor(selectedQuote.status)}">
              {getStatusLabel(selectedQuote.status)}
            </span>
            <button
              onclick={printQuotePDF}
              title="Imprimir / Guardar PDF"
              class="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-md"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z"/>
              </svg>
              PDF
            </button>
            <button onclick={() => { showQuoteDetail = false; editingPrices = false; }} class="text-gray-400 hover:text-gray-600">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>
        </div>

        <!-- Info: 2 columnas (Empresa | Cliente) -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <!-- Empresa -->
          <div class="bg-gray-50 rounded-lg p-4">
            <h3 class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Empresa</h3>
            <div class="space-y-1.5 text-sm">
              <div class="font-semibold text-gray-900">{selectedQuote.razon_social}</div>
              {#if selectedQuote.rfc}
                <div class="text-gray-600">RFC: <span class="font-mono">{selectedQuote.rfc}</span></div>
              {/if}
              {#if selectedQuote.direccion || selectedQuote.ciudad}
                <div class="text-gray-600 flex items-start gap-1 mt-1">
                  <svg class="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/>
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/>
                  </svg>
                  <span>
                    {#if selectedQuote.direccion}{selectedQuote.direccion}{/if}
                    {#if selectedQuote.ciudad}{selectedQuote.direccion ? ', ' : ''}{selectedQuote.ciudad}{/if}
                    {#if selectedQuote.estado_empresa}, {selectedQuote.estado_empresa}{/if}
                    {#if selectedQuote.codigo_postal} C.P. {selectedQuote.codigo_postal}{/if}
                  </span>
                </div>
              {/if}
              {#if selectedQuote.telefono}
                <div class="text-gray-600">Tel: {selectedQuote.telefono}</div>
              {/if}
              {#if selectedQuote.email}
                <div class="text-gray-600">{selectedQuote.email}</div>
              {/if}
            </div>
          </div>

          <!-- Cliente / detalles cotización -->
          <div class="bg-gray-50 rounded-lg p-4">
            <h3 class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Cliente</h3>
            <div class="space-y-1.5 text-sm">
              <div class="font-semibold text-gray-900">{selectedQuote.cliente_nombre}</div>
              <div class="text-gray-600">Fecha solicitud: <span class="font-medium">{formatDate(selectedQuote.created_at)}</span></div>
              {#if selectedQuote.numero_transformadores}
                <div class="text-gray-600">Transformadores: <span class="font-medium">{selectedQuote.numero_transformadores}</span></div>
              {/if}
            </div>
          </div>
        </div>

        {#if selectedQuote.observaciones}
          <div class="mb-5">
            <h3 class="text-sm font-medium text-gray-700 mb-1">Observaciones del cliente</h3>
            <p class="text-sm text-gray-600 bg-yellow-50 border border-yellow-200 rounded-lg p-3 whitespace-pre-line">{selectedQuote.observaciones}</p>
          </div>
        {/if}

        <!-- Panel admin: IVA, vigencia, comentarios -->
        <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-5">
          <h3 class="text-xs font-semibold text-blue-700 uppercase tracking-wider mb-3">Configuración de cotización</h3>
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1">IVA aplicable</label>
              <select
                bind:value={draftIva}
                class="w-full text-sm border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-400 focus:border-transparent bg-white"
              >
                <option value={0}>Sin IVA (0%)</option>
                <option value={8}>8%</option>
                <option value={16}>16%</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1">Vigencia hasta</label>
              <input
                type="date"
                bind:value={draftVigencia}
                class="w-full text-sm border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-400 focus:border-transparent bg-white"
              />
            </div>
            <div class="flex items-end">
              <button
                onclick={saveDetails}
                disabled={savingDetails}
                class="w-full inline-flex items-center justify-center gap-1.5 px-3 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md disabled:opacity-60"
              >
                {#if savingDetails}
                  <svg class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
                  </svg>
                  Guardando...
                {:else}
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                  </svg>
                  Guardar cambios
                {/if}
              </button>
            </div>
          </div>
          <div class="mt-3">
            <label class="block text-xs font-medium text-gray-600 mb-1">Comentarios / Condiciones para el cliente</label>
            <textarea
              bind:value={draftComentarios}
              rows="3"
              placeholder="Ej: Precios sujetos a cambio, incluye mano de obra, garantía de 6 meses..."
              class="w-full text-sm border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-400 focus:border-transparent resize-none bg-white"
            ></textarea>
          </div>
        </div>

        <!-- Conceptos + edición de precios -->
        <div class="flex items-center justify-between mb-3">
          <h3 class="text-sm font-medium text-gray-700">Conceptos solicitados ({selectedQuote.lines.length})</h3>
          {#if !editingPrices}
            <button
              onclick={startEditPrices}
              class="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 rounded-md"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
              </svg>
              Editar precios
            </button>
          {:else}
            <div class="flex gap-2">
              <button
                onclick={() => editingPrices = false}
                class="px-3 py-1.5 text-sm border border-gray-300 rounded-md text-gray-600 hover:bg-gray-50"
                disabled={savingPrices}
              >
                Cancelar
              </button>
              <button
                onclick={savePrices}
                disabled={savingPrices}
                class="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md disabled:opacity-60"
              >
                {#if savingPrices}
                  <svg class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
                  </svg>
                  Guardando...
                {:else}
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                  </svg>
                  Guardar precios
                {/if}
              </button>
            </div>
          {/if}
        </div>

        {#if selectedQuote.lines.length === 0}
          <p class="text-sm text-gray-400 italic">Sin conceptos</p>
        {:else}
          <div class="overflow-x-auto rounded-lg border border-gray-200">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Descripción</th>
                  <th class="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase w-20">Cant.</th>
                  <th class="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase w-36">Precio Unit.</th>
                  <th class="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase w-32">Subtotal</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-100">
                {#each selectedQuote.lines as line, i}
                  <tr class={i % 2 === 0 ? '' : 'bg-gray-50/50'}>
                    <td class="px-4 py-2.5 text-sm text-gray-900">{line.description}</td>
                    <td class="px-4 py-2.5 text-sm text-gray-700 text-right">{line.quantity}</td>
                    <td class="px-4 py-2.5 text-right">
                      {#if editingPrices}
                        <div class="flex items-center justify-end">
                          <span class="text-gray-400 text-sm mr-1">$</span>
                          <input
                            type="number"
                            min="0"
                            step="0.01"
                            bind:value={draftPrices[line.id]}
                            class="w-28 text-right px-2 py-1 text-sm border border-blue-300 rounded focus:ring-2 focus:ring-blue-400 focus:border-transparent"
                          />
                        </div>
                      {:else if line.unit_price > 0}
                        <span class="text-sm text-gray-900">{formatCurrency(line.unit_price)}</span>
                      {:else}
                        <span class="text-xs text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full">Por definir</span>
                      {/if}
                    </td>
                    <td class="px-4 py-2.5 text-sm font-medium text-right">
                      {#if editingPrices}
                        <span class="text-gray-500">{formatCurrency((draftPrices[line.id] || 0) * line.quantity)}</span>
                      {:else if line.unit_price > 0}
                        <span class="text-gray-900">{formatCurrency(line.subtotal)}</span>
                      {:else}
                        <span class="text-gray-400">—</span>
                      {/if}
                    </td>
                  </tr>
                {/each}
              </tbody>
              <tfoot class="bg-gray-50 border-t-2 border-gray-200">
                <tr>
                  <td colspan="3" class="px-4 py-2 text-sm text-gray-600 text-right">Subtotal:</td>
                  <td class="px-4 py-2 text-sm font-medium text-gray-900 text-right">{formatCurrency(modalSubtotal)}</td>
                </tr>
                {#if modalIvaPct > 0}
                  <tr>
                    <td colspan="3" class="px-4 py-2 text-sm text-gray-600 text-right">IVA ({modalIvaPct}%):</td>
                    <td class="px-4 py-2 text-sm text-gray-900 text-right">{formatCurrency(modalIvaAmt)}</td>
                  </tr>
                {/if}
                <tr class="border-t border-gray-200">
                  <td colspan="3" class="px-4 py-2.5 text-sm font-bold text-gray-900 text-right">TOTAL{modalIvaPct > 0 ? ' CON IVA' : ''}:</td>
                  <td class="px-4 py-2.5 text-base font-bold text-gray-900 text-right">{formatCurrency(modalTotal)}</td>
                </tr>
              </tfoot>
            </table>
          </div>
        {/if}

        <!-- Footer actions -->
        {#if selectedQuote.status === 'sent'}
          <div class="flex justify-end gap-3 mt-6 pt-5 border-t border-gray-200">
            <button
              onclick={() => openStatusModal(selectedQuote!, 'rejected')}
              class="px-4 py-2 border border-red-300 text-red-700 rounded-lg hover:bg-red-50 flex items-center gap-2"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
              Rechazar
            </button>
            <button
              onclick={() => openStatusModal(selectedQuote!, 'approved')}
              class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
              </svg>
              Aprobar
            </button>
          </div>
        {/if}

      </div>
    </div>
  </div>
{/if}


<!-- Status change confirmation modal -->
{#if showStatusModal && quoteForStatus}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60] p-4">
    <div class="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
      <div class="flex items-start gap-4 mb-4">
        <div class="w-12 h-12 rounded-full flex items-center justify-center flex-shrink-0
          {newStatus === 'approved' ? 'bg-green-100' : 'bg-red-100'}">
          {#if newStatus === 'approved'}
            <svg class="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
            </svg>
          {:else}
            <svg class="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          {/if}
        </div>
        <div>
          <h3 class="text-lg font-medium text-gray-900">
            {newStatus === 'approved' ? 'Aprobar cotización' : 'Rechazar cotización'}
          </h3>
          <p class="text-sm text-gray-600 mt-1">
            {quoteForStatus.quote_number} — {quoteForStatus.title}
          </p>
          <p class="text-sm text-gray-500 mt-2">
            {newStatus === 'approved'
              ? 'El cliente podrá ver que su cotización fue aprobada.'
              : 'El cliente será notificado de que su cotización fue rechazada.'}
          </p>
        </div>
      </div>
      <div class="flex justify-end gap-3 mt-4">
        <button
          onclick={() => { showStatusModal = false; quoteForStatus = null; }}
          class="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
        >
          Cancelar
        </button>
        <button
          onclick={confirmStatusChange}
          class="px-4 py-2 text-white rounded-lg
            {newStatus === 'approved' ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'}"
        >
          {newStatus === 'approved' ? 'Sí, aprobar' : 'Sí, rechazar'}
        </button>
      </div>
    </div>
  </div>
{/if}

