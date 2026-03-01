<script lang="ts">
  import { onMount } from 'svelte';
  import { authStore } from '../../stores/auth';

  interface ComplianceRequirement {
    id: number;
    codigo: string;
    nombre: string;
    descripcion: string | null;
    parent_id: number | null;
    orden: number;
    is_active: boolean;
    created_at: string;
    updated_at: string;
    children?: ComplianceRequirement[];
  }

  interface RequirementForm {
    codigo: string;
    nombre: string;
    descripcion: string;
    parent_id: number | null;
    orden: number;
    is_active: boolean;
  }

  interface ComplianceRule {
    id: number;
    requirement_id: number;
    tipo_centro_carga: 'TIPO_A' | 'TIPO_B' | 'TIPO_C';
    estado_aplicabilidad: 'APLICA' | 'NO_APLICA' | 'APLICA_RDC' | 'APLICA_TIC';
    notas: string | null;
  }

  interface RuleForm {
    tipo_centro_carga: 'TIPO_A' | 'TIPO_B' | 'TIPO_C';
    estado_aplicabilidad: 'APLICA' | 'NO_APLICA' | 'APLICA_RDC' | 'APLICA_TIC';
    notas: string;
  }

  let requirements = $state<ComplianceRequirement[]>([]);
  let loading = $state(true);
  let showModal = $state(false);
  let isEditing = $state(false);
  let currentRequirement = $state<ComplianceRequirement | null>(null);
  let searchTerm = $state('');
  let showDeleteModal = $state(false);
  let requirementToDelete = $state<ComplianceRequirement | null>(null);
  let errorMessage = $state('');
  let successMessage = $state('');

  // Rules management
  let showRulesModal = $state(false);
  let currentRequirementForRules = $state<ComplianceRequirement | null>(null);
  let rules = $state<ComplianceRule[]>([]);
  let loadingRules = $state(false);
  let showRuleFormModal = $state(false);
  let isEditingRule = $state(false);
  let currentRule = $state<ComplianceRule | null>(null);

  let form = $state<RequirementForm>({
    codigo: '',
    nombre: '',
    descripcion: '',
    parent_id: null,
    orden: 0,
    is_active: true
  });

  let ruleForm = $state<RuleForm>({
    tipo_centro_carga: 'TIPO_A',
    estado_aplicabilidad: 'NO_APLICA',
    notas: ''
  });

  const tiposCentroCarga = [
    { value: 'TIPO_A', label: 'Tipo A - Media Tensión < 1 MW' },
    { value: 'TIPO_B', label: 'Tipo B - Media Tensión >= 1 MW' },
    { value: 'TIPO_C', label: 'Tipo C - Alta Tensión' }
  ];

  const estadosAplicabilidad = [
    { value: 'NO_APLICA', label: 'No Aplica' },
    { value: 'APLICA', label: 'Aplica' },
    { value: 'APLICA_RDC', label: 'Aplica solo RDC' },
    { value: 'APLICA_TIC', label: 'Aplica conforme Manual TIC' }
  ];

  // Obtener lista plana de todos los requirements para el dropdown de padre
  const flatRequirements = $derived(
    requirements.flatMap(req => [req, ...(req.children || [])])
  );

  const filteredRequirements = $derived(
    requirements.filter(req => {
      const matchesSearch = req.codigo.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          req.nombre.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          (req.descripcion?.toLowerCase().includes(searchTerm.toLowerCase()) ?? false);
      return matchesSearch;
    })
  );

  onMount(() => {
    loadRequirements();
  });

  async function loadRequirements() {
    try {
      loading = true;
      const response = await authStore.fetch(
        `${import.meta.env.VITE_API_BASE_URL}/api/v1/compliance/admin/requirements`,
        {
          headers: { 'Authorization': `Bearer ${$authStore.accessToken}` }
        }
      );

      if (!response.ok) throw new Error('Error al cargar obligaciones');
      
      requirements = await response.json();
    } catch (error: any) {
      console.error('Error:', error);
      errorMessage = error.message || 'Error al cargar obligaciones';
    } finally {
      loading = false;
    }
  }

  function openCreateModal() {
    isEditing = false;
    currentRequirement = null;
    form = {
      codigo: '',
      nombre: '',
      descripcion: '',
      parent_id: null,
      orden: 0,
      is_active: true
    };
    showModal = true;
  }

  function openEditModal(req: ComplianceRequirement) {
    isEditing = true;
    currentRequirement = req;
    form = {
      codigo: req.codigo,
      nombre: req.nombre,
      descripcion: req.descripcion || '',
      parent_id: req.parent_id,
      orden: req.orden,
      is_active: req.is_active
    };
    showModal = true;
  }

  function closeModal() {
    showModal = false;
    currentRequirement = null;
    errorMessage = '';
  }

  async function handleSubmit() {
    try {
      errorMessage = '';
      const url = isEditing
        ? `${import.meta.env.VITE_API_BASE_URL}/api/v1/compliance/admin/requirements/${currentRequirement!.id}`
        : `${import.meta.env.VITE_API_BASE_URL}/api/v1/compliance/admin/requirements`;
      
      const method = isEditing ? 'PUT' : 'POST';

      const response = await authStore.fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${$authStore.accessToken}`
        },
        body: JSON.stringify(form)
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Error al guardar');
      }

      await loadRequirements();
      closeModal();
      successMessage = isEditing ? 'Obligación actualizada correctamente' : 'Obligación creada correctamente';
      setTimeout(() => successMessage = '', 3000);
    } catch (error: any) {
      console.error('Error:', error);
      errorMessage = error.message || 'Error al guardar la obligación';
    }
  }

  function confirmDelete(req: ComplianceRequirement) {
    requirementToDelete = req;
    showDeleteModal = true;
  }

  async function handleDelete() {
    if (!requirementToDelete) return;

    try {
      const response = await authStore.fetch(
        `${import.meta.env.VITE_API_BASE_URL}/api/v1/compliance/admin/requirements/${requirementToDelete.id}`,
        {
          method: 'DELETE',
          headers: { 'Authorization': `Bearer ${$authStore.accessToken}` }
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Error al eliminar');
      }

      await loadRequirements();
      showDeleteModal = false;
      requirementToDelete = null;
      successMessage = 'Obligación eliminada correctamente';
      setTimeout(() => successMessage = '', 3000);
    } catch (error: any) {
      console.error('Error:', error);
      errorMessage = error.message || 'Error al eliminar la obligación';
      showDeleteModal = false;
    }
  }

  function getParentName(parentId: number | null): string {
    if (!parentId) return '-';
    const parent = flatRequirements.find(r => r.id === parentId);
    return parent ? `${parent.codigo} - ${parent.nombre}` : '-';
  }

  // === RULES MANAGEMENT ===
  
  async function openRulesModal(req: ComplianceRequirement) {
    currentRequirementForRules = req;
    showRulesModal = true;
    await loadRules(req.id);
  }

  function closeRulesModal() {
    showRulesModal = false;
    currentRequirementForRules = null;
    rules = [];
  }

  async function loadRules(requirementId: number) {
    try {
      loadingRules = true;
      const response = await authStore.fetch(
        `${import.meta.env.VITE_API_BASE_URL}/api/v1/compliance/admin/rules`,
        {
          headers: { 'Authorization': `Bearer ${$authStore.accessToken}` }
        }
      );

      if (!response.ok) throw new Error('Error al cargar reglas');
      
      const allRules = await response.json();
      rules = allRules.filter((r: ComplianceRule) => r.requirement_id === requirementId);
    } catch (error: any) {
      console.error('Error:', error);
      errorMessage = error.message || 'Error al cargar reglas';
    } finally {
      loadingRules = false;
    }
  }

  function openCreateRuleModal() {
    isEditingRule = false;
    currentRule = null;
    ruleForm = {
      tipo_centro_carga: 'TIPO_A',
      estado_aplicabilidad: 'NO_APLICA',
      notas: ''
    };
    showRuleFormModal = true;
  }

  function openEditRuleModal(rule: ComplianceRule) {
    isEditingRule = true;
    currentRule = rule;
    ruleForm = {
      tipo_centro_carga: rule.tipo_centro_carga,
      estado_aplicabilidad: rule.estado_aplicabilidad,
      notas: rule.notas || ''
    };
    showRuleFormModal = true;
  }

  function closeRuleFormModal() {
    showRuleFormModal = false;
    currentRule = null;
  }

  async function handleRuleSubmit() {
    if (!currentRequirementForRules) return;

    try {
      errorMessage = '';
      const url = isEditingRule
        ? `${import.meta.env.VITE_API_BASE_URL}/api/v1/compliance/admin/rules/${currentRule!.id}`
        : `${import.meta.env.VITE_API_BASE_URL}/api/v1/compliance/admin/rules`;
      
      const method = isEditingRule ? 'PUT' : 'POST';
      const body = isEditingRule 
        ? { estado_aplicabilidad: ruleForm.estado_aplicabilidad, notas: ruleForm.notas }
        : { requirement_id: currentRequirementForRules.id, ...ruleForm };

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
        throw new Error(error.detail || 'Error al guardar regla');
      }

      await loadRules(currentRequirementForRules.id);
      closeRuleFormModal();
      successMessage = isEditingRule ? 'Regla actualizada correctamente' : 'Regla creada correctamente';
      setTimeout(() => successMessage = '', 3000);
    } catch (error: any) {
      console.error('Error:', error);
      errorMessage = error.message || 'Error al guardar la regla';
    }
  }

  async function deleteRule(rule: ComplianceRule) {
    if (!confirm(`¿Eliminar regla para ${getTipoLabel(rule.tipo_centro_carga)}?`)) return;

    try {
      const response = await authStore.fetch(
        `${import.meta.env.VITE_API_BASE_URL}/api/v1/compliance/admin/rules/${rule.id}`,
        {
          method: 'DELETE',
          headers: { 'Authorization': `Bearer ${$authStore.accessToken}` }
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Error al eliminar');
      }

      if (currentRequirementForRules) {
        await loadRules(currentRequirementForRules.id);
      }
      successMessage = 'Regla eliminada correctamente';
      setTimeout(() => successMessage = '', 3000);
    } catch (error: any) {
      console.error('Error:', error);
      errorMessage = error.message || 'Error al eliminar la regla';
    }
  }

  function getTipoLabel(tipo: string): string {
    return tiposCentroCarga.find(t => t.value === tipo)?.label || tipo;
  }

  function getEstadoLabel(estado: string): string {
    return estadosAplicabilidad.find(e => e.value === estado)?.label || estado;
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
</script>

<div class="p-6">
  <!-- Header -->
  <div class="flex justify-between items-center mb-6">
    <div>
      <h1 class="text-2xl font-bold text-gray-900">Catálogo de Obligaciones</h1>
      <p class="text-gray-600 mt-1">Administra el catálogo de obligaciones para la matriz de cumplimiento</p>
    </div>
    <button
      onclick={openCreateModal}
      class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2 transition-colors"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
      </svg>
      Nueva Obligación
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

  <!-- Filters -->
  <div class="bg-white rounded-lg shadow-sm p-4 mb-6">
    <div class="flex gap-4">
      <div class="flex-1">
        <input
          type="text"
          bind:value={searchTerm}
          placeholder="Buscar por código, nombre o descripción..."
          class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>
      <button
        onclick={loadRequirements}
        class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2"
        title="Recargar"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
        </svg>
        Recargar
      </button>
    </div>
  </div>

  <!-- Table -->
  {#if loading}
    <div class="text-center py-12">
      <div class="inline-block animate-spin rounded-full h-12 w-12 border-4 border-gray-300 border-t-blue-600"></div>
      <p class="mt-4 text-gray-600">Cargando obligaciones...</p>
    </div>
  {:else if filteredRequirements.length === 0}
    <div class="bg-white rounded-lg shadow-sm p-12 text-center">
      <svg class="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
      </svg>
      <p class="text-gray-600">No se encontraron obligaciones</p>
      <button
        onclick={openCreateModal}
        class="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
      >
        Crear primera obligación
      </button>
    </div>
  {:else}
    <div class="bg-white rounded-lg shadow-sm overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Código</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nombre</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Padre</th>
            <th class="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Orden</th>
            <th class="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Hijos</th>
            <th class="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
            <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          {#each filteredRequirements as req}
            <!-- Requirement padre -->
            <tr class="hover:bg-gray-50">
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm font-mono font-semibold text-gray-900">{req.codigo}</div>
              </td>
              <td class="px-6 py-4">
                <div class="text-sm font-medium text-gray-900">{req.nombre}</div>
                {#if req.descripcion}
                  <div class="text-xs text-gray-500 mt-1 line-clamp-2">{req.descripcion}</div>
                {/if}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {getParentName(req.parent_id)}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-center">
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                  {req.orden}
                </span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-center">
                {#if req.children && req.children.length > 0}
                  <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    {req.children.length}
                  </span>
                {:else}
                  <span class="text-gray-400 text-sm">-</span>
                {/if}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-center">
                <span 
                  class="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full"
                  class:bg-green-100={req.is_active}
                  class:text-green-800={req.is_active}
                  class:bg-red-100={!req.is_active}
                  class:text-red-800={!req.is_active}
                >
                  {req.is_active ? 'Activo' : 'Inactivo'}
                </span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                <div class="flex items-center justify-end gap-2">
                  <button
                    onclick={() => openRulesModal(req)}
                    class="p-1.5 text-purple-600 hover:text-purple-900 hover:bg-purple-50 rounded transition-colors"
                    title="Configurar reglas"
                  >
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"/>
                    </svg>
                  </button>
                  <button
                    onclick={() => openEditModal(req)}
                    class="p-1.5 text-blue-600 hover:text-blue-900 hover:bg-blue-50 rounded transition-colors"
                    title="Editar"
                  >
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                    </svg>
                  </button>
                  <button
                    onclick={() => confirmDelete(req)}
                    class="p-1.5 text-red-600 hover:text-red-900 hover:bg-red-50 rounded transition-colors"
                    title="Eliminar"
                  >
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                    </svg>
                  </button>
                </div>
              </td>
            </tr>

            <!-- Children (hijos) -->
            {#if req.children && req.children.length > 0}
              {#each req.children as child}
                <tr class="hover:bg-blue-50 bg-blue-25">
                  <td class="px-6 py-3 whitespace-nowrap pl-12">
                    <div class="text-sm font-mono text-gray-700 flex items-center gap-2">
                      <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                      </svg>
                      {child.codigo}
                    </div>
                  </td>
                  <td class="px-6 py-3">
                    <div class="text-sm text-gray-900">{child.nombre}</div>
                    {#if child.descripcion}
                      <div class="text-xs text-gray-500 mt-1 line-clamp-1">{child.descripcion}</div>
                    {/if}
                  </td>
                  <td class="px-6 py-3 whitespace-nowrap text-sm text-gray-500">
                    <span class="text-xs text-blue-600">{req.codigo}</span>
                  </td>
                  <td class="px-6 py-3 whitespace-nowrap text-center">
                    <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-700">
                      {child.orden}
                    </span>
                  </td>
                  <td class="px-6 py-3 whitespace-nowrap text-center">
                    <span class="text-gray-400 text-sm">-</span>
                  </td>
                  <td class="px-6 py-3 whitespace-nowrap text-center">
                    <span 
                      class="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full"
                      class:bg-green-100={child.is_active}
                      class:text-green-800={child.is_active}
                      class:bg-red-100={!child.is_active}
                      class:text-red-800={!child.is_active}
                    >
                      {child.is_active ? 'Activo' : 'Inactivo'}
                    </span>
                  </td>
                  <td class="px-6 py-3 whitespace-nowrap text-right text-sm font-medium">
                    <div class="flex items-center justify-end gap-2">
                      <button
                        onclick={() => openRulesModal(child)}
                        class="p-1.5 text-purple-600 hover:text-purple-900 hover:bg-purple-50 rounded transition-colors"
                        title="Configurar reglas"
                      >
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"/>
                        </svg>
                      </button>
                      <button
                        onclick={() => openEditModal(child)}
                        class="p-1.5 text-blue-600 hover:text-blue-900 hover:bg-blue-50 rounded transition-colors"
                        title="Editar"
                      >
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                        </svg>
                      </button>
                      <button
                        onclick={() => confirmDelete(child)}
                        class="p-1.5 text-red-600 hover:text-red-900 hover:bg-red-50 rounded transition-colors"
                        title="Eliminar"
                      >
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                        </svg>
                      </button>
                    </div>
                  </td>
                </tr>
              {/each}
            {/if}
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>

<!-- Create/Edit Modal -->
{#if showModal}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
      <div class="p-6">
        <div class="flex justify-between items-center mb-6">
          <h2 class="text-2xl font-bold text-gray-900">
            {isEditing ? 'Editar Obligación' : 'Nueva Obligación'}
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
                bind:value={form.codigo}
                required
                maxlength="20"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono"
                placeholder="Ej: 1.1"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Orden</label>
              <input
                type="number"
                bind:value={form.orden}
                min="0"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div class="col-span-2">
              <label class="block text-sm font-medium text-gray-700 mb-1">Nombre *</label>
              <input
                type="text"
                bind:value={form.nombre}
                required
                maxlength="200"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Nombre de la obligación"
              />
            </div>

            <div class="col-span-2">
              <label class="block text-sm font-medium text-gray-700 mb-1">Descripción</label>
              <textarea
                bind:value={form.descripcion}
                rows="3"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Descripción detallada de la obligación..."
              ></textarea>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Obligación Padre</label>
              <select
                bind:value={form.parent_id}
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value={null}>Sin padre (nivel superior)</option>
                {#each flatRequirements as req}
                  {#if !isEditing || req.id !== currentRequirement?.id}
                    <option value={req.id}>{req.codigo} - {req.nombre}</option>
                  {/if}
                {/each}
              </select>
              <p class="mt-1 text-xs text-gray-500">Selecciona una obligación padre para crear una sub-obligación</p>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Estado</label>
              <div class="flex items-center h-10">
                <label class="flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    bind:checked={form.is_active}
                    class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <span class="ml-2 text-sm text-gray-700">
                    {form.is_active ? 'Activa' : 'Inactiva'}
                  </span>
                </label>
              </div>
            </div>
          </div>

          <div class="flex justify-end gap-3 mt-6 pt-6 border-t border-gray-200">
            <button
              type="button"
              onclick={closeModal}
              class="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              {isEditing ? 'Actualizar' : 'Crear'} Obligación
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
{/if}

<!-- Delete Confirmation Modal -->
{#if showDeleteModal && requirementToDelete}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
      <div class="flex items-center gap-3 mb-4">
        <div class="flex-shrink-0 w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
          <svg class="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
          </svg>
        </div>
        <h3 class="text-lg font-bold text-gray-900">Confirmar Eliminación</h3>
      </div>
      
      <p class="text-gray-600 mb-2">
        ¿Estás seguro de que deseas eliminar la obligación?
      </p>
      <div class="bg-gray-50 p-3 rounded-lg mb-4">
        <p class="text-sm"><strong class="text-gray-700">Código:</strong> {requirementToDelete.codigo}</p>
        <p class="text-sm"><strong class="text-gray-700">Nombre:</strong> {requirementToDelete.nombre}</p>
      </div>
      
      {#if requirementToDelete.children && requirementToDelete.children.length > 0}
        <div class="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
          <p class="text-sm text-yellow-800">
            <strong>Advertencia:</strong> Esta obligación tiene {requirementToDelete.children.length} sub-obligación(es).
            Debes eliminar las sub-obligaciones primero.
          </p>
        </div>
      {/if}

      <div class="flex justify-end gap-3">
        <button
          onclick={() => { showDeleteModal = false; requirementToDelete = null; }}
          class="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
        >
          Cancelar
        </button>
        <button
          onclick={handleDelete}
          class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
        >
          Eliminar
        </button>
      </div>
    </div>
  </div>
{/if}

<!-- Rules Management Modal -->
{#if showRulesModal && currentRequirementForRules}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
      <div class="p-6">
        <div class="flex justify-between items-center mb-6">
          <div>
            <h2 class="text-2xl font-bold text-gray-900">Reglas de Aplicabilidad</h2>
            <p class="text-sm text-gray-600 mt-1">
              <strong>{currentRequirementForRules.codigo}</strong> - {currentRequirementForRules.nombre}
            </p>
          </div>
          <button onclick={closeRulesModal} class="text-gray-400 hover:text-gray-600">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>

        <div class="mb-4">
          <button
            onclick={openCreateRuleModal}
            class="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 flex items-center gap-2"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
            </svg>
            Nueva Regla
          </button>
        </div>

        {#if loadingRules}
          <div class="text-center py-8">
            <div class="inline-block animate-spin rounded-full h-8 w-8 border-4 border-gray-300 border-t-purple-600"></div>
            <p class="mt-2 text-gray-600">Cargando reglas...</p>
          </div>
        {:else if rules.length === 0}
          <div class="bg-gray-50 rounded-lg p-8 text-center">
            <svg class="w-12 h-12 mx-auto text-gray-400 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"/>
            </svg>
            <p class="text-gray-600">No hay reglas configuradas</p>
            <p class="text-sm text-gray-500 mt-1">Define qué tipos de empresa deben cumplir esta obligación</p>
          </div>
        {:else}
          <div class="space-y-3">
            {#each rules as rule}
              <div class="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
                <div class="flex items-start justify-between">
                  <div class="flex-1">
                    <div class="flex items-center gap-3 mb-2">
                      <span class="font-semibold text-gray-900">{getTipoLabel(rule.tipo_centro_carga)}</span>
                      <span class="px-2.5 py-0.5 rounded-full text-xs font-semibold {getEstadoColor(rule.estado_aplicabilidad)}">
                        {getEstadoLabel(rule.estado_aplicabilidad)}
                      </span>
                    </div>
                    {#if rule.notas}
                      <p class="text-sm text-gray-600">{rule.notas}</p>
                    {/if}
                  </div>
                  <div class="flex items-center gap-2 ml-4">
                    <button
                      onclick={() => openEditRuleModal(rule)}
                      class="p-1.5 text-blue-600 hover:text-blue-900 hover:bg-blue-50 rounded"
                      title="Editar"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                      </svg>
                    </button>
                    <button
                      onclick={() => deleteRule(rule)}
                      class="p-1.5 text-red-600 hover:text-red-900 hover:bg-red-50 rounded"
                      title="Eliminar"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            {/each}
          </div>
        {/if}

        <div class="mt-6 pt-4 border-t border-gray-200">
          <button
            onclick={closeRulesModal}
            class="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  </div>
{/if}

<!-- Rule Form Modal (Create/Edit) -->
{#if showRuleFormModal}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60] p-4">
    <div class="bg-white rounded-lg shadow-xl max-w-lg w-full">
      <div class="p-6">
        <div class="flex justify-between items-center mb-6">
          <h3 class="text-xl font-bold text-gray-900">
            {isEditingRule ? 'Editar Regla' : 'Nueva Regla'}
          </h3>
          <button onclick={closeRuleFormModal} class="text-gray-400 hover:text-gray-600">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>

        {#if errorMessage}
          <div class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-800 text-sm">
            {errorMessage}
          </div>
        {/if}

        <form onsubmit={(e) => { e.preventDefault(); handleRuleSubmit(); }} class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Tipo de Centro de Carga *</label>
            <select
              bind:value={ruleForm.tipo_centro_carga}
              disabled={isEditingRule}
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
            >
              {#each tiposCentroCarga as tipo}
                <option value={tipo.value}>{tipo.label}</option>
              {/each}
            </select>
            {#if isEditingRule}
              <p class="mt-1 text-xs text-gray-500">El tipo de empresa no se puede cambiar</p>
            {/if}
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Estado de Aplicabilidad *</label>
            <select
              bind:value={ruleForm.estado_aplicabilidad}
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            >
              {#each estadosAplicabilidad as estado}
                <option value={estado.value}>{estado.label}</option>
              {/each}
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Notas</label>
            <textarea
              bind:value={ruleForm.notas}
              rows="3"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              placeholder="Notas adicionales sobre la aplicabilidad..."
            ></textarea>
          </div>

          <div class="flex justify-end gap-3 pt-4 border-t border-gray-200">
            <button
              type="button"
              onclick={closeRuleFormModal}
              class="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              class="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
            >
              {isEditingRule ? 'Actualizar' : 'Crear'} Regla
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
{/if}
