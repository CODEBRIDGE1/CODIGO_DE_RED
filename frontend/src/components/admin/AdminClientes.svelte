<script lang="ts">
  import { onMount } from 'svelte';
  import { authStore } from '../../stores/auth';

  interface Tenant {
    id: number;
    name: string;
    slug: string;
    contact_email: string | null;
    contact_phone: string | null;
    address: string | null;
    max_users: number | null;
    max_companies: number | null;
    is_active: boolean;
    created_at: string;
    users_count?: number;
    companies_count?: number;
    projects_count?: number;
  }

  interface TenantForm {
    name: string;
    slug: string;
    contact_email: string;
    contact_phone: string;
    address: string;
    max_users: number | null;
    max_companies: number | null;
  }

  let tenants = $state<Tenant[]>([]);
  let loading = $state(true);
  let showModal = $state(false);
  let isEditing = $state(false);
  let currentTenant = $state<Tenant | null>(null);
  let searchTerm = $state('');
  let filterActive = $state<'all' | 'active' | 'inactive'>('all');
  let currentPage = $state(1);
  let totalPages = $state(1);
  let showDeleteModal = $state(false);
  let tenantToDelete = $state<Tenant | null>(null);

  let form = $state<TenantForm>({
    name: '',
    slug: '',
    contact_email: '',
    contact_phone: '',
    address: '',
    max_users: null,
    max_companies: null
  });

  const filteredTenants = $derived(
    tenants.filter(t => {
      const matchesSearch = t.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          t.slug.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          (t.contact_email?.toLowerCase().includes(searchTerm.toLowerCase()) ?? false);
      const matchesActive = filterActive === 'all' ? true :
                          filterActive === 'active' ? t.is_active : !t.is_active;
      return matchesSearch && matchesActive;
    })
  );

  onMount(() => {
    loadTenants();
  });

  async function loadTenants() {
    try {
      loading = true;
      const response = await fetch('http://localhost:8000/api/v1/admin/tenants', {
        headers: {
          'Authorization': `Bearer ${$authStore.token}`
        }
      });

      if (!response.ok) throw new Error('Error al cargar clientes');
      
      const data = await response.json();
      tenants = data;
    } catch (error) {
      console.error('Error:', error);
      alert('Error al cargar los clientes');
    } finally {
      loading = false;
    }
  }

  function openCreateModal() {
    isEditing = false;
    currentTenant = null;
    form = {
      name: '',
      slug: '',
      contact_email: '',
      contact_phone: '',
      address: '',
      max_users: null,
      max_companies: null
    };
    showModal = true;
  }

  function openEditModal(tenant: Tenant) {
    isEditing = true;
    currentTenant = tenant;
    form = {
      name: tenant.name,
      slug: tenant.slug,
      contact_email: tenant.contact_email || '',
      contact_phone: tenant.contact_phone || '',
      address: tenant.address || '',
      max_users: tenant.max_users,
      max_companies: tenant.max_companies
    };
    showModal = true;
  }

  function closeModal() {
    showModal = false;
    currentTenant = null;
  }

  function generateSlug() {
    form.slug = form.name
      .toLowerCase()
      .replace(/[áàäâ]/g, 'a')
      .replace(/[éèëê]/g, 'e')
      .replace(/[íìïî]/g, 'i')
      .replace(/[óòöô]/g, 'o')
      .replace(/[úùüû]/g, 'u')
      .replace(/ñ/g, 'n')
      .replace(/[^a-z0-9]/g, '-')
      .replace(/-+/g, '-')
      .replace(/^-|-$/g, '');
  }

  async function handleSubmit() {
    try {
      const url = isEditing
        ? `http://localhost:8000/api/v1/admin/tenants/${currentTenant!.id}`
        : 'http://localhost:8000/api/v1/admin/tenants';
      
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

      await loadTenants();
      closeModal();
      alert(isEditing ? 'Cliente actualizado correctamente' : 'Cliente creado correctamente');
    } catch (error: any) {
      console.error('Error:', error);
      alert(error.message || 'Error al guardar el cliente');
    }
  }

  function confirmDelete(tenant: Tenant) {
    tenantToDelete = tenant;
    showDeleteModal = true;
  }

  async function handleDelete() {
    if (!tenantToDelete) return;

    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/admin/tenants/${tenantToDelete.id}`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${$authStore.token}`
          }
        }
      );

      if (!response.ok) throw new Error('Error al eliminar');

      await loadTenants();
      showDeleteModal = false;
      tenantToDelete = null;
      alert('Cliente desactivado correctamente');
    } catch (error) {
      console.error('Error:', error);
      alert('Error al desactivar el cliente');
    }
  }
</script>

