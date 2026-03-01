<script lang="ts">
  import { onMount } from 'svelte';
  import { authStore } from '../stores/auth';

  interface RecentItem {
    type: 'empresa' | 'proyecto' | 'cotizacion';
    action: string;
    name: string;
    time: string;
    status?: string;
  }

  let stats = $state({
    totalEmpresas: 0,
    proyectosAbiertos: 0,
    proyectosEnProgreso: 0,
    cotizacionesDraft: 0,
    cotizacionesTotal: 0,
    documentosTotal: 0
  });

  let loading = $state(true);
  let errorMsg = $state('');
  let recentEmpresas = $state<any[]>([]);
  let recentProyectos = $state<any[]>([]);
  let recentCotizaciones = $state<any[]>([]);

  const user = $derived($authStore.user);
  const API = import.meta.env.VITE_API_BASE_URL;

  function headers() {
    return { 'Authorization': `Bearer ${$authStore.accessToken}` };
  }

  function timeAgo(dateStr: string): string {
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    if (mins < 60) return `Hace ${mins} min`;
    if (hours < 24) return `Hace ${hours} h`;
    return `Hace ${days} día${days > 1 ? 's' : ''}`;
  }

  function getStatusLabel(status: string): string {
    const m: Record<string, string> = {
      ABIERTO: 'Abierto', EN_PROGRESO: 'En progreso', CERRADO: 'Cerrado',
      draft: 'Borrador', sent: 'Enviada', approved: 'Aprobada', rejected: 'Rechazada'
    };
    return m[status] || status;
  }

  function getStatusColor(status: string): string {
    const m: Record<string, string> = {
      ABIERTO: 'bg-blue-100 text-blue-700',
      EN_PROGRESO: 'bg-yellow-100 text-yellow-700',
      CERRADO: 'bg-gray-100 text-gray-600',
      draft: 'bg-gray-100 text-gray-700',
      sent: 'bg-blue-100 text-blue-700',
      approved: 'bg-green-100 text-green-700',
      rejected: 'bg-red-100 text-red-700'
    };
    return m[status] || 'bg-gray-100 text-gray-600';
  }

  onMount(async () => {
    try {
      loading = true;

      const [companiesRes, projectsRes, quotesRes, openProjectsRes] = await Promise.allSettled([
        fetch(`${API}/api/v1/companies/?page_size=5`, { headers: headers() }),
        fetch(`${API}/api/v1/projects/?status=EN_PROGRESO`, { headers: headers() }),
        fetch(`${API}/api/v1/quotes/?page_size=5`, { headers: headers() }),
        fetch(`${API}/api/v1/projects/?status=ABIERTO`, { headers: headers() }),
      ]);

      // Empresas
      if (companiesRes.status === 'fulfilled' && companiesRes.value.ok) {
        const data = await companiesRes.value.json();
        stats.totalEmpresas = data.total ?? 0;
        recentEmpresas = (data.companies ?? []).slice(0, 3);
      }

      // Proyectos en progreso
      if (projectsRes.status === 'fulfilled' && projectsRes.value.ok) {
        const data = await projectsRes.value.json();
        stats.proyectosEnProgreso = Array.isArray(data) ? data.length : 0;
        recentProyectos = (Array.isArray(data) ? data : []).slice(0, 3);
      }

      // Proyectos abiertos
      if (openProjectsRes.status === 'fulfilled' && openProjectsRes.value.ok) {
        const data = await openProjectsRes.value.json();
        stats.proyectosAbiertos = Array.isArray(data) ? data.length : 0;
        // Mezclar con en progreso si no hay proyectos en progreso
        if (recentProyectos.length === 0) {
          recentProyectos = (Array.isArray(data) ? data : []).slice(0, 3);
        }
      }

      // Cotizaciones
      if (quotesRes.status === 'fulfilled' && quotesRes.value.ok) {
        const data = await quotesRes.value.json();
        stats.cotizacionesTotal = data.total ?? 0;
        stats.cotizacionesDraft = (data.quotes ?? []).filter((q: any) => q.status === 'draft').length;
        recentCotizaciones = (data.quotes ?? []).slice(0, 3);
      }

    } catch (e: any) {
      errorMsg = 'Error al cargar el panel';
      console.error(e);
    } finally {
      loading = false;
    }
  });
