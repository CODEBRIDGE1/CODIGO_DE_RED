<script lang="ts">
  import { onMount } from 'svelte';
  import { authStore } from '../stores/auth';

  // ─── Types ────────────────────────────────────────────────────────────────
  interface AuditLog {
    id: number;
    tenant_id: number | null;
    user_id: number | null;
    user_email: string | null;
    module_key: string | null;
    action: string | null;
    entity_type: string | null;
    entity_id: number | null;
    ip_address: string | null;
    after_data: Record<string, unknown> | null;
    before_data: Record<string, unknown> | null;
    request_id: string | null;
    created_at: string;
  }

  interface AuditResponse {
    items: AuditLog[];
    total: number;
    page: number;
    page_size: number;
    pages: number;
  }

  // ─── State ────────────────────────────────────────────────────────────────
  const user = $derived($authStore.user);
  const isSuperadmin = $derived(user?.isSuperadmin ?? false);

  let logs = $state<AuditLog[]>([]);
  let total = $state(0);
  let pages = $state(1);
  let loading = $state(false);
  let error = $state('');

  // Filters
  let filterModule = $state('');
  let filterAction = $state('');
  let filterDateFrom = $state('');
  let filterDateTo = $state('');
  let filterUser = $state('');
  let page = $state(1);
  const PAGE_SIZE = 50;

  // Available filter options
  let availableModules = $state<string[]>([]);
  let availableActions = $state<string[]>([]);

  // Detail modal
  let selectedLog = $state<AuditLog | null>(null);

  // ─── Labels ───────────────────────────────────────────────────────────────
  const MODULE_LABELS: Record<string, string> = {
    auth: 'Autenticación',
    companies: 'Empresas',
    projects: 'Proyectos',
    quotes: 'Cotizaciones',
    compliance: 'Cumplimiento',
    users: 'Usuarios',
    evidences: 'Evidencias',
    tasks: 'Tareas',
    documents: 'Documentos',
    tenants: 'Organizaciones',
    'quote-items': 'Conceptos',
    'security-levels': 'Niveles de Seguridad',
    obligations: 'Obligaciones',
  };

  const ACTION_LABELS: Record<string, string> = {
    create: 'Creación',
    update: 'Actualización',
    delete: 'Eliminación',
    login: 'Inicio de sesión',
    logout: 'Cierre de sesión',
    upload: 'Carga de archivo',
  };

  const ACTION_COLORS: Record<string, string> = {
    create: 'bg-green-100 text-green-800',
    update: 'bg-blue-100 text-blue-800',
    delete: 'bg-red-100 text-red-800',
    login: 'bg-purple-100 text-purple-800',
    logout: 'bg-gray-100 text-gray-700',
    upload: 'bg-yellow-100 text-yellow-800',
  };

  function actionColor(action: string | null): string {
    return ACTION_COLORS[action ?? ''] ?? 'bg-slate-100 text-slate-700';
  }

  function fmtDate(dt: string): string {
    return new Date(dt).toLocaleString('es-MX', {
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit', second: '2-digit',
    });
  }

  // ─── API ──────────────────────────────────────────────────────────────────
  const BASE = isSuperadmin
    ? `${import.meta.env.VITE_API_BASE_URL}/api/v1/admin/audit-logs`
    : `${import.meta.env.VITE_API_BASE_URL}/api/v1/audit-logs`;

  function getHeaders(): Record<string, string> {
    const token = localStorage.getItem('access_token');
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  async function loadOptions() {
    try {
      const [modRes, actRes] = await Promise.all([
        fetch(`${BASE}/modules`, { headers: getHeaders() }),
        fetch(`${BASE}/actions`, { headers: getHeaders() }),
      ]);
      if (modRes.ok) availableModules = await modRes.json();
      if (actRes.ok) availableActions = await actRes.json();
    } catch { /* non-critical */ }
  }

  async function loadLogs() {
    loading = true;
    error = '';
    try {
      const params = new URLSearchParams();
      params.set('page', String(page));
      params.set('page_size', String(PAGE_SIZE));
      if (filterModule) params.set('module_key', filterModule);
      if (filterAction) params.set('action', filterAction);
      if (filterDateFrom) params.set('date_from', filterDateFrom);
      if (filterDateTo) params.set('date_to', filterDateTo);
      if (filterUser && isSuperadmin) params.set('user_id', filterUser);

      const res = await authStore.fetch(`${BASE}?${params}`, { headers: getHeaders() });
      if (!res.ok) throw new Error(`Error ${res.status}`);
      const data: AuditResponse = await res.json();
      logs = data.items;
      total = data.total;
      pages = data.pages;
    } catch (e: unknown) {
      error = e instanceof Error ? e.message : 'Error al cargar la bitácora';
    } finally {
      loading = false;
    }
  }

  function applyFilters() {
    page = 1;
    loadLogs();
  }

  function clearFilters() {
    filterModule = '';
    filterAction = '';
    filterDateFrom = '';
    filterDateTo = '';
    filterUser = '';
    page = 1;
    loadLogs();
  }

  function prevPage() { if (page > 1) { page--; loadLogs(); } }
  function nextPage() { if (page < pages) { page++; loadLogs(); } }

  onMount(() => {
    loadOptions();
    loadLogs();
  });
</script>

<div class="flex flex-col h-full bg-gray-50">

  <!-- Header -->
  <div class="bg-white border-b border-gray-200 px-6 py-4 flex-shrink-0">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Bitácora de Auditoría</h1>
        <p class="text-sm text-gray-500 mt-0.5">
          {isSuperadmin ? 'Todas las organizaciones' : 'Tu organización'} ·
          {total.toLocaleString()} registro{total !== 1 ? 's' : ''}
        </p>
      </div>
      <button
        onclick={loadLogs}
        disabled={loading}
        class="flex items-center gap-2 px-4 py-2 bg-slate-700 text-white rounded-lg text-sm font-medium hover:bg-slate-800 disabled:opacity-50 transition-colors"
      >
        {#if loading}
          <svg class="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
          </svg>
        {:else}
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
          </svg>
        {/if}
        Actualizar
      </button>
    </div>
  </div>

  <!-- Filters -->
  <div class="bg-white border-b border-gray-200 px-6 py-3 flex-shrink-0">
    <div class="flex flex-wrap gap-3 items-end">
      <!-- Module filter -->
      <div class="flex flex-col gap-1">
        <label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Módulo</label>
        <select
          bind:value={filterModule}
          class="border border-gray-300 rounded-lg px-3 py-1.5 text-sm bg-white focus:ring-2 focus:ring-slate-400 focus:border-transparent min-w-[150px]"
        >
          <option value="">Todos</option>
          {#each availableModules as mod}
            <option value={mod}>{MODULE_LABELS[mod] ?? mod}</option>
          {/each}
        </select>
      </div>

      <!-- Action filter -->
      <div class="flex flex-col gap-1">
        <label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Acción</label>
        <select
          bind:value={filterAction}
          class="border border-gray-300 rounded-lg px-3 py-1.5 text-sm bg-white focus:ring-2 focus:ring-slate-400 focus:border-transparent min-w-[140px]"
        >
          <option value="">Todas</option>
          {#each availableActions as act}
            <option value={act}>{ACTION_LABELS[act] ?? act}</option>
          {/each}
        </select>
      </div>

      <!-- Date from -->
      <div class="flex flex-col gap-1">
        <label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Desde</label>
        <input
          type="date"
          bind:value={filterDateFrom}
          class="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:ring-2 focus:ring-slate-400 focus:border-transparent"
        />
      </div>

      <!-- Date to -->
      <div class="flex flex-col gap-1">
        <label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Hasta</label>
        <input
          type="date"
          bind:value={filterDateTo}
          class="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:ring-2 focus:ring-slate-400 focus:border-transparent"
        />
      </div>

      <!-- User filter (superadmin only) -->
      {#if isSuperadmin}
        <div class="flex flex-col gap-1">
          <label class="text-xs font-medium text-gray-500 uppercase tracking-wide">ID Usuario</label>
          <input
            type="number"
            bind:value={filterUser}
            placeholder="Ej: 3"
            class="border border-gray-300 rounded-lg px-3 py-1.5 text-sm w-28 focus:ring-2 focus:ring-slate-400 focus:border-transparent"
          />
        </div>
      {/if}

      <!-- Buttons -->
      <div class="flex gap-2">
        <button
          onclick={applyFilters}
          class="px-4 py-1.5 bg-slate-700 text-white rounded-lg text-sm font-medium hover:bg-slate-800 transition-colors"
        >
          Filtrar
        </button>
        <button
          onclick={clearFilters}
          class="px-3 py-1.5 border border-gray-300 text-gray-600 rounded-lg text-sm hover:bg-gray-50 transition-colors"
        >
          Limpiar
        </button>
      </div>
    </div>
  </div>

  <!-- Error -->
  {#if error}
    <div class="mx-6 mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm flex-shrink-0">
      {error}
    </div>
  {/if}

  <!-- Table -->
  <div class="flex-1 overflow-auto px-6 py-4">
    {#if loading && logs.length === 0}
      <div class="flex items-center justify-center h-48 text-gray-400">
        <svg class="w-6 h-6 animate-spin mr-2" viewBox="0 0 24 24" fill="none">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
        </svg>
        Cargando bitácora…
      </div>
    {:else if logs.length === 0}
      <div class="flex flex-col items-center justify-center h-48 text-gray-400">
        <svg class="w-12 h-12 mb-3 opacity-40" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
        </svg>
        <p class="text-sm">No hay registros con los filtros aplicados</p>
      </div>
    {:else}
      <div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="bg-gray-50 border-b border-gray-200">
                <th class="text-left px-4 py-3 font-semibold text-gray-600 text-xs uppercase tracking-wide whitespace-nowrap">Fecha y hora</th>
                <th class="text-left px-4 py-3 font-semibold text-gray-600 text-xs uppercase tracking-wide">Usuario</th>
                <th class="text-left px-4 py-3 font-semibold text-gray-600 text-xs uppercase tracking-wide">Módulo</th>
                <th class="text-left px-4 py-3 font-semibold text-gray-600 text-xs uppercase tracking-wide">Acción</th>
                <th class="text-left px-4 py-3 font-semibold text-gray-600 text-xs uppercase tracking-wide">Entidad</th>
                {#if isSuperadmin}
                  <th class="text-left px-4 py-3 font-semibold text-gray-600 text-xs uppercase tracking-wide">Org.</th>
                {/if}
                <th class="text-left px-4 py-3 font-semibold text-gray-600 text-xs uppercase tracking-wide">IP</th>
                <th class="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100">
              {#each logs as log (log.id)}
                <tr class="hover:bg-gray-50 transition-colors">
                  <td class="px-4 py-3 text-gray-500 whitespace-nowrap font-mono text-xs">
                    {fmtDate(log.created_at)}
                  </td>
                  <td class="px-4 py-3">
                    {#if log.user_email}
                      <span class="text-gray-800 font-medium">{log.user_email}</span>
                    {:else if log.user_id}
                      <span class="text-gray-400 text-xs">ID #{log.user_id}</span>
                    {:else}
                      <span class="text-gray-300 italic text-xs">Sistema</span>
                    {/if}
                  </td>
                  <td class="px-4 py-3">
                    <span class="text-gray-700">
                      {MODULE_LABELS[log.module_key ?? ''] ?? log.module_key ?? '—'}
                    </span>
                  </td>
                  <td class="px-4 py-3">
                    <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium {actionColor(log.action)}">
                      {ACTION_LABELS[log.action ?? ''] ?? log.action ?? '—'}
                    </span>
                  </td>
                  <td class="px-4 py-3 text-gray-600">
                    {log.entity_type ?? '—'}{log.entity_id ? ` #${log.entity_id}` : ''}
                  </td>
                  {#if isSuperadmin}
                    <td class="px-4 py-3 text-gray-400 text-xs">
                      {log.tenant_id ? `#${log.tenant_id}` : '—'}
                    </td>
                  {/if}
                  <td class="px-4 py-3 text-gray-400 font-mono text-xs whitespace-nowrap">
                    {log.ip_address ?? '—'}
                  </td>
                  <td class="px-4 py-3">
                    <button
                      onclick={() => selectedLog = log}
                      class="text-slate-500 hover:text-slate-700 p-1 rounded hover:bg-slate-100 transition-colors"
                      title="Ver detalle"
                    >
                      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                        <path stroke-linecap="round" stroke-linejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                      </svg>
                    </button>
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        {#if pages > 1}
          <div class="border-t border-gray-200 px-4 py-3 flex items-center justify-between bg-gray-50">
            <p class="text-xs text-gray-500">
              Página {page} de {pages} · {total.toLocaleString()} registros totales
            </p>
            <div class="flex gap-2">
              <button
                onclick={prevPage}
                disabled={page <= 1 || loading}
                class="px-3 py-1.5 border border-gray-300 rounded-lg text-xs text-gray-600 hover:bg-white disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                ← Anterior
              </button>
              <button
                onclick={nextPage}
                disabled={page >= pages || loading}
                class="px-3 py-1.5 border border-gray-300 rounded-lg text-xs text-gray-600 hover:bg-white disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                Siguiente →
              </button>
            </div>
          </div>
        {/if}
      </div>
    {/if}
  </div>
</div>

<!-- Detail Modal -->
{#if selectedLog}
  {@const log = selectedLog}
  <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
  <div
    class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
    onclick={() => selectedLog = null}
  >
    <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
    <div
      class="bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[80vh] overflow-y-auto"
      onclick={(e) => e.stopPropagation()}
    >
      <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
        <h2 class="text-lg font-bold text-gray-900">Detalle del registro</h2>
        <button
          onclick={() => selectedLog = null}
          class="text-gray-400 hover:text-gray-600 p-1 rounded-lg hover:bg-gray-100"
        >
          <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/>
          </svg>
        </button>
      </div>

      <div class="px-6 py-5 space-y-4">

        <div class="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">Fecha y hora</p>
            <p class="text-gray-800 font-mono text-xs">{fmtDate(log.created_at)}</p>
          </div>
          <div>
            <p class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">Acción</p>
            <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium {actionColor(log.action)}">
              {ACTION_LABELS[log.action ?? ''] ?? log.action ?? '—'}
            </span>
          </div>
          <div>
            <p class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">Usuario</p>
            <p class="text-gray-800">{log.user_email ?? `ID #${log.user_id}` ?? 'Sistema'}</p>
          </div>
          <div>
            <p class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">Módulo</p>
            <p class="text-gray-800">{MODULE_LABELS[log.module_key ?? ''] ?? log.module_key ?? '—'}</p>
          </div>
          <div>
            <p class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">Entidad</p>
            <p class="text-gray-800">{log.entity_type ?? '—'}{log.entity_id ? ` #${log.entity_id}` : ''}</p>
          </div>
          <div>
            <p class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">Dirección IP</p>
            <p class="text-gray-800 font-mono text-xs">{log.ip_address ?? '—'}</p>
          </div>
          {#if isSuperadmin}
            <div>
              <p class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">Organización</p>
              <p class="text-gray-800">{log.tenant_id ? `#${log.tenant_id}` : 'Global'}</p>
            </div>
          {/if}
          <div class="col-span-2">
            <p class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">Request ID</p>
            <p class="text-gray-500 font-mono text-xs break-all">{log.request_id ?? '—'}</p>
          </div>
        </div>

        {#if log.after_data && Object.keys(log.after_data).length > 0}
          <div>
            <p class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">Datos registrados</p>
            <pre class="bg-gray-50 border border-gray-200 rounded-lg p-3 text-xs text-gray-700 overflow-x-auto whitespace-pre-wrap">{JSON.stringify(log.after_data, null, 2)}</pre>
          </div>
        {/if}

        {#if log.before_data && Object.keys(log.before_data).length > 0}
          <div>
            <p class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">Estado anterior</p>
            <pre class="bg-amber-50 border border-amber-200 rounded-lg p-3 text-xs text-amber-900 overflow-x-auto whitespace-pre-wrap">{JSON.stringify(log.before_data, null, 2)}</pre>
          </div>
        {/if}
      </div>
    </div>
  </div>
{/if}