<div class="p-6">
  <!-- Header -->
  <div class="flex justify-between items-center mb-6">
    <div>
      <h1 class="text-2xl font-bold text-gray-900">Gestión de Clientes</h1>
      <p class="text-gray-600 mt-1">Administra los clientes (tenants) de la plataforma</p>
    </div>
    <button
      onclick={openCreateModal}
      class="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 flex items-center gap-2"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
      </svg>
      Nuevo Cliente
    </button>
  </div>

  <!-- Filters -->
  <div class="bg-white rounded-lg shadow-sm p-4 mb-6">
    <div class="flex gap-4 flex-wrap">
      <div class="flex-1 min-w-[300px]">
        <input
          type="text"
          bind:value={searchTerm}
          placeholder="Buscar por nombre, slug o email..."
          class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
        />
      </div>
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
      <p class="mt-4 text-gray-600">Cargando clientes...</p>
    </div>
  {:else if filteredTenants.length === 0}
    <div class="bg-white rounded-lg shadow-sm p-12 text-center">
      <svg class="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
      </svg>
      <p class="text-gray-600">No se encontraron clientes</p>
    </div>
  {:else}
    <div class="bg-white rounded-lg shadow-sm overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cliente</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Contacto</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Límites</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estadísticas</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
            <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          {#each filteredTenants as tenant}
            <tr class="hover:bg-gray-50">
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm font-medium text-gray-900">{tenant.name}</div>
                <div class="text-sm text-gray-500">{tenant.slug}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-900">{tenant.contact_email || '-'}</div>
                <div class="text-sm text-gray-500">{tenant.contact_phone || '-'}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                <div>Usuarios: {tenant.max_users || '∞'}</div>
                <div>Empresas: {tenant.max_companies || '∞'}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                <div>👥 {tenant.users_count || 0} usuarios</div>
                <div>🏢 {tenant.companies_count || 0} empresas</div>
                <div>📁 {tenant.projects_count || 0} proyectos</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <span class="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full"
                  class:bg-green-100={tenant.is_active}
                  class:text-green-800={tenant.is_active}
                  class:bg-red-100={!tenant.is_active}
                  class:text-red-800={!tenant.is_active}
                >
                  {tenant.is_active ? 'Activo' : 'Inactivo'}
                </span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                <button
                  onclick={() => openEditModal(tenant)}
                  class="text-purple-600 hover:text-purple-900 mr-3"
                  title="Editar"
                >
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                </button>
                {#if tenant.is_active}
                  <button
                    onclick={() => confirmDelete(tenant)}
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
            {isEditing ? 'Editar Cliente' : 'Nuevo Cliente'}
          </h2>
          <button onclick={closeModal} class="text-gray-400 hover:text-gray-600">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onsubmit={(e) => { e.preventDefault(); handleSubmit(); }} class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div class="col-span-2">
              <label class="block text-sm font-medium text-gray-700 mb-1">Nombre *</label>
              <input
                type="text"
                bind:value={form.name}
                oninput={generateSlug}
                required
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>

            <div class="col-span-2">
              <label class="block text-sm font-medium text-gray-700 mb-1">Slug *</label>
              <input
                type="text"
                bind:value={form.slug}
                required
                pattern="[a-z0-9-]+"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
              <p class="text-xs text-gray-500 mt-1">Solo letras minúsculas, números y guiones</p>
            </div>

            <div class="col-span-2 sm:col-span-1">
              <label class="block text-sm font-medium text-gray-700 mb-1">Email de Contacto</label>
              <input
                type="email"
                bind:value={form.contact_email}
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>

            <div class="col-span-2 sm:col-span-1">
              <label class="block text-sm font-medium text-gray-700 mb-1">Teléfono de Contacto</label>
              <input
                type="text"
                bind:value={form.contact_phone}
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>

            <div class="col-span-2">
              <label class="block text-sm font-medium text-gray-700 mb-1">Dirección</label>
              <textarea
                bind:value={form.address}
                rows="2"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              ></textarea>
            </div>

            <div class="col-span-2 sm:col-span-1">
              <label class="block text-sm font-medium text-gray-700 mb-1">Máximo de Usuarios</label>
              <input
                type="number"
                bind:value={form.max_users}
                min="1"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="Ilimitado"
              />
            </div>

            <div class="col-span-2 sm:col-span-1">
              <label class="block text-sm font-medium text-gray-700 mb-1">Máximo de Empresas</label>
              <input
                type="number"
                bind:value={form.max_companies}
                min="1"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="Ilimitado"
              />
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
              {isEditing ? 'Actualizar' : 'Crear'} Cliente
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
        ¿Estás seguro de que deseas desactivar el cliente <strong>{tenantToDelete?.name}</strong>?
        Los usuarios de este cliente no podrán acceder al sistema.
      </p>
      <div class="flex justify-end gap-3">
        <button
          onclick={() => { showDeleteModal = false; tenantToDelete = null; }}
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
