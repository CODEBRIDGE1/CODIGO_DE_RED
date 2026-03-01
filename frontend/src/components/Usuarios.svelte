<script lang="ts">
  import { onMount } from 'svelte';
  import { authStore } from '../stores/auth';

  interface User {
    id: number;
    email: string;
    full_name: string;
    is_active: boolean;
    is_superadmin: boolean;
    tenant_id: number | null;
    last_login_at: string | null;
    created_at: string;
  }

  let users = $state<User[]>([]);
  let loading = $state(true);
  let showModal = $state(false);
  let modalMode = $state<'create' | 'edit'>('create');
  let selectedUser = $state<User | null>(null);
  let errorMessage = $state('');
  let successMessage = $state('');
  
  // Detectar si estamos en la vista de admin
  const isAdminView = $derived(window.location.pathname === '/admin/usuarios');
  const currentUser = $derived($authStore.user);
  
  // Filtros
  let searchTerm = $state('');
  let filterActive = $state<boolean | null>(null);
  
  // Paginación
  let currentPage = $state(1);
  let totalUsers = $state(0);
  let pageSize = $state(10);

  // Form data
  let formData = $state({
    email: '',
    full_name: '',
    password: '',
    is_active: true,
    is_superadmin: false
  });

  const accessToken = $derived($authStore.accessToken);

  // Cargar usuarios cuando el token esté disponible
  let hasLoadedOnce = false;
  $effect(() => {
    if (accessToken && !hasLoadedOnce) {
      hasLoadedOnce = true;
      loadUsers();
    }
  });

  async function loadUsers() {
    loading = true;
    errorMessage = '';
    
    // Verificar que tenemos token antes de hacer la petición
    if (!accessToken) {
      errorMessage = 'No hay sesión activa';
      loading = false;
      return;
    }
    
    try {
      const params = new URLSearchParams({
        page: currentPage.toString(),
        page_size: pageSize.toString()
      });
      
      if (searchTerm) params.append('search', searchTerm);
      if (filterActive !== null) params.append('is_active', filterActive.toString());

      const response = await authStore.fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/users/?${params}`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Error ${response.status}: No se pudieron cargar los usuarios`);
      }

      const data = await response.json();
      users = data.users;
      totalUsers = data.total;
      
    } catch (err: any) {
      errorMessage = err.message || 'Error al conectar con el servidor';
      console.error('Error loading users:', err);
    } finally {
      loading = false;
    }
  }

  function openCreateModal() {
    modalMode = 'create';
    selectedUser = null;
    formData = {
      email: '',
      full_name: '',
      password: '',
      is_active: true,
      is_superadmin: false
    };
    showModal = true;
  }

  function openEditModal(user: User) {
    modalMode = 'edit';
    selectedUser = user;
    formData = {
      email: user.email,
      full_name: user.full_name,
      password: '',
      is_active: user.is_active,
      is_superadmin: user.is_superadmin || false
    };
    showModal = true;
  }

  async function handleSubmit() {
    errorMessage = '';
    successMessage = '';

    try {
      const url = modalMode === 'create' 
        ? `/api/v1/users`
        : `/api/v1/users/${selectedUser?.id}`;
      
      const method = modalMode === 'create' ? 'POST' : 'PUT';
      
      const body: any = {
        email: formData.email,
        full_name: formData.full_name,
        is_active: formData.is_active
      };
      
      // Solo superadmin puede asignar rol de superadmin
      if (isAdminView && currentUser?.isSuperadmin) {
        body.is_superadmin = formData.is_superadmin;
      }
      
      // Solo incluir password si se proporcionó
      if (formData.password) {
        body.password = formData.password;
      }

      const response = await authStore.fetch(url, {
        method,
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(body)
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Error al guardar usuario');
      }

      successMessage = modalMode === 'create' 
        ? 'Usuario creado exitosamente'
        : 'Usuario actualizado exitosamente';
      
      showModal = false;
      await loadUsers();
      
      // Limpiar mensaje después de 3 segundos
      setTimeout(() => {
        successMessage = '';
      }, 3000);

    } catch (err: any) {
      errorMessage = err.message || 'Error al guardar usuario';
    }
  }

  async function handleToggleActive(user: User) {
    if (!confirm(`¿Está seguro que desea ${user.is_active ? 'desactivar' : 'activar'} este usuario?`)) {
      return;
    }

    try {
      const response = await authStore.fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/users/${user.id}/`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          is_active: !user.is_active
        })
      });

      if (!response.ok) {
        throw new Error('Error al actualizar usuario');
      }

      await loadUsers();
      successMessage = `Usuario ${user.is_active ? 'desactivado' : 'activado'} exitosamente`;
      setTimeout(() => {
        successMessage = '';
      }, 3000);

    } catch (err: any) {
      errorMessage = err.message || 'Error al actualizar usuario';
    }
  }

  function handleSearch() {
    currentPage = 1;
    loadUsers();
  }

  function handlePageChange(newPage: number) {
    currentPage = newPage;
    loadUsers();
  }

  function formatDate(dateString: string | null) {
    if (!dateString) return 'Nunca';
    return new Date(dateString).toLocaleDateString('es-MX', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  const totalPages = $derived(Math.ceil(totalUsers / pageSize));
</script>

<div class="p-6">
  <!-- Header -->
  <div class="flex justify-between items-center mb-6">
    <div>
      <h1 class="text-3xl font-bold text-gray-900">Usuarios y Roles</h1>
      <p class="text-gray-600 mt-1">Gestión de usuarios de su organización</p>
    </div>
    <button
      onclick={openCreateModal}
      class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
      </svg>
      <span>Nuevo Usuario</span>
      <span class="text-xs opacity-75">(N)</span>
    </button>
  </div>

  <!-- Messages -->
  {#if errorMessage}
    <div class="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-center justify-between">
      <span>{errorMessage}</span>
      <button onclick={() => errorMessage = ''} class="text-red-700 hover:text-red-900">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  {/if}

  {#if successMessage}
    <div class="mb-4 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg flex items-center justify-between">
      <span>{successMessage}</span>
      <button onclick={() => successMessage = ''} class="text-green-700 hover:text-green-900">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  {/if}

  <!-- Search and Filters -->
  <div class="bg-white rounded-lg shadow p-4 mb-6">
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div class="md:col-span-2">
        <label class="block text-sm font-medium text-gray-700 mb-2">Buscar</label>
        <div class="flex space-x-2">
          <input
            type="text"
            bind:value={searchTerm}
            placeholder="Nombre o email..."
            onkeypress={(e) => e.key === 'Enter' && handleSearch()}
            class="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
          <button
            onclick={handleSearch}
            class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            Buscar
          </button>
        </div>
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">Estado</label>
        <select
          bind:value={filterActive}
          onchange={handleSearch}
          class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value={null}>Todos</option>
          <option value={true}>Activos</option>
          <option value={false}>Inactivos</option>
        </select>
      </div>
    </div>
  </div>

  {#if loading}
    <!-- Loading State -->
    <div class="bg-white rounded-lg shadow p-6">
      <div class="animate-pulse space-y-4">
        {#each Array(5) as _}
          <div class="h-16 bg-gray-200 rounded"></div>
        {/each}
      </div>
    </div>
  {:else if users.length === 0}
    <!-- Empty State -->
    <div class="bg-white rounded-lg shadow p-12 text-center">
      <svg class="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
      </svg>
      <h3 class="text-lg font-medium text-gray-900 mb-2">No hay usuarios</h3>
      <p class="text-gray-600 mb-4">Comience creando su primer usuario</p>
      <button
        onclick={openCreateModal}
        class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
      >
        Crear Usuario
      </button>
    </div>
  {:else}
    <!-- Table -->
    <div class="bg-white rounded-lg shadow overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Usuario</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Último Acceso</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fecha Registro</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          {#each users as user}
            <tr class="hover:bg-gray-50 transition-colors">
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="flex items-center">
                  <div class="flex-shrink-0 h-10 w-10 bg-blue-100 rounded-full flex items-center justify-center">
                    <span class="text-blue-600 font-semibold text-sm">
                      {user.full_name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)}
                    </span>
                  </div>
                  <div class="ml-4">
                    <div class="text-sm font-medium text-gray-900">{user.full_name}</div>
                    {#if user.is_superadmin}
                      <span class="text-xs text-purple-600 font-semibold">SUPERADMIN</span>
                    {/if}
                  </div>
                </div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{user.email}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{formatDate(user.last_login_at)}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{formatDate(user.created_at)}</td>
              <td class="px-6 py-4 whitespace-nowrap">
                <button
                  onclick={() => handleToggleActive(user)}
                  class="px-3 py-1 text-xs font-semibold rounded transition-colors {user.is_active ? 'bg-green-100 text-green-800 hover:bg-green-200' : 'bg-red-100 text-red-800 hover:bg-red-200'}"
                >
                  {user.is_active ? 'Activo' : 'Inactivo'}
                </button>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm">
                <div class="flex space-x-2">
                  <button
                    onclick={() => openEditModal(user)}
                    class="text-blue-600 hover:text-blue-800"
                    title="Editar usuario"
                  >
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
        Mostrando {(currentPage - 1) * pageSize + 1}-{Math.min(currentPage * pageSize, totalUsers)} de {totalUsers} usuarios
      </div>
      <div class="flex space-x-2">
        <button
          onclick={() => handlePageChange(currentPage - 1)}
          disabled={currentPage === 1}
          class="px-3 py-1 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Anterior
        </button>
        <span class="px-3 py-1 text-sm text-gray-600">
          Página {currentPage} de {totalPages}
        </span>
        <button
          onclick={() => handlePageChange(currentPage + 1)}
          disabled={currentPage >= totalPages}
          class="px-3 py-1 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Siguiente
        </button>
      </div>
    </div>
  {/if}
</div>

<!-- Modal -->
{#if showModal}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-lg max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
      <div class="p-6">
        <div class="flex justify-between items-center mb-4">
          <h2 class="text-2xl font-bold text-gray-900">
            {modalMode === 'create' ? 'Nuevo Usuario' : 'Editar Usuario'}
          </h2>
          <button
            onclick={() => showModal = false}
            class="text-gray-400 hover:text-gray-600"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onsubmit={(e) => { e.preventDefault(); handleSubmit(); }} class="space-y-4">
          <!-- Nombre Completo -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Nombre Completo *
            </label>
            <input
              type="text"
              bind:value={formData.full_name}
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <!-- Email -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Email *
            </label>
            <input
              type="email"
              bind:value={formData.email}
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <!-- Password -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Contraseña {modalMode === 'edit' ? '(dejar en blanco para no cambiar)' : '*'}
            </label>
            <input
              type="password"
              bind:value={formData.password}
              required={modalMode === 'create'}
              minlength="8"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            <p class="text-xs text-gray-500 mt-1">Mínimo 8 caracteres</p>
          </div>

          <!-- Tipo de Usuario (solo para superadmin) -->
          {#if isAdminView && currentUser?.isSuperadmin}
            <div class="flex items-center">
              <input
                type="checkbox"
                id="is_superadmin"
                bind:checked={formData.is_superadmin}
                class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label for="is_superadmin" class="ml-2 block text-sm text-gray-700">
                <span class="font-medium">Superadministrador</span>
                <span class="text-xs text-gray-500 block">Acceso completo al sistema</span>
              </label>
            </div>
          {/if}

          <!-- Estado -->
          <div class="flex items-center">
            <input
              type="checkbox"
              id="is_active"
              bind:checked={formData.is_active}
              class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label for="is_active" class="ml-2 block text-sm text-gray-700">
              Usuario activo
            </label>
          </div>

          <!-- Buttons -->
          <div class="flex justify-end space-x-3 pt-4">
            <button
              type="button"
              onclick={() => showModal = false}
              class="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
            >
              {modalMode === 'create' ? 'Crear Usuario' : 'Guardar Cambios'}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
{/if}
