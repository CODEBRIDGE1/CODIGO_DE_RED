<script lang="ts">
import { onMount } from 'svelte';
import { fly } from 'svelte/transition';

interface Company {
  id: number;
  razon_social: string;
  nombre_comercial?: string;
  rfc: string;
  telefono?: string;
  email?: string;
  is_active: boolean;
  created_at: string;
}

let companies = $state<Company[]>([]);
let selectedCompany = $state<Company | null>(null);
let showClassificationModal = $state(false);
let showMatrixModal = $state(false);
let loading = $state(false);
let errorMessage = $state('');
let successMessage = $state('');

// Auto-close alerts after 4 seconds
$effect(() => {
  if (errorMessage) {
    const timer = setTimeout(() => errorMessage = '', 4000);
    return () => clearTimeout(timer);
  }
});

$effect(() => {
  if (successMessage) {
    const timer = setTimeout(() => successMessage = '', 4000);
    return () => clearTimeout(timer);
  }
});

// Classification form
let tipoSelected = $state('TIPO_A');
let justificacion = $state('');

// Matrix data
let matrixData = $state<any>(null);



interface CompanyWithClassification extends Company {
  classification?: {
    tipo_centro_carga: string;
    justificacion?: string;
  };
}

async function loadCompanies() {
  loading = true;
  errorMessage = '';
  
  try {
    const token = localStorage.getItem('access_token');
    if (!token) {
      throw new Error('No hay sesión activa. Por favor inicie sesión.');
    }
    
    const params = new URLSearchParams({
      page: '1',
      page_size: '100'
    });
    
    const response = await fetch(`/api/v1/companies/?${params}`, {
      headers: { 
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Error al cargar empresas' }));
      throw new Error(errorData.detail || 'Error al cargar empresas');
    }
    
    const data = await response.json();
    console.log('[Obligaciones] API Response:', data);
    console.log('[Obligaciones] Companies array:', data.companies);
    console.log('[Obligaciones] Array length:', data.companies?.length);
    
    companies = data.companies || [];
    console.log('[Obligaciones] State after assignment:', companies);
    console.log('[Obligaciones] State length:', companies.length);
    
    // Cargar clasificaciones en paralelo
    const classificationPromises = companies.map(async (company) => {
      try {
        const classResp = await fetch(
          `/api/v1/compliance/companies/${company.id}/classification`,
          { headers: { 'Authorization': `Bearer ${token}` } }
        );
        if (classResp.ok) {
          (company as CompanyWithClassification).classification = await classResp.json();
        }
      } catch (e) {
        // No tiene clasificación, esto es normal
      }
    });
    
    await Promise.all(classificationPromises);
    
  } catch (e: any) {
    errorMessage = e.message;
    console.error('Error loading companies:', e);
  } finally {
    loading = false;
  }
}

async function openClassificationModal(company: Company) {
  selectedCompany = company;
  const companyWithClass = company as CompanyWithClassification;
  
  if (companyWithClass.classification) {
    tipoSelected = companyWithClass.classification.tipo_centro_carga;
    justificacion = companyWithClass.classification.justificacion || '';
  } else {
    tipoSelected = 'TIPO_A';
    justificacion = '';
  }
  
  showClassificationModal = true;
}

async function saveClassification() {
  if (!selectedCompany) return;
  
  loading = true;
  errorMessage = '';
  
  try {
    const token = localStorage.getItem('access_token');
    const companyWithClass = selectedCompany as CompanyWithClassification;
    const method = companyWithClass.classification ? 'PUT' : 'POST';
    
    const payload = {
      tipo_centro_carga: tipoSelected,
      justificacion: justificacion || null
    };
    console.log('[Obligaciones] Saving classification:', {
      method,
      company_id: selectedCompany.id,
      payload
    });
    
    const response = await fetch(
      `/api/v1/compliance/companies/${selectedCompany.id}/classification`,
      {
        method,
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      }
    );
    
    console.log('[Obligaciones] Save response status:', response.status);
    
    if (!response.ok) {
      const err = await response.json();
      console.error('[Obligaciones] Save error:', err);
      throw new Error(err.detail || 'Error al guardar');
    }
    
    showClassificationModal = false;
    await loadCompanies();
    successMessage = 'Clasificación guardada exitosamente';
    
  } catch (e: any) {
    errorMessage = e.message;
  } finally {
    loading = false;
  }
}

async function viewMatrix(company: Company) {
  selectedCompany = company;
  loading = true;
  errorMessage = '';
  
  try {
    const token = localStorage.getItem('access_token');
    const response = await fetch(
      `/api/v1/compliance/companies/${company.id}/compliance-matrix`,
      { headers: { 'Authorization': `Bearer ${token}` } }
    );
    
    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('Primero debe clasificar la empresa');
      }
      throw new Error('Error al cargar matriz');
    }
    
    matrixData = await response.json();
    showMatrixModal = true;
    
  } catch (e: any) {
    errorMessage = e.message;
  } finally {
    loading = false;
  }
}