</script>

<div class="p-6 max-w-7xl mx-auto">
  <!-- Header -->
  <div class="mb-8">
    <h1 class="text-3xl font-bold text-gray-900">Panel de Control</h1>
    <p class="text-gray-600 mt-2">Bienvenido, {user?.fullName || 'Usuario'}</p>
  </div>

  {#if errorMsg}
    <div class="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">{errorMsg}</div>
  {/if}

  {#if loading}
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      {#each Array(4) as _}
        <div class="bg-white rounded-lg shadow p-6 animate-pulse">
          <div class="h-3 bg-gray-200 rounded w-2/3 mb-4"></div>
          <div class="h-8 bg-gray-200 rounded w-1/3"></div>
        </div>
      {/each}
    </div>
  {:else}
    <!-- Stats Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">

      <!-- Empresas -->
      <div class="bg-white rounded-xl shadow hover:shadow-md transition-shadow p-6 border-l-4 border-blue-500">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-xs font-semibold text-gray-500 uppercase tracking-wide">Empresas</p>
            <p class="text-4xl font-bold text-gray-900 mt-2">{stats.totalEmpresas}</p>
            <p class="text-xs text-gray-500 mt-1">registradas</p>
          </div>
          <div class="bg-blue-100 p-3 rounded-xl">
            <svg class="w-7 h-7 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
          </div>
        </div>
      </div>

      <!-- Proyectos Abiertos -->
      <div class="bg-white rounded-xl shadow hover:shadow-md transition-shadow p-6 border-l-4 border-green-500">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-xs font-semibold text-gray-500 uppercase tracking-wide">Proyectos Abiertos</p>
            <p class="text-4xl font-bold text-gray-900 mt-2">{stats.proyectosAbiertos}</p>
            <p class="text-xs text-gray-500 mt-1">{stats.proyectosEnProgreso} en progreso</p>
          </div>
          <div class="bg-green-100 p-3 rounded-xl">
            <svg class="w-7 h-7 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          </div>
        </div>
      </div>

      <!-- Cotizaciones -->
      <div class="bg-white rounded-xl shadow hover:shadow-md transition-shadow p-6 border-l-4 border-orange-500">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-xs font-semibold text-gray-500 uppercase tracking-wide">Cotizaciones</p>
            <p class="text-4xl font-bold text-gray-900 mt-2">{stats.cotizacionesTotal}</p>
            <p class="text-xs text-gray-500 mt-1">{stats.cotizacionesDraft} en borrador</p>
          </div>
          <div class="bg-orange-100 p-3 rounded-xl">
            <svg class="w-7 h-7 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 14l6-6m-5.5.5h.01m4.99 5h.01M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16l3.5-2 3.5 2 3.5-2 3.5 2z" />
            </svg>
          </div>
        </div>
      </div>

      <!-- Empresas con proyectos activos (calculado) -->
      <div class="bg-white rounded-xl shadow hover:shadow-md transition-shadow p-6 border-l-4 border-purple-500">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-xs font-semibold text-gray-500 uppercase tracking-wide">Proyectos Totales</p>
            <p class="text-4xl font-bold text-gray-900 mt-2">{stats.proyectosAbiertos + stats.proyectosEnProgreso}</p>
            <p class="text-xs text-gray-500 mt-1">activos en el sistema</p>
          </div>
          <div class="bg-purple-100 p-3 rounded-xl">
            <svg class="w-7 h-7 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
        </div>
      </div>
    </div>

    <!-- Listas recientes -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">

      <!-- Empresas recientes -->
      <div class="bg-white rounded-xl shadow">
        <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <h2 class="text-base font-semibold text-gray-900">Empresas Recientes</h2>
          <a href="/empresas" class="text-xs text-blue-600 hover:underline">Ver todas</a>
        </div>
        <div class="divide-y divide-gray-50">
          {#if recentEmpresas.length === 0}
            <div class="px-6 py-8 text-center text-gray-400 text-sm">Sin empresas registradas</div>
          {:else}
            {#each recentEmpresas as empresa}
              <div class="px-6 py-4 hover:bg-gray-50 transition-colors">
                <div class="flex items-center gap-3">
                  <div class="w-9 h-9 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
                    <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                    </svg>
                  </div>
                  <div class="flex-1 min-w-0">
                    <p class="text-sm font-medium text-gray-900 truncate">{empresa.razon_social}</p>
                    <p class="text-xs text-gray-500">{empresa.rfc}</p>
                  </div>
                </div>
              </div>
            {/each}
          {/if}
        </div>
      </div>

      <!-- Proyectos recientes -->
      <div class="bg-white rounded-xl shadow">
        <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <h2 class="text-base font-semibold text-gray-900">Proyectos Activos</h2>
          <a href="/proyectos" class="text-xs text-blue-600 hover:underline">Ver todos</a>
        </div>
        <div class="divide-y divide-gray-50">
          {#if recentProyectos.length === 0}
            <div class="px-6 py-8 text-center text-gray-400 text-sm">Sin proyectos activos</div>
          {:else}
            {#each recentProyectos as proyecto}
              <div class="px-6 py-4 hover:bg-gray-50 transition-colors">
                <div class="flex items-start gap-3">
                  <div class="w-9 h-9 bg-purple-100 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5">
                    <svg class="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                    </svg>
                  </div>
                  <div class="flex-1 min-w-0">
                    <p class="text-sm font-medium text-gray-900 truncate">{proyecto.name}</p>
                    <div class="flex items-center gap-2 mt-1">
                      <span class="text-xs px-2 py-0.5 rounded-full {getStatusColor(proyecto.status)}">
                        {getStatusLabel(proyecto.status)}
                      </span>
                      {#if proyecto.total_tasks}
                        <span class="text-xs text-gray-400">{proyecto.completed_tasks}/{proyecto.total_tasks} tareas</span>
                      {/if}
                    </div>
                  </div>
                </div>
              </div>
            {/each}
          {/if}
        </div>
      </div>

      <!-- Cotizaciones recientes -->
      <div class="bg-white rounded-xl shadow">
        <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <h2 class="text-base font-semibold text-gray-900">Cotizaciones Recientes</h2>
          <a href="/cotizaciones" class="text-xs text-blue-600 hover:underline">Ver todas</a>
        </div>
        <div class="divide-y divide-gray-50">
          {#if recentCotizaciones.length === 0}
            <div class="px-6 py-8 text-center text-gray-400 text-sm">Sin cotizaciones</div>
          {:else}
            {#each recentCotizaciones as cot}
              <div class="px-6 py-4 hover:bg-gray-50 transition-colors">
                <div class="flex items-start gap-3">
                  <div class="w-9 h-9 bg-orange-100 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5">
                    <svg class="w-5 h-5 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 14l6-6m-5.5.5h.01m4.99 5h.01M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16l3.5-2 3.5 2 3.5-2 3.5 2z" />
                    </svg>
                  </div>
                  <div class="flex-1 min-w-0">
                    <p class="text-xs font-mono text-gray-500">{cot.quote_number}</p>
                    <p class="text-sm font-medium text-gray-900 truncate">{cot.title}</p>
                    <div class="flex items-center gap-2 mt-1">
                      <span class="text-xs px-2 py-0.5 rounded-full {getStatusColor(cot.status)}">
                        {getStatusLabel(cot.status)}
                      </span>
                      <span class="text-xs text-gray-400 truncate">{cot.razon_social}</span>
                    </div>
                  </div>
                </div>
              </div>
            {/each}
          {/if}
        </div>
      </div>

    </div>
  {/if}
</div>
