<script lang="ts">
  import { onMount } from 'svelte';
  import { authStore } from '../../stores/auth';

  // ─── Types ────────────────────────────────────────────────────────────────
  interface SystemModule {
    id: number;
    key: string;
    name: string;
    description?: string | null;
    icon?: string | null;
    sort_order: number;
  }

  interface SecurityLevel {
    id: number;
    name: string;
    description?: string | null;
    color: string;
    is_active: boolean;
    created_at: string;
    modules: SystemModule[];
    users_count: number;
  }

  // ─── State ────────────────────────────────────────────────────────────────
  let levels = $state<SecurityLevel[]>([]);
  let allModules = $state<SystemModule[]>([]);
  let loading = $state(false);
  let errorMessage = $state('');
  let successMessage = $state('');

  // Modal
  let showModal = $state(false);
  let editingLevel = $state<SecurityLevel | null>(null);
  let saving = $state(false);

  // Form
  let formName = $state('');
  let formDescription = $state('');
  let formColor = $state('blue');
  let formModuleIds = $state<Set<number>>(new Set());

  // Confirmación borrar
  let levelToDelete = $state<SecurityLevel | null>(null);
  let showDeleteConfirm = $state(false);
  let deleting = $state(false);

  // ─── Colors ───────────────────────────────────────────────────────────────
  const COLOR_OPTIONS = [
    { value: 'blue',   label: 'Azul',     bg: 'bg-blue-100',   text: 'text-blue-700',   dot: 'bg-blue-500' },
    { value: 'green',  label: 'Verde',    bg: 'bg-green-100',  text: 'text-green-700',  dot: 'bg-green-500' },
    { value: 'red',    label: 'Rojo',     bg: 'bg-red-100',    text: 'text-red-700',    dot: 'bg-red-500' },
    { value: 'yellow', label: 'Amarillo', bg: 'bg-yellow-100', text: 'text-yellow-700', dot: 'bg-yellow-500' },
    { value: 'purple', label: 'Morado',   bg: 'bg-purple-100', text: 'text-purple-700', dot: 'bg-purple-500' },
    { value: 'gray',   label: 'Gris',     bg: 'bg-gray-100',   text: 'text-gray-700',   dot: 'bg-gray-500' },
    { value: 'orange', label: 'Naranja',  bg: 'bg-orange-100', text: 'text-orange-700', dot: 'bg-orange-500' },
    { value: 'teal',   label: 'Verde azulado', bg: 'bg-teal-100', text: 'text-teal-700', dot: 'bg-teal-500' },
  ];

  function getColorStyle(color: string) {
    return COLOR_OPTIONS.find(c => c.value === color) ?? COLOR_OPTIONS[0];
  }

  // ─── Module Icons ─────────────────────────────────────────────────────────
  const MODULE_ICONS: Record<string, string> = {
    'chart-bar':       'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z',
    'building-office': 'M3 21V7a2 2 0 012-2h4a2 2 0 012 2v2h4a2 2 0 012 2v10M9 21V9m0 0H5m4 0h4m4 0v12M13 21v-6a2 2 0 012-2h2a2 2 0 012 2v6',
    'clipboard-list':  'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01',
    'folder-open':     'M5 19a2 2 0 01-2-2V7a2 2 0 012-2h4l2 2h4a2 2 0 012 2v1M5 19h14a2 2 0 002-2v-5a2 2 0 00-2-2H9a2 2 0 00-2 2v5a2 2 0 01-2 2z',
    'document':        'M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z',
    'chart-pie':       'M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z',
    'users':           'M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z',
    'shield-check':    'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z',
    'currency-dollar': 'M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
  };

  function getModuleIcon(icon?: string | null): string {
    return (icon && MODULE_ICONS[icon]) ? MODULE_ICONS[icon] : MODULE_ICONS['document'];
  }

  // ─── API calls ────────────────────────────────────────────────────────────
  const API = import.meta.env.VITE_API_BASE_URL;

  async function fetchData() {
    loading = true;
    errorMessage = '';
    try {
      const headers = { Authorization: `Bearer ${$authStore.accessToken}` };
      const [levelsRes, modulesRes] = await Promise.all([
        fetch(`${API}/api/v1/admin/security-levels/`, { headers }),
        fetch(`${API}/api/v1/admin/security-levels/modules/`, { headers }),
      ]);
      if (!levelsRes.ok || !modulesRes.ok) throw new Error('Error al cargar datos');
      levels = await levelsRes.json();
      allModules = await modulesRes.json();
    } catch (e: any) {
      errorMessage = e.message || 'Error inesperado';
    } finally {
      loading = false;
    }
  }

  // Cargar al montar
  onMount(() => { fetchData(); });

  // ─── Modal helpers ────────────────────────────────────────────────────────
  function openCreate() {
    editingLevel = null;
    formName = '';
    formDescription = '';
    formColor = 'blue';
    formModuleIds = new Set();
    showModal = true;
    errorMessage = '';
  }

  function openEdit(level: SecurityLevel) {
    editingLevel = level;
    formName = level.name;
    formDescription = level.description ?? '';
    formColor = level.color;
    formModuleIds = new Set(level.modules.map(m => m.id));
    showModal = true;
    errorMessage = '';
  }

  function toggleModule(id: number) {
    const next = new Set(formModuleIds);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    formModuleIds = next;
  }

  function selectAllModules() {
    formModuleIds = new Set(allModules.map(m => m.id));
  }

  function clearAllModules() {
    formModuleIds = new Set();
  }

  async function saveLevel() {
    if (!formName.trim()) { errorMessage = 'El nombre es requerido'; return; }
    saving = true;
    errorMessage = '';
    try {
      const headers = {
        Authorization: `Bearer ${$authStore.accessToken}`,
        'Content-Type': 'application/json',
      };
      const body = JSON.stringify({
        name: formName.trim(),
        description: formDescription.trim() || null,
        color: formColor,
        module_ids: Array.from(formModuleIds),
      });
      const url = editingLevel
        ? `${API}/api/v1/admin/security-levels/${editingLevel.id}`
        : `${API}/api/v1/admin/security-levels/`;
      const method = editingLevel ? 'PUT' : 'POST';
      const res = await authStore.fetch(url, { method, headers, body });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Error al guardar');
      }
      successMessage = editingLevel ? 'Nivel actualizado correctamente' : 'Nivel creado correctamente';
      showModal = false;
      await fetchData();
      setTimeout(() => successMessage = '', 3000);
    } catch (e: any) {
      errorMessage = e.message || 'Error inesperado';
    } finally {
      saving = false;
    }
  }

  function confirmDelete(level: SecurityLevel) {
    levelToDelete = level;
    showDeleteConfirm = true;
  }

  async function deleteLevel() {
    if (!levelToDelete) return;
    deleting = true;
    try {
      const res = await authStore.fetch(`${API}/api/v1/admin/security-levels/${levelToDelete.id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${$authStore.accessToken}` },
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Error al eliminar');
      }
      successMessage = 'Nivel eliminado correctamente';
      showDeleteConfirm = false;
      levelToDelete = null;
      await fetchData();
      setTimeout(() => successMessage = '', 3000);
    } catch (e: any) {
      errorMessage = e.message || 'Error al eliminar';
      showDeleteConfirm = false;
    } finally {
      deleting = false;
    }
  }
