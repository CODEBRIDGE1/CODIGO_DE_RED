<script lang="ts">
  import { onMount } from 'svelte';

  let empresas = $state<any[]>([]);
  let loading = $state(true);
  let showModal = $state(false);

  onMount(async () => {
    // Simular carga de datos
    await new Promise(resolve => setTimeout(resolve, 500));
    
    empresas = [
      {
        id: 1,
        nombre: 'Industrias ABC S.A. de C.V.',
        rfc: 'IAB950101XXX',
        suministro: 'RPU-001234',
        clasificacion: 'GDMTH',
        obligaciones: 15,
        cumplimiento: 87,
        status: 'Activo'
      },
      {
        id: 2,
        nombre: 'Manufactura XYZ',
        rfc: 'MXY960215YYY',
        suministro: 'RPU-005678',
        clasificacion: 'GDMTO',
        obligaciones: 12,
        cumplimiento: 92,
        status: 'Activo'
      },
      {
        id: 3,
        nombre: 'Servicios LMN Corp',
        rfc: 'SLM970330ZZZ',
        suministro: 'RPU-009012',
        clasificacion: 'GDBT',
        obligaciones: 8,
        cumplimiento: 75,
        status: 'Pendiente'
      }
    ];
    
    loading = false;
  });

  function handleNew() {
    showModal = true;
  }

  function getStatusColor(status: string) {
    return status === 'Activo' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800';
  }

  function getCumplimientoColor(value: number) {
    if (value >= 90) return 'text-green-600';
    if (value >= 70) return 'text-yellow-600';
    return 'text-red-600';
  }
</script>

<div class="p-6">
  <!-- Header -->
  <div class="flex justify-between items-center mb-6">
    <div>
      <h1 class="text-3xl font-bold text-gray-900">Empresas</h1>
      <p class="text-gray-600 mt-1">Gestión del expediente electrónico y datos generales</p>
    </div>
    <button
      onclick={handleNew}
      class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
      </svg>
      <span>Nueva Empresa</span>
      <span class="text-xs opacity-75">(N)</span>
    </button>
  </div>

  <!-- Search and Filters -->
  <div class="bg-white rounded-lg shadow p-4 mb-6">
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">Buscar</label>
        <input
          type="text"
          placeholder="Nombre, RFC, RPU..."
          class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">Clasificación</label>
        <select class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
          <option value="">Todas</option>
          <option value="GDMTH">GDMTH</option>
          <option value="GDMTO">GDMTO</option>
          <option value="GDBT">GDBT</option>
        </select>
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">Estado</label>
        <select class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
          <option value="">Todos</option>
          <option value="activo">Activo</option>
          <option value="pendiente">Pendiente</option>
          <option value="inactivo">Inactivo</option>
        </select>
      </div>
    </div>
  </div>

  {#if loading}
    <!-- Loading State -->
    <div class="bg-white rounded-lg shadow p-6">
      <div class="animate-pulse space-y-4">
        {#each Array(3) as _}
          <div class="h-16 bg-gray-200 rounded"></div>
        {/each}
      </div>
    </div>
  {:else}
    <!-- Table -->
    <div class="bg-white rounded-lg shadow overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Empresa</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">RFC</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Suministro</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Clasificación</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Obligaciones</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cumplimiento</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          {#each empresas as empresa}
            <tr class="hover:bg-gray-50 transition-colors">
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm font-medium text-gray-900">{empresa.nombre}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{empresa.rfc}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{empresa.suministro}</td>
              <td class="px-6 py-4 whitespace-nowrap">
                <span class="px-2 py-1 text-xs font-semibold rounded bg-blue-100 text-blue-800">
                  {empresa.clasificacion}
                </span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600 text-center">
                {empresa.obligaciones}
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="flex items-center">
                  <span class="text-sm font-semibold {getCumplimientoColor(empresa.cumplimiento)}">
                    {empresa.cumplimiento}%
                  </span>
                  <div class="ml-2 flex-1 w-16 bg-gray-200 rounded-full h-2">
                    <div
                      class="h-2 rounded-full {empresa.cumplimiento >= 90 ? 'bg-green-500' : empresa.cumplimiento >= 70 ? 'bg-yellow-500' : 'bg-red-500'}"
                      style="width: {empresa.cumplimiento}%"
                    ></div>
                  </div>
                </div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <span class="px-2 py-1 text-xs font-semibold rounded {getStatusColor(empresa.status)}">
                  {empresa.status}
                </span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm">
                <div class="flex space-x-2">
                  <button class="text-blue-600 hover:text-blue-800" title="Ver detalles">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  </button>
                  <button class="text-green-600 hover:text-green-800" title="Editar">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </button>
                </div>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div class="mt-4 flex justify-between items-center">
      <div class="text-sm text-gray-600">
        Mostrando 1-{empresas.length} de {empresas.length} empresas
      </div>
      <div class="flex space-x-2">
        <button class="px-3 py-1 border border-gray-300 rounded hover:bg-gray-50" disabled>
          Anterior
        </button>
        <button class="px-3 py-1 border border-gray-300 rounded hover:bg-gray-50" disabled>
          Siguiente
        </button>
      </div>
    </div>
  {/if}
</div>

{#if showModal}
  <!-- Modal Placeholder -->
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-white rounded-lg p-6 max-w-2xl w-full mx-4">
      <h2 class="text-2xl font-bold mb-4">Nueva Empresa</h2>
      <p class="text-gray-600 mb-4">Formulario de alta de empresa en construcción...</p>
      <button
        onclick={() => showModal = false}
        class="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg"
      >
        Cerrar
      </button>
    </div>
  </div>
{/if}
