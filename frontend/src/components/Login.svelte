<script lang="ts">
  import { authStore } from '../stores/auth';
  import { navigate } from '../lib/router';

  let email = $state('')
  let password = $state('')
  let rememberMe = $state(false)
  let showPassword = $state(false)
  let loading = $state(false)
  let error = $state('')
  let emailTouched = $state(false)
  let passwordTouched = $state(false)

  // RFC 5322-compatible: allows user+tag@domain.tld, dots, hyphens, etc.
  function isValidEmail(val: string): boolean {
    return /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+$/.test(val.trim());
  }

  const emailError = $derived(
    emailTouched && email.trim().length > 0 && !isValidEmail(email)
      ? 'Ingresa un correo electrónico válido'
      : emailTouched && email.trim().length === 0
        ? 'El correo es obligatorio'
        : ''
  );

  const passwordError = $derived(
    passwordTouched && password.length === 0
      ? 'La contraseña es obligatoria'
      : passwordTouched && password !== password.trim()
        ? 'La contraseña no debe tener espacios al inicio o al final'
        : ''
  );

  const formValid = $derived(
    isValidEmail(email) && password.trim().length > 0
  );

  async function handleLogin() {
    emailTouched = true;
    passwordTouched = true;
    if (!formValid) return;

    loading = true
    error = ''
    
    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/auth/login`, {
        method: 'POST',
        mode: 'cors',
        credentials: 'omit',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: email.trim(),
          password: password.trim()
        })
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Error al iniciar sesión')
      }

      // Obtener perfil del usuario con el token
      const profileResponse = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/auth/me`, {
        headers: {
          'Authorization': `Bearer ${data.access_token}`
        }
      });

      if (!profileResponse.ok) {
        throw new Error('Error al obtener perfil del usuario');
      }

      const userProfile = await profileResponse.json();

      // Convertir permissions de objeto a array plano
      // Backend envía: { "module": ["action1", "action2"] }
      // Frontend necesita: ["module.action1", "module.action2"]
      let permissionsArray: string[] = [];
      if (userProfile.permissions && typeof userProfile.permissions === 'object') {
        Object.entries(userProfile.permissions).forEach(([module, actions]) => {
          if (Array.isArray(actions)) {
            actions.forEach((action: string) => {
              permissionsArray.push(`${module}.${action}`);
            });
          }
        });
      }

      const user = {
        id: userProfile.id,
        email: userProfile.email,
        fullName: userProfile.full_name,
        tenantId: userProfile.tenant_id,
        isSuperadmin: userProfile.is_superadmin,
        photoUrl: userProfile.photo_url ?? null,
        permissions: permissionsArray,
        securityModules: userProfile.security_modules ?? [],
        securityLevelId: userProfile.security_level_id ?? null,
        securityLevelName: userProfile.security_level_name ?? null
      };

      // Login en el store
      authStore.login(data.access_token, data.refresh_token, user);
      
      if (rememberMe) {
        localStorage.setItem('remember_email', email.trim())
      } else {
        localStorage.removeItem('remember_email')
      }

      // Redirigir al dashboard
      navigate('/dashboard');
      
    } catch (err: any) {
      error = err.message || 'Error al conectar con el servidor'
      console.error('Login error:', err)
    } finally {
      loading = false
    }
  }

  // Cargar email recordado si existe
  $effect(() => {
    const rememberedEmail = localStorage.getItem('remember_email')
    if (rememberedEmail) {
      email = rememberedEmail
      rememberMe = true
    }
  })
</script>

