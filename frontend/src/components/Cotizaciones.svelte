<script lang="ts">
  import { onMount } from 'svelte';
  import { authStore } from '../stores/auth';

  interface Company {
    id: number;
    razon_social: string;
    rfc: string;
    tipo_centro_carga?: string;
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
  }

  interface QuoteLine {
    quote_item_id: number | null;
    description: string;
    quantity: number;
    unit_price: number;
    subtotal?: number;
  }

  interface Quote {
    id: number;
    quote_number: string;
    title: string;
    company_id: number;
    razon_social: string;
    tipo_centro_carga: string | null;
    numero_transformadores: number | null;
    observaciones: string | null;
    status: string;
    total: number;
    iva_percent: number;
    iva_amount: number;
    total_con_iva: number;
    fecha_vigencia: string | null;
    comentarios_admin: string | null;
    created_at: string;
    lines: QuoteLine[];
  }

  let quotes = $state<Quote[]>([]);
  let companies = $state<Company[]>([]);
  let quoteItems = $state<QuoteItem[]>([]);
  let loading = $state(true);
  let loadingItems = $state(false);
  let showModal = $state(false);
  let showItemsModal = $state(false);
  let showDeleteModal = $state(false);
  let showSendModal = $state(false);
  let isEditing = $state(false);
  let editingQuoteId = $state<number | null>(null);
  let quoteToDelete = $state<Quote | null>(null);
  let quoteToSend = $state<Quote | null>(null);
  let showApprovedDetail = $state(false);
  let selectedApprovedQuote = $state<Quote | null>(null);
  let showAcceptModal = $state(false);
  let quoteToAccept = $state<Quote | null>(null);
  let acceptingQuote = $state(false);
  let errorMessage = $state('');
  let successMessage = $state('');
  let searchTerm = $state('');

  // Formulario
  let selectedCompany = $state<Company | null>(null);
  let formTitle = $state('');
  let numeroTransformadores = $state<number>(0);
  let observaciones = $state('');
  let lines = $state<QuoteLine[]>([]);
  let itemSearchTerm = $state('');
  let useCustomConcept = $state(false);
  let customDescription = $state('');
  let customQuantity = $state(1);

  const filteredItems = $derived(
    quoteItems.filter(item => 
      item.is_active && (
        item.code.toLowerCase().includes(itemSearchTerm.toLowerCase()) ||
        item.name.toLowerCase().includes(itemSearchTerm.toLowerCase())
      )
    )
  );

  onMount(() => {
    loadQuotes();
    loadCompanies();
  });

  async function loadQuotes() {
    try {
      loading = true;
      const response = await authStore.fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/quotes/`, {
        headers: { 'Authorization': `Bearer ${$authStore.accessToken}` }
      });

      if (!response.ok) throw new Error('Error al cargar cotizaciones');
      
      const data = await response.json();
      quotes = data.quotes || [];
    } catch (error: any) {
      console.error('Error:', error);
      errorMessage = error.message || 'Error al cargar cotizaciones';
    } finally {
      loading = false;
    }
  }

  async function loadCompanies() {
    try {
      const response = await authStore.fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/companies/`, {
        headers: { 'Authorization': `Bearer ${$authStore.accessToken}` }
      });

      if (!response.ok) throw new Error('Error al cargar empresas');
      
      const data = await response.json();
      companies = data.companies || [];
    } catch (error: any) {
      console.error('Error:', error);
    }
  }

  async function loadQuoteItems() {
    try {
      loadingItems = true;
      const response = await authStore.fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/quotes/catalog`, {
        headers: { 'Authorization': `Bearer ${$authStore.accessToken}` }
      });

      if (!response.ok) throw new Error('Error al cargar conceptos');
      
      const data = await response.json();
      quoteItems = data.items || [];
    } catch (error: any) {
      console.error('Error:', error);
      errorMessage = error.message || 'Error al cargar conceptos';
    } finally {
      loadingItems = false;
    }
  }

  function openCreateModal() {
    isEditing = false;
    editingQuoteId = null;
    selectedCompany = null;
    formTitle = '';
    numeroTransformadores = 0;
    observaciones = '';
    lines = [];
    useCustomConcept = false;
    customDescription = '';
    customQuantity = 1;
    showModal = true;
  }

  function openEditModal(quote: Quote) {
    isEditing = true;
    editingQuoteId = quote.id;
    
    // Buscar la empresa
    const company = companies.find(c => c.id === quote.company_id);
    selectedCompany = company ? {
      ...company,
      tipo_centro_carga: quote.tipo_centro_carga
    } : null;
    
    formTitle = quote.title;
    numeroTransformadores = quote.numero_transformadores || 0;
    observaciones = quote.observaciones || '';
    lines = quote.lines.map(line => ({
      quote_item_id: line.quote_item_id,
      description: line.description,
      quantity: line.quantity,
      unit_price: line.unit_price
    }));
    
    showModal = true;
  }

  function selectCompany(company: Company) {
    selectedCompany = company;
  }

  function openItemsModal() {
    if (!selectedCompany) {
      errorMessage = 'Primero selecciona una empresa';
      return;
    }
    if (quoteItems.length === 0) {
      loadQuoteItems();
    }
    showItemsModal = true;
  }

  function addItem(item: QuoteItem) {
    lines = [...lines, {
      quote_item_id: item.id,
      description: item.name,
      quantity: 1,
      unit_price: item.base_price
    }];
    showItemsModal = false;
    itemSearchTerm = '';
  }

  function addCustomConcept() {
    if (!customDescription.trim()) {
      errorMessage = 'Ingresa una descripción para el concepto';
      return;
    }

    lines = [...lines, {
      quote_item_id: null,
      description: customDescription,
      quantity: customQuantity,
      unit_price: 0
    }];

    // Reset campos
    customDescription = '';
    customQuantity = 1;
    useCustomConcept = false;
    errorMessage = '';
  }

  function removeLine(index: number) {
    lines = lines.filter((_, i) => i !== index);
  }

  function updateLineQuantity(index: number, quantity: number) {
    lines[index].quantity = quantity;
    lines = [...lines];
  }

  function updateLinePrice(index: number, price: number) {
    lines[index].unit_price = price;
    lines = [...lines];
  }

  const totalQuote = $derived(
    lines.reduce((sum, line) => sum + (line.quantity * line.unit_price), 0)
  );

  async function handleSubmit() {
    if (!selectedCompany) {
      errorMessage = 'Selecciona una empresa';
      return;
    }

    if (!formTitle.trim()) {
      errorMessage = 'Ingresa un título';
      return;
    }

    if (lines.length === 0) {
      errorMessage = 'Agrega al menos un concepto';
      return;
    }

    try {
      errorMessage = '';
      
      const url = isEditing 
        ? `${import.meta.env.VITE_API_BASE_URL}/api/v1/quotes/${editingQuoteId}`
        : `${import.meta.env.VITE_API_BASE_URL}/api/v1/quotes/`;
      
      const method = isEditing ? 'PUT' : 'POST';
      
      const body = isEditing 
        ? {
            title: formTitle,
            numero_transformadores: numeroTransformadores || null,
            observaciones: observaciones || null,
            lines: lines
          }
        : {
            company_id: selectedCompany.id,
            title: formTitle,
            numero_transformadores: numeroTransformadores || null,
            observaciones: observaciones || null,
            lines: lines
          };
      
      const response = await authStore.fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${$authStore.accessToken}`
        },
        body: JSON.stringify(body)
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Error al guardar');
      }

      await loadQuotes();
      showModal = false;
      successMessage = isEditing ? 'Cotización actualizada correctamente' : 'Cotización creada correctamente';
      setTimeout(() => successMessage = '', 3000);
    } catch (error: any) {
      console.error('Error:', error);
      errorMessage = error.message || (isEditing ? 'Error al actualizar cotización' : 'Error al crear cotización');
    }
  }

  function confirmDelete(quote: Quote) {
    quoteToDelete = quote;
    showDeleteModal = true;
  }

  async function deleteQuote() {
    if (!quoteToDelete) return;

    try {
      const response = await authStore.fetch(
        `${import.meta.env.VITE_API_BASE_URL}/api/v1/quotes/${quoteToDelete.id}`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${$authStore.accessToken}`
          }
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Error al eliminar');
      }

      await loadQuotes();
      showDeleteModal = false;
      quoteToDelete = null;
      successMessage = 'Cotización eliminada correctamente';
      setTimeout(() => successMessage = '', 3000);
    } catch (error: any) {
      console.error('Error:', error);
      errorMessage = error.message || 'Error al eliminar cotización';
      showDeleteModal = false;
    }
  }

  function confirmSend(quote: Quote) {
    quoteToSend = quote;
    showSendModal = true;
  }

  async function sendQuote() {
    if (!quoteToSend) return;

    try {
      const response = await authStore.fetch(
        `${import.meta.env.VITE_API_BASE_URL}/api/v1/quotes/${quoteToSend.id}`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${$authStore.accessToken}`
          },
          body: JSON.stringify({ status: 'sent' })
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Error al enviar');
      }

      await loadQuotes();
      showSendModal = false;
      quoteToSend = null;
      successMessage = 'Cotización enviada al administrador correctamente';
      setTimeout(() => successMessage = '', 4000);
    } catch (error: any) {
      console.error('Error:', error);
      errorMessage = error.message || 'Error al enviar cotización';
      showSendModal = false;
    }
  }

  function formatCurrency(value: number) {
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency: 'MXN'
    }).format(value);
  }

  function formatDate(date: string) {
    return new Date(date).toLocaleDateString('es-MX');
  }

  function getStatusColor(status: string) {
    const colors: Record<string, string> = {
      draft: 'bg-gray-100 text-gray-800',
      sent: 'bg-blue-100 text-blue-800',
      approved: 'bg-green-100 text-green-800',
      rejected: 'bg-red-100 text-red-800',
      accepted: 'bg-emerald-100 text-emerald-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  }

  function getStatusLabel(status: string) {
    const labels: Record<string, string> = {
      draft: 'Borrador',
      sent: 'En revisión',
      approved: 'Aprobada',
      rejected: 'Rechazada',
      accepted: 'Aceptada'
    };
    return labels[status] || status;
  }

  function openApprovedDetail(quote: Quote) {
    selectedApprovedQuote = quote;
    showApprovedDetail = true;
  }

  function printQuotePDF(quote: Quote) {
    const q = quote;
    const subtotal = Number(q.total);
    const ivaAmt = Number(q.iva_amount ?? 0);
    const totalFinal = Number(q.total_con_iva) > 0 ? Number(q.total_con_iva) : subtotal;
    const vigencia = q.fecha_vigencia
      ? new Date(q.fecha_vigencia + 'T12:00:00').toLocaleDateString('es-MX', { day: '2-digit', month: 'long', year: 'numeric' })
      : 'No especificada';
    const fechaEmision = new Date(q.created_at).toLocaleDateString('es-MX', { day: '2-digit', month: 'long', year: 'numeric' });
    const badgeBgMap: Record<string, string> = { sent: '#dbeafe', approved: '#dcfce7', rejected: '#fee2e2', draft: '#f3f4f6', accepted: '#d1fae5' };
    const badgeColorMap: Record<string, string> = { sent: '#1d4ed8', approved: '#15803d', rejected: '#b91c1c', draft: '#374151', accepted: '#065f46' };
    const badgeBg = badgeBgMap[q.status] || '#f3f4f6';
    const badgeColor = badgeColorMap[q.status] || '#374151';
    const statusLabel: Record<string, string> = { draft: 'Borrador', sent: 'En revisión', approved: 'Aprobada', rejected: 'Rechazada', accepted: 'Aceptada' };
    const styleTag = 'style';
    function fmtMXN(v: number) {
      return new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(v);
    }
    const linesRows = q.lines.map((l, i) => `
      <tr>
        <td>${i + 1}</td>
        <td>${l.description}</td>
        <td style="text-align:right">${Number(l.quantity)}</td>
        <td style="text-align:right">${l.unit_price > 0 ? fmtMXN(l.unit_price) : '<em style="color:#999">Por definir</em>'}</td>
        <td style="text-align:right">${l.unit_price > 0 ? fmtMXN(Number(l.unit_price) * Number(l.quantity)) : '—'}</td>
      </tr>`).join('');

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
    .status-badge { display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 8pt; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; background: ${badgeBg}; color: ${badgeColor}; }
    .card { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 14px; margin-bottom: 20px; }
    .card h3 { font-size: 8pt; font-weight: 700; text-transform: uppercase; color: #64748b; letter-spacing: 0.8px; margin-bottom: 8px; }
    .card p { font-size: 10pt; line-height: 1.6; color: #1e293b; }
    .card .name { font-size: 12pt; font-weight: 700; color: #0f172a; }
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
    .total-row { background: #1d4ed8; color: white; font-weight: 700; font-size: 11pt; }
    .total-row td { padding: 8px 10px; border-radius: 4px; }
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
        <span class="status-badge">${statusLabel[q.status] || q.status}</span>
      </div>
    </div>
  </div>
  <div class="card">
    <h3>Empresa</h3>
    <p class="name">${q.razon_social}</p>
    <p>${q.title}</p>
    ${q.numero_transformadores ? `<p>Transformadores: ${q.numero_transformadores}</p>` : ''}
    ${q.observaciones ? `<p style="margin-top:6px;font-size:9pt;color:#64748b">${q.observaciones}</p>` : ''}
  </div>
  <table>
    <thead>
      <tr>
        <th>#</th><th>Descripción</th>
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
      ${q.iva_percent > 0 ? `<tr><td>IVA (${q.iva_percent}%)</td><td style="text-align:right">${fmtMXN(ivaAmt)}</td></tr>` : ''}
      <tr class="total-row"><td>TOTAL</td><td style="text-align:right">${fmtMXN(totalFinal)}</td></tr>
    </table>
  </div>
  ${q.comentarios_admin ? `
  <div class="comments">
    <h3>Notas y Condiciones</h3>
    <p>${q.comentarios_admin}</p>
  </div>` : ''}
  <div class="footer">Cotización generada el ${new Date().toLocaleDateString('es-MX', { day: '2-digit', month: 'long', year: 'numeric' })} — Código de Red</div>
</body>
</html>`;
    const win = window.open('', '_blank', 'width=900,height=700');
    if (!win) return;
    win.document.write(html);
    win.document.close();
    win.focus();
    setTimeout(() => win.print(), 600);
  }

  function confirmAccept(quote: Quote) {
    quoteToAccept = quote;
    showAcceptModal = true;
  }

  async function acceptQuote() {
    if (!quoteToAccept) return;
    try {
      acceptingQuote = true;
      const response = await authStore.fetch(
        `${import.meta.env.VITE_API_BASE_URL}/api/v1/quotes/${quoteToAccept.id}`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${$authStore.accessToken}` },
          body: JSON.stringify({ status: 'accepted' })
        }
      );
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Error al aceptar');
      }
      await loadQuotes();
      showAcceptModal = false;
      showApprovedDetail = false;
      quoteToAccept = null;
      successMessage = '¡Cotización aceptada! Nos pondremos en contacto contigo pronto.';
      setTimeout(() => successMessage = '', 5000);
    } catch (error: any) {
      errorMessage = error.message || 'Error al aceptar la cotización';
      showAcceptModal = false;
    } finally {
      acceptingQuote = false;
    }
  }

  function getTipoCentroCargaLabel(tipo: string | null) {
    if (!tipo) return 'No clasificada';
    const labels: Record<string, string> = {
      TIPO_A: 'Tipo A (MT < 1MW)',
      TIPO_B: 'Tipo B (MT ≥ 1MW)',
      TIPO_C: 'Tipo C (AT)'
    };
    return labels[tipo] || tipo;
  }
</script>

<div class="p-6">
  <!-- Header -->
  <div class="flex justify-between items-center mb-6">
    <div>
      <h1 class="text-2xl font-bold text-gray-900">Cotizaciones</h1>
      <p class="text-gray-600 mt-1">Solicita cotizaciones para tus empresas</p>
    </div>
    <button
      onclick={openCreateModal}
      class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
      </svg>
      Nueva Solicitud
    </button>
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

  <!-- Quotes List -->
  {#if loading}
    <div class="text-center py-12">
      <div class="inline-block animate-spin rounded-full h-12 w-12 border-4 border-gray-300 border-t-blue-600"></div>
      <p class="mt-4 text-gray-600">Cargando cotizaciones...</p>
    </div>
  {:else if quotes.length === 0}
    <div class="bg-white rounded-lg shadow-sm p-12 text-center">
      <svg class="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
      </svg>
      <h3 class="text-lg font-medium text-gray-900 mb-2">No hay solicitudes de cotización</h3>
      <p class="text-gray-500 mb-4">Comienza solicitando tu primera cotización</p>
      <button
        onclick={openCreateModal}
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
      >
        Solicitar Primera Cotización
      </button>
    </div>
  {:else}
    <div class="bg-white rounded-lg shadow-sm overflow-x-auto">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Folio</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Título</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Empresa</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tipo Centro</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Transformadores</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Estado</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Fecha</th>
            <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase sticky right-0 bg-gray-50 shadow-[-2px_0_4px_rgba(0,0,0,0.05)]">Acciones</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          {#each quotes as quote}
            <tr class="hover:bg-gray-50">
              <td class="px-6 py-4 whitespace-nowrap text-sm font-mono font-medium text-gray-900">
                {quote.quote_number}
              </td>
              <td class="px-6 py-4">
                <div class="text-sm font-medium text-gray-900">{quote.title}</div>
              </td>
              <td class="px-6 py-4">
                <div class="text-sm text-gray-900">{quote.razon_social}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <span class="text-xs px-2 py-1 bg-purple-100 text-purple-800 rounded-full">
                  {getTipoCentroCargaLabel(quote.tipo_centro_carga)}
                </span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-center">
                {quote.numero_transformadores || '-'}
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <span class="px-2 py-1 text-xs rounded-full {getStatusColor(quote.status)}">
                  {getStatusLabel(quote.status)}
                </span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {formatDate(quote.created_at)}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-right text-sm sticky right-0 bg-white shadow-[-2px_0_4px_rgba(0,0,0,0.05)]">
                <div class="flex justify-end gap-1">
                  {#if quote.status === 'draft'}
                    <button
                      onclick={() => confirmSend(quote)}
                      class="inline-flex items-center px-3 py-1.5 text-sm font-medium text-emerald-700 bg-emerald-50 hover:bg-emerald-100 rounded-md transition-colors"
                      title="Enviar al administrador"
                    >
                      <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/>
                      </svg>
                      Enviar
                    </button>
                    <button
                      onclick={() => openEditModal(quote)}
                      class="inline-flex items-center px-3 py-1.5 text-sm font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 rounded-md transition-colors"
                      title="Editar"
                    >
                      <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                      </svg>
                      Editar
                    </button>
                    <button
                      onclick={() => confirmDelete(quote)}
                      class="inline-flex items-center px-3 py-1.5 text-sm font-medium text-red-700 bg-red-50 hover:bg-red-100 rounded-md transition-colors"
                      title="Eliminar"
                    >
                      <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                      </svg>
                      Eliminar
                    </button>
                  {:else if quote.status === 'approved'}
                    <button
                      onclick={() => openApprovedDetail(quote)}
                      class="inline-flex items-center px-3 py-1.5 text-sm font-medium text-green-700 bg-green-50 hover:bg-green-100 rounded-md transition-colors"
                      title="Ver cotización con precios"
                    >
                      <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                      </svg>
                      Ver
                    </button>
                    <button
                      onclick={() => printQuotePDF(quote)}
                      class="inline-flex items-center px-3 py-1.5 text-sm font-medium text-red-700 bg-red-50 hover:bg-red-100 rounded-md transition-colors"
                      title="Imprimir / Guardar PDF"
                    >
                      <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z"/>
                      </svg>
                      PDF
                    </button>
                    <button
                      onclick={() => confirmAccept(quote)}
                      class="inline-flex items-center px-3 py-1.5 text-sm font-medium text-white bg-emerald-600 hover:bg-emerald-700 rounded-md transition-colors"
                      title="Aceptar cotización"
                    >
                      <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                      </svg>
                      Aceptar
                    </button>
                  {:else if quote.status === 'accepted'}
                    <button
                      onclick={() => openApprovedDetail(quote)}
                      class="inline-flex items-center px-3 py-1.5 text-sm font-medium text-emerald-700 bg-emerald-50 hover:bg-emerald-100 rounded-md transition-colors"
                    >
                      <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                      </svg>
                      Ver
                    </button>
                    <button
                      onclick={() => printQuotePDF(quote)}
                      class="inline-flex items-center px-3 py-1.5 text-sm font-medium text-red-700 bg-red-50 hover:bg-red-100 rounded-md transition-colors"
                    >
                      <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z"/>
                      </svg>
                      PDF
                    </button>
                  {:else}
                    <span class="text-xs text-gray-400 italic px-2">Sin acciones</span>
                  {/if}
                </div>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>

<!-- Create Modal -->
{#if showModal}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
      <div class="p-6">
        <div class="flex justify-between items-center mb-6">
          <h2 class="text-2xl font-bold text-gray-900">{isEditing ? 'Editar Solicitud de Cotización' : 'Nueva Solicitud de Cotización'}</h2>
          <button onclick={() => showModal = false} class="text-gray-400 hover:text-gray-600">
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

        <form onsubmit={(e) => { e.preventDefault(); handleSubmit(); }} class="space-y-6">
          <!-- Selección de Empresa -->
          {#if !isEditing}
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Empresa *</label>
            <div class="grid grid-cols-2 gap-3 max-h-48 overflow-y-auto border border-gray-200 rounded-lg p-3">
              {#each companies as company}
                <button
                  type="button"
                  onclick={() => selectCompany(company)}
                  class="p-3 border-2 rounded-lg text-left transition-all"
                  class:border-blue-600={selectedCompany?.id === company.id}
                  class:bg-blue-50={selectedCompany?.id === company.id}
                  class:border-gray-200={selectedCompany?.id !== company.id}
                  class:hover:border-gray-300={selectedCompany?.id !== company.id}
                >
                  <div class="font-medium text-sm text-gray-900">{company.razon_social}</div>
                  <div class="text-xs text-gray-500 mt-1">{company.rfc}</div>
                </button>
              {/each}
            </div>
            {#if selectedCompany}
              <p class="text-sm text-gray-600 mt-2">
                Tipo: <span class="font-medium">{getTipoCentroCargaLabel(selectedCompany.tipo_centro_carga || null)}</span>
              </p>
            {/if}
          </div>
          {:else}
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Empresa</label>
            <div class="p-3 bg-gray-50 border border-gray-200 rounded-lg">
              <div class="font-medium text-sm text-gray-900">{selectedCompany?.razon_social}</div>
              <div class="text-xs text-gray-500 mt-1">
                Tipo: {getTipoCentroCargaLabel(selectedCompany?.tipo_centro_carga || null)}
              </div>
            </div>
          </div>
          {/if}

          <!-- Título -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Título *</label>
            <input
              type="text"
              bind:value={formTitle}
              required
              placeholder="Ej: Instalación de medidores CFE"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <!-- Número de Transformadores -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Número de Transformadores</label>
            <input
              type="number"
              bind:value={numeroTransformadores}
              min="0"
              placeholder="0"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <!-- Conceptos -->
          <div>
            <div class="flex justify-between items-center mb-2">
              <label class="block text-sm font-medium text-gray-700">Conceptos *</label>
              <div class="flex gap-2">
                <button
                  type="button"
                  onclick={openItemsModal}
                  class="px-3 py-1 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm flex items-center gap-1"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
                  </svg>
                  Agregar del Catálogo
                </button>
              </div>
            </div>

            <!-- Checkbox para concepto personalizado -->
            <div class="mb-3">
              <label class="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
                <input
                  type="checkbox"
                  bind:checked={useCustomConcept}
                  class="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                />
                <span>No encuentro el concepto que necesito (agregar personalizado)</span>
              </label>
            </div>

            <!-- Formulario de concepto personalizado -->
            {#if useCustomConcept}
              <div class="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <h4 class="text-sm font-medium text-gray-900 mb-3">Agregar Concepto Personalizado</h4>
                <p class="text-xs text-gray-600 mb-3">El precio será determinado por el administrador al procesar la cotización.</p>
                <div class="grid grid-cols-2 gap-3">
                  <div class="col-span-2">
                    <label class="block text-xs font-medium text-gray-700 mb-1">Descripción *</label>
                    <textarea
                      bind:value={customDescription}
                      rows="2"
                      placeholder="Describe detalladamente el concepto que necesitas..."
                      class="w-full px-3 py-2 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    ></textarea>
                  </div>
                  <div>
                    <label class="block text-xs font-medium text-gray-700 mb-1">Cantidad *</label>
                    <input
                      type="number"
                      bind:value={customQuantity}
                      min="1"
                      step="1"
                      class="w-full px-3 py-2 border border-gray-300 rounded text-sm"
                    />
                  </div>
                  <div class="flex items-end">
                    <button
                      type="button"
                      onclick={addCustomConcept}
                      class="w-full px-3 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
                    >
                      Agregar
                    </button>
                  </div>
                </div>
              </div>
            {/if}

            {#if lines.length === 0}
              <div class="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
                <svg class="w-12 h-12 mx-auto text-gray-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
                </svg>
                <p class="text-gray-600">No hay conceptos agregados</p>
              </div>
            {:else}
              <div class="space-y-2">
                {#each lines as line, index}
                  <div class="flex items-center gap-2 p-3 border border-gray-200 rounded-lg">
                    <div class="flex-1">
                      <div class="text-sm font-medium text-gray-900">{line.description}</div>
                    </div>
                    <div class="flex items-center gap-2">
                      <label class="text-xs text-gray-600">Cant:</label>
                      <input
                        type="number"
                        value={line.quantity}
                        onchange={(e) => updateLineQuantity(index, parseFloat(e.currentTarget.value))}
                        min="0.01"
                        step="0.01"
                        class="w-20 px-2 py-1 border border-gray-300 rounded text-sm"
                        placeholder="Cant"
                      />
                    </div>
                    <button
                      type="button"
                      onclick={() => removeLine(index)}
                      class="p-1 text-red-600 hover:text-red-800"
                    >
                      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                      </svg>
                    </button>
                  </div>
                {/each}
              </div>
            {/if}
          </div>

          <!-- Observaciones -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Observaciones</label>
            <textarea
              bind:value={observaciones}
              rows="3"
              placeholder="Notas adicionales..."
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            ></textarea>
          </div>

          <!-- Buttons -->
          <div class="flex justify-end gap-3 pt-4 border-t border-gray-200">
            <button
              type="button"
              onclick={() => showModal = false}
              class="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              {isEditing ? 'Actualizar Solicitud' : 'Solicitar Cotización'}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
{/if}

<!-- Items Selection Modal -->
{#if showItemsModal}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60] p-4">
    <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] overflow-hidden flex flex-col">
      <div class="p-4 border-b border-gray-200">
        <div class="flex justify-between items-center mb-3">
          <h3 class="text-lg font-bold text-gray-900">Seleccionar Concepto</h3>
          <button onclick={() => showItemsModal = false} class="text-gray-400 hover:text-gray-600">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
        <input
          type="text"
          bind:value={itemSearchTerm}
          placeholder="Buscar por código o nombre..."
          class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      <div class="flex-1 overflow-y-auto p-4">
        {#if loadingItems}
          <div class="text-center py-8">
            <div class="inline-block animate-spin rounded-full h-8 w-8 border-4 border-gray-300 border-t-blue-600"></div>
          </div>
        {:else if filteredItems.length === 0}
          <p class="text-center text-gray-500 py-8">No se encontraron conceptos</p>
        {:else}
          <div class="space-y-2">
            {#each filteredItems as item}
              <button
                type="button"
                onclick={() => addItem(item)}
                class="w-full p-3 border border-gray-200 rounded-lg hover:border-blue-600 hover:bg-blue-50 text-left transition-colors"
              >
                <div class="flex justify-between items-start">
                  <div>
                    <div class="font-mono text-sm font-medium text-gray-900">{item.code}</div>
                    <div class="text-sm text-gray-900 mt-1">{item.name}</div>
                    {#if item.description}
                      <div class="text-xs text-gray-500 mt-1">{item.description}</div>
                    {/if}
                  </div>
                  <div class="text-right">
                    <div class="text-xs text-gray-500">{item.unit}</div>
                  </div>
                </div>
              </button>
            {/each}
          </div>
        {/if}
      </div>
    </div>
  </div>
{/if}

<!-- Delete Confirmation Modal -->
{#if showDeleteModal && quoteToDelete}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-lg shadow-xl max-w-md w-full">
      <div class="p-6">
        <div class="flex items-start gap-4">
          <div class="flex-shrink-0 w-12 h-12 rounded-full bg-red-100 flex items-center justify-center">
            <svg class="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
            </svg>
          </div>
          <div class="flex-1">
            <h3 class="text-lg font-medium text-gray-900 mb-2">Eliminar Cotización</h3>
            <p class="text-sm text-gray-600 mb-1">
              ¿Estás seguro de que deseas eliminar la cotización:
            </p>
            <p class="text-sm font-medium text-gray-900 mb-1">
              {quoteToDelete.quote_number} - {quoteToDelete.title}
            </p>
            <p class="text-sm text-gray-600">
              Esta acción no se puede deshacer.
            </p>
          </div>
        </div>

        <div class="flex justify-end gap-3 mt-6">
          <button
            onclick={() => { showDeleteModal = false; quoteToDelete = null; }}
            class="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
          >
            Cancelar
          </button>
          <button
            onclick={deleteQuote}
            class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
          >
            Eliminar
          </button>
        </div>
      </div>
    </div>
  </div>
{/if}

<!-- Send Confirmation Modal -->
{#if showSendModal && quoteToSend}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-lg shadow-xl max-w-md w-full">
      <div class="p-6">
        <div class="flex items-start gap-4">
          <div class="flex-shrink-0 w-12 h-12 rounded-full bg-emerald-100 flex items-center justify-center">
            <svg class="w-6 h-6 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/>
            </svg>
          </div>
          <div class="flex-1">
            <h3 class="text-lg font-medium text-gray-900 mb-2">Enviar Cotización</h3>
            <p class="text-sm text-gray-600 mb-1">
              ¿Deseas enviar la siguiente cotización al administrador?
            </p>
            <p class="text-sm font-medium text-gray-900 mb-1">
              {quoteToSend.quote_number} — {quoteToSend.title}
            </p>
            <p class="text-sm text-gray-500 mt-2">
              Una vez enviada, <span class="font-medium text-gray-700">no podrás editar ni eliminar</span> la cotización. El administrador la revisará y asignará precios.
            </p>
          </div>
        </div>

        <div class="flex justify-end gap-3 mt-6">
          <button
            onclick={() => { showSendModal = false; quoteToSend = null; }}
            class="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
          >
            Cancelar
          </button>
          <button
            onclick={sendQuote}
            class="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 flex items-center gap-2"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/>
            </svg>
            Sí, enviar
          </button>
        </div>
      </div>
    </div>
  </div>
{/if}
<!-- Approved Quote Detail Modal -->
{#if showApprovedDetail && selectedApprovedQuote}
  {@const q = selectedApprovedQuote}
  {@const subtotal = Number(q.total)}
  {@const ivaAmt = Number(q.iva_amount ?? 0)}
  {@const totalFinal = Number(q.total_con_iva) > 0 ? Number(q.total_con_iva) : subtotal}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
      <div class="p-6">

        <!-- Header -->
        <div class="flex justify-between items-start mb-5">
          <div>
            <h2 class="text-xl font-bold text-gray-900">{q.quote_number}</h2>
            <p class="text-gray-600 mt-0.5">{q.title}</p>
          </div>
          <div class="flex items-center gap-2">
            <span class="px-3 py-1 text-sm rounded-full {getStatusColor(q.status)}">
              {getStatusLabel(q.status)}
            </span>
            <button
              onclick={() => printQuotePDF(q)}
              class="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-md"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z"/>
              </svg>
              PDF
            </button>
            <button onclick={() => showApprovedDetail = false} class="text-gray-400 hover:text-gray-600">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>
        </div>

        <!-- Info rápida -->
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5 text-sm">
          <div class="bg-gray-50 rounded-lg p-3">
            <div class="text-xs text-gray-500 mb-0.5">Empresa</div>
            <div class="font-medium text-gray-900">{q.razon_social}</div>
          </div>
          <div class="bg-gray-50 rounded-lg p-3">
            <div class="text-xs text-gray-500 mb-0.5">Fecha solicitud</div>
            <div class="font-medium text-gray-900">{formatDate(q.created_at)}</div>
          </div>
          {#if q.fecha_vigencia}
            <div class="bg-green-50 rounded-lg p-3">
              <div class="text-xs text-green-600 mb-0.5">Vigencia hasta</div>
              <div class="font-medium text-green-800">
                {new Date(q.fecha_vigencia + 'T12:00:00').toLocaleDateString('es-MX', { day: '2-digit', month: 'short', year: 'numeric' })}
              </div>
            </div>
          {/if}
          {#if q.numero_transformadores}
            <div class="bg-gray-50 rounded-lg p-3">
              <div class="text-xs text-gray-500 mb-0.5">Transformadores</div>
              <div class="font-medium text-gray-900">{q.numero_transformadores}</div>
            </div>
          {/if}
        </div>

        {#if q.observaciones}
          <div class="mb-4">
            <h3 class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Tus observaciones</h3>
            <p class="text-sm text-gray-700 bg-yellow-50 border border-yellow-200 rounded-lg p-3 whitespace-pre-line">{q.observaciones}</p>
          </div>
        {/if}

        <!-- Tabla de conceptos con precios -->
        <h3 class="text-sm font-semibold text-gray-700 mb-2">Conceptos cotizados</h3>
        <div class="overflow-x-auto rounded-lg border border-gray-200 mb-4">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Descripción</th>
                <th class="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase w-16">Cant.</th>
                <th class="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase w-36">Precio unit.</th>
                <th class="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase w-32">Subtotal</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100">
              {#each q.lines as line, i}
                <tr class={i % 2 === 0 ? '' : 'bg-gray-50/50'}>
                  <td class="px-4 py-2.5 text-sm text-gray-900">{line.description}</td>
                  <td class="px-4 py-2.5 text-sm text-gray-700 text-right">{line.quantity}</td>
                  <td class="px-4 py-2.5 text-right">
                    {#if line.unit_price > 0}
                      <span class="text-sm font-medium text-gray-900">{formatCurrency(line.unit_price)}</span>
                    {:else}
                      <span class="text-xs text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full">Por definir</span>
                    {/if}
                  </td>
                  <td class="px-4 py-2.5 text-sm text-right">
                    {#if line.unit_price > 0}
                      <span class="font-medium text-gray-900">{formatCurrency(Number(line.unit_price) * Number(line.quantity))}</span>
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
                <td class="px-4 py-2 text-sm font-medium text-gray-900 text-right">{formatCurrency(subtotal)}</td>
              </tr>
              {#if q.iva_percent > 0}
                <tr>
                  <td colspan="3" class="px-4 py-2 text-sm text-gray-600 text-right">IVA ({q.iva_percent}%):</td>
                  <td class="px-4 py-2 text-sm text-gray-900 text-right">{formatCurrency(ivaAmt)}</td>
                </tr>
              {/if}
              <tr class="border-t border-gray-200">
                <td colspan="3" class="px-4 py-2.5 text-sm font-bold text-gray-900 text-right">
                  TOTAL{q.iva_percent > 0 ? ' CON IVA' : ''}:
                </td>
                <td class="px-4 py-2.5 text-base font-bold text-gray-900 text-right">{formatCurrency(totalFinal)}</td>
              </tr>
            </tfoot>
          </table>
        </div>

        {#if q.comentarios_admin}
          <div class="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-4">
            <h3 class="text-xs font-semibold text-amber-700 uppercase tracking-wider mb-2">Notas y condiciones</h3>
            <p class="text-sm text-amber-900 whitespace-pre-line">{q.comentarios_admin}</p>
          </div>
        {/if}

        <!-- Footer actions -->
        <div class="flex justify-end gap-3 pt-4 border-t border-gray-200">
          <button
            onclick={() => showApprovedDetail = false}
            class="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
          >
            Cerrar
          </button>
          {#if q.status === 'approved'}
            <button
              onclick={() => confirmAccept(q)}
              class="px-5 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 font-medium flex items-center gap-2"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
              </svg>
              Aceptar cotización
            </button>
          {/if}
        </div>

      </div>
    </div>
  </div>
{/if}

<!-- Accept Confirmation Modal -->
{#if showAcceptModal && quoteToAccept}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60] p-4">
    <div class="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
      <div class="flex items-start gap-4 mb-4">
        <div class="w-12 h-12 rounded-full bg-emerald-100 flex items-center justify-center flex-shrink-0">
          <svg class="w-6 h-6 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
        </div>
        <div>
          <h3 class="text-lg font-medium text-gray-900">Aceptar cotización</h3>
          <p class="text-sm text-gray-600 mt-1">
            {quoteToAccept.quote_number} — {quoteToAccept.title}
          </p>
          <p class="text-sm text-gray-500 mt-2">
            Al aceptar, confirmas que estás de acuerdo con los precios y condiciones presentadas. Nos pondremos en contacto para coordinar los siguientes pasos.
          </p>
        </div>
      </div>
      <div class="flex justify-end gap-3 mt-2">
        <button
          onclick={() => { showAcceptModal = false; quoteToAccept = null; }}
          disabled={acceptingQuote}
          class="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 disabled:opacity-60"
        >
          Cancelar
        </button>
        <button
          onclick={acceptQuote}
          disabled={acceptingQuote}
          class="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-60 flex items-center gap-2"
        >
          {#if acceptingQuote}
            <svg class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
            </svg>
            Procesando...
          {:else}
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
            </svg>
            Sí, aceptar
          {/if}
        </button>
      </div>
    </div>
  </div>
{/if}