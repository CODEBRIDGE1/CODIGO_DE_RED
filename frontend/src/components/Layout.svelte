<script lang="ts">
  import { authStore } from '../stores/auth';
  import { navigate } from '../lib/router';
  import { fly } from 'svelte/transition';

  interface MenuItem {
    id: string;
    label: string;
    icon: string;
    path: string;
    shortcut?: string;
    permission?: string;
    children?: MenuItem[];
  }

  let sidebarOpen = $state(true);
  let currentPath = $state('/dashboard');
  let showHelpModal = $state(false);
  const user = $derived($authStore.user);

  const menuItems: MenuItem[] = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6',
      path: '/dashboard',
      shortcut: 'ALT+D'
    },
    {
      id: 'empresas',
      label: 'Mis Empresas',
      icon: 'M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4',
      path: '/empresas',
      shortcut: 'ALT+E',
      permission: 'empresas.read'
    },
    {
      id: 'obligaciones',
      label: 'Matriz de Obligaciones',
      icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4',
      path: '/obligaciones',
      shortcut: 'ALT+O',
      permission: 'obligaciones.read'
    },
    {
      id: 'proyectos',
      label: 'Proyectos',
      icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2',
      path: '/proyectos',
      shortcut: 'ALT+P',
      permission: 'proyectos.read'
    },
    {
      id: 'evidencias',
      label: 'Evidencias',
      icon: 'M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z',
      path: '/evidencias',
      shortcut: 'ALT+V',
      permission: 'evidencias.read'
    },
    {
      id: 'cotizaciones',
      label: 'Cotizaciones',
      icon: 'M9 14l6-6m-5.5.5h.01m4.99 5h.01M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16l3.5-2 3.5 2 3.5-2 3.5 2z',
      path: '/cotizaciones',
      shortcut: 'ALT+C',
      permission: 'cotizaciones.read'
    },
    {
      id: 'reportes',
      label: 'Reportes',
      icon: 'M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
      path: '/reportes',
      shortcut: 'ALT+R',
      permission: 'reportes.read'
    },
    {
      id: 'usuarios',
      label: 'Usuarios y Roles',
      icon: 'M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z',
      path: '/usuarios',
      shortcut: 'ALT+U',
      permission: 'usuarios.read'
    },
    {
      id: 'auditoria',
      label: 'Auditoría',
      icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
      path: '/auditoria',
      shortcut: 'ALT+A',
      permission: 'auditoria.read'
    }
  ];

  function handleNavigate(path: string) {
    currentPath = path;
    navigate(path);
  }

  function handleLogout() {
    if (confirm('¿Está seguro que desea cerrar sesión?')) {
      authStore.logout();
      navigate('/');
    }
  }

  function hasPermission(permission?: string): boolean {
    if (!permission) return true;
    if (!user) return false;
    if (user.isSuperadmin) return true;
    return user.permissions.includes(permission);
  }

  // Keyboard shortcuts
  $effect(() => {
    function handleKeydown(e: KeyboardEvent) {
      if (e.altKey) {
        const key = e.key.toLowerCase();
        const item = menuItems.find(m => m.shortcut?.toLowerCase().includes(`alt+${key}`));
        if (item && hasPermission(item.permission)) {
          e.preventDefault();
          handleNavigate(item.path);
        }
      }
    }

    window.addEventListener('keydown', handleKeydown);
    return () => window.removeEventListener('keydown', handleKeydown);
  });

  interface Props {
    children: any;
  }

  let { children }: Props = $props();
</script>

