<script lang="ts">
  import { authStore } from '../stores/auth';
  import { navigate } from '../lib/router';

  const user = $derived($authStore.user);

  // ── Notificaciones ──────────────────────────────────────
  let notifEmail = $state(true);
  let notifApp = $state(true);
  let notifResumen = $state(false);

  // ── Apariencia ──────────────────────────────────────────
  let compactMode = $state(false);
  let sidebarCollapsed = $state(false);

  // ── Idioma y región ─────────────────────────────────────
  let idioma = $state('es');
  let formatoFecha = $state('dd/mm/yyyy');
  let zonaHoraria = $state('America/Mexico_City');

  // ── Feedback ────────────────────────────────────────────
  let saving = $state(false);
  let saved = $state(false);

  async function guardar() {
    saving = true;
    await new Promise(r => setTimeout(r, 600));
    saving = false;
    saved = true;
    setTimeout(() => saved = false, 3000);
  }
</script>

<div class="min-h-full bg-gray-50">
  <!-- Header -->
  <div class="bg-white border-b border-gray-200 px-6 py-4">
    <div class="max-w-3xl mx-auto flex items-center gap-3">
      <button
        onclick={() => navigate('/perfil')}
        class="text-gray-400 hover:text-gray-600 transition-colors"
        aria-label="Volver"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
        </svg>
      </button>
      <div>
        <h1 class="text-lg font-semibold text-gray-900">Configuración</h1>
        <p class="text-sm text-gray-500">Preferencias de tu cuenta</p>
      </div>
    </div>
  </div>

  <!-- Content -->
  <div class="max-w-3xl mx-auto px-6 py-8 space-y-6">

    <!-- ── Notificaciones ──────────────────────────────── -->
    <div class="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
      <h3 class="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-5">Notificaciones</h3>
      <div class="space-y-4">
        <label class="flex items-center justify-between cursor-pointer">
          <div>
            <p class="text-sm font-medium text-gray-800">Notificaciones por correo</p>
            <p class="text-xs text-gray-500 mt-0.5">Recibe alertas de vencimientos y tareas en tu email</p>
          </div>
          <button
            role="switch"
            aria-checked={notifEmail}
            onclick={() => notifEmail = !notifEmail}
            class="relative w-10 h-6 rounded-full transition-colors {notifEmail ? 'bg-blue-600' : 'bg-gray-200'}"
          >
            <span class="absolute top-1 left-1 w-4 h-4 bg-white rounded-full shadow transition-transform {notifEmail ? 'translate-x-4' : 'translate-x-0'}"></span>
          </button>
        </label>

        <div class="border-t border-gray-100"></div>

        <label class="flex items-center justify-between cursor-pointer">
          <div>
            <p class="text-sm font-medium text-gray-800">Notificaciones en la app</p>
            <p class="text-xs text-gray-500 mt-0.5">Alertas y recordatorios dentro de la plataforma</p>
          </div>
          <button
            role="switch"
            aria-checked={notifApp}
            onclick={() => notifApp = !notifApp}
            class="relative w-10 h-6 rounded-full transition-colors {notifApp ? 'bg-blue-600' : 'bg-gray-200'}"
          >
            <span class="absolute top-1 left-1 w-4 h-4 bg-white rounded-full shadow transition-transform {notifApp ? 'translate-x-4' : 'translate-x-0'}"></span>
          </button>
        </label>

        <div class="border-t border-gray-100"></div>

        <label class="flex items-center justify-between cursor-pointer">
          <div>
            <p class="text-sm font-medium text-gray-800">Resumen semanal</p>
            <p class="text-xs text-gray-500 mt-0.5">Email con el resumen de actividad de la semana</p>
          </div>
          <button
            role="switch"
            aria-checked={notifResumen}
            onclick={() => notifResumen = !notifResumen}
            class="relative w-10 h-6 rounded-full transition-colors {notifResumen ? 'bg-blue-600' : 'bg-gray-200'}"
          >
            <span class="absolute top-1 left-1 w-4 h-4 bg-white rounded-full shadow transition-transform {notifResumen ? 'translate-x-4' : 'translate-x-0'}"></span>
          </button>
        </label>
      </div>
    </div>

    <!-- ── Apariencia ──────────────────────────────────── -->
    <div class="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
      <h3 class="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-5">Apariencia</h3>
      <div class="space-y-4">
        <label class="flex items-center justify-between cursor-pointer">
          <div>
            <p class="text-sm font-medium text-gray-800">Modo compacto</p>
            <p class="text-xs text-gray-500 mt-0.5">Reduce el espaciado para ver más información a la vez</p>
          </div>
          <button
            role="switch"
            aria-checked={compactMode}
            onclick={() => compactMode = !compactMode}
            class="relative w-10 h-6 rounded-full transition-colors {compactMode ? 'bg-blue-600' : 'bg-gray-200'}"
          >
            <span class="absolute top-1 left-1 w-4 h-4 bg-white rounded-full shadow transition-transform {compactMode ? 'translate-x-4' : 'translate-x-0'}"></span>
          </button>
        </label>

        <div class="border-t border-gray-100"></div>

        <label class="flex items-center justify-between cursor-pointer">
          <div>
            <p class="text-sm font-medium text-gray-800">Sidebar minimizado por defecto</p>
            <p class="text-xs text-gray-500 mt-0.5">Inicia con el menú lateral colapsado</p>
          </div>
          <button
            role="switch"
            aria-checked={sidebarCollapsed}
            onclick={() => sidebarCollapsed = !sidebarCollapsed}
            class="relative w-10 h-6 rounded-full transition-colors {sidebarCollapsed ? 'bg-blue-600' : 'bg-gray-200'}"
          >
            <span class="absolute top-1 left-1 w-4 h-4 bg-white rounded-full shadow transition-transform {sidebarCollapsed ? 'translate-x-4' : 'translate-x-0'}"></span>
          </button>
        </label>
      </div>
    </div>

    <!-- ── Idioma y región ─────────────────────────────── -->
    <div class="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
      <h3 class="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-5">Idioma y región</h3>
      <div class="space-y-4">
        <div>
          <label class="block text-xs font-medium text-gray-500 mb-1.5">Idioma</label>
          <select
            bind:value={idioma}
            class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
          >
            <option value="es">Español</option>
            <option value="en">English</option>
          </select>
        </div>

        <div>
          <label class="block text-xs font-medium text-gray-500 mb-1.5">Formato de fecha</label>
          <select
            bind:value={formatoFecha}
            class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
          >
            <option value="dd/mm/yyyy">DD/MM/YYYY</option>
            <option value="mm/dd/yyyy">MM/DD/YYYY</option>
            <option value="yyyy-mm-dd">YYYY-MM-DD</option>
          </select>
        </div>

        <div>
          <label class="block text-xs font-medium text-gray-500 mb-1.5">Zona horaria</label>
          <select
            bind:value={zonaHoraria}
            class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
          >
            <option value="America/Mexico_City">Ciudad de México (UTC-6)</option>
            <option value="America/Monterrey">Monterrey (UTC-6)</option>
            <option value="America/Tijuana">Tijuana (UTC-8)</option>
            <option value="America/Bogota">Bogotá (UTC-5)</option>
            <option value="America/Lima">Lima (UTC-5)</option>
            <option value="America/Santiago">Santiago (UTC-4)</option>
            <option value="America/Argentina/Buenos_Aires">Buenos Aires (UTC-3)</option>
          </select>
        </div>
      </div>
    </div>

    <!-- ── Guardar ──────────────────────────────────────── -->
    <div class="flex items-center justify-between">
      <button
        onclick={() => navigate('/perfil')}
        class="text-sm text-gray-500 hover:text-gray-700 transition-colors"
      >
        Cancelar
      </button>
      <button
        onclick={guardar}
        disabled={saving}
        class="flex items-center gap-2 px-6 py-2.5 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
      >
        {#if saving}
          <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
          </svg>
          Guardando…
        {:else if saved}
          <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
          </svg>
          Guardado
        {:else}
          Guardar cambios
        {/if}
      </button>
    </div>

  </div>
</div>