<div class="min-h-screen flex">
  <!-- Left Panel - Dark with Background Image -->
  <div class="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-slate-900 via-blue-900 to-slate-800 relative overflow-hidden">
    <!-- Background Image Overlay -->
    <div class="absolute inset-0 opacity-20">
      <img 
        src="https://images.unsplash.com/photo-1473341304170-971dccb5ac1e?q=80&w=2070" 
        alt="Industrial Energy" 
        class="w-full h-full object-cover"
      />
    </div>
    
    <!-- Grid Pattern Overlay -->
    <div class="absolute inset-0 opacity-10">
      <svg class="w-full h-full" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <pattern id="grid" width="60" height="60" patternUnits="userSpaceOnUse">
            <path d="M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z" fill="white" fill-opacity="0.4"/>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)"/>
      </svg>
    </div>
    
    <!-- Content -->
    <div class="relative z-10 flex flex-col justify-between p-12 text-white">
      <!-- Logo -->
      <div class="flex items-center space-x-3">
        <div class="w-12 h-12 bg-blue-500 rounded-lg flex items-center justify-center">
          <svg class="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </div>
        <div>
          <div class="text-xl font-bold">CÓDIGO DE RED</div>
          <div class="text-xs text-blue-300 uppercase tracking-wider">Gestión Energética</div>
        </div>
      </div>
      
      <!-- Main Content -->
      <div class="space-y-6">
        <h1 class="text-5xl font-bold leading-tight">
          Control de Calidad<br />
          Energética Industrial
        </h1>
        <p class="text-lg text-blue-100 max-w-md leading-relaxed">
          Monitoree y optimice la eficiencia energética de su empresa. 
          Gestione el consumo eléctrico y asegure la calidad de la red en tiempo real.
        </p>
        <div class="flex items-center space-x-4 text-sm">
          <div class="flex items-center space-x-2">
            <svg class="w-5 h-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
            </svg>
            <span>Monitoreo en tiempo real</span>
          </div>
          <div class="flex items-center space-x-2">
            <svg class="w-5 h-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
            </svg>
            <span>Optimización energética</span>
          </div>
          <div class="flex items-center space-x-2">
            <svg class="w-5 h-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
            </svg>
            <span>Calidad de red eléctrica</span>
          </div>
        </div>
      </div>
      
      <!-- Footer -->
      <div class="text-sm text-blue-200">
        CÓDIGO DE RED ENERGY MANAGEMENT<br />
        <span class="text-xs text-blue-300">v1.0.0 • 2026</span>
      </div>
    </div>
  </div>

  <!-- Right Panel - Login Form -->
  <div class="flex-1 flex items-center justify-center p-8 bg-white">
    <div class="w-full max-w-md">
      <!-- Mobile Logo -->
      <div class="lg:hidden mb-8 text-center">
        <div class="inline-flex items-center space-x-3">
          <div class="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
            <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <div class="text-left">
            <div class="text-lg font-bold text-gray-900">CÓDIGO DE RED</div>
            <div class="text-xs text-blue-600 uppercase tracking-wider">Gestión Energética</div>
          </div>
        </div>
      </div>

      <!-- Welcome Text -->
      <div class="mb-8">
        <h2 class="text-3xl font-bold text-gray-900 mb-2">Bienvenido</h2>
        <p class="text-gray-600">Ingrese a su cuenta corporativa</p>
      </div>

      <!-- Login Form -->
      <form onsubmit={(e) => { e.preventDefault(); handleLogin(); }} class="space-y-6">
        <!-- Error Message -->
        {#if error}
          <div class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
            {error}
          </div>
        {/if}

        <!-- Email Field -->
        <div>
          <label for="email" class="block text-sm font-medium text-gray-700 mb-2">
            Correo Electrónico
          </label>
          <div class="relative">
            <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg class="h-5 w-5 {emailTouched && emailError ? 'text-red-400' : 'text-gray-400'}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
            <input
              type="text"
              id="email"
              bind:value={email}
              oninput={() => emailTouched = true}
              onblur={() => emailTouched = true}
              autocomplete="email"
              inputmode="email"
              placeholder="usuario+etiqueta@empresa.com"
              class="block w-full pl-10 pr-10 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition
                {emailTouched && emailError
                  ? 'border-red-400 bg-red-50 focus:ring-red-400 focus:border-red-400'
                  : emailTouched && !emailError && email.trim()
                    ? 'border-green-400 bg-green-50'
                    : 'border-gray-300'}"
            />
            {#if emailTouched && !emailError && email.trim()}
              <div class="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                <svg class="h-4 w-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"/>
                </svg>
              </div>
            {/if}
          </div>
          {#if emailError}
            <p class="mt-1.5 text-xs text-red-600 flex items-center gap-1">
              <svg class="w-3.5 h-3.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
              {emailError}
            </p>
          {/if}
        </div>

        <!-- Password Field -->
        <div>
          <label for="password" class="block text-sm font-medium text-gray-700 mb-2">
            Contraseña
          </label>
          <div class="relative">
            <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg class="h-5 w-5 {passwordTouched && passwordError ? 'text-red-400' : 'text-gray-400'}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <input
              type={showPassword ? 'text' : 'password'}
              id="password"
              bind:value={password}
              oninput={() => passwordTouched = true}
              onblur={() => passwordTouched = true}
              autocomplete="current-password"
              placeholder="••••••••"
              class="block w-full pl-10 pr-12 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition
                {passwordTouched && passwordError
                  ? 'border-red-400 bg-red-50 focus:ring-red-400 focus:border-red-400'
                  : 'border-gray-300'}"
            />
            <button
              type="button"
              onclick={() => showPassword = !showPassword}
              class="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600"
              tabindex="-1"
            >
              {#if showPassword}
                <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                </svg>
              {:else}
                <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
              {/if}
            </button>
          </div>
          {#if passwordError}
            <p class="mt-1.5 text-xs text-red-600 flex items-center gap-1">
              <svg class="w-3.5 h-3.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
              {passwordError}
            </p>
          {/if}
        </div>

        <!-- Remember Me -->
        <div class="flex items-center">
          <input
            type="checkbox"
            id="remember"
            bind:checked={rememberMe}
            class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
          <label for="remember" class="ml-2 block text-sm text-gray-700">
            Recordar en este equipo
          </label>
        </div>

        <!-- Submit Button -->
        <button
          type="submit"
          disabled={loading || !formValid}
          class="w-full text-white font-semibold py-3 px-4 rounded-lg transition-all duration-200 flex items-center justify-center
            {formValid && !loading
              ? 'bg-blue-600 hover:bg-blue-700 cursor-pointer'
              : 'bg-gray-300 text-gray-400 cursor-not-allowed'}"
        >
          {#if loading}
            <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Accediendo...
          {:else}
            Acceder al Portal
          {/if}
        </button>


      <!-- Footer -->
      <div class="mt-8 text-center text-xs text-gray-500">
        © 2026 Código de Red. Acceso exclusivo autorizado.
      </div>

    </div>
  </div>
</div>