function getEstadoColor(estado: string): string {
  switch (estado) {
    case 'APLICA': return 'bg-green-100 text-green-800';
    case 'NO_APLICA': return 'bg-gray-100 text-gray-800';
    case 'APLICA_RDC': return 'bg-blue-100 text-blue-800';
    case 'APLICA_TIC': return 'bg-purple-100 text-purple-800';
    default: return 'bg-gray-100 text-gray-800';
  }
}

function getEstadoText(estado: string): string {
  switch (estado) {
    case 'APLICA': return 'Aplica';
    case 'NO_APLICA': return 'No Aplica';
    case 'APLICA_RDC': return 'Aplica (RDC)';
    case 'APLICA_TIC': return 'Aplica (TIC)';
    default: return estado;
  }
}

function getTipoLabel(tipo: string): string {
  switch (tipo) {
    case 'TIPO_A': return 'Media Tensión < 1 MW';
    case 'TIPO_B': return 'Media Tensión ≥ 1 MW';
    case 'TIPO_C': return 'Alta Tensión';
    default: return tipo;
  }
}

onMount(() => {
  loadCompanies();
});
</script>

<div class="p-6">
  <div class="mb-6">
    <h1 class="text-2xl font-bold text-gray-900">Matriz de Obligaciones</h1>
    <p class="text-gray-600 mt-1">Gestión de clasificación y requerimientos de centros de carga</p>
  </div>

  {#if loading && companies.length === 0}
    <div class="text-center py-12">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
      <p class="mt-4 text-gray-600">Cargando empresas...</p>
    </div>
  {:else if companies.length === 0}
    <div class="text-center py-12 bg-white rounded-lg shadow">
      <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
      </svg>
      <h3 class="mt-2 text-sm font-medium text-gray-900">No hay empresas</h3>
      <p class="mt-1 text-sm text-gray-500">Primero debe crear empresas en el módulo de Empresas</p>
    </div>
  {:else}
    <!-- Desktop table -->
    <div class="hidden md:block bg-white rounded-lg shadow overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Empresa</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">RFC</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Clasificación</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tipo Centro Carga</th>
            <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Acciones</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          {#each companies as company (company.id)}
            {@const companyWithClass = company as CompanyWithClassification}
            <tr class="hover:bg-gray-50">
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm font-medium text-gray-900">{company.razon_social}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {company.rfc}
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                {#if companyWithClass.classification}
                  <span class="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">
                    Clasificada
                  </span>
                {:else}
                  <span class="px-2 py-1 text-xs font-medium rounded-full bg-yellow-100 text-yellow-800">
                    Sin clasificar
                  </span>
                {/if}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {#if companyWithClass.classification}
                  <div class="text-sm font-medium text-gray-900">
                    {companyWithClass.classification.tipo_centro_carga}
                  </div>
                  <div class="text-xs text-gray-500">
                    {getTipoLabel(companyWithClass.classification.tipo_centro_carga)}
                  </div>
                {:else}
                  -
                {/if}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                <button
                  onclick={() => openClassificationModal(company)}
                  class="text-blue-600 hover:text-blue-900 mr-3"
                >
                  {companyWithClass.classification ? 'Editar' : 'Clasificar'}
                </button>
                {#if companyWithClass.classification}
                  <button
                    onclick={() => viewMatrix(company)}
                    class="text-green-600 hover:text-green-900"
                  >
                    Ver Matriz
                  </button>
                {/if}
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>

    <!-- Mobile cards -->
    <div class="md:hidden space-y-4">
      {#each companies as company (company.id)}
        {@const companyWithClass = company as CompanyWithClassification}
        <div class="bg-white rounded-lg shadow p-4">
          <div class="flex justify-between items-start mb-2">
            <div>
              <h3 class="font-medium text-gray-900">{company.razon_social}</h3>
              <p class="text-sm text-gray-500">{company.rfc}</p>
            </div>
            {#if companyWithClass.classification}
              <span class="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">
                Clasificada
              </span>
            {:else}
              <span class="px-2 py-1 text-xs font-medium rounded-full bg-yellow-100 text-yellow-800">
                Sin clasificar
              </span>
            {/if}
          </div>
          
          {#if companyWithClass.classification}
            <div class="mt-2 p-2 bg-gray-50 rounded text-sm">
              <div class="font-medium">{companyWithClass.classification.tipo_centro_carga}</div>
              <div class="text-xs text-gray-600">{getTipoLabel(companyWithClass.classification.tipo_centro_carga)}</div>
            </div>
          {/if}
          
          <div class="flex space-x-2 mt-3 pt-3 border-t">
            <button
              onclick={() => openClassificationModal(company)}
              class="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              {companyWithClass.classification ? 'Editar' : 'Clasificar'}
            </button>
            {#if companyWithClass.classification}
              <button
                onclick={() => viewMatrix(company)}
                class="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
              >
                Ver Matriz
              </button>
            {/if}
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>

<!-- Classification Modal -->
{#if showClassificationModal}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9998] p-4">
    <div class="bg-white rounded-lg shadow-xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
      <div class="p-6">
        <h2 class="text-xl font-bold mb-4">
          Clasificación de Centro de Carga
        </h2>
        
        <div class="mb-4">
          <h3 class="font-semibold text-gray-900">{selectedCompany?.razon_social}</h3>
          <p class="text-sm text-gray-600">{selectedCompany?.rfc}</p>
        </div>

        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Tipo de Centro de Carga *
            </label>
            <select
              bind:value={tipoSelected}
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="TIPO_A">TIPO A - Media Tensión {'<'} 1 MW</option>
              <option value="TIPO_B">TIPO B - Media Tensión ≥ 1 MW</option>
              <option value="TIPO_C">TIPO C - Alta Tensión</option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Justificación
            </label>
            <textarea
              bind:value={justificacion}
              rows={4}
              placeholder="Describa los criterios técnicos para esta clasificación..."
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            ></textarea>
          </div>
        </div>

        <div class="mt-6 flex space-x-3">
          <button
            onclick={saveClassification}
            disabled={loading}
            class="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Guardando...' : 'Guardar'}
          </button>
          <button
            onclick={() => showClassificationModal = false}
            class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Cancelar
          </button>
        </div>
      </div>
    </div>
  </div>
{/if}

<!-- Matrix Modal -->
{#if showMatrixModal && matrixData}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9998] p-2 md:p-4">
    <div class="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[95vh] md:max-h-[90vh] overflow-y-auto">
      <div class="p-4 md:p-6">
        <div class="flex justify-between items-start mb-4">
          <div>
            <h2 class="text-xl font-bold">Matriz de Cumplimiento</h2>
            <p class="text-sm text-gray-600 mt-1">{matrixData.razon_social}</p>
          </div>
          <button
            onclick={() => showMatrixModal = false}
            class="text-gray-400 hover:text-gray-600"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div class="mb-4 p-4 bg-blue-50 rounded-lg">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <div class="text-sm text-gray-600">Tipo de Centro de Carga</div>
              <div class="font-semibold">{matrixData.tipo_centro_carga}</div>
              <div class="text-xs text-gray-500">{getTipoLabel(matrixData.tipo_centro_carga)}</div>
            </div>
            {#if matrixData.justificacion}
              <div>
                <div class="text-sm text-gray-600">Justificación</div>
                <div class="text-sm">{matrixData.justificacion}</div>
              </div>
            {/if}
          </div>
        </div>

        <div class="space-y-3">
          {#each matrixData.requerimientos as req}
            <div class="border border-gray-200 rounded-lg overflow-hidden">
              <div class="flex flex-col md:flex-row md:items-center md:justify-between p-3 md:p-4 bg-gray-50">
                <div class="flex-1">
                  <div class="flex flex-col md:flex-row md:items-center md:space-x-3 space-y-2 md:space-y-0">
                    <span class="px-2 py-1 bg-gray-200 text-gray-700 text-xs font-mono rounded w-fit">
                      {req.codigo}
                    </span>
                    <span class="font-medium text-gray-900 text-sm md:text-base">{req.nombre}</span>
                  </div>
                  {#if req.descripcion}
                    <p class="text-xs md:text-sm text-gray-600 mt-2">{req.descripcion}</p>
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
                        <div class="flex flex-col md:flex-row md:items-center md:space-x-3 space-y-2 md:space-y-0">
                          <span class="px-2 py-1 bg-gray-100 text-gray-600 text-xs font-mono rounded w-fit">
                            {child.codigo}
                          </span>
                          <span class="text-xs md:text-sm text-gray-700">{child.nombre}</span>
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
            class="w-full px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  </div>
{/if}

<!-- Toast Notifications -->
{#if errorMessage}
  <div 
    transition:fly="{{ x: 300, duration: 300 }}"
    class="fixed top-4 right-4 z-[9999] bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg shadow-lg max-w-md"
  >
    <div class="flex items-start justify-between">
      <div class="flex items-center">
        <svg class="w-5 h-5 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span>{errorMessage}</span>
      </div>
      <button onclick={() => errorMessage = ''} class="ml-4 flex-shrink-0 hover:text-red-900">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
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
    class="fixed top-4 right-4 z-[9999] bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg shadow-lg max-w-md"
  >
    <div class="flex items-start justify-between">
      <div class="flex items-center">
        <svg class="w-5 h-5 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span>{successMessage}</span>
      </div>
      <button onclick={() => successMessage = ''} class="ml-4 flex-shrink-0 hover:text-green-900">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
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
  to { width: 0%; }
}
</style>
