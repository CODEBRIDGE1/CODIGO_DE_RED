<script lang="ts">
  import { onMount } from 'svelte';
  import { authStore } from '../stores/auth';
  import { navigate } from '../lib/router';

  const BASE = (import.meta as any).env?.VITE_API_BASE_URL ?? '';

  // ── Estado ──────────────────────────────────────────────
  let user = $derived($authStore.user);

  let editingName = $state(false);
  let newName = $state('');
  let savingName = $state(false);
  let nameError = $state('');
  let nameSuccess = $state(false);

  let uploadingPhoto = $state(false);
  let photoError = $state('');
  let photoSuccess = $state(false);
  let photoPreview = $state<string | null>(null);

  let fileInput: HTMLInputElement;

  onMount(() => {
    newName = user?.fullName ?? '';
    photoPreview = user?.photoUrl ?? null;
  });

  // ── Foto ─────────────────────────────────────────────────
  function onFileChange(e: Event) {
    const input = e.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;

    // Preview local
    const reader = new FileReader();
    reader.onload = (ev) => { photoPreview = ev.target?.result as string; };
    reader.readAsDataURL(file);

    uploadPhoto(file);
  }

  async function uploadPhoto(file: File) {
    uploadingPhoto = true;
    photoError = '';
    photoSuccess = false;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`${BASE}/api/v1/auth/me/photo`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail ?? 'Error al subir la foto');
      }

      const profile = await res.json();
      // Actualizar store con nueva foto
      authStore.updateUser({
        ...user!,
        photoUrl: profile.photo_url ?? null,
        fullName: profile.full_name,
      });
      photoPreview = profile.photo_url ?? photoPreview;
      photoSuccess = true;
      setTimeout(() => { photoSuccess = false; }, 3000);
    } catch (err: any) {
      photoError = err.message ?? 'Error desconocido';
      photoPreview = user?.photoUrl ?? null;
    } finally {
      uploadingPhoto = false;
    }
  }

  // ── Nombre ───────────────────────────────────────────────
  async function saveName() {
    if (!newName.trim() || newName.trim().length < 2) {
      nameError = 'El nombre debe tener al menos 2 caracteres.';
      return;
    }
    savingName = true;
    nameError = '';
    nameSuccess = false;

    try {
      const res = await authStore.fetch(`${BASE}/api/v1/auth/me`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ full_name: newName.trim() }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail ?? 'Error al guardar');
      }

      const profile = await res.json();
      authStore.updateUser({
        ...user!,
        fullName: profile.full_name,
        photoUrl: profile.photo_url ?? user?.photoUrl ?? null,
      });
      editingName = false;
      nameSuccess = true;
      setTimeout(() => { nameSuccess = false; }, 3000);
    } catch (err: any) {
      nameError = err.message ?? 'Error desconocido';
    } finally {
      savingName = false;
    }
  }

  function cancelEdit() {
    newName = user?.fullName ?? '';
    nameError = '';
    editingName = false;
  }

  let changingPassword = $state(false);
  let pwCurrent = $state('');
  let pwNew = $state('');
  let pwConfirm = $state('');
  let pwSaving = $state(false);
  let pwError = $state('');
  let pwSuccess = $state(false);
  let showPwCurrent = $state(false);
  let showPwNew = $state(false);
  let showPwConfirm = $state(false);

  async function savePassword() {
    pwError = '';
    if (!pwCurrent) { pwError = 'Ingresa tu contraseña actual.'; return; }
    if (pwNew.length < 8) { pwError = 'La nueva contraseña debe tener al menos 8 caracteres.'; return; }
    if (pwNew !== pwConfirm) { pwError = 'Las contraseñas no coinciden.'; return; }
    pwSaving = true;
    try {
      const res = await authStore.fetch(`${BASE}/api/v1/auth/me/password`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ current_password: pwCurrent, new_password: pwNew }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail ?? 'Error al cambiar la contraseña');
      }
      pwSuccess = true;
      pwCurrent = pwNew = pwConfirm = '';
      changingPassword = false;
      setTimeout(() => { pwSuccess = false; }, 4000);
    } catch (err: any) {
      pwError = err.message ?? 'Error desconocido';
    } finally {
      pwSaving = false;
    }
  }

  function cancelPassword() {
    pwCurrent = pwNew = pwConfirm = pwError = '';
    changingPassword = false;
  }
  const MODULE_LABELS: Record<string, string> = {
    empresas: 'Empresas',
    proyectos: 'Proyectos',
    cotizaciones: 'Cotizaciones',
    obligaciones: 'Obligaciones',
    usuarios: 'Usuarios',
    auditoria: 'Auditoría',
    reportes: 'Reportes',
    evidencias: 'Evidencias',
    dashboard: 'Dashboard',
  };
  function modLabel(key: string) { return MODULE_LABELS[key] ?? key; }
