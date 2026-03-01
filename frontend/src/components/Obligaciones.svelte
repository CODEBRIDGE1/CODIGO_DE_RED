<script lang="ts">
import { onMount } from 'svelte';
import { authStore } from '../stores/auth';
import { fly } from 'svelte/transition';

interface CompanySlim {
  id: number;
  razon_social: string;
  rfc: string;
  is_active: boolean;
  tipo_centro_carga?: string | null;
  justificacion?: string | null;
}

// ── State ───────────────────────────────────────────────────────────────────
let companies      = $state<CompanySlim[]>([]);
let selectedCompany = $state<CompanySlim | null>(null);

let showClassificationModal = $state(false);
let showMatrixModal         = $state(false);

let loading              = $state(false);   // carga inicial
let savingClassification = $state(false);   // botón Guardar del modal
let loadingMatrixId      = $state<number | null>(null); // fila cuya matriz se carga

let errorMessage   = $state('');
let successMessage = $state('');

// Filters & search
let searchTerm   = $state('');
let filterActive = $state<boolean>(true);
let searchInput  = $state<HTMLInputElement | null>(null);

// Pagination
let currentPage = $state(1);
const pageSize  = 10;

// Classification form
let tipoSelected  = $state('TIPO_A');
let justificacion = $state('');

// Matrix data
let matrixData = $state<any>(null);

// ── Alert auto-close ─────────────────────────────────────────────────────────
$effect(() => {
  if (errorMessage) {
    const t = setTimeout(() => errorMessage = '', 4000);
    return () => clearTimeout(t);
  }
});
$effect(() => {
  if (successMessage) {
    const t = setTimeout(() => successMessage = '', 4000);
    return () => clearTimeout(t);
  }
});

// ── Derived ───────────────────────────────────────────────────────────────────
function normalizeStr(s: string): string {
  return s.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
}

const totalActivas   = $derived(companies.filter(c => c.is_active).length);
const totalInactivas = $derived(companies.filter(c => !c.is_active).length);

const filteredCompanies = $derived.by(() => {
  const term = normalizeStr(searchTerm.trim());
  return companies.filter(c => {
    const matchesActive  = c.is_active === filterActive;
    const matchesSearch  = !term ||
      normalizeStr(c.razon_social).includes(term) ||
      normalizeStr(c.rfc).includes(term);
    return matchesActive && matchesSearch;
  });
});

const totalFiltered = $derived(filteredCompanies.length);
const totalPages    = $derived(Math.ceil(totalFiltered / pageSize));
const pagedCompanies = $derived(
  filteredCompanies.slice((currentPage - 1) * pageSize, currentPage * pageSize)
);

// Reset page when filters change
$effect(() => {
  searchTerm; filterActive;
  currentPage = 1;
});

// ── API ───────────────────────────────────────────────────────────────────────
async function loadCompanies() {
  loading = true;
  errorMessage = '';
  try {
    const token = localStorage.getItem('access_token');
    if (!token) throw new Error('No hay sesión activa. Por favor inicie sesión.');

    const response = await authStore.fetch(
      `${import.meta.env.VITE_API_BASE_URL}/api/v1/compliance/companies/`,
      { headers: { 'Authorization': `Bearer ${token}` } }
    );

    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: 'Error al cargar empresas' }));
      throw new Error(err.detail || 'Error al cargar empresas');
    }

    companies = await response.json();
  } catch (e: any) {
    errorMessage = e.message;
  } finally {
    loading = false;
  }
}

function openClassificationModal(company: CompanySlim) {
  selectedCompany = company;
  tipoSelected    = company.tipo_centro_carga ?? 'TIPO_A';
  justificacion   = company.justificacion ?? '';
  showClassificationModal = true;
}