</script>

<!-- ─── Main Content ───────────────────────────────────────────────────────── -->
<div class="p-6 max-w-6xl mx-auto">

  <!-- Header -->
  <div class="flex items-center justify-between mb-6">
    <div>
      <h1 class="text-2xl font-bold text-gray-900">Niveles de Seguridad</h1>
      <p class="text-sm text-gray-500 mt-1">Define qué módulos puede acceder cada tipo de usuario tenant</p>
    </div>
    <button
      onclick={openCreate}
      class="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
    >
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
      </svg>
      Nuevo Nivel
    </button>
  </div>

  <!-- Alerts -->
  {#if successMessage}
    <div class="mb-4 flex items-center gap-2 px-4 py-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">
      <svg class="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
      </svg>
      {successMessage}
    </div>
  {/if}
  {#if errorMessage && !showModal}
    <div class="mb-4 flex items-center gap-2 px-4 py-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
      <svg class="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
      </svg>
      {errorMessage}
    </div>
  {/if}

  <!-- Loading -->
  {#if loading}
    <div class="flex justify-center items-center py-20">
      <svg class="animate-spin w-8 h-8 text-blue-600" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
      </svg>
    </div>

  <!-- Empty state -->
  {:else if levels.length === 0}
    <div class="flex flex-col items-center justify-center py-20 text-center">
      <div class="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
        <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
        </svg>
      </div>
      <p class="text-gray-500 text-base font-medium">No hay niveles de seguridad</p>
      <p class="text-gray-400 text-sm mt-1">Crea el primer nivel para asignarlo a los usuarios</p>
      <button onclick={openCreate} class="mt-4 px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700">
        Crear primer nivel
      </button>
    </div>

  <!-- Grid of levels -->
  {:else}
    <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      {#each levels as level (level.id)}
        {@const cs = getColorStyle(level.color)}
        <div class="bg-white border border-gray-200 rounded-xl overflow-hidden hover:shadow-md transition-shadow">

          <!-- Card header -->
          <div class="px-5 py-4 border-b border-gray-100 flex items-start justify-between gap-3">
            <div class="flex items-center gap-3 min-w-0">
              <span class={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${cs.bg} ${cs.text}`}>
                <span class={`w-2 h-2 rounded-full ${cs.dot}`}></span>
                {level.name}
              </span>
              {#if !level.is_active}
                <span class="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">Inactivo</span>
              {/if}
            </div>
            <div class="flex items-center gap-1 flex-shrink-0">
              <button
                onclick={() => openEdit(level)}
                class="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                title="Editar"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                </svg>
              </button>
              <button
                onclick={() => confirmDelete(level)}
                class="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                title="Eliminar"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                </svg>
              </button>
            </div>
          </div>

          <!-- Description -->
          {#if level.description}
            <p class="px-5 pt-3 text-xs text-gray-500 leading-relaxed">{level.description}</p>
          {/if}

          <!-- Modules -->
          <div class="px-5 py-3">
            <p class="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">
              Módulos accesibles ({level.modules.length})
            </p>
            {#if level.modules.length === 0}
              <p class="text-xs text-gray-400 italic">Sin módulos asignados</p>
            {:else}
              <div class="flex flex-wrap gap-1.5">
                {#each [...level.modules].sort((a, b) => a.sort_order - b.sort_order) as mod}
                  <span class="inline-flex items-center gap-1 px-2 py-1 bg-gray-50 border border-gray-200 rounded-md text-xs text-gray-600">
                    <svg class="w-3 h-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d={getModuleIcon(mod.icon)}/>
                    </svg>
                    {mod.name}
                  </span>
                {/each}
              </div>
            {/if}
          </div>

          <!-- Footer -->
          <div class="px-5 py-3 bg-gray-50 border-t border-gray-100 flex items-center justify-between">
            <span class="text-xs text-gray-500">
              <span class="font-medium text-gray-700">{level.users_count}</span>
              usuario{level.users_count !== 1 ? 's' : ''} asignado{level.users_count !== 1 ? 's' : ''}
            </span>
            <span class="text-xs text-gray-400">
              {new Date(level.created_at).toLocaleDateString('es-MX', { day: '2-digit', month: 'short', year: 'numeric' })}
            </span>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>

<!-- ─── Modal crear/editar ─────────────────────────────────────────────────── -->
{#if showModal}
  <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
    <div class="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col overflow-hidden">

      <!-- Header -->
      <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200">
        <div>
          <h2 class="text-lg font-semibold text-gray-900">
            {editingLevel ? 'Editar nivel de seguridad' : 'Nuevo nivel de seguridad'}
          </h2>
          <p class="text-sm text-gray-500 mt-0.5">Define nombre, color y módulos accesibles</p>
        </div>
        <button
          onclick={() => showModal = false}
          class="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
          </svg>
        </button>
      </div>

      <!-- Body -->
      <div class="flex-1 overflow-y-auto px-6 py-5 space-y-5">

        <!-- Error en modal -->
        {#if errorMessage}
          <div class="flex items-center gap-2 px-3 py-2.5 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            <svg class="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            {errorMessage}
          </div>
        {/if}

        <!-- Nombre -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">
            Nombre <span class="text-red-500">*</span>
          </label>
          <input
            type="text"
            bind:value={formName}
            placeholder="Ej. Administrador, Consultor, Solo lectura..."
            class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        <!-- Descripción -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">Descripción</label>
          <textarea
            bind:value={formDescription}
            rows="2"
            placeholder="Descripción opcional del nivel..."
            class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
          ></textarea>
        </div>

        <!-- Color -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Color de identificación</label>
          <div class="flex flex-wrap gap-2">
            {#each COLOR_OPTIONS as opt}
              <button
                type="button"
                onclick={() => formColor = opt.value}
                class={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border-2 transition-all ${
                  formColor === opt.value
                    ? `${opt.bg} ${opt.text} border-current`
                    : 'bg-white text-gray-500 border-gray-200 hover:border-gray-300'
                }`}
              >
                <span class={`w-2.5 h-2.5 rounded-full ${opt.dot}`}></span>
                {opt.label}
              </button>
            {/each}
          </div>
        </div>

        <!-- Módulos -->
        <div>
          <div class="flex items-center justify-between mb-2">
            <label class="block text-sm font-medium text-gray-700">
              Módulos accesibles
              <span class="ml-1.5 text-xs font-normal text-gray-400">({formModuleIds.size} seleccionados)</span>
            </label>
            <div class="flex gap-2">
              <button
                type="button"
                onclick={selectAllModules}
                class="text-xs text-blue-600 hover:underline"
              >Todos</button>
              <span class="text-gray-300">|</span>
              <button
                type="button"
                onclick={clearAllModules}
                class="text-xs text-gray-500 hover:underline"
              >Ninguno</button>
            </div>
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 p-3 bg-gray-50 border border-gray-200 rounded-xl">
            {#each allModules as mod (mod.id)}
              <label class={`flex items-center gap-3 p-2.5 rounded-lg cursor-pointer transition-colors ${
                formModuleIds.has(mod.id)
                  ? 'bg-blue-50 border border-blue-200'
                  : 'bg-white border border-gray-200 hover:border-gray-300'
              }`}>
                <input
                  type="checkbox"
                  checked={formModuleIds.has(mod.id)}
                  onchange={() => toggleModule(mod.id)}
                  class="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 flex-shrink-0"
                />
                <div class="flex items-center gap-2 min-w-0">
                  <div class={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 ${
                    formModuleIds.has(mod.id) ? 'bg-blue-100' : 'bg-gray-100'
                  }`}>
                    <svg class={`w-4 h-4 ${formModuleIds.has(mod.id) ? 'text-blue-600' : 'text-gray-400'}`}
                         fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d={getModuleIcon(mod.icon)}/>
                    </svg>
                  </div>
                  <div class="min-w-0">
                    <p class="text-sm font-medium text-gray-800 truncate">{mod.name}</p>
                    {#if mod.description}
                      <p class="text-xs text-gray-400 truncate">{mod.description}</p>
                    {/if}
                  </div>
                </div>
              </label>
            {/each}
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-200 bg-gray-50">
        <button
          onclick={() => showModal = false}
          class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
        >
          Cancelar
        </button>
        <button
          onclick={saveLevel}
          disabled={saving}
          class="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {#if saving}
            <svg class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
            </svg>
            Guardando...
          {:else}
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
            </svg>
            {editingLevel ? 'Guardar cambios' : 'Crear nivel'}
          {/if}
        </button>
      </div>
    </div>
  </div>
{/if}

<!-- ─── Confirm Delete ─────────────────────────────────────────────────────── -->
{#if showDeleteConfirm && levelToDelete}
  <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
    <div class="bg-white rounded-2xl shadow-2xl w-full max-w-sm p-6">
      <div class="flex items-start gap-4 mb-5">
        <div class="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center flex-shrink-0">
          <svg class="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
          </svg>
        </div>
        <div>
          <h3 class="text-base font-semibold text-gray-900">Eliminar nivel</h3>
          <p class="text-sm text-gray-600 mt-1">
            ¿Eliminar <span class="font-medium">"{levelToDelete.name}"</span>?
            {#if levelToDelete.users_count > 0}
              <br/><span class="text-red-600">⚠️ Tiene {levelToDelete.users_count} usuario(s) asignado(s). No se puede eliminar.</span>
            {:else}
              Esta acción no se puede deshacer.
            {/if}
          </p>
        </div>
      </div>
      <div class="flex gap-3 justify-end">
        <button
          onclick={() => { showDeleteConfirm = false; levelToDelete = null; }}
          class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          Cancelar
        </button>
        {#if levelToDelete.users_count === 0}
          <button
            onclick={deleteLevel}
            disabled={deleting}
            class="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 disabled:opacity-50"
          >
            {deleting ? 'Eliminando...' : 'Sí, eliminar'}
          </button>
        {/if}
      </div>
    </div>
  </div>
{/if}
