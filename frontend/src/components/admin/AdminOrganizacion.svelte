<script lang="ts">
  import { onMount } from 'svelte';
  import { authStore } from '../../stores/auth';

  interface OrganizationData {
    id?: number;
    razon_social: string;
    nombre_comercial: string;
    rfc: string;
    regimen_fiscal: string;
    logo_url?: string | null;
    color_primario?: string | null;
    color_secundario?: string | null;
    calle: string;
    numero_exterior: string;
    numero_interior?: string;
    colonia: string;
    ciudad: string;
    estado: string;
    codigo_postal: string;
    pais: string;
    telefono: string;
    email: string;
    sitio_web?: string;
  }

  let organization = $state<OrganizationData>({
    razon_social: '',
    nombre_comercial: '',
    rfc: '',
    regimen_fiscal: '',
    calle: '',
    numero_exterior: '',
    numero_interior: '',
    colonia: '',
    ciudad: '',
    estado: '',
    codigo_postal: '',
    pais: 'México',
    telefono: '',
    email: '',
    sitio_web: '',
    color_primario: '#1E40AF',
    color_secundario: '#3B82F6',
  });

  let loading = $state(true);
  let saving = $state(false);
  let errorMessage = $state('');
  let successMessage = $state('');
  let hasOrganization = $state(false);
  let logoFile = $state<File | null>(null);
  let logoPreview = $state<string | null>(null);

  const REGIMENES_FISCALES = [
    { value: '601', label: '601 - General de Ley Personas Morales' },
    { value: '603', label: '603 - Personas Morales con Fines no Lucrativos' },
    { value: '605', label: '605 - Sueldos y Salarios e Ingresos Asimilados a Salarios' },
    { value: '606', label: '606 - Arrendamiento' },
    { value: '607', label: '607 - Régimen de Enajenación o Adquisición de Bienes' },
    { value: '608', label: '608 - Demás ingresos' },
    { value: '610', label: '610 - Residentes en el Extranjero sin Establecimiento Permanente en México' },
    { value: '611', label: '611 - Ingresos por Dividendos (socios y accionistas)' },
    { value: '612', label: '612 - Personas Físicas con Actividades Empresariales y Profesionales' },
    { value: '614', label: '614 - Ingresos por intereses' },
    { value: '615', label: '615 - Régimen de los ingresos por obtención de premios' },
    { value: '616', label: '616 - Sin obligaciones fiscales' },
    { value: '620', label: '620 - Sociedades Cooperativas de Producción que optan por diferir sus ingresos' },
    { value: '621', label: '621 - Incorporación Fiscal' },
    { value: '622', label: '622 - Actividades Agrícolas, Ganaderas, Silvícolas y Pesqueras' },
    { value: '623', label: '623 - Opcional para Grupos de Sociedades' },
    { value: '624', label: '624 - Coordinados' },
    { value: '625', label: '625 - Régimen de las Actividades Empresariales con ingresos a través de Plataformas Tecnológicas' },
    { value: '626', label: '626 - Régimen Simplificado de Confianza' },
  ];

  const ESTADOS = [
    'Aguascalientes', 'Baja California', 'Baja California Sur', 'Campeche', 'Chiapas', 'Chihuahua',
    'Ciudad de México', 'Coahuila', 'Colima', 'Durango', 'Estado de México', 'Guanajuato',
    'Guerrero', 'Hidalgo', 'Jalisco', 'Michoacán', 'Morelos', 'Nayarit', 'Nuevo León', 'Oaxaca',
    'Puebla', 'Querétaro', 'Quintana Roo', 'San Luis Potosí', 'Sinaloa', 'Sonora', 'Tabasco',
    'Tamaulipas', 'Tlaxcala', 'Veracruz', 'Yucatán', 'Zacatecas'
  ];

  onMount(() => {
    loadOrganization();
  });

  async function loadOrganization() {
    try {
      loading = true;
      errorMessage = '';
      const response = await authStore.fetch(
        `${import.meta.env.VITE_API_BASE_URL}/api/v1/admin/organization/me`,
        { headers: { Authorization: `Bearer ${$authStore.accessToken}` } }
      );
      
      if (response.ok) {
        const data = await response.json();
        organization = { ...organization, ...data };
        hasOrganization = true;
        logoPreview = data.logo_url;
      } else if (response.status === 404) {
        // No existe organización aún
        hasOrganization = false;
      } else {
        throw new Error('Error al cargar la información de la organización');
      }
    } catch (error: any) {
      console.error('Error al cargar organización:', error);
      errorMessage = error.message || 'Error al cargar la información';
    } finally {
      loading = false;
    }
  }

  function handleLogoChange(event: Event) {
    const target = event.target as HTMLInputElement;
    const file = target.files?.[0];
    if (!file) return;

    // Validar tipo de archivo
    if (!file.type.startsWith('image/')) {
      errorMessage = 'Por favor selecciona un archivo de imagen válido';
      return;
    }

    // Validar tamaño (max 2MB)
    if (file.size > 2 * 1024 * 1024) {
      errorMessage = 'El tamaño del logo no debe exceder 2MB';
      return;
    }

    logoFile = file;
    
    // Crear preview
    const reader = new FileReader();
    reader.onload = (e) => {
      logoPreview = e.target?.result as string;
    };
    reader.readAsDataURL(file);
  }

  function validateRFC(rfc: string): boolean {
    const rfcRegex = /^[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}$/;
    return rfcRegex.test(rfc.toUpperCase());
  }

  function validateEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }

  function validateColor(color: string): boolean {
    const hexRegex = /^#[0-9A-Fa-f]{6}$/;
    return hexRegex.test(color);
  }

  async function handleSubmit(e: Event) {
    e.preventDefault();
    
    // Validaciones
    if (!organization.razon_social.trim()) {
      errorMessage = 'La razón social es requerida';
      return;
    }
    if (!organization.rfc.trim()) {
      errorMessage = 'El RFC es requerido';
      return;
    }
    if (!validateRFC(organization.rfc)) {
      errorMessage = 'El RFC no tiene un formato válido';
      return;
    }
    if (!organization.email.trim() || !validateEmail(organization.email)) {
      errorMessage = 'El email no es válido';
      return;
    }
    if (organization.color_primario && !validateColor(organization.color_primario)) {
      errorMessage = 'El color primario debe ser un código hexadecimal válido (ej: #1E40AF)';
      return;
    }
    if (organization.color_secundario && !validateColor(organization.color_secundario)) {
      errorMessage = 'El color secundario debe ser un código hexadecimal válido';
      return;
    }

    try {
      saving = true;
      errorMessage = '';
      successMessage = '';

      // Crear FormData si hay logo
      let body: any = {
        razon_social: organization.razon_social,
        nombre_comercial: organization.nombre_comercial,
        rfc: organization.rfc.toUpperCase(),
        regimen_fiscal: organization.regimen_fiscal,
        color_primario: organization.color_primario,
        color_secundario: organization.color_secundario,
        calle: organization.calle,
        numero_exterior: organization.numero_exterior,
        numero_interior: organization.numero_interior || null,
        colonia: organization.colonia,
        ciudad: organization.ciudad,
        estado: organization.estado,
        codigo_postal: organization.codigo_postal,
        pais: organization.pais,
        telefono: organization.telefono,
        email: organization.email,
        sitio_web: organization.sitio_web || null,
      };

      const method = hasOrganization ? 'PUT' : 'POST';
      const response = await authStore.fetch(
        `${import.meta.env.VITE_API_BASE_URL}/api/v1/admin/organization/me`,
        {
          method,
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${$authStore.accessToken}`,
          },
          body: JSON.stringify(body),
        }
      );

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Error al guardar la información');
      }

      const data = await response.json();
      organization = { ...organization, ...data };
      hasOrganization = true;

      // Si hay logo, subirlo
      if (logoFile) {
        await uploadLogo();
      }

      successMessage = 'Información guardada exitosamente';
      setTimeout(() => {
        successMessage = '';
      }, 3000);
    } catch (error: any) {
      console.error('Error al guardar:', error);
      errorMessage = error.message || 'Error al guardar la información';
    } finally {
      saving = false;
    }
  }

  async function uploadLogo() {
    if (!logoFile) return;

    try {
      const formData = new FormData();
      formData.append('logo', logoFile);

      const response = await authStore.fetch(
        `${import.meta.env.VITE_API_BASE_URL}/api/v1/admin/organization/me/logo`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${$authStore.accessToken}`,
          },
          body: formData,
        }
      );

      if (!response.ok) {
        throw new Error('Error al subir el logo');
      }

      const data = await response.json();
      organization.logo_url = data.logo_url;
      logoPreview = data.logo_url;
      logoFile = null;
    } catch (error: any) {
      console.error('Error al subir logo:', error);
      errorMessage = error.message || 'Error al subir el logo';
    }
  }
