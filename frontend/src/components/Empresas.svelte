<script lang="ts">
  import { onMount } from 'svelte';
  import { fade, fly } from 'svelte/transition';
  import { authStore } from '../stores/auth';

  let accessToken = $state('');
  $effect(() => {
    accessToken = localStorage.getItem('access_token') || '';
  });

  interface Company {
    id: number;
    razon_social: string;
    nombre_comercial?: string;
    rfc: string;
    telefono?: string;
    email?: string;
    rpu: string;
    tipo_suministro: string;
    demanda_contratada_kw?: number;
    clasificacion?: string;
    is_active: boolean;
    created_at: string;
  }

  let companies = $state<Company[]>([]);
  let loading = $state(true);
  let showModal = $state(false);
  let modalMode = $state<'create' | 'edit'>('create');
  let selectedCompany = $state<Company | null>(null);
  let errorMessage = $state('');
  let validationErrors = $state<Record<string, string>>({});
  let successMessage = $state('');
  let showElectricalData = $state(false);
  
  // Auto-close alerts after 4 seconds
  $effect(() => {
    if (errorMessage) {
      const timer = setTimeout(() => errorMessage = '', 4000);
      return () => clearTimeout(timer);
    }
  });
  
  $effect(() => {
    if (successMessage) {
      const timer = setTimeout(() => successMessage = '', 4000);
      return () => clearTimeout(timer);
    }
  });
  
  // Estado para modal de documentos
  let showDocumentsModal = $state(false);
  let selectedCompanyForDocs = $state<Company | null>(null);
  let documents = $state<any[]>([]);
  let loadingDocuments = $state(false);
  let uploadingDocument = $state(false);
  let uploadProgress = $state(0);
  let showViewerModal = $state(false);

  // Estado para eliminar empresa
  let showDeleteModal = $state(false);
  let companyToDelete = $state<Company | null>(null);
  let deletingCompany = $state(false);
  let currentDocumentUrl = $state('');
  let currentDocumentName = $state('');
  let currentDocumentType = $state('');
  
  // Filtros
  let searchTerm = $state('');
  let filterTipo = $state<string | null>(null);
  let filterActive = $state<boolean>(true); // true = activas, false = inactivas

  // Paginación
  let currentPage = $state(1);
  let totalCompanies = $state(0);
  let pageSize = $state(10);

  // Form data
  let formData = $state({
    // Datos generales
    razon_social: '',
    nombre_comercial: '',
    rfc: '',
    
    // Contacto
    telefono: '',
    email: '',
    direccion: '',
    ciudad: '',
    estado: '',
    codigo_postal: '',
    
    // Datos eléctricos
    rpu: '',
    tipo_suministro: 'GDMTH',
    tension_suministro: '',
    demanda_contratada_kw: null as number | null,
    demanda_maxima_kw: null as number | null,
    factor_carga: null as number | null,
    factor_potencia: null as number | null,
    consumo_mensual_kwh: null as number | null,
    costo_mensual_aproximado: null as number | null,
    nombre_centro_carga: '',
    ubicacion_centro_carga: '',
    notas: '',
    is_active: true
  });

  // Cargar empresas cuando el token esté disponible
  let hasLoadedOnce = false;
  $effect(() => {
    if (accessToken && !hasLoadedOnce) {
      hasLoadedOnce = true;
      loadCompanies();
    }
  });

  async function loadCompanies() {
    loading = true;
    errorMessage = '';
    
    // Verificar que tenemos token antes de hacer la petición
    if (!accessToken) {
      errorMessage = 'No hay sesión activa';
      loading = false;
      return;
    }
    
    try {
      // Carga todas las empresas para filtrado client-side en tiempo real
      const params = new URLSearchParams({ page: '1', page_size: '500' });

      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/companies/?${params}`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Error ${response.status}: No se pudieron cargar las empresas`);
      }

      const data = await response.json();
      companies = data.companies;
      totalCompanies = data.total;
      
    } catch (err: any) {
      errorMessage = err.message || 'Error al conectar con el servidor';
      console.error('Error loading companies:', err);
    } finally {
      loading = false;
    }
  }

  function openCreateModal() {
    modalMode = 'create';
    validationErrors = {};
    selectedCompany = null;
    showElectricalData = false;
    modalTab = 'general';
    formData = {
      razon_social: '',
      nombre_comercial: '',
      rfc: '',
      telefono: '',
      email: '',
      direccion: '',
      ciudad: '',
      estado: '',
      codigo_postal: '',
      rpu: '',
      tipo_suministro: 'GDMTH',
      tension_suministro: '',
      demanda_contratada_kw: null,
      demanda_maxima_kw: null,
      factor_carga: null,
      factor_potencia: null,
      consumo_mensual_kwh: null,
      costo_mensual_aproximado: null,
      nombre_centro_carga: '',
      ubicacion_centro_carga: '',
      notas: '',
      is_active: true
    };
    showModal = true;
    // Focus en el primer campo del modal
    setTimeout(() => firstModalInput?.focus(), 100);
  }

  function confirmDeleteCompany(company: Company) {
    companyToDelete = company;
    showDeleteModal = true;
  }

  async function deleteCompany() {
    if (!companyToDelete) return;
    deletingCompany = true;
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(
        `${import.meta.env.VITE_API_BASE_URL}/api/v1/companies/${companyToDelete.id}/`,
        { method: 'DELETE', headers: { 'Authorization': `Bearer ${token}` } }
      );
      if (response.ok || response.status === 204) {
        showDeleteModal = false;
        companyToDelete = null;
        successMessage = `"${companyToDelete.razon_social}" desactivada correctamente`;
        setTimeout(() => successMessage = '', 3000);
        await loadCompanies();
      } else {
        const data = await response.json().catch(() => ({}));
        errorMessage = data.detail || 'Error al eliminar la empresa';
      }
    } catch (err: any) {
      errorMessage = err.message || 'Error al eliminar la empresa';
    } finally {
      deletingCompany = false;
    }
  }

  async function reactivateCompany(company: Company) {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(
        `${import.meta.env.VITE_API_BASE_URL}/api/v1/companies/${company.id}/`,
        {
          method: 'PUT',
          headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
          body: JSON.stringify({ is_active: true })
        }
      );
      if (response.ok) {
        successMessage = `"${company.razon_social}" reactivada correctamente`;
        setTimeout(() => successMessage = '', 3000);
        await loadCompanies();
      } else {
        const data = await response.json().catch(() => ({}));
        errorMessage = data.detail || 'Error al reactivar la empresa';
      }
    } catch (err: any) {
      errorMessage = err.message || 'Error al reactivar la empresa';
    }
  }

  function openEditModal(company: Company) {
    modalMode = 'edit';    validationErrors = {};    selectedCompany = company;
    // Cargar todos los datos de la empresa
    loadCompanyDetails(company.id);
  }

  async function loadCompanyDetails(id: number) {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/companies/${id}/`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      });

      if (!response.ok) throw new Error('Error al cargar empresa');

      const company = await response.json();
      formData = { ...company };
      modalTab = 'general';
      showModal = true;
    } catch (err: any) {
      errorMessage = err.message;
    }
  }

  async function handleSubmit() {
    errorMessage = '';
    successMessage = '';

    try {
      const url = modalMode === 'create' 
        ? `${import.meta.env.VITE_API_BASE_URL}/api/v1/companies`
        : `${import.meta.env.VITE_API_BASE_URL}/api/v1/companies/${selectedCompany?.id}`;
      
      const method = modalMode === 'create' ? 'POST' : 'PUT';

      // Limpiar datos: eliminar campos vacíos opcionales y convertir strings vacíos a null
      const cleanData: any = {};
      
      // Campos requeridos siempre
      cleanData.razon_social = formData.razon_social;
      cleanData.rfc = formData.rfc.toUpperCase();
      cleanData.is_active = formData.is_active;
      
      // RPU y tipo_suministro solo si la sección eléctrica está activa
      if (formData.rpu) cleanData.rpu = formData.rpu;
      if (formData.tipo_suministro) cleanData.tipo_suministro = formData.tipo_suministro;
      
      // Campos opcionales de texto - solo agregar si tienen valor
      if (formData.nombre_comercial) cleanData.nombre_comercial = formData.nombre_comercial;
      if (formData.telefono) cleanData.telefono = formData.telefono;
      if (formData.email) cleanData.email = formData.email;
      if (formData.direccion) cleanData.direccion = formData.direccion;
      if (formData.ciudad) cleanData.ciudad = formData.ciudad;
      if (formData.estado) cleanData.estado = formData.estado;
      if (formData.codigo_postal) cleanData.codigo_postal = formData.codigo_postal;
      if (formData.tension_suministro) cleanData.tension_suministro = formData.tension_suministro;
      if (formData.nombre_centro_carga) cleanData.nombre_centro_carga = formData.nombre_centro_carga;
      if (formData.ubicacion_centro_carga) cleanData.ubicacion_centro_carga = formData.ubicacion_centro_carga;
      if (formData.notas) cleanData.notas = formData.notas;
      
      // Campos numéricos - solo agregar si tienen valor y son mayores a 0
      if (formData.demanda_contratada_kw != null && formData.demanda_contratada_kw > 0) {
        cleanData.demanda_contratada_kw = formData.demanda_contratada_kw;
      }
      if (formData.demanda_maxima_kw != null && formData.demanda_maxima_kw > 0) {
        cleanData.demanda_maxima_kw = formData.demanda_maxima_kw;
      }
      if (formData.factor_carga != null && formData.factor_carga > 0) {
        cleanData.factor_carga = formData.factor_carga;
      }
      if (formData.factor_potencia != null && formData.factor_potencia > 0) {
        cleanData.factor_potencia = formData.factor_potencia;
      }
      if (formData.consumo_mensual_kwh != null && formData.consumo_mensual_kwh > 0) {
        cleanData.consumo_mensual_kwh = formData.consumo_mensual_kwh;
      }
      if (formData.costo_mensual_aproximado != null && formData.costo_mensual_aproximado > 0) {
        cleanData.costo_mensual_aproximado = formData.costo_mensual_aproximado;
      }

      const response = await fetch(url, {
        method,
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(cleanData)
      });

      const data = await response.json();

      if (!response.ok) {
        if (response.status === 422 && Array.isArray(data.detail)) {
          // Errores de validación de Pydantic
          validationErrors = {};
          const errorMessages: string[] = [];
          data.detail.forEach((error: any) => {
            const field = error.loc[error.loc.length - 1]; // Último elemento de loc es el nombre del campo
            const message = error.msg;
            validationErrors[field] = message;
            errorMessages.push(`${field}: ${message}`);
          });
          throw new Error('Errores de validación:\n' + errorMessages.join('\n'));
        }
        throw new Error(data.detail || 'Error al guardar empresa');
      }

      successMessage = modalMode === 'create' 
        ? 'Empresa creada exitosamente'
        : 'Empresa actualizada exitosamente';
      
      showModal = false;
      await loadCompanies();
      
      setTimeout(() => {
        successMessage = '';
      }, 3000);

    } catch (err: any) {
      errorMessage = err.message || 'Error al guardar empresa';
      // Auto-cerrar mensaje de error después de 5 segundos
      setTimeout(() => {
        errorMessage = '';
        validationErrors = {};
      }, 5000);
    }
  }

  // Filtrado en tiempo real via $derived — handleSearch ya no es necesario
  function handleSearch() { /* no-op: filtrado client-side */ }

  function handlePageChange(newPage: number) {
    currentPage = newPage;
    loadCompanies();
  }

  async function openDocumentsModal(company: Company) {
    selectedCompanyForDocs = company;
    showDocumentsModal = true;
    await loadDocuments(company.id);
  }

  async function loadDocuments(companyId: number) {
    loadingDocuments = true;
    const token = localStorage.getItem('access_token');

    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/documents/${companyId}/documents/`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        documents = data.documents;
      }
    } catch (err) {
      console.error('Error al cargar documentos:', err);
    } finally {
      loadingDocuments = false;
    }
  }

  async function uploadDocument(event: Event) {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file || !selectedCompanyForDocs) return;

    const tipoDocumento = (document.getElementById('tipo_documento') as HTMLSelectElement)?.value;
    const descripcion = (document.getElementById('descripcion_doc') as HTMLInputElement)?.value;

    if (!tipoDocumento) {
      errorMessage = 'Debe seleccionar el tipo de documento';
      return;
    }

    uploadingDocument = true;
    uploadProgress = 0;
    const token = localStorage.getItem('access_token');

    const formData = new FormData();
    formData.append('file', file);
    formData.append('tipo_documento', tipoDocumento);
    if (descripcion) formData.append('descripcion', descripcion);

    try {
      // Simular progreso
      const progressInterval = setInterval(() => {
        if (uploadProgress < 90) {
          uploadProgress += 10;
        }
      }, 200);

      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/documents/${selectedCompanyForDocs.id}/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      clearInterval(progressInterval);
      uploadProgress = 100;

      if (response.ok) {
        successMessage = 'Documento subido exitosamente';
        setTimeout(() => {
          successMessage = '';
          uploadProgress = 0;
        }, 3000);
        await loadDocuments(selectedCompanyForDocs.id);
        // Limpiar formulario
        input.value = '';
        (document.getElementById('tipo_documento') as HTMLSelectElement).value = '';
        (document.getElementById('descripcion_doc') as HTMLInputElement).value = '';
      } else {
        const data = await response.json();
        errorMessage = data.detail || 'Error al subir documento';
        uploadProgress = 0;
      }
    } catch (err: any) {
      errorMessage = err.message || 'Error al subir documento';
      uploadProgress = 0;
    } finally {
      uploadingDocument = false;
    }
  }

  async function viewDocument(documentId: number) {
    if (!selectedCompanyForDocs) return;

    const token = localStorage.getItem('access_token');

    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/documents/${selectedCompanyForDocs.id}/documents/${documentId}/download`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        currentDocumentUrl = data.url;
        currentDocumentName = data.nombre_original;
        currentDocumentType = data.mime_type;
        showViewerModal = true;
      }
    } catch (err) {
      console.error('Error al cargar documento:', err);
    }
  }

  async function downloadDocument(documentId: number) {
    if (!selectedCompanyForDocs) return;

    const token = localStorage.getItem('access_token');

    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/documents/${selectedCompanyForDocs.id}/documents/${documentId}/download`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        window.open(data.url, '_blank');
      }
    } catch (err) {
      console.error('Error al descargar documento:', err);
    }
  }

  async function deleteDocument(documentId: number) {
    if (!selectedCompanyForDocs || !confirm('¿Está seguro de eliminar este documento?')) return;

    const token = localStorage.getItem('access_token');

    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/documents/${selectedCompanyForDocs.id}/documents/${documentId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        successMessage = 'Documento eliminado exitosamente';
        setTimeout(() => successMessage = '', 3000);
        await loadDocuments(selectedCompanyForDocs.id);
      }
    } catch (err) {
      console.error('Error al eliminar documento:', err);
    }
  }

  function formatDate(dateString: string) {
    return new Date(dateString).toLocaleDateString('es-MX', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  }

  function getCumplimientoColor(value: number) {
    if (value >= 90) return 'text-green-600';
    if (value >= 70) return 'text-yellow-600';
    return 'text-red-600';
  }

  // Normaliza texto eliminando acentos para búsqueda insensible
  function normalizeStr(s: string): string {
    return (s ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  }

  // Pestaña activa del modal
  let modalTab = $state<'general' | 'contacto' | 'electrico'>('general');

  // Filtrado client-side (tiempo real + insensible a acentos)
  const filteredCompanies = $derived.by(() => {
    const term = normalizeStr(searchTerm);
    return companies.filter(c => {
      const matchesSearch = !term ||
        normalizeStr(c.razon_social).includes(term) ||
        normalizeStr(c.rfc).includes(term) ||
        normalizeStr(c.rpu ?? '').includes(term) ||
        normalizeStr(c.nombre_comercial ?? '').includes(term);
      const matchesTipo = !filterTipo || c.tipo_suministro === filterTipo;
      const matchesActive = c.is_active === filterActive;
      return matchesSearch && matchesTipo && matchesActive;
    });
  });

  const totalActivas = $derived(companies.filter(c => c.is_active).length);
  const totalInactivas = $derived(companies.filter(c => !c.is_active).length);
  const totalFiltered = $derived(filteredCompanies.length);
  const totalPages = $derived(Math.ceil(totalFiltered / pageSize));
  const pagedCompanies = $derived(
    filteredCompanies.slice((currentPage - 1) * pageSize, currentPage * pageSize)
  );

  // Resetear página al cambiar filtros
  $effect(() => {
    searchTerm; filterTipo; filterActive;
    currentPage = 1;
  });

  // Referencias para focus
  let searchInput: HTMLInputElement;
  let firstModalInput: HTMLInputElement;

  // Keyboard shortcuts
  onMount(() => {
    // Focus en búsqueda al cargar
    setTimeout(() => searchInput?.focus(), 100);

    const handleKeyPress = (e: KeyboardEvent) => {
      // Ignorar si estamos en un input/textarea o modal abierto
      const target = e.target as HTMLElement;
      const isInInput = target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.tagName === 'SELECT';
      
      // ESC siempre cierra modales
      if (e.key === 'Escape') {
        if (showViewerModal) {
          showViewerModal = false;
        } else if (showDocumentsModal) {
          showDocumentsModal = false;
        } else if (showModal) {
          showModal = false;
        }
        return;
      }

      // Si estamos en un modal, no procesar otros atajos
      if (showModal || showDocumentsModal || showViewerModal) return;

      // Atajos solo cuando NO estamos en inputs
      if (!isInInput) {
        switch(e.key.toLowerCase()) {
          case 'n':
            e.preventDefault();
            openCreateModal();
            break;
          case 'b':
          case '/':
            e.preventDefault();
            searchInput?.focus();
            break;
          case 'r':
            e.preventDefault();
            loadCompanies();
            break;
        }
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  });
</script>

<div class="p-6">
  <!-- Header -->
  <div class="flex justify-between items-center mb-6">
    <div>
      <h1 class="text-3xl font-bold text-gray-900">Mis Empresas</h1>
      <p class="text-gray-600 mt-1">Registro y gestión del expediente electrónico</p>
    </div>
    <button
      onclick={openCreateModal}
      class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors shadow-sm"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
      </svg>
      <span>Nueva Empresa</span>
    </button>
  </div>

  <!-- Messages (Toast Notifications) -->
  {#if errorMessage}
    <div 
      transition:fly="{{ x: 300, duration: 300 }}"
      class="fixed top-4 right-4 z-[9999] bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg shadow-lg max-w-md"
    >
      <div class="flex items-start justify-between">
        <div class="flex items-center">
          <svg class="w-5 h-5 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>{errorMessage}</span>
        </div>
        <button onclick={() => errorMessage = ''} class="ml-4 flex-shrink-0 hover:text-red-900">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      <div class="mt-2 h-1 bg-red-200 rounded-full overflow-hidden">
        <div class="h-full bg-red-500 animate-[shrink_4s_linear]" style="animation: shrink 4s linear;"></div>
      </div>
    </div>
  {/if}

  {#if successMessage}
    <div 
      transition:fly="{{ x: 300, duration: 300 }}"
      class="fixed top-4 right-4 z-[9999] bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg shadow-lg max-w-md"
    >
      <div class="flex items-start justify-between">
        <div class="flex items-center">
          <svg class="w-5 h-5 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>{successMessage}</span>
        </div>
        <button onclick={() => successMessage = ''} class="ml-4 flex-shrink-0 hover:text-green-900">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      <div class="mt-2 h-1 bg-green-200 rounded-full overflow-hidden">
        <div class="h-full bg-green-500" style="animation: shrink 4s linear;"></div>
      </div>
    </div>
  {/if}

  <!-- Tabs activas / inactivas -->
  <div class="flex gap-1 mb-4 bg-white rounded-lg shadow p-1 w-fit">
    <button
      onclick={() => filterActive = true}
      class="px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2
        {filterActive ? 'bg-blue-600 text-white shadow-sm' : 'text-gray-600 hover:bg-gray-100'}"
    >
      <span class="w-2 h-2 rounded-full {filterActive ? 'bg-blue-200' : 'bg-green-400'}"></span>
      Activas
      <span class="{filterActive ? 'bg-blue-500 text-blue-100' : 'bg-gray-100 text-gray-600'} text-xs px-1.5 py-0.5 rounded-full font-semibold">{totalActivas}</span>
    </button>
    <button
      onclick={() => filterActive = false}
      class="px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2
        {!filterActive ? 'bg-gray-700 text-white shadow-sm' : 'text-gray-600 hover:bg-gray-100'}"
    >
      <span class="w-2 h-2 rounded-full {!filterActive ? 'bg-gray-400' : 'bg-gray-300'}"></span>
      Inactivas
      <span class="{!filterActive ? 'bg-gray-600 text-gray-200' : 'bg-gray-100 text-gray-600'} text-xs px-1.5 py-0.5 rounded-full font-semibold">{totalInactivas}</span>
    </button>
  </div>

  <!-- Search and Filters -->
  <div class="bg-white rounded-lg shadow p-4 mb-6">
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div class="md:col-span-2">
        <label class="block text-sm font-medium text-gray-700 mb-2">Buscar</label>
        <div class="relative">
          <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0"/>
          </svg>
          <input
            bind:this={searchInput}
            type="text"
            bind:value={searchTerm}
            placeholder="Razón social, RFC"
            tabindex="1"
            class="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
          {#if searchTerm}
            <button onclick={() => searchTerm = ''} class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          {/if}
        </div>
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">Tipo de Suministro</label>
        <select
          bind:value={filterTipo}
          tabindex="2"
          class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value={null}>Todos</option>
          <option value="GDMTH">GDMTH</option>
          <option value="GDMTO">GDMTO</option>
          <option value="GDBT">GDBT</option>
          <option value="DIST">DIST</option>
        </select>
      </div>
    </div>
  </div>

  {#if loading}
    <!-- Loading State -->
    <div class="bg-white rounded-lg shadow p-6">
      <div class="animate-pulse space-y-4">
        {#each Array(5) as _}
          <div class="h-16 bg-gray-200 rounded"></div>
        {/each}
      </div>
    </div>
  {:else if filteredCompanies.length === 0 && companies.length === 0}
    <!-- Empty State -->
    <div class="bg-white rounded-lg shadow p-12 text-center">
      <svg class="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
      </svg>
      <h3 class="text-lg font-medium text-gray-900 mb-2">No hay empresas registradas</h3>
      <p class="text-gray-600 mb-4">Comience registrando su primera empresa</p>
      <button
        onclick={openCreateModal}
        class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
      >
        Registrar Empresa
      </button>
    </div>
  {:else if filteredCompanies.length === 0}
    <!-- No results from filter -->
    <div class="bg-white rounded-lg shadow p-10 text-center">
      <svg class="w-12 h-12 mx-auto text-gray-300 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0"/>
      </svg>
      <p class="text-gray-500">Sin resultados para <strong>"{searchTerm}"</strong></p>
      <button onclick={() => { searchTerm = ''; filterTipo = null; }} class="mt-3 text-sm text-blue-600 hover:underline">Limpiar filtros</button>
    </div>
  {:else}
    <!-- Table - Desktop -->
    <div class="hidden md:block bg-white rounded-lg shadow overflow-hidden">
      <div class="overflow-x-auto">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Empresa</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">RFC</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">RPU</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tipo</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Demanda (kW)</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Clasificación</th>
            <th class="sticky right-0 z-10 bg-gray-50 px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider shadow-[-4px_0_6px_-1px_rgba(0,0,0,0.08)]">Acciones</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          {#each pagedCompanies as company}
            <tr class="group hover:bg-gray-50 transition-colors">
              <td class="px-6 py-4">
                <div class="text-sm font-medium text-gray-900">{company.razon_social}</div>
                {#if company.nombre_comercial}
                  <div class="text-sm text-gray-500">{company.nombre_comercial}</div>
                {/if}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{company.rfc}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{company.rpu}</td>
              <td class="px-6 py-4 whitespace-nowrap">
                <span class="px-2 py-1 text-xs font-semibold rounded bg-blue-100 text-blue-800">
                  {company.tipo_suministro}
                </span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600 text-right">
                {company.demanda_contratada_kw ? company.demanda_contratada_kw.toLocaleString() : '-'}
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                {#if company.clasificacion}
                  <span class="px-2 py-1 text-xs font-semibold rounded bg-green-100 text-green-800">
                    {company.clasificacion}
                  </span>
                {/if}
              </td>
              <td class="sticky right-0 z-10 bg-white group-hover:bg-gray-50 px-6 py-4 whitespace-nowrap text-sm shadow-[-4px_0_6px_-1px_rgba(0,0,0,0.08)] transition-colors">
                <div class="flex space-x-2">
                  <button
                    onclick={() => openDocumentsModal(company)}
                    class="text-yellow-600 hover:text-yellow-800"
                    title="Ver expediente digital"
                  >
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                    </svg>
                  </button>
                  <button
                    onclick={() => openEditModal(company)}
                    class="text-blue-600 hover:text-blue-800"
                    title="Editar empresa"
                  >
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </button>
                  {#if company.is_active}
                    <button
                      onclick={() => confirmDeleteCompany(company)}
                      class="text-red-500 hover:text-red-700"
                      title="Desactivar empresa"
                    >
                      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
                      </svg>
                    </button>
                  {:else}
                    <button
                      onclick={() => reactivateCompany(company)}
                      class="text-green-600 hover:text-green-800"
                      title="Reactivar empresa"
                    >
                      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </button>
                  {/if}
                </div>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
      </div>
    </div>

    <!-- Cards - Mobile -->
    <div class="md:hidden space-y-4">
      {#each pagedCompanies as company}
        <div class="bg-white rounded-lg shadow p-4">
          <div class="flex justify-between items-start mb-3">
            <div class="flex-1 min-w-0">
              <h3 class="text-sm font-semibold text-gray-900 truncate">{company.razon_social}</h3>
              {#if company.nombre_comercial}
                <p class="text-xs text-gray-500 truncate">{company.nombre_comercial}</p>
              {/if}
            </div>
            <span class="ml-2 px-2 py-1 text-xs font-semibold rounded bg-blue-100 text-blue-800 whitespace-nowrap">
              {company.tipo_suministro}
            </span>
          </div>
          
          <div class="space-y-2 text-xs text-gray-600 mb-3">
            <div class="flex justify-between">
              <span class="font-medium">RFC:</span>
              <span>{company.rfc}</span>
            </div>
            <div class="flex justify-between">
              <span class="font-medium">RPU:</span>
              <span>{company.rpu || '-'}</span>
            </div>
            <div class="flex justify-between">
              <span class="font-medium">Demanda:</span>
              <span>{company.demanda_contratada_kw ? company.demanda_contratada_kw.toLocaleString() + ' kW' : '-'}</span>
            </div>
            {#if company.clasificacion}
              <div class="flex justify-between">
                <span class="font-medium">Clasificación:</span>
                <span class="px-2 py-0.5 text-xs font-semibold rounded bg-green-100 text-green-800">
                  {company.clasificacion}
                </span>
              </div>
            {/if}
          </div>
          
          <div class="flex space-x-2 pt-3 border-t">
            <button
              onclick={() => openDocumentsModal(company)}
              class="flex-1 flex items-center justify-center space-x-2 px-3 py-2 text-sm text-yellow-700 bg-yellow-50 hover:bg-yellow-100 rounded-lg transition-colors"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
              </svg>
              <span>Docs</span>
            </button>
            <button
              onclick={() => openEditModal(company)}
              class="flex-1 flex items-center justify-center space-x-2 px-3 py-2 text-sm text-blue-700 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
              <span>Editar</span>
            </button>
            {#if company.is_active}
              <button
                onclick={() => confirmDeleteCompany(company)}
                class="flex items-center justify-center gap-1 px-3 py-2 text-sm text-red-600 bg-red-50 hover:bg-red-100 rounded-lg transition-colors"
                title="Desactivar empresa"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 115.636 5.636m12.728 12.728L5.636 5.636" />
                </svg>
                <span>Desactivar</span>
              </button>
            {:else}
              <button
                onclick={() => reactivateCompany(company)}
                class="flex items-center justify-center gap-1 px-3 py-2 text-sm text-green-700 bg-green-50 hover:bg-green-100 rounded-lg transition-colors"
                title="Reactivar empresa"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>Reactivar</span>
              </button>
            {/if}
          </div>
        </div>
      {/each}
    </div>

    <!-- Pagination -->
    <div class="mt-4 flex flex-col sm:flex-row justify-between items-center gap-4">
      <div class="text-sm text-gray-600">
        {#if searchTerm || filterTipo}
          <span>{totalFiltered} resultado{totalFiltered !== 1 ? 's' : ''} de {totalCompanies} empresas</span>
        {:else}
          Mostrando {Math.min((currentPage - 1) * pageSize + 1, totalFiltered)}-{Math.min(currentPage * pageSize, totalFiltered)} de {totalFiltered} empresas
        {/if}
      </div>
      <div class="flex space-x-2">
        <button
          onclick={() => handlePageChange(currentPage - 1)}
          disabled={currentPage === 1}
          class="px-3 py-1 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
        >
          Anterior
        </button>
        <span class="px-3 py-1 text-sm text-gray-600">
          {currentPage} / {totalPages}
        </span>
        <button
          onclick={() => handlePageChange(currentPage + 1)}
          disabled={currentPage >= totalPages}
          class="px-3 py-1 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
        >
          Siguiente
        </button>
      </div>
    </div>
  {/if}
</div>

<!-- Modal confirmar eliminación -->
{#if showDeleteModal && companyToDelete}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
      <div class="flex items-start gap-4 mb-5">
        <div class="flex-shrink-0 w-10 h-10 rounded-full bg-orange-100 flex items-center justify-center">
          <svg class="w-5 h-5 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 115.636 5.636m12.728 12.728L5.636 5.636"/>
          </svg>
        </div>
        <div>
          <h3 class="text-lg font-semibold text-gray-900">Desactivar empresa</h3>
          <p class="text-sm text-gray-600 mt-1">
            ¿Desactivar
            <strong class="text-gray-900">{companyToDelete.razon_social}</strong>?
          </p>
          <p class="text-xs text-gray-500 mt-2">La empresa pasará a la pestaña de Inactivas y podrás reactivarla en cualquier momento.</p>
        </div>
      </div>
      <div class="flex justify-end gap-3">
        <button
          type="button"
          onclick={() => { showDeleteModal = false; companyToDelete = null; }}
          disabled={deletingCompany}
          class="px-4 py-2 text-sm border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 disabled:opacity-50"
        >
          Cancelar
        </button>
        <button
          type="button"
          onclick={deleteCompany}
          disabled={deletingCompany}
          class="px-4 py-2 text-sm bg-orange-600 hover:bg-orange-700 text-white rounded-lg transition-colors disabled:opacity-50 flex items-center gap-2"
        >
          {#if deletingCompany}
            <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
            </svg>
            Desactivando...
          {:else}
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 115.636 5.636m12.728 12.728L5.636 5.636"/>
            </svg>
            Desactivar empresa
          {/if}
        </button>
      </div>
    </div>
  </div>
{/if}

<!-- Modal de formulario completo -->
{#if showModal}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 overflow-y-auto">
    <div class="bg-white rounded-lg max-w-4xl w-full mx-4 my-8">
      <div class="p-6 max-h-[85vh] overflow-y-auto">
        <div class="flex justify-between items-center mb-6">
          <h2 class="text-2xl font-bold text-gray-900">
            {modalMode === 'create' ? 'Registrar Nueva Empresa' : 'Editar Empresa'}
          </h2>
          <button
            onclick={() => showModal = false}
            class="text-gray-400 hover:text-gray-600"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Tab nav -->
        <div class="flex border-b border-gray-200 mb-5 -mx-1">
          {#each [['general','General'],['contacto','Contacto'],['electrico','Eléctrico']] as [tab, label]}
            <button
              type="button"
              onclick={() => modalTab = tab}
              class="px-5 py-2.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap
                {modalTab === tab
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
            >{label}</button>
          {/each}
        </div>

        <form onsubmit={(e) => { e.preventDefault(); handleSubmit(); }}>

          <!-- ── TAB: GENERAL ── -->
          {#if modalTab === 'general'}
            <div class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">
                  Razón Social <span class="text-red-500">*</span>
                  <span class="text-xs text-gray-400 ml-1">(mín. 3 caracteres)</span>
                </label>
                <input
                  bind:this={firstModalInput}
                  type="text"
                  bind:value={formData.razon_social}
                  required
                  minlength="3"
                  maxlength="300"
                  placeholder="Ej: Empresa Industrial S.A. de C.V."
                  class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 {validationErrors['razon_social'] ? 'border-red-500 bg-red-50' : 'border-gray-300 focus:border-blue-500'}"
                />
                {#if validationErrors['razon_social']}
                  <p class="text-red-600 text-xs mt-1">{validationErrors['razon_social']}</p>
                {/if}
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">
                  Nombre Comercial
                  <span class="text-xs text-gray-400 ml-1">(opcional)</span>
                </label>
                <input
                  type="text"
                  bind:value={formData.nombre_comercial}
                  maxlength="200"
                  placeholder="Ej: Industrias del Norte"
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">
                  RFC <span class="text-red-500">*</span>
                  <span class="text-xs text-gray-400 ml-1">(12-13 caracteres)</span>
                </label>
                <input
                  type="text"
                  bind:value={formData.rfc}
                  oninput={(e) => formData.rfc = e.target.value.toUpperCase()}
                  required
                  minlength="12"
                  maxlength="13"
                  placeholder="XAXX010101000"
                  class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 uppercase {validationErrors['rfc'] ? 'border-red-500 bg-red-50' : 'border-gray-300 focus:border-blue-500'}"
                />
                {#if validationErrors['rfc']}
                  <p class="text-red-600 text-xs mt-1">{validationErrors['rfc']}</p>
                {/if}
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Notas Adicionales</label>
                <textarea
                  bind:value={formData.notas}
                  rows="3"
                  placeholder="Observaciones generales..."
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                ></textarea>
              </div>
              <div class="flex items-center pt-1">
                <input
                  type="checkbox"
                  id="company_active"
                  bind:checked={formData.is_active}
                  class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label for="company_active" class="ml-2 text-sm text-gray-700">
                  Empresa activa
                </label>
              </div>
            </div>
          {/if}

          <!-- ── TAB: CONTACTO ── -->
          {#if modalTab === 'contacto'}
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">
                  Teléfono
                  <span class="text-xs text-gray-400 ml-1">(opcional)</span>
                </label>
                <input
                  type="text"
                  inputmode="tel"
                  bind:value={formData.telefono}
                  maxlength="20"
                  placeholder="55 1234 5678"
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input
                  type="email"
                  bind:value={formData.email}
                  placeholder="contacto@empresa.com"
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div class="md:col-span-2">
                <label class="block text-sm font-medium text-gray-700 mb-1">Dirección</label>
                <textarea
                  bind:value={formData.direccion}
                  rows="2"
                  maxlength="500"
                  placeholder="Calle, número, colonia..."
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                ></textarea>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Ciudad</label>
                <input
                  type="text"
                  bind:value={formData.ciudad}
                  maxlength="100"
                  placeholder="Ej: Monterrey"
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Estado</label>
                <input
                  type="text"
                  bind:value={formData.estado}
                  maxlength="100"
                  placeholder="Ej: Nuevo León"
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">
                  Código Postal
                  <span class="text-xs text-gray-400 ml-1">(opcional)</span>
                </label>
                <input
                  type="text"
                  inputmode="numeric"
                  bind:value={formData.codigo_postal}
                  maxlength="10"
                  placeholder="64000"
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>
          {/if}

          <!-- ── TAB: ELÉCTRICO ── -->
          {#if modalTab === 'electrico'}
            <div class="space-y-5">
              <!-- Toggle eléctrico -->
              <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span class="text-sm font-medium text-gray-700">¿Incluir datos eléctricos?</span>
                <button
                  type="button"
                  onclick={() => showElectricalData = !showElectricalData}
                  class="px-4 py-1.5 text-sm font-medium rounded-lg transition-colors {showElectricalData ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'}"
                >
                  {showElectricalData ? '✓ Activo' : 'Activar'}
                </button>
              </div>

              {#if showElectricalData}
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 bg-blue-50 p-4 rounded-lg">
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">
                      RPU
                      <span class="text-xs text-gray-400 ml-1">(5-50 caracteres)</span>
                    </label>
                    <input
                      type="text"
                      bind:value={formData.rpu}
                      minlength="5"
                      maxlength="50"
                      placeholder="Ej: 1234567890"
                      class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Tipo de Suministro</label>
                    <select
                      bind:value={formData.tipo_suministro}
                      class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
                    >
                      <option value="">Seleccionar...</option>
                      <option value="GDMTH">GDMTH - Gran Demanda MT Horaria</option>
                      <option value="GDMTO">GDMTO - Gran Demanda MT Ordinaria</option>
                      <option value="GDBT">GDBT - Gran Demanda BT</option>
                      <option value="DIST">DIST - Distribución</option>
                    </select>
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">
                      Tensión de Suministro
                      <span class="text-xs text-gray-400 ml-1">(Ej: 13.2 kV)</span>
                    </label>
                    <input
                      type="text"
                      bind:value={formData.tension_suministro}
                      maxlength="50"
                      placeholder="13.2 kV"
                      class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Demanda Contratada (kW)</label>
                    <input
                      type="number"
                      bind:value={formData.demanda_contratada_kw}
                      step="0.01"
                      min="0"
                      placeholder="0.00"
                      class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Demanda Máxima (kW)</label>
                    <input
                      type="number"
                      bind:value={formData.demanda_maxima_kw}
                      step="0.01"
                      min="0"
                      placeholder="0.00"
                      class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">
                      Factor de Carga
                      <span class="text-xs text-gray-400 ml-1">(0–1)</span>
                    </label>
                    <input
                      type="number"
                      bind:value={formData.factor_carga}
                      step="0.01"
                      min="0"
                      max="1"
                      placeholder="0.00"
                      class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">
                      Factor de Potencia
                      <span class="text-xs text-gray-400 ml-1">(0–1)</span>
                    </label>
                    <input
                      type="number"
                      bind:value={formData.factor_potencia}
                      step="0.01"
                      min="0"
                      max="1"
                      placeholder="0.00"
                      class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Consumo Mensual (kWh)</label>
                    <input
                      type="number"
                      bind:value={formData.consumo_mensual_kwh}
                      step="0.01"
                      min="0"
                      placeholder="0.00"
                      class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Costo Mensual Aprox. ($)</label>
                    <input
                      type="number"
                      bind:value={formData.costo_mensual_aproximado}
                      step="0.01"
                      min="0"
                      placeholder="0.00"
                      class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
                    />
                  </div>
                </div>
              {/if}

              <!-- Centro de carga (siempre visible en tab eléctrico) -->
              <div class="grid grid-cols-1 gap-4 pt-2">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Nombre del Centro de Carga</label>
                  <input
                    type="text"
                    bind:value={formData.nombre_centro_carga}
                    maxlength="200"
                    placeholder="Ej: Planta Principal"
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Ubicación del Centro de Carga</label>
                  <textarea
                    bind:value={formData.ubicacion_centro_carga}
                    rows="2"
                    placeholder="Dirección o descripción del centro de carga..."
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  ></textarea>
                </div>
              </div>
            </div>
          {/if}

          <!-- Buttons — always visible -->
          <div class="flex justify-between items-center pt-5 mt-5 border-t">
            <div class="flex gap-1">
              {#each [['general','General'],['contacto','Contacto'],['electrico','Eléctrico']] as [tab, label], i}
                <button
                  type="button"
                  onclick={() => modalTab = tab}
                  class="w-2 h-2 rounded-full transition-colors {modalTab === tab ? 'bg-blue-600' : 'bg-gray-300 hover:bg-gray-400'}"
                  title={label}
                ></button>
              {/each}
            </div>
            <div class="flex space-x-3">
              <button
                type="button"
                onclick={() => showModal = false}
                class="px-5 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 text-sm"
              >
                Cancelar
              </button>
              <button
                type="submit"
                class="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors text-sm font-medium"
              >
                {modalMode === 'create' ? 'Registrar Empresa' : 'Guardar Cambios'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  </div>
{/if}

<!-- Modal de Documentos -->
{#if showDocumentsModal && selectedCompanyForDocs}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
      <!-- Header -->
      <div class="p-6 border-b bg-gradient-to-r from-yellow-50 to-orange-50">
        <div class="flex justify-between items-start">
          <div>
            <h2 class="text-2xl font-bold text-gray-900 flex items-center">
              <svg class="w-7 h-7 mr-2 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
              </svg>
              Expediente Digital
            </h2>
            <p class="text-gray-600 mt-1">{selectedCompanyForDocs.razon_social}</p>
            <p class="text-sm text-gray-500">RFC: {selectedCompanyForDocs.rfc}</p>
          </div>
          <button
            onclick={() => showDocumentsModal = false}
            class="text-gray-400 hover:text-gray-600"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Content -->
      <div class="flex-1 overflow-y-auto p-6">
        <!-- Subir nuevo documento -->
        <div class="bg-blue-50 border-2 border-dashed border-blue-300 rounded-lg p-6 mb-6">
          <h3 class="text-lg font-semibold text-gray-900 mb-4">Subir Nuevo Documento</h3>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">Tipo de Documento *</label>
              <select
                id="tipo_documento"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">Seleccionar tipo...</option>
                <option value="ACTA_CONSTITUTIVA">Acta Constitutiva</option>
                <option value="INE">INE</option>
                <option value="IFE">IFE</option>
                <option value="PODER_LEGAL">Poder Legal</option>
                <option value="PLANO">Plano</option>
                <option value="CONSTANCIA_SITUACION_FISCAL">Constancia de Situación Fiscal</option>
                <option value="COMPROBANTE_DOMICILIO">Comprobante de Domicilio</option>
                <option value="RECIBO_CFE">Recibo CFE</option>
                <option value="CONTRATO_SUMINISTRO">Contrato de Suministro</option>
                <option value="OTRO">Otro</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">Descripción (Opcional)</label>
              <input
                type="text"
                id="descripcion_doc"
                placeholder="Ej: Acta constitutiva con poderes actualizados"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>
          <div class="mt-4">
            <label class="block">
              <span class="sr-only">Seleccionar archivo</span>
              <input
                type="file"
                onchange={uploadDocument}
                disabled={uploadingDocument}
                accept=".pdf,.doc,.docx,.jpg,.jpeg,.png,.xls,.xlsx,.zip"
                class="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-700 file:cursor-pointer disabled:opacity-50"
              />
            </label>
            {#if uploadingDocument}
              <div class="mt-3">
                <div class="flex justify-between items-center mb-1">
                  <span class="text-sm text-blue-600 font-medium">Subiendo documento...</span>
                  <span class="text-sm text-blue-600 font-medium">{uploadProgress}%</span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-2.5 overflow-hidden">
                  <div 
                    class="bg-blue-600 h-2.5 rounded-full transition-all duration-300 ease-out"
                    style="width: {uploadProgress}%"
                  ></div>
                </div>
              </div>
            {/if}
          </div>
        </div>

        <!-- Lista de documentos -->
        <div>
          <h3 class="text-lg font-semibold text-gray-900 mb-4">Documentos Cargados ({documents.length})</h3>
          
          {#if loadingDocuments}
            <div class="text-center py-8">
              <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
              <p class="text-gray-600 mt-4">Cargando documentos...</p>
            </div>
          {:else if documents.length === 0}
            <div class="text-center py-12 bg-gray-50 rounded-lg">
              <svg class="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <p class="text-gray-600">No hay documentos cargados</p>
              <p class="text-sm text-gray-500 mt-1">Suba el primer documento usando el formulario de arriba</p>
            </div>
          {:else}
            <div class="space-y-3">
              {#each documents as doc}
                <div class="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                  <div class="flex items-center flex-1 min-w-0">
                    <div class="flex-shrink-0 w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center mr-3">
                      <svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    </div>
                    <div class="flex-1 min-w-0">
                      <div class="flex items-center gap-2">
                        <span class="text-xs px-2 py-1 bg-purple-100 text-purple-800 rounded font-medium">
                          {doc.tipo_documento.replace(/_/g, ' ')}
                        </span>
                        {#if doc.descripcion}
                          <p class="text-sm text-gray-600 truncate">{doc.descripcion}</p>
                        {/if}
                      </div>
                      <p class="text-xs text-gray-500 mt-1">
                        {doc.nombre_original} • 
                        {(doc.tamano_bytes / 1024).toFixed(1)} KB •
                        {new Date(doc.created_at).toLocaleDateString('es-MX')}
                      </p>
                    </div>
                  </div>
                  <div class="flex items-center space-x-2 ml-4">
                    <button
                      onclick={() => viewDocument(doc.id)}
                      class="p-2 text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                      title="Ver documento"
                    >
                      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                    </button>
                    <button
                      onclick={() => downloadDocument(doc.id)}
                      class="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                      title="Descargar"
                    >
                      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                      </svg>
                    </button>
                    <button
                      onclick={() => deleteDocument(doc.id)}
                      class="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      title="Eliminar"
                    >
                      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                </div>
              {/each}
            </div>
          {/if}
        </div>
      </div>

      <!-- Footer -->
      <div class="p-4 border-t bg-gray-50 flex justify-end">
        <button
          onclick={() => showDocumentsModal = false}
          class="px-6 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors"
        >
          Cerrar
        </button>
      </div>
    </div>
  </div>
{/if}

<!-- Modal de Visualización de Documento -->
{#if showViewerModal}
  <div class="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-[60] p-4">
    <div class="bg-white rounded-lg max-w-6xl w-full h-[90vh] flex flex-col">
      <!-- Header -->
      <div class="p-4 border-b flex justify-between items-center bg-gray-50">
        <div class="flex items-center space-x-3">
          <svg class="w-6 h-6 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <div>
            <h3 class="font-semibold text-gray-900">{currentDocumentName}</h3>
            <p class="text-xs text-gray-500">{currentDocumentType}</p>
          </div>
        </div>
        <div class="flex items-center space-x-2">
          <a
            href={currentDocumentUrl}
            target="_blank"
            class="px-3 py-2 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors flex items-center space-x-2"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
            <span>Abrir en nueva pestaña</span>
          </a>
          <button
            onclick={() => showViewerModal = false}
            class="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
      
      <!-- Viewer Content -->
      <div class="flex-1 overflow-hidden bg-gray-100">
        {#if currentDocumentType?.includes('pdf')}
          <iframe
            src={currentDocumentUrl}
            class="w-full h-full"
            title={currentDocumentName}
          ></iframe>
        {:else if currentDocumentType?.includes('image')}
          <div class="w-full h-full flex items-center justify-center p-4">
            <img
              src={currentDocumentUrl}
              alt={currentDocumentName}
              class="max-w-full max-h-full object-contain"
            />
          </div>
        {:else}
          <div class="w-full h-full flex flex-col items-center justify-center p-8 text-center">
            <svg class="w-20 h-20 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <h3 class="text-lg font-medium text-gray-900 mb-2">Vista previa no disponible</h3>
            <p class="text-gray-600 mb-4">Este tipo de archivo no puede visualizarse en el navegador</p>
            <a
              href={currentDocumentUrl}
              download
              class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
            >
              Descargar Archivo
            </a>
          </div>
        {/if}
      </div>
    </div>
  </div>
{/if}

<style>
  @keyframes shrink {
    from {
      width: 100%;
    }
    to {
      width: 0%;
    }
  }
</style>
