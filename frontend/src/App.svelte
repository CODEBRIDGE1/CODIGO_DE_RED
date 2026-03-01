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
  import Cotizaciones from './components/Cotizaciones.svelte';
  import Auditoria from './components/Auditoria.svelte';
  import Perfil from './components/Perfil.svelte';
  import AdminClientes from './components/admin/AdminClientes.svelte';
  import AdminConceptos from './components/admin/AdminConceptos.svelte';
  import AdminNiveles from './components/admin/AdminNiveles.svelte';
  import AdminCotizaciones from './components/admin/AdminCotizaciones.svelte';
  
  const isAuthenticated = $derived($authStore.isAuthenticated);

  // Cargar autenticación desde storage al iniciar, luego refrescar perfil del servidor
  onMount(async () => {
    const loaded = authStore.loadFromStorage();
    if (loaded) {
      if (window.location.pathname === '/') {
        navigate('/dashboard');
      }
      // Refrescar perfil para obtener securityModules actualizados
      try {
        const token = localStorage.getItem('access_token');
        if (token) {
          const res = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/auth/me`, {
            headers: { 'Authorization': `Bearer ${token}` }
          });
          if (res.ok) {
            const profile = await res.json();
            let permissionsArray: string[] = [];
            if (profile.permissions && typeof profile.permissions === 'object') {
              Object.entries(profile.permissions).forEach(([module, actions]) => {
                if (Array.isArray(actions)) {
                  (actions as string[]).forEach((action: string) => {
                    permissionsArray.push(`${module}.${action}`);
                  });
                }
              });
            }
            authStore.updateUser({
              id: profile.id,
              email: profile.email,
              fullName: profile.full_name,
              tenantId: profile.tenant_id,
              isSuperadmin: profile.is_superadmin,
              photoUrl: profile.photo_url ?? null,
              permissions: permissionsArray,
              securityModules: profile.security_modules ?? [],
              securityLevelId: profile.security_level_id ?? null,
              securityLevelName: profile.security_level_name ?? null
            });
          }
        }
      } catch (_) {
        // Si falla, se usan los datos de localStorage sin interrumpir la sesión
      }
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
      <Cotizaciones />
    {:else if $currentPath === '/reportes'}
      <div class="p-6">
        <h1 class="text-2xl font-bold">Reportes</h1>
        <p class="text-gray-600 mt-2">Módulo en construcción...</p>
      </div>
    {:else if $currentPath === '/usuarios'}
      <Usuarios />
    {:else if $currentPath === '/auditoria'}
      <Auditoria />
    {:else if $currentPath === '/perfil'}
      <Perfil />
    {:else if $currentPath === '/admin/clientes'}
      <AdminClientes />
    {:else if $currentPath === '/admin/conceptos'}
      <AdminConceptos />
    {:else if $currentPath === '/admin/niveles'}
      <AdminNiveles />
    {:else if $currentPath === '/admin/cotizaciones'}
      <AdminCotizaciones />
    {:else if $currentPath === '/admin/usuarios'}
      <Usuarios />
    {:else if $currentPath === '/admin/matrices'}
      <div class="p-6">
        <h1 class="text-2xl font-bold">Matrices de Obligación</h1>
        <p class="text-gray-600 mt-2">Módulo en construcción...</p>
      </div>
    {:else if $currentPath === '/admin/proyectos'}
      <div class="p-6">
        <h1 class="text-2xl font-bold">Todos los Proyectos</h1>
        <p class="text-gray-600 mt-2">Módulo en construcción...</p>
      </div>
    {:else if $currentPath === '/admin/reportes'}
      <div class="p-6">
        <h1 class="text-2xl font-bold">Reportes Generales</h1>
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