</script>

<!-- ═══════════════════════════════════════════════════════ -->
<!--  PÁGINA DE PERFIL                                      -->
<!-- ═══════════════════════════════════════════════════════ -->
<div class="min-h-screen bg-gray-50">

  <!-- ── Barra superior ──────────────────────────────────── -->
  <div class="bg-white border-b border-gray-200 px-6 py-4 flex items-center gap-3">
    <button
      onclick={() => navigate('/dashboard')}
      class="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-900 transition-colors"
    >
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
      </svg>
      Volver
    </button>
    <span class="text-gray-300">|</span>
    <h1 class="text-lg font-semibold text-gray-900">Mi Perfil</h1>
  </div>

  <div class="max-w-3xl mx-auto px-4 py-8 space-y-6">

    <!-- ── Tarjeta principal: foto + nombre ─────────────── -->
    <div class="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
      <!-- Banner degradado -->
      <div class="h-28 bg-gradient-to-r from-blue-600 to-indigo-500"></div>

      <!-- Foto + info -->
      <div class="px-6 pb-6">
        <div class="flex flex-col sm:flex-row sm:items-end gap-4 -mt-12 mb-4">
          <!-- Foto de perfil -->
          <div class="relative flex-shrink-0">
            <div class="w-24 h-24 rounded-full border-4 border-white shadow-lg bg-blue-600 flex items-center justify-center text-white text-3xl font-bold overflow-hidden">
              {#if photoPreview}
                <img src={photoPreview} alt="foto de perfil" class="w-full h-full object-cover" />
              {:else}
                {(user?.fullName ?? 'U')[0].toUpperCase()}
              {/if}
            </div>

            <!-- Botón cámara -->
            <button
              onclick={() => fileInput.click()}
              disabled={uploadingPhoto}
              class="absolute bottom-0 right-0 w-8 h-8 rounded-full bg-white border-2 border-gray-200 shadow flex items-center justify-center text-gray-600 hover:bg-blue-50 hover:border-blue-300 hover:text-blue-600 transition-colors disabled:opacity-50"
              title="Cambiar foto"
            >
              {#if uploadingPhoto}
                <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
                </svg>
              {:else}
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"/>
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"/>
                </svg>
              {/if}
            </button>

            <!-- Input file oculto -->
            <input
              bind:this={fileInput}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              class="hidden"
              onchange={onFileChange}
            />
          </div>

          <!-- Nombre y rol -->
          <div class="flex-1 min-w-0 pt-2 sm:pt-0">
            <h2 class="text-xl font-bold text-gray-900 truncate">{user?.fullName}</h2>
            <p class="text-sm text-gray-500 mt-0.5">
              {user?.isSuperadmin ? '🛡️ Super Administrador' : '👤 Usuario de organización'}
            </p>
          </div>
        </div>

        <!-- Mensajes foto -->
        {#if photoSuccess}
          <p class="text-sm text-green-600 flex items-center gap-1.5 mb-2">
            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/></svg>
            Foto actualizada correctamente
          </p>
        {/if}
        {#if photoError}
          <p class="text-sm text-red-500 mb-2">{photoError}</p>
        {/if}
        <p class="text-xs text-gray-400">JPG, PNG o WEBP · máx. 5 MB</p>
      </div>
    </div>

    <!-- ── Información personal ──────────────────────────── -->
    <div class="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
      <h3 class="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4">Información Personal</h3>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">

        <!-- Nombre -->
        <div class="sm:col-span-2">
          <p class="text-xs font-medium text-gray-400 mb-1">Nombre completo</p>
          {#if editingName}
            <div class="flex gap-2">
              <input
                type="text"
                bind:value={newName}
                onkeydown={(e) => { if (e.key === 'Enter') saveName(); if (e.key === 'Escape') cancelEdit(); }}
                class="flex-1 px-3 py-2 border border-blue-400 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                autofocus
              />
              <button
                onclick={saveName}
                disabled={savingName}
                class="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                {savingName ? 'Guardando…' : 'Guardar'}
              </button>
              <button
                onclick={cancelEdit}
                class="px-3 py-2 text-gray-500 hover:text-gray-700 rounded-lg text-sm transition-colors"
              >
                Cancelar
              </button>
            </div>
            {#if nameError}
              <p class="text-xs text-red-500 mt-1">{nameError}</p>
            {/if}
          {:else}
            <div class="flex items-center gap-2 group">
              <p class="text-sm font-medium text-gray-900">{user?.fullName}</p>
              <button
                onclick={() => { editingName = true; newName = user?.fullName ?? ''; }}
                class="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-blue-600 transition-all rounded"
                title="Editar nombre"
              >
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"/>
                </svg>
              </button>
            </div>
            {#if nameSuccess}
              <p class="text-xs text-green-600 mt-0.5 flex items-center gap-1">
                <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/></svg>
                Nombre actualizado
              </p>
            {/if}
          {/if}
        </div>

        <!-- Email -->
        <div>
          <p class="text-xs font-medium text-gray-400 mb-1">Correo electrónico</p>
          <p class="text-sm text-gray-900">{user?.email}</p>
        </div>

        <!-- Tipo de cuenta -->
        <div>
          <p class="text-xs font-medium text-gray-400 mb-1">Tipo de cuenta</p>
          <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium {user?.isSuperadmin ? 'bg-purple-100 text-purple-700' : 'bg-blue-100 text-blue-700'}">
            {user?.isSuperadmin ? '🛡️ Super Administrador' : '👤 Usuario'}
          </span>
        </div>

        <!-- Nivel de seguridad (solo si no es superadmin) -->
        {#if !user?.isSuperadmin && user?.securityLevelName}
          <div>
            <p class="text-xs font-medium text-gray-400 mb-1">Nivel de seguridad</p>
            <p class="text-sm text-gray-900">{user.securityLevelName}</p>
          </div>
        {/if}

      </div>
    </div>

    <!-- ── Módulos con acceso (solo si tiene asignados) ──── -->
    {#if !user?.isSuperadmin && user?.securityModules && user.securityModules.length > 0}
      <div class="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
        <h3 class="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4">Módulos con acceso</h3>
        <div class="flex flex-wrap gap-2">
          {#each user.securityModules as mod}
            <span class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-50 text-blue-700 text-sm rounded-lg font-medium border border-blue-100">
              <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
              </svg>
              {modLabel(mod)}
            </span>
          {/each}
        </div>
      </div>
    {/if}

    <!-- ── Cambiar contraseña ────────────────────────────── -->
    <div class="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-sm font-semibold text-gray-500 uppercase tracking-wider">Seguridad</h3>
        {#if !changingPassword}
          <button
            onclick={() => changingPassword = true}
            class="text-sm text-blue-600 hover:text-blue-700 font-medium transition-colors"
          >
            Cambiar contraseña
          </button>
        {/if}
      </div>

      {#if pwSuccess}
        <p class="text-sm text-green-600 flex items-center gap-1.5">
          <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/></svg>
          Contraseña actualizada correctamente
        </p>
      {/if}

      {#if !changingPassword && !pwSuccess}
        <p class="text-sm text-gray-500">••••••••••••</p>
      {/if}

      {#if changingPassword}
        <div class="space-y-4">
          <!-- Contraseña actual -->
          <div>
            <label class="block text-xs font-medium text-gray-500 mb-1">Contraseña actual</label>
            <div class="relative">
              <input
                type={showPwCurrent ? 'text' : 'password'}
                bind:value={pwCurrent}
                placeholder="Contraseña actual"
                class="w-full px-3 py-2 pr-10 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button type="button" onclick={() => showPwCurrent = !showPwCurrent}
                class="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                {#if showPwCurrent}
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"/></svg>
                {:else}
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
                {/if}
              </button>
            </div>
          </div>

          <!-- Nueva contraseña -->
          <div>
            <label class="block text-xs font-medium text-gray-500 mb-1">Nueva contraseña</label>
            <div class="relative">
              <input
                type={showPwNew ? 'text' : 'password'}
                bind:value={pwNew}
                placeholder="Mínimo 8 caracteres"
                class="w-full px-3 py-2 pr-10 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button type="button" onclick={() => showPwNew = !showPwNew}
                class="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                {#if showPwNew}
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"/></svg>
                {:else}
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
                {/if}
              </button>
            </div>
            <!-- Barra de fortaleza -->
            {#if pwNew}
              {@const strength = pwNew.length >= 12 && /[A-Z]/.test(pwNew) && /[0-9]/.test(pwNew) && /[^A-Za-z0-9]/.test(pwNew) ? 3 : pwNew.length >= 8 && (/[A-Z]/.test(pwNew) || /[0-9]/.test(pwNew)) ? 2 : 1}
              <div class="mt-1.5 flex gap-1">
                <div class="h-1 flex-1 rounded-full {strength >= 1 ? 'bg-red-400' : 'bg-gray-200'}"></div>
                <div class="h-1 flex-1 rounded-full {strength >= 2 ? 'bg-yellow-400' : 'bg-gray-200'}"></div>
                <div class="h-1 flex-1 rounded-full {strength >= 3 ? 'bg-green-500' : 'bg-gray-200'}"></div>
              </div>
              <p class="text-xs mt-0.5 {strength === 1 ? 'text-red-500' : strength === 2 ? 'text-yellow-600' : 'text-green-600'}">
                {strength === 1 ? 'Débil' : strength === 2 ? 'Aceptable' : 'Fuerte'}
              </p>
            {/if}
          </div>

          <!-- Confirmar -->
          <div>
            <label class="block text-xs font-medium text-gray-500 mb-1">Confirmar nueva contraseña</label>
            <div class="relative">
              <input
                type={showPwConfirm ? 'text' : 'password'}
                bind:value={pwConfirm}
                placeholder="Repite la nueva contraseña"
                onkeydown={(e) => { if (e.key === 'Enter') savePassword(); if (e.key === 'Escape') cancelPassword(); }}
                class="w-full px-3 py-2 pr-10 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500
                  {pwConfirm && pwConfirm !== pwNew ? 'border-red-400' : pwConfirm && pwConfirm === pwNew ? 'border-green-400' : 'border-gray-300'}"
              />
              <button type="button" onclick={() => showPwConfirm = !showPwConfirm}
                class="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                {#if showPwConfirm}
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"/></svg>
                {:else}
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
                {/if}
              </button>
            </div>
            {#if pwConfirm && pwConfirm !== pwNew}
              <p class="text-xs text-red-500 mt-0.5">Las contraseñas no coinciden</p>
            {/if}
          </div>

          {#if pwError}
            <p class="text-sm text-red-500 flex items-center gap-1.5">
              <svg class="w-4 h-4 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/></svg>
              {pwError}
            </p>
          {/if}

          <div class="flex gap-2 pt-1">
            <button
              onclick={savePassword}
              disabled={pwSaving}
              class="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {pwSaving ? 'Guardando…' : 'Cambiar contraseña'}
            </button>
            <button
              onclick={cancelPassword}
              class="px-4 py-2 text-gray-600 hover:text-gray-800 rounded-lg text-sm transition-colors"
            >
              Cancelar
            </button>
          </div>
        </div>
      {/if}
    </div>

    <!-- ── Cerrar sesión ───────────────────────────────────── -->
    <div class="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
      <h3 class="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4">Sesión</h3>
      <button
        onclick={() => { authStore.logout(); navigate('/'); }}
        class="flex items-center gap-2 px-4 py-2.5 rounded-lg border border-red-200 text-sm text-red-600 hover:bg-red-50 transition-colors"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
        </svg>
        Cerrar sesión
      </button>
    </div>

  </div>
</div>
