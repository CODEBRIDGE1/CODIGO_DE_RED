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
    moduleKey?: string;  // clave del módulo en el nivel de seguridad
    children?: MenuItem[];
  }

  let sidebarOpen = $state(window.innerWidth >= 768);
  let currentPath = $state(window.location.pathname);
  let showHelpModal = $state(false);
  let showUserDropdown = $state(false);
  let showProfileModal = false; // deprecated — se usa /perfil ahora
  let showSearch = $state(false);
  let searchQuery = $state('');
  let searchInput = $state<HTMLInputElement | null>(null);
  let activeIndex = $state(-1);
  let searchDropdownEl = $state<HTMLDivElement | null>(null);
  const user = $derived($authStore.user);

  // Menu items para usuarios con tenant
  const menuItems: MenuItem[] = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6',
      path: '/dashboard',
      shortcut: 'ALT+D',
      moduleKey: 'dashboard'
    },
    {
      id: 'empresas',
      label: 'Mis Empresas',
      icon: 'M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4',
      path: '/empresas',
      shortcut: 'ALT+E',
      permission: 'empresas.read',
      moduleKey: 'empresas'
    },
    {
      id: 'obligaciones',
      label: 'Matriz de Obligaciones',
      icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4',
      path: '/obligaciones',
      shortcut: 'ALT+O',
      permission: 'obligaciones.read',
      moduleKey: 'obligaciones'
    },
    {
      id: 'proyectos',
      label: 'Proyectos',
      icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2',
      path: '/proyectos',
      shortcut: 'ALT+P',
      permission: 'proyectos.read',
      moduleKey: 'proyectos'
    },
    {
      id: 'evidencias',
      label: 'Evidencias',
      icon: 'M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z',
      path: '/evidencias',
      shortcut: 'ALT+V',
      permission: 'evidencias.read',
      moduleKey: 'documentos'
    },
    {
      id: 'cotizaciones',
      label: 'Cotizaciones',
      icon: 'M9 14l6-6m-5.5.5h.01m4.99 5h.01M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16l3.5-2 3.5 2 3.5-2 3.5 2z',
      path: '/cotizaciones',
      shortcut: 'ALT+C',
      permission: 'cotizaciones.read',
      moduleKey: 'cotizaciones'
    },
    {
      id: 'reportes',
      label: 'Reportes',
      icon: 'M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
      path: '/reportes',
      shortcut: 'ALT+R',
      permission: 'reportes.read',
      moduleKey: 'reportes'
    },
    {
      id: 'usuarios',
      label: 'Usuarios y Roles',
      icon: 'M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z',
      path: '/usuarios',
      shortcut: 'ALT+U',
      permission: 'usuarios.read',
      moduleKey: 'usuarios'
    },
    {
      id: 'auditoria',
      label: 'Auditoría',
      icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
      path: '/auditoria',
      shortcut: 'ALT+A',
      permission: 'auditoria.read',
      moduleKey: 'auditoria'
    }
  ];

  // Menu items para superadmin
  const adminMenuItems: MenuItem[] = [
    {
      id: 'admin-clientes',
      label: 'Clientes',
      icon: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z',
      path: '/admin/clientes',
    },
    {
      id: 'admin-conceptos',
      label: 'Reglas de Cumplimiento',
      icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01',
      path: '/admin/conceptos',
    },
    {
      id: 'admin-niveles',
      label: 'Niveles de Seguridad',
      icon: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z',
      path: '/admin/niveles',
    },
    {
      id: 'admin-cotizaciones',
      label: 'Cotizaciones',
      icon: 'M9 14l6-6m-5.5.5h.01m4.99 5h.01M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16l3.5-2 3.5 2 3.5-2 3.5 2z',
      path: '/admin/cotizaciones',
    },
    {
      id: 'admin-usuarios',
      label: 'Usuarios y Roles',
      icon: 'M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z',
      path: '/admin/usuarios',
    },
    {
      id: 'admin-proyectos',
      label: 'Todos los Proyectos',
      icon: 'M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z',
      path: '/admin/proyectos',
    },
    {
      id: 'admin-reportes',
      label: 'Reportes Generales',
      icon: 'M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
      path: '/admin/reportes',
    }
  ];

  const searchResults = $derived.by(() => {
    if (!user) return [];
    const q = searchQuery.trim().toLowerCase();
    if (!q) return [];
    const isSuperadmin = user.isSuperadmin;
    const securityModules = user.securityModules ?? [];

    // Mirror exactly what the sidebar shows: hasModuleAccess logic only
    const allowed = (item: MenuItem) => {
      if (!item.moduleKey) return true;
      if (isSuperadmin) return true;
      if (item.moduleKey === 'dashboard') return true;
      // Without a security level assigned → full access
      if (securityModules.length === 0) return true;
      return securityModules.includes(item.moduleKey);
    };

    const base = isSuperadmin ? [...adminMenuItems, ...menuItems] : menuItems;
    return base.filter(allowed).filter(item => item.label.toLowerCase().includes(q));
  });

  // Reset active index when query changes; scroll selected item into view
  $effect(() => {
    searchQuery;
    activeIndex = -1;
  });
  $effect(() => {
    if (activeIndex >= 0 && searchDropdownEl) {
      const btns = searchDropdownEl.querySelectorAll<HTMLButtonElement>('button[data-search-result]');
      btns[activeIndex]?.scrollIntoView({ block: 'nearest' });
    }
  });

  function handleNavigate(path: string) {
    currentPath = path;
    navigate(path);
    if (window.innerWidth < 768) sidebarOpen = false;
    showSearch = false;
    searchQuery = '';
  }

  function handleLogout() {
    authStore.logout();
    window.location.href = '/';
  }

  function hasPermission(permission?: string): boolean {
    if (!permission) return true;
    if (!user) return false;
    if (user.isSuperadmin) return true;
    return user.permissions.includes(permission);
  }

  // Verifica si el módulo está habilitado por el nivel de seguridad del usuario.
  // dashboard siempre es visible. Sin nivel asignado → acceso total.
  // Con nivel asignado → solo módulos del nivel.
  function hasModuleAccess(moduleKey?: string): boolean {
    if (!moduleKey) return true;
    if (!user) return false;
    if (user.isSuperadmin) return true;
    // Dashboard siempre visible (es el home de todos los usuarios)
    if (moduleKey === 'dashboard') return true;
    // Sin nivel de seguridad asignado: sin restricción de módulos
    if (!user.securityModules || user.securityModules.length === 0) return true;
    return user.securityModules.includes(moduleKey);
  }

  // Sincronizar currentPath con la URL actual
  $effect(() => {
    currentPath = window.location.pathname;
  });

  // Keyboard shortcuts
  $effect(() => {
    function handleKeydown(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        showSearch = false; showUserDropdown = false;
        showHelpModal = false;
        searchQuery = '';
        return;
      }
      if (e.altKey && e.key.toLowerCase() === 'b') {
        e.preventDefault();
        searchInput?.focus();
        searchInput?.select();
        return;
      }
      if (e.altKey && !showSearch) {
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
        <div class="flex items-center gap-2 flex-1 justify-end">

          <!-- Global Search Bar (always visible) -->
          <div class="relative hidden sm:block w-48 lg:w-72">
            <div class="flex items-center gap-2 px-3 py-1.5 bg-gray-100 hover:bg-gray-200 focus-within:bg-white focus-within:ring-2 focus-within:ring-blue-500 focus-within:shadow-sm rounded-lg transition-all">
              <svg class="w-4 h-4 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0"/>
              </svg>
              <input
                bind:this={searchInput}
                type="text"
                bind:value={searchQuery}
                onfocus={() => showSearch = true}
                onblur={(e) => { if (!e.relatedTarget?.closest?.('[data-search-result]')) { setTimeout(() => { showSearch = false; activeIndex = -1; }, 150); } }}
                onkeydown={(e) => {
                  if (!searchResults.length) return;
                  if (e.key === 'ArrowDown') {
                    e.preventDefault();
                    activeIndex = Math.min(activeIndex + 1, searchResults.length - 1);
                  } else if (e.key === 'ArrowUp') {
                    e.preventDefault();
                    activeIndex = Math.max(activeIndex - 1, -1);
                  } else if (e.key === 'Tab') {
                    e.preventDefault();
                    activeIndex = e.shiftKey
                      ? Math.max(activeIndex - 1, 0)
                      : Math.min(activeIndex + 1, searchResults.length - 1);
                  } else if (e.key === 'Enter' && activeIndex >= 0) {
                    e.preventDefault();
                    handleNavigate(searchResults[activeIndex].path);
                    activeIndex = -1;
                  }
                }}
                placeholder="Buscar módulo..."
                class="flex-1 bg-transparent outline-none text-sm text-gray-700 placeholder-gray-400 min-w-0"
              />
              {#if searchQuery}
                <button
                  tabindex="-1"
                  onclick={() => { searchQuery = ''; searchInput?.focus(); }}
                  class="text-gray-400 hover:text-gray-600 flex-shrink-0"
                >
                  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                  </svg>
                </button>
              {:else}
                <kbd class="text-xs text-gray-300 font-mono hidden lg:block flex-shrink-0">Alt+B</kbd>
              {/if}
            </div>

            <!-- Dropdown results -->
            {#if showSearch && searchQuery.trim()}
              <div class="absolute top-full left-0 right-0 mt-1 bg-white rounded-xl shadow-xl border border-gray-200 z-50 overflow-hidden">
                <div bind:this={searchDropdownEl} class="max-h-72 overflow-y-auto">
                  {#if searchResults.length > 0}
                    {#each searchResults as item, i}
                      <button
                        data-search-result
                        onclick={() => { handleNavigate(item.path); activeIndex = -1; }}
                        onmouseenter={() => activeIndex = i}
                        class="w-full flex items-center gap-3 px-3 py-2 transition-colors text-left
                          {i === activeIndex ? 'bg-blue-100 border-l-2 border-blue-600' : currentPath === item.path ? 'bg-blue-50 border-l-2 border-blue-500' : 'hover:bg-blue-50'}"
                      >
                        <div class="w-7 h-7 rounded-md {i === activeIndex ? 'bg-blue-200' : 'bg-gray-100'} flex items-center justify-center flex-shrink-0 transition-colors">
                          <svg class="w-4 h-4 {i === activeIndex ? 'text-blue-700' : 'text-gray-600'}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d={item.icon}/>
                          </svg>
                        </div>
                        <span class="flex-1 text-sm {i === activeIndex ? 'text-blue-800 font-medium' : 'text-gray-700'}">{item.label}</span>
                        {#if item.shortcut}
                          <kbd class="px-1.5 py-0.5 bg-gray-100 border border-gray-200 rounded text-xs font-mono text-gray-400">{item.shortcut}</kbd>
                        {/if}
                      </button>
                    {/each}
                  {:else}
                    <div class="px-4 py-6 text-center">
                      <svg class="w-8 h-8 text-gray-300 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0"/>
                      </svg>
                      <p class="text-sm text-gray-400">Sin resultados para <span class="font-medium text-gray-500">"{searchQuery}"</span></p>
                    </div>
                  {/if}
                </div>
                {#if searchResults.length > 0}
                  <div class="px-3 py-1.5 bg-gray-50 border-t border-gray-100 flex items-center gap-3 text-xs text-gray-400">
                    <span><kbd class="font-mono">↑↓</kbd> navegar</span>
                    <span><kbd class="font-mono">↵</kbd> abrir</span>
                    <span><kbd class="font-mono">Esc</kbd> cerrar</span>
                  </div>
                {/if}
              </div>
            {/if}
          </div>

          <!-- Mobile search icon (sm and below) -->
          <button
            class="sm:hidden p-2 text-gray-500 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
            onclick={() => { showSearch = !showSearch; setTimeout(() => searchInput?.focus(), 50); }}
            title="Buscar (Alt+B)"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0"/>
            </svg>
          </button>

          <!-- Notifications (placeholder) -->
          <button class="p-2 text-gray-500 hover:text-gray-900 hover:bg-gray-100 rounded-lg relative transition-colors">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
          </button>

          <!-- User Dropdown -->
          <div class="relative">
            <button
              onclick={() => showUserDropdown = !showUserDropdown}
              class="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <div class="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-sm font-bold flex-shrink-0 overflow-hidden">
                {#if user?.photoUrl}
                  <img src={user.photoUrl} alt="foto" class="w-full h-full object-cover" />
                {:else}
                  {(user?.fullName ?? 'U')[0].toUpperCase()}
                {/if}
              </div>
              <div class="hidden sm:block text-left">
                <div class="text-sm font-medium text-gray-900 leading-tight">{user?.fullName || 'Usuario'}</div>
                <div class="text-xs text-gray-500 leading-tight truncate max-w-[120px]">{user?.email || ''}</div>
              </div>
              <svg class="w-4 h-4 text-gray-400 transition-transform {showUserDropdown ? 'rotate-180' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
              </svg>
            </button>

            {#if showUserDropdown}
              <div class="fixed inset-0 z-40" onclick={() => showUserDropdown = false}></div>
              <div class="absolute right-0 top-full mt-1 w-56 bg-white rounded-xl shadow-xl border border-gray-200 z-50 py-1 overflow-hidden">
                <!-- User header -->
                <div class="px-4 py-3 bg-gray-50 border-b border-gray-100">
                  <div class="flex items-center gap-3">
                    <div class="w-9 h-9 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold text-sm overflow-hidden">
                      {#if user?.photoUrl}
                        <img src={user.photoUrl} alt="foto" class="w-full h-full object-cover" />
                      {:else}
                        {(user?.fullName ?? 'U')[0].toUpperCase()}
                      {/if}
                    </div>
                    <div class="min-w-0">
                      <div class="text-sm font-semibold text-gray-900 truncate">{user?.fullName}</div>
                      <div class="text-xs text-gray-500 truncate">{user?.email}</div>
                    </div>
                  </div>
                </div>
                <!-- Options -->
                <div class="py-1">
                  <button
                    onclick={() => { navigate('/perfil'); showUserDropdown = false; }}
                    class="w-full flex items-center gap-3 px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 hover:text-blue-700 transition-colors text-left"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
                    </svg>
                    Mi Perfil
                  </button>
                  <button
                    onclick={() => { navigate('/configuracion'); showUserDropdown = false; }}
                    class="w-full flex items-center gap-3 px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 hover:text-blue-700 transition-colors text-left"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                    </svg>
                    Configuración
                  </button>
                </div>
                <div class="border-t border-gray-100 pt-1">
                  <button
                    onclick={handleLogout}
                    class="w-full flex items-center gap-3 px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors text-left"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
                    </svg>
                    Cerrar Sesión
                  </button>
                </div>
              </div>
            {/if}
          </div>
        </div>
      </div>
    </div>
  </nav>

  <!-- Sidebar -->
  <aside
    class="fixed left-0 top-16 bottom-0 w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out z-30 flex flex-col md:translate-x-0"
    class:translate-x-0={sidebarOpen}
    class:-translate-x-full={!sidebarOpen}
  >
    <!-- Contenido scrollable del menú -->
    <nav class="flex-1 overflow-y-auto p-4 space-y-1">
      <!-- Admin Section (only for superadmin) -->
      {#if user?.isSuperadmin}
        <div class="px-4 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider border-b border-gray-200 mb-2">
          Panel Administrativo
        </div>
        {#each adminMenuItems as item}
          <button
            onclick={() => handleNavigate(item.path)}
            class="w-full flex items-center px-4 py-3 text-left rounded-lg transition-colors hover:bg-blue-100"
            class:bg-blue-50={currentPath === item.path}
            class:text-blue-600={currentPath === item.path}
            class:font-semibold={currentPath === item.path}
            class:text-gray-700={currentPath !== item.path}
          >
            <svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d={item.icon} />
            </svg>
            <span>{item.label}</span>
          </button>
        {/each}
        
        <div class="my-3 border-t border-gray-300"></div>
        
        <div class="px-4 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
          Mi Tenant
        </div>
      {/if}

      <!-- Regular Menu Items -->
      {#each menuItems as item}
        {#if hasModuleAccess(item.moduleKey)}
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

    <!-- Sidebar Footer fijo -->
    <div class="flex-shrink-0 p-4 border-t border-gray-200 bg-white">
      <div class="text-xs text-center text-gray-400">
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

  <!-- Botón flotante de ayuda (estilo chat assistant) -->
  <button
    onclick={() => showHelpModal = !showHelpModal}
    class="fixed bottom-6 right-6 w-14 h-14 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow-lg flex items-center justify-center z-40 transition-all duration-300 hover:scale-110"
    class:rotate-180={showHelpModal}
    title="Ayuda y Atajos"
  >
    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      {#if showHelpModal}
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
      {:else}
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      {/if}
    </svg>
  </button>

  <!-- Help Modal (Panel lateral deslizable desde abajo/derecha) -->
  {#if showHelpModal}
    <!-- Backdrop -->
    <div 
      class="fixed inset-0 bg-black bg-opacity-50 z-40 transition-opacity"
      onclick={() => showHelpModal = false}
    ></div>
    
    <!-- Panel de ayuda -->
    <div 
      transition:fly="{{ x: 400, duration: 300 }}"
      class="fixed right-0 top-0 bottom-0 w-full md:w-96 bg-white shadow-2xl z-50 flex flex-col"
    >
      <!-- Header fijo -->
      <div class="p-6 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50 flex-shrink-0">
        <div class="flex justify-between items-start">
          <div>
            <h2 class="text-xl font-bold text-gray-900 flex items-center">
              <svg class="w-6 h-6 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Ayuda
            </h2>
            <p class="text-sm text-gray-600 mt-1">Atajos de teclado</p>
          </div>
          <button
            onclick={() => showHelpModal = false}
            class="text-gray-400 hover:text-gray-600 p-1 hover:bg-gray-200 rounded transition-colors"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Contenido scrollable -->
      <div class="flex-1 overflow-y-auto p-6">
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
          <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
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
