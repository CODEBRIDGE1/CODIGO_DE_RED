<script lang="ts">
  import { onMount } from 'svelte';
  import { authStore } from '../../stores/auth';

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
    { value: 'maquinaria', label: 'Maquinaria' },
    { value: 'materiales', label: 'Materiales' },
    { value: 'mano_obra', label: 'Mano de Obra' },
    { value: 'servicios', label: 'Servicios' },
    { value: 'equipos', label: 'Equipos' },
    { value: 'transporte', label: 'Transporte' },
    { value: 'consultoria', label: 'Consultoría' },
    { value: 'licencias', label: 'Licencias' },
    { value: 'otros', label: 'Otros' }
  ];

  const units = [
    { value: 'unidad', label: 'Unidad' },
    { value: 'metro', label: 'Metro' },
    { value: 'metro_cuadrado', label: 'Metro Cuadrado' },
    { value: 'metro_cubico', label: 'Metro Cúbico' },
    { value: 'kilogramo', label: 'Kilogramo' },
    { value: 'tonelada', label: 'Tonelada' },
    { value: 'litro', label: 'Litro' },
    { value: 'hora', label: 'Hora' },
    { value: 'dia', label: 'Día' },
    { value: 'mes', label: 'Mes' }
  ];

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

  let form = $state<QuoteItemForm>({
    code: '',
    name: '',
    description: '',
    category: 'materiales',
    unit: 'unidad',
    base_price: 0
  });

  const filteredItems = $derived(
    items.filter(item => {
      const matchesSearch = item.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          (item.description?.toLowerCase().includes(searchTerm.toLowerCase()) ?? false);
      const matchesCategory = filterCategory === 'all' || item.category === filterCategory;
      const matchesActive = filterActive === 'all' ? true :
                          filterActive === 'active' ? item.is_active : !item.is_active;
      return matchesSearch && matchesCategory && matchesActive;
    })
  );

  onMount(() => {
    loadItems();
  });

  async function loadItems() {
    try {
      loading = true;
      const response = await fetch('http://localhost:8000/api/v1/admin/quote-items', {
        headers: {
          'Authorization': `Bearer ${$authStore.token}`
        }
      });

      if (!response.ok) throw new Error('Error al cargar conceptos');
      
      const data = await response.json();
      items = data;
    } catch (error) {
      console.error('Error:', error);
      alert('Error al cargar los conceptos');
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
      category: 'materiales',
      unit: 'unidad',
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
  }

  async function handleSubmit() {
    try {
      const url = isEditing
        ? `http://localhost:8000/api/v1/admin/quote-items/${currentItem!.id}`
        : 'http://localhost:8000/api/v1/admin/quote-items';
      
      const method = isEditing ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${$authStore.token}`
        },
        body: JSON.stringify(form)
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Error al guardar');
      }

      await loadItems();
      closeModal();
      alert(isEditing ? 'Concepto actualizado correctamente' : 'Concepto creado correctamente');
    } catch (error: any) {
      console.error('Error:', error);
      alert(error.message || 'Error al guardar el concepto');
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
        `http://localhost:8000/api/v1/admin/quote-items/${itemToDelete.id}`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${$authStore.token}`
          }
        }
      );

      if (!response.ok) throw new Error('Error al eliminar');

      await loadItems();
      showDeleteModal = false;
      itemToDelete = null;
      alert('Concepto desactivado correctamente');
    } catch (error) {
      console.error('Error:', error);
      alert('Error al desactivar el concepto');
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
  <div class="flex justify-between items-center mb-6">
    <div>
      <h1 class="text-2xl font-bold text-gray-900">Catálogo de Conceptos</h1>
      <p class="text-gray-600 mt-1">Administra el catálogo global de conceptos para cotizaciones</p>
    </div>
    <button
      onclick={openCreateModal}
      class="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 flex items-center gap-2"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
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
          class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
        />
      </div>
      <select
        bind:value={filterCategory}
        class="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
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
          class:bg-purple-600={filterActive === 'all'}
          class:text-white={filterActive === 'all'}
          class:border-purple-600={filterActive === 'all'}
          class:bg-white={filterActive !== 'all'}
          class:text-gray-700={filterActive !== 'all'}
        >
          Todos
        </button>
        <button
          onclick={() => filterActive = 'active'}
          class="px-4 py-2 rounded-lg border"
          class:bg-purple-600={filterActive === 'active'}
          class:text-white={filterActive === 'active'}
          class:border-purple-600={filterActive === 'active'}
          class:bg-white={filterActive !== 'active'}
          class:text-gray-700={filterActive !== 'active'}
        >
          Activos
        </button>
        <button
          onclick={() => filterActive = 'inactive'}
          class="px-4 py-2 rounded-lg border"
          class:bg-purple-600={filterActive === 'inactive'}
          class:text-white={filterActive === 'inactive'}
          class:border-purple-600={filterActive === 'inactive'}
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
      <div class="inline-block animate-spin rounded-full h-12 w-12 border-4 border-gray-300 border-t-purple-600"></div>
      <p class="mt-4 text-gray-600">Cargando conceptos...</p>
    </div>
  {:else if filteredItems.length === 0}
    <div class="bg-white rounded-lg shadow-sm p-12 text-center">
      <svg class="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
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
                <button
                  onclick={() => openEditModal(item)}
                  class="text-purple-600 hover:text-purple-900 mr-3"
                  title="Editar"
                >
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                </button>
                {#if item.is_active}
                  <button
                    onclick={() => confirmDelete(item)}
                    class="text-red-600 hover:text-red-900"
                    title="Desactivar"
                  >
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                {/if}
              </td>
            </tr>
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
            {isEditing ? 'Editar Concepto' : 'Nuevo Concepto'}
          </h2>
          <button onclick={closeModal} class="text-gray-400 hover:text-gray-600">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onsubmit={(e) => { e.preventDefault(); handleSubmit(); }} class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Código *</label>
              <input
                type="text"
                bind:value={form.code}
                required
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent font-mono"
                placeholder="Ej: MAT-001"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Categoría *</label>
              <select
                bind:value={form.category}
                required
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
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
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="Ej: Cemento Portland"
              />
            </div>

            <div class="col-span-2">
              <label class="block text-sm font-medium text-gray-700 mb-1">Descripción</label>
              <textarea
                bind:value={form.description}
                rows="3"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="Descripción detallada del concepto..."
              ></textarea>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Unidad *</label>
              <select
                bind:value={form.unit}
                required
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
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
                  class="w-full pl-7 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
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
              class="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
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
{#if showDeleteModal}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
      <h3 class="text-lg font-bold text-gray-900 mb-4">Confirmar Desactivación</h3>
      <p class="text-gray-600 mb-6">
        ¿Estás seguro de que deseas desactivar el concepto <strong>{itemToDelete?.code} - {itemToDelete?.name}</strong>?
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