</script>

<div class="p-6">
  <!-- Mensajes de error/éxito -->
  {#if errorMessage}
    <div class="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-center justify-between">
      <span class="text-sm">{errorMessage}</span>
      <button onclick={() => errorMessage = ''} class="text-red-500 hover:text-red-700 ml-3">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
        </svg>
      </button>
    </div>
  {/if}
  {#if successMessage}
    <div class="mb-4 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg flex items-center justify-between">
      <span class="text-sm">{successMessage}</span>
      <button onclick={() => successMessage = ''} class="text-green-500 hover:text-green-700 ml-3">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
        </svg>
      </button>
    </div>
  {/if}

  <!-- Header -->
  <div class="mb-6">
    <h1 class="text-2xl font-bold text-gray-900">Mi Organización</h1>
    <p class="text-gray-600 mt-1">Configura la información fiscal y de marca de tu organización</p>
  </div>

  {#if loading}
    <div class="flex justify-center items-center py-12">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>
  {:else}
    <form onsubmit={handleSubmit} class="bg-white rounded-lg shadow-sm">
      <!-- Logo y Branding -->
      <div class="p-6 border-b border-gray-200">
        <h2 class="text-lg font-semibold text-gray-900 mb-4">Logo y Branding</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Logo de la Empresa</label>
            {#if logoPreview}
              <div class="mb-3">
                <img src={logoPreview} alt="Logo preview" class="h-24 object-contain border rounded p-2" />
              </div>
            {/if}
            <input
              type="file"
              accept="image/*"
              onchange={handleLogoChange}
              class="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            />
            <p class="text-xs text-gray-500 mt-1">PNG, JPG o SVG. Máximo 2MB.</p>
          </div>
          <div class="space-y-4">
            <div>
              <label for="color_primario" class="block text-sm font-medium text-gray-700 mb-1">Color Primario</label>
              <div class="flex gap-2 items-center">
                <input
                  type="color"
                  id="color_primario"
                  bind:value={organization.color_primario}
                  class="h-10 w-20 rounded border border-gray-300"
                />
                <input
                  type="text"
                  bind:value={organization.color_primario}
                  placeholder="#1E40AF"
                  class="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
            <div>
              <label for="color_secundario" class="block text-sm font-medium text-gray-700 mb-1">Color Secundario</label>
              <div class="flex gap-2 items-center">
                <input
                  type="color"
                  id="color_secundario"
                  bind:value={organization.color_secundario}
                  class="h-10 w-20 rounded border border-gray-300"
                />
                <input
                  type="text"
                  bind:value={organization.color_secundario}
                  placeholder="#3B82F6"
                  class="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Información Fiscal -->
      <div class="p-6 border-b border-gray-200">
        <h2 class="text-lg font-semibold text-gray-900 mb-4">Información Fiscal</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label for="razon_social" class="block text-sm font-medium text-gray-700 mb-1">Razón Social *</label>
            <input
              type="text"
              id="razon_social"
              bind:value={organization.razon_social}
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <div>
            <label for="nombre_comercial" class="block text-sm font-medium text-gray-700 mb-1">Nombre Comercial</label>
            <input
              type="text"
              id="nombre_comercial"
              bind:value={organization.nombre_comercial}
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <div>
            <label for="rfc" class="block text-sm font-medium text-gray-700 mb-1">RFC *</label>
            <input
              type="text"
              id="rfc"
              bind:value={organization.rfc}
              required
              maxlength="13"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent uppercase"
              style="text-transform: uppercase;"
            />
          </div>
          <div>
            <label for="regimen_fiscal" class="block text-sm font-medium text-gray-700 mb-1">Régimen Fiscal *</label>
            <select
              id="regimen_fiscal"
              bind:value={organization.regimen_fiscal}
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">Selecciona un régimen</option>
              {#each REGIMENES_FISCALES as regimen}
                <option value={regimen.value}>{regimen.label}</option>
              {/each}
            </select>
          </div>
        </div>
      </div>

      <!-- Dirección -->
      <div class="p-6 border-b border-gray-200">
        <h2 class="text-lg font-semibold text-gray-900 mb-4">Dirección</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="md:col-span-2">
            <label for="calle" class="block text-sm font-medium text-gray-700 mb-1">Calle *</label>
            <input
              type="text"
              id="calle"
              bind:value={organization.calle}
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <div>
            <label for="numero_exterior" class="block text-sm font-medium text-gray-700 mb-1">Número Exterior *</label>
            <input
              type="text"
              id="numero_exterior"
              bind:value={organization.numero_exterior}
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <div>
            <label for="numero_interior" class="block text-sm font-medium text-gray-700 mb-1">Número Interior</label>
            <input
              type="text"
              id="numero_interior"
              bind:value={organization.numero_interior}
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <div>
            <label for="colonia" class="block text-sm font-medium text-gray-700 mb-1">Colonia *</label>
            <input
              type="text"
              id="colonia"
              bind:value={organization.colonia}
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <div>
            <label for="ciudad" class="block text-sm font-medium text-gray-700 mb-1">Ciudad *</label>
            <input
              type="text"
              id="ciudad"
              bind:value={organization.ciudad}
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <div>
            <label for="estado" class="block text-sm font-medium text-gray-700 mb-1">Estado *</label>
            <select
              id="estado"
              bind:value={organization.estado}
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">Selecciona un estado</option>
              {#each ESTADOS as estado}
                <option value={estado}>{estado}</option>
              {/each}
            </select>
          </div>
          <div>
            <label for="codigo_postal" class="block text-sm font-medium text-gray-700 mb-1">Código Postal *</label>
            <input
              type="text"
              id="codigo_postal"
              bind:value={organization.codigo_postal}
              required
              maxlength="5"
              pattern="[0-9]{5}"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <div>
            <label for="pais" class="block text-sm font-medium text-gray-700 mb-1">País *</label>
            <input
              type="text"
              id="pais"
              bind:value={organization.pais}
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-gray-50"
              readonly
            />
          </div>
        </div>
      </div>

      <!-- Contacto -->
      <div class="p-6 border-b border-gray-200">
        <h2 class="text-lg font-semibold text-gray-900 mb-4">Información de Contacto</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label for="telefono" class="block text-sm font-medium text-gray-700 mb-1">Teléfono *</label>
            <input
              type="tel"
              id="telefono"
              bind:value={organization.telefono}
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <div>
            <label for="email" class="block text-sm font-medium text-gray-700 mb-1">Email *</label>
            <input
              type="email"
              id="email"
              bind:value={organization.email}
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <div class="md:col-span-2">
            <label for="sitio_web" class="block text-sm font-medium text-gray-700 mb-1">Sitio Web</label>
            <input
              type="url"
              id="sitio_web"
              bind:value={organization.sitio_web}
              placeholder="https://www.ejemplo.com"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>
      </div>

      <!-- Botones de acción -->
      <div class="p-6 bg-gray-50 flex justify-end gap-3">
        <button
          type="submit"
          disabled={saving}
          class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {#if saving}
            <svg class="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Guardando...
          {:else}
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
            Guardar Cambios
          {/if}
        </button>
      </div>
    </form>
  {/if}
</div>