async function saveClassification() {
  if (!selectedCompany || savingClassification) return;
  savingClassification = true;
  errorMessage = '';

  try {
    const token  = localStorage.getItem('access_token');
    const method = selectedCompany.tipo_centro_carga ? 'PUT' : 'POST';

    const response = await authStore.fetch(
      `${import.meta.env.VITE_API_BASE_URL}/api/v1/compliance/companies/${selectedCompany.id}/classification`,
      {
        method,
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ tipo_centro_carga: tipoSelected, justificacion: justificacion || null })
      }
    );

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || 'Error al guardar');
    }

    showClassificationModal = false;
    successMessage = 'Clasificación guardada exitosamente';
    await loadCompanies();
  } catch (e: any) {
    errorMessage = e.message;
  } finally {
    savingClassification = false;
  }
}

async function viewMatrix(company: CompanySlim) {
  if (loadingMatrixId !== null) return;
  loadingMatrixId = company.id;
  selectedCompany = company;
  errorMessage    = '';

  try {
    const token    = localStorage.getItem('access_token');
    const response = await authStore.fetch(
      `${import.meta.env.VITE_API_BASE_URL}/api/v1/compliance/companies/${company.id}/compliance-matrix`,
      { headers: { 'Authorization': `Bearer ${token}` } }
    );

    if (!response.ok) {
      if (response.status === 404) throw new Error('Primero debe clasificar la empresa');
      throw new Error('Error al cargar la matriz');
    }

    matrixData      = await response.json();
    showMatrixModal = true;
  } catch (e: any) {
    errorMessage = e.message;
  } finally {
    loadingMatrixId = null;
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function getEstadoColor(estado: string): string {
  switch (estado) {
    case 'APLICA':     return 'bg-green-100 text-green-800';
    case 'NO_APLICA':  return 'bg-gray-100 text-gray-800';
    case 'APLICA_RDC': return 'bg-blue-100 text-blue-800';
    case 'APLICA_TIC': return 'bg-purple-100 text-purple-800';
    default:           return 'bg-gray-100 text-gray-800';
  }
}
function getEstadoText(estado: string): string {
  switch (estado) {
    case 'APLICA':     return 'Aplica';
    case 'NO_APLICA':  return 'No Aplica';
    case 'APLICA_RDC': return 'Aplica (RDC)';
    case 'APLICA_TIC': return 'Aplica (TIC)';
    default:           return estado;
  }
}
function getTipoLabel(tipo: string): string {
  switch (tipo) {
    case 'TIPO_A': return 'Media Tensión < 1 MW';
    case 'TIPO_B': return 'Media Tensión ≥ 1 MW';
    case 'TIPO_C': return 'Alta Tensión';
    default:       return tipo;
  }
}

onMount(() => {
  loadCompanies();
  setTimeout(() => searchInput?.focus(), 50);
});
</script>

<div class="p-6">
  <!-- Header -->
  <div class="mb-6">
    <h1 class="text-2xl font-bold text-gray-900">Matriz de Obligaciones</h1>
    <p class="text-gray-600 mt-1">Gestión de clasificación y requerimientos de centros de carga</p>
  </div>

  <!-- Initial loading spinner -->
  {#if loading && companies.length === 0}
    <div class="text-center py-16">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
      <p class="mt-4 text-gray-500 text-sm">Cargando empresas...</p>
    </div>

  {:else if !loading && companies.length === 0}
    <div class="text-center py-16 bg-white rounded-xl shadow">
      <svg class="mx-auto h-12 w-12 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
          d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
      </svg>
      <h3 class="mt-3 text-sm font-semibold text-gray-900">No hay empresas</h3>
      <p class="mt-1 text-sm text-gray-500">Primero cree empresas en el módulo de <strong>Mis Empresas</strong></p>
    </div>

  {:else}
    <!-- Tabs activas / inactivas -->
    <div class="flex gap-1 mb-4 bg-white rounded-lg shadow p-1 w-fit">
      <button
        onclick={() => filterActive = true}
        class="px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2
          {filterActive ? 'bg-blue-600 text-white shadow-sm' : 'text-gray-600 hover:bg-gray-100'}"
      >
        <span class="w-2 h-2 rounded-full {filterActive ? 'bg-blue-200' : 'bg-green-400'}"></span>
        Activas
        <span class="{filterActive ? 'bg-blue-500 text-blue-100' : 'bg-gray-100 text-gray-600'} text-xs px-1.5 py-0.5 rounded-full font-semibold">{totalActivas}</span>
      </button>
      <button
        onclick={() => filterActive = false}
        class="px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2
          {!filterActive ? 'bg-gray-700 text-white shadow-sm' : 'text-gray-600 hover:bg-gray-100'}"
      >
        <span class="w-2 h-2 rounded-full {!filterActive ? 'bg-gray-400' : 'bg-gray-300'}"></span>
        Inactivas
        <span class="{!filterActive ? 'bg-gray-600 text-gray-200' : 'bg-gray-100 text-gray-600'} text-xs px-1.5 py-0.5 rounded-full font-semibold">{totalInactivas}</span>
      </button>
    </div>

    <!-- Search -->
    <div class="bg-white rounded-lg shadow p-4 mb-6">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">Buscar</label>
        <div class="relative">
          <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0"/>
          </svg>
          <input
            bind:this={searchInput}
            type="text"
            bind:value={searchTerm}
            placeholder="Razón social, RFC"
            class="w-full pl-9 pr-9 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
          {#if searchTerm}
            <button onclick={() => searchTerm = ''} class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          {/if}
        </div>
      </div>
    </div>

    <!-- Loading skeleton (reload) -->
    {#if loading && companies.length > 0}
      <div class="bg-white rounded-lg shadow p-6">
        <div class="animate-pulse space-y-4">
          {#each Array(5) as _}
            <div class="h-16 bg-gray-200 rounded"></div>
          {/each}
        </div>
      </div>
    {/if}

    <!-- No results -->
    {#if filteredCompanies.length === 0}
      <div class="bg-white rounded-lg shadow p-10 text-center">
        <svg class="w-12 h-12 mx-auto text-gray-300 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0"/>
        </svg>
        <p class="text-gray-500">Sin resultados para <strong>"{searchTerm}"</strong></p>
        <button onclick={() => searchTerm = ''} class="mt-3 text-sm text-blue-600 hover:underline">Limpiar filtros</button>
      </div>

    {:else}
      <!-- Desktop table -->
      <div class="hidden md:block bg-white rounded-xl shadow overflow-hidden">
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Empresa</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">RFC</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Clasificación</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tipo Centro Carga</th>
                <th class="sticky right-0 z-10 bg-gray-50 px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider shadow-[-4px_0_6px_-1px_rgba(0,0,0,0.08)]">
                  Acciones
                </th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              {#each pagedCompanies as company (company.id)}
                <tr class="hover:bg-gray-50 group">
                  <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm font-medium text-gray-900">{company.razon_social}</div>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 font-mono">
                    {company.rfc}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    {#if company.tipo_centro_carga}
                      <span class="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">
                        <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
                        </svg>
                        Clasificada
                      </span>
                    {:else}
                      <span class="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded-full bg-amber-100 text-amber-800">
                        <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                          <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
                        </svg>
                        Sin clasificar
                      </span>
                    {/if}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    {#if company.tipo_centro_carga}
                      <div class="text-sm font-semibold text-gray-900">{company.tipo_centro_carga}</div>
                      <div class="text-xs text-gray-500">{getTipoLabel(company.tipo_centro_carga)}</div>
                    {:else}
                      <span class="text-gray-400 text-sm">—</span>
                    {/if}
                  </td>
                  <!-- Sticky actions -->
                  <td class="sticky right-0 z-10 bg-white group-hover:bg-gray-50 px-4 py-4 whitespace-nowrap shadow-[-4px_0_6px_-1px_rgba(0,0,0,0.08)] transition-colors">
                    <div class="flex items-center gap-1">
                      <!-- Clasificar / Editar clasificación -->
                      <button
                        onclick={() => openClassificationModal(company)}
                        disabled={savingClassification || loadingMatrixId !== null}
                        title={company.tipo_centro_carga ? 'Editar clasificación' : 'Clasificar empresa'}
                        class="p-2 rounded-lg transition-colors disabled:opacity-40
                          {company.tipo_centro_carga
                            ? 'text-blue-600 hover:bg-blue-50 hover:text-blue-800'
                            : 'text-amber-600 hover:bg-amber-50 hover:text-amber-800'}"
                      >
                        {#if company.tipo_centro_carga}
                          <!-- Pencil icon -->
                          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                              d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                          </svg>
                        {:else}
                          <!-- Plus icon -->
                          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
                          </svg>
                        {/if}
                      </button>

                      <!-- Ver Matriz (only if classified) -->
                      {#if company.tipo_centro_carga}
                        <button
                          onclick={() => viewMatrix(company)}
                          disabled={loadingMatrixId !== null || savingClassification}
                          title="Ver Matriz de Cumplimiento"
                          class="p-2 rounded-lg text-green-600 hover:bg-green-50 hover:text-green-800 transition-colors disabled:opacity-40"
                        >
                          {#if loadingMatrixId === company.id}
                            <!-- Spinner -->
                            <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
                            </svg>
                          {:else}
                            <!-- Eye icon -->
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                            </svg>
                          {/if}
                        </button>
                      {/if}
                    </div>
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      </div>

      <!-- Mobile cards -->
      <div class="md:hidden space-y-3">
        {#each pagedCompanies as company (company.id)}
          <div class="bg-white rounded-xl shadow p-4">
            <div class="flex justify-between items-start mb-2">
              <div>
                <h3 class="font-semibold text-gray-900 text-sm">{company.razon_social}</h3>
                <p class="text-xs text-gray-500 font-mono mt-0.5">{company.rfc}</p>
              </div>
              {#if company.tipo_centro_carga}
                <span class="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">Clasificada</span>
              {:else}
                <span class="px-2 py-1 text-xs font-medium rounded-full bg-amber-100 text-amber-800">Sin clasificar</span>
              {/if}
            </div>

            {#if company.tipo_centro_carga}
              <div class="mt-2 px-3 py-2 bg-gray-50 rounded-lg text-sm">
                <span class="font-semibold text-gray-800">{company.tipo_centro_carga}</span>
                <span class="text-gray-500 text-xs ml-1">— {getTipoLabel(company.tipo_centro_carga)}</span>
              </div>
            {/if}

            <div class="flex gap-2 mt-3 pt-3 border-t border-gray-100">
              <button
                onclick={() => openClassificationModal(company)}
                disabled={savingClassification || loadingMatrixId !== null}
                class="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 text-sm font-medium rounded-lg transition-colors disabled:opacity-50
                  {company.tipo_centro_carga
                    ? 'bg-blue-50 text-blue-700 hover:bg-blue-100'
                    : 'bg-amber-50 text-amber-700 hover:bg-amber-100'}"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  {#if company.tipo_centro_carga}
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                  {:else}
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
                  {/if}
                </svg>
                {company.tipo_centro_carga ? 'Editar' : 'Clasificar'}
              </button>

              {#if company.tipo_centro_carga}
                <button
                  onclick={() => viewMatrix(company)}
                  disabled={loadingMatrixId !== null || savingClassification}
                  class="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 text-sm font-medium rounded-lg bg-green-50 text-green-700 hover:bg-green-100 transition-colors disabled:opacity-50"
                >
                  {#if loadingMatrixId === company.id}
                    <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
                    </svg>
                  {:else}
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                    </svg>
                  {/if}
                  Ver Matriz
                </button>
              {/if}
            </div>
          </div>
        {/each}
      </div>

      <!-- Pagination -->
      {#if totalPages > 1}
        <div class="flex items-center justify-between mt-4 px-1">
          <p class="text-sm text-gray-500">
            Mostrando {Math.min((currentPage - 1) * pageSize + 1, totalFiltered)}–{Math.min(currentPage * pageSize, totalFiltered)} de {totalFiltered} empresas
          </p>
          <div class="flex items-center gap-1">
            <button
              onclick={() => currentPage = Math.max(1, currentPage - 1)}
              disabled={currentPage <= 1}
              class="p-2 rounded-lg hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              <svg class="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
              </svg>
            </button>
            <span class="px-3 py-1 text-sm text-gray-700 font-medium">{currentPage} / {totalPages}</span>
            <button
              onclick={() => currentPage = Math.min(totalPages, currentPage + 1)}
              disabled={currentPage >= totalPages}
              class="p-2 rounded-lg hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              <svg class="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
              </svg>
            </button>
          </div>
        </div>
      {/if}
    {/if}
  {/if}
</div>

<!-- ══ Classification Modal ══════════════════════════════════════════════════ -->
{#if showClassificationModal && selectedCompany}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9998] p-4">
    <div class="bg-white rounded-xl shadow-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
      <div class="p-6">
        <!-- Header -->
        <div class="flex items-center justify-between mb-5">
          <div>
            <h2 class="text-lg font-bold text-gray-900">Clasificación de Centro de Carga</h2>
            <p class="text-sm text-gray-500 mt-0.5">{selectedCompany.razon_social} · {selectedCompany.rfc}</p>
          </div>
          <button
            onclick={() => { showClassificationModal = false; }}
            disabled={savingClassification}
            class="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-40"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>

        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">Tipo de Centro de Carga *</label>
            <select
              bind:value={tipoSelected}
              disabled={savingClassification}
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm disabled:bg-gray-50 disabled:text-gray-500"
            >
              <option value="TIPO_A">TIPO A — Media Tensión &lt; 1 MW</option>
              <option value="TIPO_B">TIPO B — Media Tensión ≥ 1 MW</option>
              <option value="TIPO_C">TIPO C — Alta Tensión</option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">Justificación</label>
            <textarea
              bind:value={justificacion}
              rows={4}
              disabled={savingClassification}
              placeholder="Describa los criterios técnicos para esta clasificación..."
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm resize-none disabled:bg-gray-50 disabled:text-gray-500"
            ></textarea>
          </div>
        </div>

        <div class="mt-6 flex gap-3">
          <button
            onclick={saveClassification}
            disabled={savingClassification}
            class="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {#if savingClassification}
              <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
              </svg>
              Guardando...
            {:else}
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
              </svg>
              Guardar
            {/if}
          </button>
          <button
            onclick={() => showClassificationModal = false}
            disabled={savingClassification}
            class="px-4 py-2.5 border border-gray-300 rounded-lg hover:bg-gray-50 text-sm text-gray-700 transition-colors disabled:opacity-50"
          >
            Cancelar
          </button>
        </div>
      </div>
    </div>
  </div>
{/if}

<!-- ══ Matrix Modal ═══════════════════════════════════════════════════════════ -->
{#if showMatrixModal && matrixData}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9998] p-2 md:p-4">
    <div class="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[95vh] md:max-h-[90vh] overflow-y-auto">
      <div class="p-4 md:p-6">
        <div class="flex justify-between items-start mb-4">
          <div>
            <h2 class="text-xl font-bold text-gray-900">Matriz de Cumplimiento</h2>
            <p class="text-sm text-gray-500 mt-1">{matrixData.razon_social}</p>
          </div>
          <button
            onclick={() => showMatrixModal = false}
            class="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>

        <div class="mb-5 p-4 bg-blue-50 border border-blue-100 rounded-xl">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <div class="text-xs text-blue-600 font-medium uppercase tracking-wide">Tipo de Centro de Carga</div>
              <div class="font-bold text-gray-900 mt-0.5">{matrixData.tipo_centro_carga}</div>
              <div class="text-xs text-gray-500">{getTipoLabel(matrixData.tipo_centro_carga)}</div>
            </div>
            {#if matrixData.justificacion}
              <div>
                <div class="text-xs text-blue-600 font-medium uppercase tracking-wide">Justificación</div>
                <div class="text-sm text-gray-700 mt-0.5">{matrixData.justificacion}</div>
              </div>
            {/if}
          </div>
        </div>

        <div class="space-y-3">
          {#each matrixData.requerimientos as req}
            <div class="border border-gray-200 rounded-xl overflow-hidden">
              <div class="flex flex-col md:flex-row md:items-center md:justify-between p-3 md:p-4 bg-gray-50">
                <div class="flex-1">
                  <div class="flex flex-col md:flex-row md:items-center md:gap-3 gap-2">
                    <span class="px-2 py-1 bg-gray-200 text-gray-700 text-xs font-mono rounded w-fit">{req.codigo}</span>
                    <span class="font-semibold text-gray-900 text-sm">{req.nombre}</span>
                  </div>
                  {#if req.descripcion}
                    <p class="text-xs text-gray-600 mt-2">{req.descripcion}</p>
                  {/if}
                </div>
                <div class="mt-3 md:mt-0 md:ml-4 flex flex-col items-start md:items-end">
                  <span class="px-3 py-1 text-xs font-medium rounded-full {getEstadoColor(req.estado_aplicabilidad)}">
                    {getEstadoText(req.estado_aplicabilidad)}
                  </span>
                  {#if req.notas}
                    <div class="text-xs text-gray-500 mt-1">{req.notas}</div>
                  {/if}
                </div>
              </div>

              {#if req.children && req.children.length > 0}
                <div class="pl-4 md:pl-8 py-2 bg-white border-t border-gray-200">
                  {#each req.children as child}
                    <div class="flex flex-col md:flex-row md:items-center md:justify-between py-3 border-b border-gray-100 last:border-0">
                      <div class="flex-1">
                        <div class="flex flex-col md:flex-row md:items-center md:gap-3 gap-2">
                          <span class="px-2 py-1 bg-gray-100 text-gray-600 text-xs font-mono rounded w-fit">{child.codigo}</span>
                          <span class="text-sm text-gray-700">{child.nombre}</span>
                        </div>
                        {#if child.descripcion}
                          <p class="text-xs text-gray-500 mt-2">{child.descripcion}</p>
                        {/if}
                      </div>
                      <div class="mt-2 md:mt-0 md:ml-4 flex flex-col items-start md:items-end">
                        <span class="px-3 py-1 text-xs font-medium rounded-full {getEstadoColor(child.estado_aplicabilidad)}">
                          {getEstadoText(child.estado_aplicabilidad)}
                        </span>
                        {#if child.notas}
                          <div class="text-xs text-gray-500 mt-1">{child.notas}</div>
                        {/if}
                      </div>
                    </div>
                  {/each}
                </div>
              {/if}
            </div>
          {/each}
        </div>

        <div class="mt-6">
          <button
            onclick={() => showMatrixModal = false}
            class="w-full px-4 py-2.5 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm font-medium transition-colors"
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  </div>
{/if}

<!-- ══ Toast Notifications ═══════════════════════════════════════════════════ -->
{#if errorMessage}
  <div
    transition:fly="{{ x: 300, duration: 300 }}"
    class="fixed top-4 right-4 z-[9999] bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl shadow-lg max-w-sm"
  >
    <div class="flex items-start justify-between gap-3">
      <div class="flex items-start gap-2">
        <svg class="w-5 h-5 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
        <span class="text-sm">{errorMessage}</span>
      </div>
      <button onclick={() => errorMessage = ''} class="flex-shrink-0 text-red-400 hover:text-red-600">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
        </svg>
      </button>
    </div>
    <div class="mt-2 h-1 bg-red-200 rounded-full overflow-hidden">
      <div class="h-full bg-red-500" style="animation: shrink 4s linear;"></div>
    </div>
  </div>
{/if}

{#if successMessage}
  <div
    transition:fly="{{ x: 300, duration: 300 }}"
    class="fixed top-4 right-4 z-[9999] bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-xl shadow-lg max-w-sm"
  >
    <div class="flex items-start justify-between gap-3">
      <div class="flex items-start gap-2">
        <svg class="w-5 h-5 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
        <span class="text-sm">{successMessage}</span>
      </div>
      <button onclick={() => successMessage = ''} class="flex-shrink-0 text-green-400 hover:text-green-600">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
        </svg>
      </button>
    </div>
    <div class="mt-2 h-1 bg-green-200 rounded-full overflow-hidden">
      <div class="h-full bg-green-500" style="animation: shrink 4s linear;"></div>
    </div>
  </div>
{/if}

<style>
@keyframes shrink {
  from { width: 100%; }
  to   { width: 0%; }
}
</style>