<div class="min-h-screen bg-gray-100">
  <!-- Top Navigation Bar -->
  <nav class="bg-white shadow-sm border-b border-gray-200 fixed top-0 left-0 right-0 z-40">
    <div class="px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between h-16">
        <!-- Left: Logo + Menu Toggle -->
        <div class="flex items-center">
          <button
            onclick={() => sidebarOpen = !sidebarOpen}
            class="p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          
          <div class="ml-4 flex items-center space-x-3">
            <div class="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div class="hidden md:block">
              <div class="text-sm font-bold text-gray-900">CÓDIGO DE RED</div>
              <div class="text-xs text-gray-500">Gestión Energética</div>
            </div>
          </div>
        </div>

        <!-- Right: User Menu -->
        <div class="flex items-center space-x-4">
          <!-- Notifications -->
          <button class="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-full relative">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
            <span class="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
          </button>

          <!-- User Dropdown -->
          <div class="flex items-center space-x-3">
            <div class="text-right hidden sm:block">
              <div class="text-sm font-medium text-gray-900">{user?.fullName || 'Usuario'}</div>
              <div class="text-xs text-gray-500">{user?.email || ''}</div>
            </div>
            <button
              onclick={handleLogout}
              class="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-full"
              title="Cerrar sesión"
            >
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </nav>

  <!-- Sidebar -->
  <aside
    class="fixed left-0 top-16 bottom-0 w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out z-30 overflow-y-auto md:translate-x-0"
    class:translate-x-0={sidebarOpen}
    class:-translate-x-full={!sidebarOpen}
  >
    <nav class="p-4 space-y-1 pb-24">
      {#each menuItems as item}
        {#if hasPermission(item.permission)}
          <button
            onclick={() => handleNavigate(item.path)}
            class="w-full flex items-center px-4 py-3 text-left rounded-lg transition-colors hover:bg-gray-100"
            class:bg-blue-50={currentPath === item.path}
            class:text-blue-600={currentPath === item.path}
            class:font-semibold={currentPath === item.path}
            class:text-gray-700={currentPath !== item.path}
          >
            <svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d={item.icon} />
            </svg>
            <span class="text-sm">{item.label}</span>
          </button>
        {/if}
      {/each}
    </nav>

    <!-- Sidebar Footer -->
    <div class="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-200 bg-white">
      <button
        onclick={() => showHelpModal = true}
        class="w-full flex items-center justify-center space-x-2 px-4 py-3 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors border border-blue-200"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span class="text-sm font-medium">Ayuda y Atajos</span>
      </button>
      <div class="mt-3 text-xs text-center text-gray-400">
        v1.0.0 • 2026
      </div>
    </div>
  </aside>

  <!-- Main Content -->
  <main
    class="pt-16 transition-all duration-300 md:ml-64"
  >
    {@render children()}
  </main>

  <!-- Overlay for mobile when sidebar is open -->
  {#if sidebarOpen}
    <div 
      class="fixed inset-0 bg-black bg-opacity-50 z-20 md:hidden"
      onclick={() => sidebarOpen = false}
    ></div>
  {/if}

  <!-- Help Modal -->
  {#if showHelpModal}
    <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div 
        transition:fly="{{ y: -20, duration: 200 }}"
        class="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-hidden"
      >
        <div class="p-6 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50">
          <div class="flex justify-between items-start">
            <div>
              <h2 class="text-2xl font-bold text-gray-900 flex items-center">
                <svg class="w-7 h-7 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Ayuda y Atajos de Teclado
              </h2>
              <p class="text-gray-600 mt-1">Navega más rápido con tu teclado</p>
            </div>
            <button
              onclick={() => showHelpModal = false}
              class="text-gray-400 hover:text-gray-600"
            >
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <div class="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
          <!-- Navegación Global -->
          <div class="mb-6">
            <h3 class="text-lg font-semibold text-gray-900 mb-3 flex items-center">
              <svg class="w-5 h-5 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
              </svg>
              Navegación Global
            </h3>
            <div class="space-y-2">
              {#each menuItems as item}
                <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div class="flex items-center space-x-3">
                    <svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d={item.icon} />
                    </svg>
                    <span class="text-sm text-gray-700">{item.label}</span>
                  </div>
                  <kbd class="px-3 py-1 bg-white border border-gray-300 rounded text-sm font-mono shadow-sm">{item.shortcut}</kbd>
                </div>
              {/each}
            </div>
          </div>

          <!-- Atajos del Módulo de Empresas -->
          <div class="mb-6">
            <h3 class="text-lg font-semibold text-gray-900 mb-3 flex items-center">
              <svg class="w-5 h-5 mr-2 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
              Empresas
            </h3>
            <div class="space-y-2">
              <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span class="text-sm text-gray-700">Nueva empresa</span>
                <kbd class="px-3 py-1 bg-white border border-gray-300 rounded text-sm font-mono shadow-sm">N</kbd>
              </div>
              <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span class="text-sm text-gray-700">Buscar</span>
                <div class="flex space-x-1">
                  <kbd class="px-3 py-1 bg-white border border-gray-300 rounded text-sm font-mono shadow-sm">B</kbd>
                  <span class="text-gray-400">o</span>
                  <kbd class="px-3 py-1 bg-white border border-gray-300 rounded text-sm font-mono shadow-sm">/</kbd>
                </div>
              </div>
              <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span class="text-sm text-gray-700">Recargar lista</span>
                <kbd class="px-3 py-1 bg-white border border-gray-300 rounded text-sm font-mono shadow-sm">R</kbd>
              </div>
            </div>
          </div>

          <!-- Atajos Generales -->
          <div class="mb-6">
            <h3 class="text-lg font-semibold text-gray-900 mb-3 flex items-center">
              <svg class="w-5 h-5 mr-2 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
              </svg>
              Atajos Generales
            </h3>
            <div class="space-y-2">
              <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span class="text-sm text-gray-700">Cerrar modales</span>
                <kbd class="px-3 py-1 bg-white border border-gray-300 rounded text-sm font-mono shadow-sm">ESC</kbd>
              </div>
              <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span class="text-sm text-gray-700">Navegar campos (formularios)</span>
                <kbd class="px-3 py-1 bg-white border border-gray-300 rounded text-sm font-mono shadow-sm">Tab</kbd>
              </div>
              <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span class="text-sm text-gray-700">Confirmar/Buscar</span>
                <kbd class="px-3 py-1 bg-white border border-gray-300 rounded text-sm font-mono shadow-sm">Enter</kbd>
              </div>
            </div>
          </div>

          <!-- Tips -->
          <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 class="font-semibold text-blue-900 mb-2 flex items-center">
              <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
              Tips
            </h4>
            <ul class="text-sm text-blue-800 space-y-1">
              <li>• Los atajos no funcionan cuando estás escribiendo en un campo</li>
              <li>• Usa Tab para navegar rápidamente entre campos de formularios</li>
              <li>• Presiona ESC en cualquier momento para cerrar modales</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .translate-x-0 {
    transform: translateX(0);
  }
  
  .-translate-x-full {
    transform: translateX(-100%);
  }
</style>
