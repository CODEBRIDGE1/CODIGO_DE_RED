<script lang="ts">
  import { onMount } from 'svelte';
  import { authStore } from './stores/auth';
  import { createRouter, currentPath, navigate } from './lib/router';
  
  import Login from './components/Login.svelte';
  import Layout from './components/Layout.svelte';
  import Dashboard from './components/Dashboard.svelte';
  import Empresas from './components/Empresas.svelte';
  import Usuarios from './components/Usuarios.svelte';
  import Obligaciones from './components/Obligaciones.svelte';
  import Proyectos from './components/Proyectos.svelte';
  
  const isAuthenticated = $derived($authStore.isAuthenticated);

  // Cargar autenticación desde storage al iniciar
  onMount(() => {
    const loaded = authStore.loadFromStorage();
    if (loaded && window.location.pathname === '/') {
      navigate('/dashboard');
    }
  });

  // Proteger rutas
  $effect(() => {
    if (!isAuthenticated && $currentPath !== '/' && $currentPath !== '/login') {
      navigate('/');
    }
  });
</script>

{#if !isAuthenticated}
  <Login />
{:else}
  <Layout>
    {#if $currentPath === '/dashboard'}
      <Dashboard />
    {:else if $currentPath === '/empresas'}
      <Empresas />
    {:else if $currentPath === '/obligaciones'}
      <Obligaciones />
    {:else if $currentPath === '/proyectos'}
      <Proyectos />
    {:else if $currentPath === '/evidencias'}
      <div class="p-6">
        <h1 class="text-2xl font-bold">Evidencias</h1>
        <p class="text-gray-600 mt-2">Módulo en construcción...</p>
      </div>
    {:else if $currentPath === '/cotizaciones'}
      <div class="p-6">
        <h1 class="text-2xl font-bold">Cotizaciones</h1>
        <p class="text-gray-600 mt-2">Módulo en construcción...</p>
      </div>
    {:else if $currentPath === '/reportes'}
      <div class="p-6">
        <h1 class="text-2xl font-bold">Reportes</h1>
        <p class="text-gray-600 mt-2">Módulo en construcción...</p>
      </div>
    {:else if $currentPath === '/usuarios'}
      <Usuarios />
    {:else if $currentPath === '/auditoria'}
      <div class="p-6">
        <h1 class="text-2xl font-bold">Auditoría</h1>
        <p class="text-gray-600 mt-2">Módulo en construcción...</p>
      </div>
    {:else}
      <div class="p-6">
        <h1 class="text-2xl font-bold">Página no encontrada</h1>
        <p class="text-gray-600 mt-2">La ruta solicitada no existe.</p>
      </div>
    {/if}
  </Layout>
{/if}

