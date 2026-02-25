<script lang="ts">
  import { onMount } from 'svelte';
  import { authStore } from '../stores/auth';
  
  let stats = $state({
    totalEmpresas: 0,
    obligacionesCumplidas: 0,
    obligacionesPendientes: 0,
    proyectosActivos: 0,
    evidenciasRecientes: 0,
    cotizacionesAbiertas: 0
  });

  let loading = $state(true);
  let recentActivity = $state<any[]>([]);

  const user = $derived($authStore.user);

  onMount(async () => {
    // Simular carga de datos (aquí irían las llamadas al API)
    await new Promise(resolve => setTimeout(resolve, 800));
    
    stats = {
      totalEmpresas: 12,
      obligacionesCumplidas: 45,
      obligacionesPendientes: 23,
      proyectosActivos: 8,
      evidenciasRecientes: 34,
      cotizacionesAbiertas: 5
    };

    recentActivity = [
      { type: 'empresa', action: 'Nueva empresa registrada', name: 'Industrias ABC', time: 'Hace 2 horas' },
      { type: 'evidencia', action: 'Evidencia cargada', name: 'Dictamen eléctrico - Planta Norte', time: 'Hace 3 horas' },
      { type: 'proyecto', action: 'Proyecto actualizado', name: 'Adecuación red baja tensión', time: 'Hace 5 horas' },
      { type: 'cotizacion', action: 'Cotización enviada', name: 'Estudio de calidad de energía', time: 'Hace 1 día' }
    ];
    
    loading = false;
  });
</script>

<div class="p-6 max-w-7xl mx-auto">
  <!-- Header -->
  <div class="mb-8">
    <h1 class="text-3xl font-bold text-gray-900">Panel de Control</h1>
    <p class="text-gray-600 mt-2">Bienvenido, {user?.fullName || 'Usuario'}</p>
  </div>

  {#if loading}
    <!-- Loading Skeleton -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
      {#each Array(6) as _}
        <div class="bg-white rounded-lg shadow p-6 animate-pulse">
          <div class="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
          <div class="h-8 bg-gray-200 rounded w-1/4"></div>
        </div>
      {/each}
    </div>
  {:else}
    <!-- Stats Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
      <!-- Total Empresas -->
      <div class="bg-white rounded-lg shadow hover:shadow-lg transition-shadow p-6 border-l-4 border-blue-500">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-600 uppercase">Empresas Registradas</p>
            <p class="text-3xl font-bold text-gray-900 mt-2">{stats.totalEmpresas}</p>
          </div>
          <div class="bg-blue-100 p-3 rounded-full">
            <svg class="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
          </div>
        </div>
      </div>

      <!-- Obligaciones Cumplidas -->
      <div class="bg-white rounded-lg shadow hover:shadow-lg transition-shadow p-6 border-l-4 border-green-500">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-600 uppercase">Obligaciones Cumplidas</p>
            <p class="text-3xl font-bold text-gray-900 mt-2">{stats.obligacionesCumplidas}</p>
          </div>
          <div class="bg-green-100 p-3 rounded-full">
            <svg class="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
        </div>
      </div>

      <!-- Obligaciones Pendientes -->
      <div class="bg-white rounded-lg shadow hover:shadow-lg transition-shadow p-6 border-l-4 border-yellow-500">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-600 uppercase">Obligaciones Pendientes</p>
            <p class="text-3xl font-bold text-gray-900 mt-2">{stats.obligacionesPendientes}</p>
          </div>
          <div class="bg-yellow-100 p-3 rounded-full">
            <svg class="w-8 h-8 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
        </div>
      </div>

      <!-- Proyectos Activos -->
      <div class="bg-white rounded-lg shadow hover:shadow-lg transition-shadow p-6 border-l-4 border-purple-500">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-600 uppercase">Proyectos Activos</p>
            <p class="text-3xl font-bold text-gray-900 mt-2">{stats.proyectosActivos}</p>
          </div>
          <div class="bg-purple-100 p-3 rounded-full">
            <svg class="w-8 h-8 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          </div>
        </div>
      </div>

      <!-- Evidencias Recientes -->
      <div class="bg-white rounded-lg shadow hover:shadow-lg transition-shadow p-6 border-l-4 border-indigo-500">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-600 uppercase">Evidencias Recientes</p>
            <p class="text-3xl font-bold text-gray-900 mt-2">{stats.evidenciasRecientes}</p>
          </div>
          <div class="bg-indigo-100 p-3 rounded-full">
            <svg class="w-8 h-8 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
            </svg>
          </div>
        </div>
      </div>

      <!-- Cotizaciones Abiertas -->
      <div class="bg-white rounded-lg shadow hover:shadow-lg transition-shadow p-6 border-l-4 border-orange-500">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-600 uppercase">Cotizaciones Abiertas</p>
            <p class="text-3xl font-bold text-gray-900 mt-2">{stats.cotizacionesAbiertas}</p>
          </div>
          <div class="bg-orange-100 p-3 rounded-full">
            <svg class="w-8 h-8 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 14l6-6m-5.5.5h.01m4.99 5h.01M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16l3.5-2 3.5 2 3.5-2 3.5 2z" />
            </svg>
          </div>
        </div>
      </div>
    </div>

    <!-- Recent Activity -->
    <div class="bg-white rounded-lg shadow">
      <div class="p-6 border-b border-gray-200">
        <h2 class="text-xl font-bold text-gray-900">Actividad Reciente</h2>
      </div>
      <div class="divide-y divide-gray-200">
        {#each recentActivity as activity}
          <div class="p-6 hover:bg-gray-50 transition-colors">
            <div class="flex items-start space-x-4">
              <div class="flex-shrink-0">
                {#if activity.type === 'empresa'}
                  <div class="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                    <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                    </svg>
                  </div>
                {:else if activity.type === 'evidencia'}
                  <div class="w-10 h-10 bg-indigo-100 rounded-full flex items-center justify-center">
                    <svg class="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                    </svg>
                  </div>
                {:else if activity.type === 'proyecto'}
                  <div class="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center">
                    <svg class="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                    </svg>
                  </div>
                {:else}
                  <div class="w-10 h-10 bg-orange-100 rounded-full flex items-center justify-center">
                    <svg class="w-5 h-5 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 14l6-6m-5.5.5h.01m4.99 5h.01M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16l3.5-2 3.5 2 3.5-2 3.5 2z" />
                    </svg>
                  </div>
                {/if}
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-gray-900">{activity.action}</p>
                <p class="text-sm text-gray-600 truncate">{activity.name}</p>
                <p class="text-xs text-gray-400 mt-1">{activity.time}</p>
              </div>
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}
</div>
