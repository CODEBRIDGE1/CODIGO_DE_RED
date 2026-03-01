<script lang="ts">
  import { onMount } from 'svelte';
  import { authStore } from '../../stores/auth';
  import { navigate } from '../../lib/router';

  interface Tenant {
    id: number;
    name: string;
    subdomain: string;
    status: string;
    contact_name?: string | null;
    contact_email?: string | null;
    contact_phone?: string | null;
    address?: string | null;
    notes?: string | null;
    created_at: string;
    updated_at: string;
    users_count?: number;
    companies_count?: number;
    projects_count?: number;
  }

  interface TenantForm {
    name: string;
    subdomain: string;
    contact_name: string;
    contact_email: string;
    contact_phone: string;
    address: string;
    notes: string;
  }

  interface TenantUser {
    id: number;
    email: string;
    full_name: string;
    is_active: boolean;
    created_at: string;
    tenant_name?: string;
    security_level_id?: number | null;
    security_level_name?: string | null;
  }

  interface UserForm {
    email: string;
    full_name: string;
    password: string;
    is_active: boolean;
    tenant_id: number;
    security_level_id: number | null;
  }

  interface TenantCompany {
    id: number;
    razon_social: string;
    nombre_comercial?: string | null;
    rfc: string;
    rpu?: string | null;
    tipo_suministro: string;
    tension_suministro?: string | null;
    telefono?: string | null;
    email?: string | null;
    direccion?: string | null;
    ciudad?: string | null;
    estado?: string | null;
    codigo_postal?: string | null;
    is_active: boolean;
    clasificacion?: string | null;
    demanda_contratada_kw?: number | null;
    demanda_maxima_kw?: number | null;
    consumo_mensual_kwh?: number | null;
    costo_mensual_aproximado?: number | null;
    notas?: string | null;
    created_at: string;
  }

  interface CompanyForm {
    razon_social: string;
    nombre_comercial: string;
    rfc: string;
    rpu: string;
    tipo_suministro: string;
    tension_suministro: string;
    telefono: string;
    email: string;
    direccion: string;
    ciudad: string;
    estado: string;
    codigo_postal: string;
    demanda_contratada_kw: number | null;
    consumo_mensual_kwh: number | null;
    costo_mensual_aproximado: number | null;
    notas: string;
  }

  interface CompanyDocument {
    id: number;
    company_id: number;
    tenant_id: number;
    tipo_documento: string;
    nombre_original: string;
    nombre_archivo: string;
    mime_type?: string | null;
    tamano_bytes?: number | null;
    descripcion?: string | null;
    vigencia?: string | null;
    is_active: boolean;
    created_at: string;
  }

  let tenants = $state<Tenant[]>([]);
  let loading = $state(true);
  let errorMessage = $state('');
  let successMessage = $state('');
  let showModal = $state(false);
  let isEditing = $state(false);
  let currentTenant = $state<Tenant | null>(null);
  let searchTerm = $state('');
  let filterActive = $state<'all' | 'active' | 'inactive'>('all');
  let showDeleteModal = $state(false);
  let tenantToDelete = $state<Tenant | null>(null);

  // Estado de gestión de usuarios
  let showUsersModal = $state(false);
  let selectedTenant = $state<Tenant | null>(null);
  let tenantUsers = $state<TenantUser[]>([]);
  let loadingUsers = $state(false);
  let showUserForm = $state(false);
  let isEditingUser = $state(false);
  let currentUser = $state<TenantUser | null>(null);
  let userForm = $state<UserForm>({
    email: '',
    full_name: '',
    password: '',
    is_active: true,
    tenant_id: 0,
    security_level_id: null,
  });

  // Niveles de seguridad disponibles
  let securityLevels = $state<{ id: number; name: string; color: string }[]>([]);
  let loadingSecurityLevels = $state(false);

  async function fetchSecurityLevels() {
    if (securityLevels.length > 0) return; // ya cargados
    loadingSecurityLevels = true;
    try {
      const res = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/admin/security-levels/`, {
        headers: { Authorization: `Bearer ${$authStore.accessToken}` }
      });
      if (res.ok) securityLevels = await res.json();
    } catch {}
    finally { loadingSecurityLevels = false; }
  }

  // Estado de gestión de empresas
  let showCompaniesModal = $state(false);
  let tenantCompanies = $state<TenantCompany[]>([]);
  let loadingCompanies = $state(false);
  let companiesView = $state<'list' | 'form' | 'docs'>('list');
  let isEditingCompany = $state(false);
  let currentCompanyId = $state<number | null>(null);
  let companyFormTab = $state<'general' | 'contacto' | 'electrico'>('general');
  let showCompanyForm = $state(false); // alias para compatibilidad

  // Estado de documentos de empresa
  let companyDocs = $state<CompanyDocument[]>([]);
  let loadingDocs = $state(false);
  let selectedCompanyForDocs = $state<TenantCompany | null>(null);
  
  // Estado para visor de documentos
  let showDocViewerModal = $state(false);
  let viewingDocUrl = $state<string | null>(null);
  let viewingDocName = $state('');
  let viewingDocType = $state('');

  let companyForm = $state<CompanyForm>({
    razon_social: '', nombre_comercial: '', rfc: '', rpu: '',
    tipo_suministro: 'GDMTH', tension_suministro: '',
    telefono: '', email: '', direccion: '', ciudad: '',
    estado: '', codigo_postal: '',
    demanda_contratada_kw: null, consumo_mensual_kwh: null,
    costo_mensual_aproximado: null, notas: ''
  });

  let form = $state<TenantForm>({
    name: '',
    subdomain: '',
    contact_name: '',
    contact_email: '',
    contact_phone: '',
    address: '',
    notes: ''
  });

  const filteredTenants = $derived(
    tenants.filter(t => {
      const matchesSearch = t.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          t.subdomain.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesActive = filterActive === 'all' ? true :
                          filterActive === 'active' ? t.status === 'active' : t.status !== 'active';
      return matchesSearch && matchesActive;
    })
  );

  onMount(() => {
    loadTenants();
  });

  async function loadTenants() {
    try {
      loading = true;
      errorMessage = '';
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/admin/tenants/`, {
        headers: {
          'Authorization': `Bearer ${$authStore.accessToken}`
        }
      });

      if (response.status === 401) {
        authStore.logout();
        navigate('/');
        return;
      }
      if (!response.ok) throw new Error('Error al cargar clientes');
      
      const data = await response.json();
      tenants = data.items || data;
    } catch (error) {
      console.error('Error:', error);
      errorMessage = 'Error al cargar los clientes. Intenta de nuevo.';
    } finally {
      loading = false;
    }
  }

  function openCreateModal() {
    isEditing = false;
    currentTenant = null;
    form = {
      name: '',
      subdomain: '',
      contact_name: '',
      contact_email: '',
      contact_phone: '',
      address: '',
      notes: ''
    };
    showModal = true;
  }

  function openEditModal(tenant: Tenant) {
    isEditing = true;
    currentTenant = tenant;
    form = {
      name: tenant.name,
      subdomain: tenant.subdomain,
      contact_name: tenant.contact_name || '',
      contact_email: tenant.contact_email || '',
      contact_phone: tenant.contact_phone || '',
      address: tenant.address || '',
      notes: tenant.notes || ''
    };
    showModal = true;
  }

  function closeModal() {
    showModal = false;
    currentTenant = null;
  }

  function generateSubdomain() {
    form.subdomain = form.name
      .toLowerCase()
      .replace(/[áàäâ]/g, 'a')
      .replace(/[éèëê]/g, 'e')
      .replace(/[íìïî]/g, 'i')
      .replace(/[óòöô]/g, 'o')
      .replace(/[úùüû]/g, 'u')
      .replace(/ñ/g, 'n')
      .replace(/[^a-z0-9]/g, '-')
      .replace(/-+/g, '-')
      .replace(/^-|-$/g, '');
  }

  async function handleSubmit() {
    try {
      const url = isEditing
        ? `${import.meta.env.VITE_API_BASE_URL}/api/v1/admin/tenants/${currentTenant!.id}/`
        : `${import.meta.env.VITE_API_BASE_URL}/api/v1/admin/tenants/`;
      
      const method = isEditing ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${$authStore.accessToken}`
        },
        body: JSON.stringify(form)
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Error al guardar');
      }

      await loadTenants();
      closeModal();
      successMessage = isEditing ? 'Cliente actualizado correctamente' : 'Cliente creado correctamente';
      setTimeout(() => successMessage = '', 4000);
    } catch (error: any) {
      console.error('Error:', error);
      errorMessage = error.message || 'Error al guardar el cliente';
    }
  }

  function confirmDelete(tenant: Tenant) {
    tenantToDelete = tenant;
    showDeleteModal = true;
  }

  async function handleDelete() {
    if (!tenantToDelete) return;

    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_BASE_URL}/api/v1/admin/tenants/${tenantToDelete.id}/`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${$authStore.accessToken}`
          }
        }
      );

      if (!response.ok) throw new Error('Error al eliminar');

      await loadTenants();
      showDeleteModal = false;
      tenantToDelete = null;
      successMessage = 'Cliente desactivado correctamente';
      setTimeout(() => successMessage = '', 4000);
    } catch (error) {
      console.error('Error:', error);
      errorMessage = 'Error al desactivar el cliente';
    }
  }

  // ─── Gestión de Usuarios por Tenant ───────────────────────────────────────

  async function openUsersModal(tenant: Tenant) {
    selectedTenant = tenant;
    showUsersModal = true;
    showUserForm = false;
    await Promise.all([loadTenantUsers(tenant.id), fetchSecurityLevels()]);
  }

  function closeUsersModal() {
    showUsersModal = false;
    selectedTenant = null;
    tenantUsers = [];
    showUserForm = false;
  }

  async function loadTenantUsers(tenantId: number) {
    try {
      loadingUsers = true;
      const response = await fetch(
        `${import.meta.env.VITE_API_BASE_URL}/api/v1/admin/users/?tenant_id=${tenantId}`,
        { headers: { 'Authorization': `Bearer ${$authStore.accessToken}` } }
      );
      if (!response.ok) throw new Error('Error al cargar usuarios');
      const data = await response.json();
      tenantUsers = data.items || data;
    } catch (error) {
      console.error('Error:', error);
      errorMessage = 'Error al cargar los usuarios del cliente';
    } finally {
      loadingUsers = false;
    }
  }

  function openCreateUserForm() {
    isEditingUser = false;
    currentUser = null;
    userForm = {
      email: '',
      full_name: '',
      password: '',
      is_active: true,
      tenant_id: selectedTenant!.id,
      security_level_id: null,
    };
    showUserForm = true;
  }

  function openEditUserForm(user: TenantUser) {
    isEditingUser = true;
    currentUser = user;
    userForm = {
      email: user.email,
      full_name: user.full_name,
      password: '',
      is_active: user.is_active,
      tenant_id: selectedTenant!.id,
      security_level_id: user.security_level_id ?? null,
    };
    showUserForm = true;
  }

  async function handleUserSubmit() {
    try {
      const url = isEditingUser
        ? `${import.meta.env.VITE_API_BASE_URL}/api/v1/admin/users/${currentUser!.id}/`
        : `${import.meta.env.VITE_API_BASE_URL}/api/v1/admin/users/`;
      const method = isEditingUser ? 'PUT' : 'POST';

      const payload: any = {
        email: userForm.email,
        full_name: userForm.full_name,
        is_active: userForm.is_active,
        tenant_id: userForm.tenant_id,
        security_level_id: userForm.security_level_id,
      };
      if (userForm.password) payload.password = userForm.password;

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${$authStore.accessToken}`
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Error al guardar');
      }

      await loadTenantUsers(selectedTenant!.id);
      await loadTenants();
      showUserForm = false;
      successMessage = isEditingUser ? 'Usuario actualizado' : 'Usuario creado correctamente';
      setTimeout(() => successMessage = '', 4000);
    } catch (error: any) {
      console.error('Error:', error);
      errorMessage = error.message || 'Error al guardar el usuario';
    }
  }

  async function toggleUserStatus(user: TenantUser) {
    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_BASE_URL}/api/v1/admin/users/${user.id}/`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${$authStore.accessToken}`
          },
          body: JSON.stringify({ is_active: !user.is_active })
        }
      );
      if (!response.ok) throw new Error('Error al actualizar');
      await loadTenantUsers(selectedTenant!.id);
      await loadTenants();
    } catch (error) {
      console.error('Error:', error);
      errorMessage = 'Error al cambiar el estado del usuario';
    }
  }

  // ─── Gestión de Empresas por Tenant ──────────────────────────────────────

  async function openCompaniesModal(tenant: Tenant) {
    selectedTenant = tenant;
    showCompaniesModal = true;
    companiesView = 'list';
    await loadTenantCompanies(tenant.id);
  }

  function closeCompaniesModal() {
    showCompaniesModal = false;
    tenantCompanies = [];
    showCompanyForm = false;
    companiesView = 'list';
    isEditingCompany = false;
    currentCompanyId = null;
  }

  async function loadTenantCompanies(tenantId: number) {
    try {
      loadingCompanies = true;
      const response = await fetch(
        `${import.meta.env.VITE_API_BASE_URL}/api/v1/admin/companies/?tenant_id=${tenantId}`,
        { headers: { 'Authorization': `Bearer ${$authStore.accessToken}` } }
      );
      if (!response.ok) throw new Error('Error al cargar empresas');
      const data = await response.json();
      tenantCompanies = data.items || data;
    } catch (error) {
      console.error('Error:', error);
      errorMessage = 'Error al cargar las empresas del cliente';
    } finally {
      loadingCompanies = false;
    }
  }

  function openCompanyForm() {
    isEditingCompany = false;
    currentCompanyId = null;
    companyFormTab = 'general';
    companyForm = {
      razon_social: '', nombre_comercial: '', rfc: '', rpu: '',
      tipo_suministro: 'GDMTH', tension_suministro: '',
      telefono: '', email: '', direccion: '', ciudad: '',
      estado: '', codigo_postal: '',
      demanda_contratada_kw: null, consumo_mensual_kwh: null,
      costo_mensual_aproximado: null, notas: ''
    };
    companiesView = 'form';
    showCompanyForm = true;
  }

  function openEditCompanyForm(company: TenantCompany) {
    isEditingCompany = true;
    currentCompanyId = company.id;
    companyFormTab = 'general';
    companyForm = {
      razon_social: company.razon_social,
      nombre_comercial: company.nombre_comercial || '',
      rfc: company.rfc,
      rpu: company.rpu || '',
      tipo_suministro: company.tipo_suministro,
      tension_suministro: company.tension_suministro || '',
      telefono: company.telefono || '',
      email: company.email || '',
      direccion: company.direccion || '',
      ciudad: company.ciudad || '',
      estado: company.estado || '',
      codigo_postal: company.codigo_postal || '',
      demanda_contratada_kw: company.demanda_contratada_kw ?? null,
      consumo_mensual_kwh: company.consumo_mensual_kwh ?? null,
      costo_mensual_aproximado: company.costo_mensual_aproximado ?? null,
      notas: company.notas || ''
    };
    companiesView = 'form';
    showCompanyForm = true;
  }

  async function handleCompanySubmit() {
    try {
      const url = isEditingCompany
        ? `${import.meta.env.VITE_API_BASE_URL}/api/v1/admin/companies/${currentCompanyId}/`
        : `${import.meta.env.VITE_API_BASE_URL}/api/v1/admin/companies/`;
      const method = isEditingCompany ? 'PUT' : 'POST';

      const payload: any = { ...companyForm };
      if (!isEditingCompany) payload.tenant_id = selectedTenant!.id;
      // Limpiar strings vacíos a null en campos opcionales
      ['rpu','tension_suministro','telefono','email','direccion','ciudad','estado','codigo_postal','nombre_comercial','notas'].forEach(k => {
        if (payload[k] === '') payload[k] = null;
      });

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${$authStore.accessToken}`
        },
        body: JSON.stringify(payload)
      });
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Error al guardar empresa');
      }
      await loadTenantCompanies(selectedTenant!.id);
      await loadTenants();
      companiesView = 'list';
      showCompanyForm = false;
      successMessage = isEditingCompany ? 'Empresa actualizada correctamente' : 'Empresa creada correctamente';
      setTimeout(() => successMessage = '', 4000);
    } catch (error: any) {
      console.error('Error:', error);
      errorMessage = error.message || 'Error al guardar la empresa';
    }
  }

  async function openDocsView(company: TenantCompany) {
    selectedCompanyForDocs = company;
    companiesView = 'docs';
    companyDocs = [];
    loadingDocs = true;
    try {
      const res = await fetch(
        `${import.meta.env.VITE_API_BASE_URL}/api/v1/admin/companies/${company.id}/documents/`,
        { headers: { Authorization: `Bearer ${$authStore.accessToken}` } }
      );
      if (!res.ok) throw new Error('Error al cargar documentos');
      const data = await res.json();
      companyDocs = data.items || [];
    } catch (e: any) {
      errorMessage = e.message || 'Error al cargar documentos';
    } finally {
      loadingDocs = false;
    }
  }

  async function downloadDocument(doc: CompanyDocument) {
    try {
      const res = await fetch(
        `${import.meta.env.VITE_API_BASE_URL}/api/v1/admin/companies/${doc.company_id}/documents/${doc.id}/download/`,
        { headers: { Authorization: `Bearer ${$authStore.accessToken}` } }
      );
      if (!res.ok) throw new Error('Error al obtener enlace de descarga');
      const data = await res.json();
      // Abrir en pestaña nueva
      window.open(data.url, '_blank');
    } catch (e: any) {
      errorMessage = e.message || 'Error al descargar documento';
    }
  }

  async function viewDocument(doc: CompanyDocument) {
    try {
      const res = await fetch(
        `${import.meta.env.VITE_API_BASE_URL}/api/v1/admin/companies/${doc.company_id}/documents/${doc.id}/download/`,
        { headers: { Authorization: `Bearer ${$authStore.accessToken}` } }
      );
      if (!res.ok) throw new Error('Error al obtener documento');
      const data = await res.json();
      viewingDocUrl = data.url;
      viewingDocName = doc.nombre_archivo;
      viewingDocType = doc.mime_type || '';
      showDocViewerModal = true;
    } catch (e: any) {
      errorMessage = e.message || 'Error al cargar documento';
    }
  }

  function formatBytes(bytes?: number | null): string {
    if (!bytes) return '—';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  const TIPO_LABELS: Record<string, string> = {
    ACTA_CONSTITUTIVA: 'Acta Constitutiva',
    INE: 'INE',
    IFE: 'IFE',
    PODER_LEGAL: 'Poder Legal',
    PLANO: 'Plano',
    CONSTANCIA_SITUACION_FISCAL: 'Constancia Fiscal',
    COMPROBANTE_DOMICILIO: 'Comprobante Domicilio',
    RECIBO_CFE: 'Recibo CFE',
    CONTRATO_SUMINISTRO: 'Contrato Suministro',
    OTRO: 'Otro',
  };
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
  <div class="flex justify-between items-center mb-6">
    <div>
      <h1 class="text-2xl font-bold text-gray-900">Gestión de Clientes</h1>
      <p class="text-gray-600 mt-1">Administra los clientes (tenants) de la plataforma</p>
    </div>
    <button
      onclick={openCreateModal}
      class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
      </svg>
      Nuevo Cliente
    </button>
  </div>

  <!-- Filters -->
  <div class="bg-white rounded-lg shadow-sm p-4 mb-6">
    <div class="flex gap-4 flex-wrap">
      <div class="flex-1 min-w-[300px]">
        <input
          type="text"
          bind:value={searchTerm}
          placeholder="Buscar por nombre, slug o email..."
          class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>
      <div class="flex gap-2">
        <button
          onclick={() => filterActive = 'all'}
          class="px-4 py-2 rounded-lg border"
          class:bg-blue-600={filterActive === 'all'}
          class:text-white={filterActive === 'all'}
          class:border-blue-600={filterActive === 'all'}
          class:bg-white={filterActive !== 'all'}
          class:text-gray-700={filterActive !== 'all'}
        >
          Todos
        </button>
        <button
          onclick={() => filterActive = 'active'}
          class="px-4 py-2 rounded-lg border"
          class:bg-blue-600={filterActive === 'active'}
          class:text-white={filterActive === 'active'}
          class:border-blue-600={filterActive === 'active'}
          class:bg-white={filterActive !== 'active'}
          class:text-gray-700={filterActive !== 'active'}
        >
          Activos
        </button>
        <button
          onclick={() => filterActive = 'inactive'}
          class="px-4 py-2 rounded-lg border"
          class:bg-blue-600={filterActive === 'inactive'}
          class:text-white={filterActive === 'inactive'}
          class:border-blue-600={filterActive === 'inactive'}
          class:bg-white={filterActive !== 'inactive'}
          class:text-gray-700={filterActive !== 'inactive'}
        >
          Inactivos
        </button>
      </div>
    </div>
  </div>

  <!-- Table -->
  {#if loading}
    <div class="text-center py-12">
      <div class="inline-block animate-spin rounded-full h-12 w-12 border-4 border-gray-300 border-t-blue-600"></div>
      <p class="mt-4 text-gray-600">Cargando clientes...</p>
    </div>
  {:else if filteredTenants.length === 0}
    <div class="bg-white rounded-lg shadow-sm p-12 text-center">
      <svg class="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
      </svg>
      <p class="text-gray-600">No se encontraron clientes</p>
    </div>
  {:else}
    <div class="bg-white rounded-lg shadow-sm overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cliente</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Contacto</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estadísticas</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Creado</th>
            <th class="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
            <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          {#each filteredTenants as tenant}
            <tr class="hover:bg-gray-50">
              <!-- Cliente -->
              <td class="px-6 py-4">
                <div class="text-sm font-bold text-gray-900">{tenant.name}</div>
                <span class="px-2 py-0.5 text-xs font-mono bg-gray-100 text-gray-600 rounded">{tenant.subdomain}</span>
                {#if tenant.notes}
                  <div class="text-xs text-gray-400 mt-1 max-w-xs truncate" title={tenant.notes}>
                    📝 {tenant.notes}
                  </div>
                {/if}
              </td>
              <!-- Contacto -->
              <td class="px-6 py-4 text-sm text-gray-600">
                {#if tenant.contact_name}
                  <div class="font-medium text-gray-800">{tenant.contact_name}</div>
                {/if}
                {#if tenant.contact_email}
                  <div class="text-xs flex items-center gap-1 mt-0.5">
                    <svg class="w-3 h-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                    {tenant.contact_email}
                  </div>
                {/if}
                {#if tenant.contact_phone}
                  <div class="text-xs flex items-center gap-1 mt-0.5">
                    <svg class="w-3 h-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                    </svg>
                    {tenant.contact_phone}
                  </div>
                {/if}
                {#if tenant.address}
                  <div class="text-xs flex items-center gap-1 mt-0.5">
                    <svg class="w-3 h-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    {tenant.address}
                  </div>
                {/if}
                {#if !tenant.contact_name && !tenant.contact_email && !tenant.contact_phone && !tenant.address}
                  <span class="text-xs text-gray-400 italic">Sin información</span>
                {/if}
              </td>
              <!-- Estadísticas -->
              <td class="px-6 py-4 text-sm text-gray-500">
                <div class="flex items-center gap-1 mb-1">
                  <svg class="w-4 h-4 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                  </svg>
                  <span>{tenant.users_count || 0} usuarios</span>
                </div>
                <div class="flex items-center gap-1 mb-1">
                  <svg class="w-4 h-4 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                  </svg>
                  <span>{tenant.companies_count || 0} empresas</span>
                </div>
                <div class="flex items-center gap-1">
                  <svg class="w-4 h-4 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                  </svg>
                  <span>{tenant.projects_count || 0} proyectos</span>
                </div>
              </td>
              <!-- Fecha -->
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                <div>{new Date(tenant.created_at).toLocaleDateString('es-MX')}</div>
                <div class="text-xs text-gray-400">{new Date(tenant.created_at).toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit' })}</div>
              </td>
              <!-- Estado -->
              <td class="px-6 py-4 whitespace-nowrap text-center">
                <span class="px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full"
                  class:bg-green-100={tenant.status === 'active'}
                  class:text-green-800={tenant.status === 'active'}
                  class:bg-red-100={tenant.status !== 'active'}
                  class:text-red-800={tenant.status !== 'active'}
                >
                  {tenant.status === 'active' ? 'Activo' : 'Inactivo'}
                </span>
              </td>
              <!-- Acciones -->
              <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                <!-- Botón Usuarios -->
                <button
                  onclick={() => openUsersModal(tenant)}
                  class="text-green-600 hover:text-green-900 mr-3"
                  title="Gestionar Usuarios"
                >
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                  </svg>
                </button>
                <!-- Botón Empresas -->
                <button
                  onclick={() => openCompaniesModal(tenant)}
                  class="text-purple-600 hover:text-purple-900 mr-3"
                  title="Ver Empresas"
                >
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                  </svg>
                </button>
                <button
                  onclick={() => openEditModal(tenant)}
                  class="text-blue-600 hover:text-blue-900 mr-3"
                  title="Editar"
                >
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                </button>
                {#if tenant.status === 'active'}
                  <button
                    onclick={() => confirmDelete(tenant)}
                    class="text-red-600 hover:text-red-900"
                    title="Desactivar"
                  >
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                {/if}
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>

<!-- Create/Edit Modal -->
{#if showModal}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
      <div class="p-6">
        <div class="flex justify-between items-center mb-6">
          <h2 class="text-2xl font-bold text-gray-900">
            {isEditing ? 'Editar Cliente' : 'Nuevo Cliente'}
          </h2>
          <button onclick={closeModal} class="text-gray-400 hover:text-gray-600">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onsubmit={(e) => { e.preventDefault(); handleSubmit(); }} class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <!-- Nombre del Cliente -->
            <div class="col-span-2">
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Nombre del Cliente *
              </label>
              <input
                type="text"
                bind:value={form.name}
                oninput={generateSubdomain}
                required
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Ej: Empresa ABC"
              />
            </div>

            <!-- Subdominio -->
            <div class="col-span-2">
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Subdominio *
              </label>
              <input
                type="text"
                bind:value={form.subdomain}
                required
                pattern="[a-z0-9-]+"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
                placeholder="ej: empresa-abc"
              />
              <p class="text-xs text-gray-500 mt-1">Solo letras minúsculas, números y guiones. Se usará como identificador único.</p>
            </div>

            <!-- Divider -->
            <div class="col-span-2 border-t border-gray-200 my-2">
              <p class="text-sm font-medium text-gray-700 mt-4 mb-2">Información de Contacto</p>
            </div>

            <!-- Nombre del Contacto -->
            <div class="col-span-2 sm:col-span-1">
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Nombre del Contacto
              </label>
              <input
                type="text"
                bind:value={form.contact_name}
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Ej: Juan Pérez"
              />
            </div>

            <!-- Email de Contacto -->
            <div class="col-span-2 sm:col-span-1">
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Email de Contacto
              </label>
              <input
                type="email"
                bind:value={form.contact_email}
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="contacto@empresa.com"
              />
            </div>

            <!-- Teléfono -->
            <div class="col-span-2 sm:col-span-1">
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Teléfono
              </label>
              <input
                type="tel"
                bind:value={form.contact_phone}
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="+52 123 456 7890"
              />
            </div>

            <!-- Dirección -->
            <div class="col-span-2 sm:col-span-1">
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Dirección
              </label>
              <input
                type="text"
                bind:value={form.address}
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Ciudad, Estado"
              />
            </div>

            <!-- Notas -->
            <div class="col-span-2">
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Notas / Descripción
              </label>
              <textarea
                bind:value={form.notes}
                rows="3"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                placeholder="Información adicional sobre el cliente..."
              ></textarea>
            </div>
          </div>

          <div class="flex justify-end gap-3 mt-6 pt-4 border-t">
            <button
              type="button"
              onclick={closeModal}
              class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-700"
            >
              Cancelar
            </button>
            <button
              type="submit"
              class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              {isEditing ? 'Actualizar' : 'Crear'} Cliente
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
{/if}

<!-- Delete Confirmation Modal -->
{#if showDeleteModal}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
      <h3 class="text-lg font-bold text-gray-900 mb-4">Confirmar Desactivación</h3>
      <p class="text-gray-600 mb-6">
        ¿Estás seguro de que deseas desactivar el cliente <strong>{tenantToDelete?.name}</strong>?
        Los usuarios de este cliente no podrán acceder al sistema.
      </p>
      <div class="flex justify-end gap-3">
        <button
          onclick={() => { showDeleteModal = false; tenantToDelete = null; }}
          class="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
        >
          Cancelar
        </button>
        <button
          onclick={handleDelete}
          class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
        >
          Desactivar
        </button>
      </div>
    </div>
  </div>
{/if}

<!-- ─── Users Management Modal ──────────────────────────────────────────── -->
{#if showUsersModal}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-lg shadow-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
      <div class="p-6">

        <!-- Header -->
        <div class="flex justify-between items-center mb-6">
          <div>
            <h2 class="text-xl font-bold text-gray-900">
              Usuarios — {selectedTenant?.name}
            </h2>
            <p class="text-sm text-gray-500">{selectedTenant?.subdomain}</p>
          </div>
          <div class="flex items-center gap-3">
            {#if !showUserForm}
              <button
                onclick={openCreateUserForm}
                class="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2 text-sm font-medium"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
                </svg>
                Nuevo Usuario
              </button>
            {/if}
            <button
              onclick={closeUsersModal}
              class="text-gray-400 hover:text-gray-600 p-1 rounded-lg hover:bg-gray-100"
              title="Cerrar"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>
        </div>

        <!-- Inline User Form -->
        {#if showUserForm}
          <form
            onsubmit={(e) => { e.preventDefault(); handleUserSubmit(); }}
            class="bg-gray-50 border border-gray-200 rounded-lg p-5 mb-6"
          >
            <h3 class="font-semibold text-gray-800 mb-4">
              {isEditingUser ? 'Editar Usuario' : 'Nuevo Usuario'}
            </h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">
                  Nombre completo *
                </label>
                <input
                  type="text"
                  bind:value={userForm.full_name}
                  required
                  placeholder="Ej: Juan Pérez"
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">
                  Correo electrónico *
                </label>
                <input
                  type="email"
                  bind:value={userForm.email}
                  required
                  placeholder="usuario@empresa.com"
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">
                  Contraseña {isEditingUser ? '(dejar vacío para no cambiar)' : '*'}
                </label>
                <input
                  type="password"
                  bind:value={userForm.password}
                  required={!isEditingUser}
                  placeholder={isEditingUser ? 'Sin cambios' : 'Mínimo 8 caracteres'}
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">
                  Nivel de seguridad
                </label>
                <select
                  bind:value={userForm.security_level_id}
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm bg-white"
                >
                  <option value={null}>— Sin nivel asignado —</option>
                  {#each securityLevels as level}
                    <option value={level.id}>{level.name}</option>
                  {/each}
                </select>
                {#if securityLevels.length === 0 && !loadingSecurityLevels}
                  <p class="text-xs text-amber-600 mt-1">
                    No hay niveles creados.
                    <a href="/admin/niveles" class="underline hover:text-amber-700">Crear niveles</a>
                  </p>
                {/if}
              </div>
              <div class="flex items-center gap-3 pt-6">
                <label class="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    bind:checked={userForm.is_active}
                    class="sr-only peer"
                  />
                  <div class="w-10 h-5 bg-gray-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-5 peer-checked:bg-blue-600 after:content-[''] after:absolute after:top-0.5 after:left-0.5 after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all"></div>
                </label>
                <span class="text-sm text-gray-700">
                  {userForm.is_active ? 'Usuario activo' : 'Usuario inactivo'}
                </span>
              </div>
            </div>

            <div class="flex justify-end gap-3 mt-5">
              <button
                type="button"
                onclick={() => showUserForm = false}
                class="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 text-sm"
              >
                Cancelar
              </button>
              <button
                type="submit"
                class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium"
              >
                {isEditingUser ? 'Actualizar' : 'Crear'} Usuario
              </button>
            </div>
          </form>
        {/if}

        <!-- Users Table -->
        {#if loadingUsers}
          <div class="flex justify-center py-10">
            <svg class="animate-spin h-8 w-8 text-blue-600" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
            </svg>
          </div>
        {:else if tenantUsers.length === 0}
          <div class="text-center py-10 text-gray-500">
            <svg class="mx-auto h-10 w-10 text-gray-300 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"/>
            </svg>
            <p class="text-sm font-medium">Sin usuarios registrados</p>
            <p class="text-xs mt-1">Crea el primer usuario para este cliente</p>
          </div>
        {:else}
          <div class="overflow-hidden rounded-lg border border-gray-200">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Usuario
                  </th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Nivel de seguridad
                  </th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Estado
                  </th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Creado
                  </th>
                  <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Acciones
                  </th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                {#each tenantUsers as user}
                  <tr class="hover:bg-gray-50 transition-colors">
                    <td class="px-4 py-3">
                      <div class="flex items-center gap-3">
                        <div class="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                          <span class="text-blue-700 text-xs font-bold">
                            {user.full_name?.charAt(0)?.toUpperCase() || '?'}
                          </span>
                        </div>
                        <div>
                          <div class="text-sm font-medium text-gray-900">{user.full_name}</div>
                          <div class="text-xs text-gray-500">{user.email}</div>
                        </div>
                      </div>
                    </td>
                    <td class="px-4 py-3">
                      {#if user.security_level_name}
                        <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200">
                          {user.security_level_name}
                        </span>
                      {:else}
                        <span class="text-xs text-gray-400">—</span>
                      {/if}
                    </td>
                    <td class="px-4 py-3">
                      {#if user.is_active}
                        <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          Activo
                        </span>
                      {:else}
                        <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                          Inactivo
                        </span>
                      {/if}
                    </td>
                    <td class="px-4 py-3 text-sm text-gray-500">
                      {new Date(user.created_at).toLocaleDateString('es-MX')}
                    </td>
                    <td class="px-4 py-3 text-right">
                      <button
                        onclick={() => openEditUserForm(user)}
                        class="text-blue-600 hover:text-blue-900 mr-3"
                        title="Editar usuario"
                      >
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                        </svg>
                      </button>
                      <button
                        onclick={() => toggleUserStatus(user)}
                        class={user.is_active
                          ? 'text-red-500 hover:text-red-700'
                          : 'text-green-600 hover:text-green-800'}
                        title={user.is_active ? 'Desactivar usuario' : 'Activar usuario'}
                      >
                        {#if user.is_active}
                          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636"/>
                          </svg>
                        {:else}
                          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                          </svg>
                        {/if}
                      </button>
                    </td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
          <p class="text-xs text-gray-400 mt-2 text-right">
            {tenantUsers.length} usuario{tenantUsers.length !== 1 ? 's' : ''} en este cliente
          </p>
        {/if}

      </div>
    </div>
  </div>
{/if}

<!-- ─── Companies Modal ──────────────────────────────────────────────────── -->
{#if showCompaniesModal}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-lg shadow-xl w-full max-w-5xl flex flex-col" style="max-height: 92vh;">

      <!-- Header -->
      <div class="border-b border-gray-200 px-6 py-4 flex-shrink-0">
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-3">
            <svg class="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
            </svg>
            <div>
              <h2 class="text-xl font-bold text-gray-900">Empresas — {selectedTenant?.name}</h2>
              <p class="text-sm text-gray-500">{selectedTenant?.subdomain}</p>
            </div>
          </div>
          <div class="flex items-center gap-3">
            <span class="text-xs font-medium text-gray-500 bg-gray-100 px-2.5 py-1 rounded-full">
              {tenantCompanies.length} empresa{tenantCompanies.length !== 1 ? 's' : ''}
            </span>
            <button onclick={closeCompaniesModal}
              class="text-gray-400 hover:text-gray-600 p-1 rounded-lg hover:bg-gray-100 transition-colors">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>
        </div>

        <!-- Tab bar -->
        <div class="flex gap-1">
          <button
            onclick={() => { companiesView = 'list'; showCompanyForm = false; }}
            class={companiesView === 'list'
              ? 'px-4 py-2 rounded-lg text-sm font-medium bg-blue-600 text-white transition-all'
              : 'px-4 py-2 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-100 transition-all'}
          >
            <span class="flex items-center gap-2">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16"/>
              </svg>
              Lista
            </span>
          </button>
          <button
            onclick={() => { if(companiesView !== 'form') openCompanyForm(); }}
            class={(companiesView === 'form' && !isEditingCompany)
              ? 'px-4 py-2 rounded-lg text-sm font-medium bg-blue-600 text-white transition-all'
              : 'px-4 py-2 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-100 transition-all'}
          >
            <span class="flex items-center gap-2">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
              </svg>
              Nueva Empresa
            </span>
          </button>
          {#if isEditingCompany}
            <button class="px-4 py-2 rounded-lg text-sm font-medium bg-blue-600 text-white">
              <span class="flex items-center gap-2">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                </svg>
                Editando empresa
              </span>
            </button>
          {/if}
          {#if companiesView === 'docs' && selectedCompanyForDocs}
            <button class="px-4 py-2 rounded-lg text-sm font-medium bg-blue-600 text-white">
              <span class="flex items-center gap-2">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                </svg>
                Documentos — {selectedCompanyForDocs.razon_social}
              </span>
            </button>
          {/if}
        </div>
      </div>

      <!-- Cuerpo scrollable -->
      <div class="flex-1 overflow-y-auto">

        <!-- ── Vista: Lista ── -->
        {#if companiesView === 'list'}
          <div class="p-6">
            {#if loadingCompanies}
              <div class="flex flex-col items-center justify-center py-16">
                <svg class="animate-spin h-8 w-8 text-gray-400 mb-3" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                </svg>
                <p class="text-sm text-gray-500">Cargando empresas...</p>
              </div>
            {:else if tenantCompanies.length === 0}
              <div class="flex flex-col items-center justify-center py-16 text-gray-400">
                <div class="w-16 h-16 bg-gray-100 rounded-xl flex items-center justify-center mb-4">
                  <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
                  </svg>
                </div>
                <p class="text-base font-semibold text-gray-500">Sin empresas registradas</p>
                <p class="text-sm text-gray-400 mt-1 mb-5">Usa la pestaña "Nueva Empresa" para agregar una</p>
                <button onclick={openCompanyForm}
                  class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium">
                  + Agregar primera empresa
                </button>
              </div>
            {:else}
              <div class="overflow-hidden rounded-lg border border-gray-200">
                <table class="min-w-full divide-y divide-gray-200">
                  <thead class="bg-gray-50">
                    <tr>
                      <th class="px-5 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Empresa / RFC</th>
                      <th class="px-5 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">RPU / Tipo</th>
                      <th class="px-5 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Ubicación</th>
                      <th class="px-5 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Demanda / Costo</th>
                      <th class="px-5 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
                      <th class="px-5 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
                    </tr>
                  </thead>
                  <tbody class="bg-white divide-y divide-gray-200">
                    {#each tenantCompanies as company}
                      <tr class="hover:bg-gray-50 transition-colors">
                        <td class="px-5 py-4">
                          <div class="flex items-start gap-3">
                            <div class="w-8 h-8 rounded-lg bg-gray-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                              <span class="text-gray-600 text-xs font-bold">
                                {company.razon_social?.charAt(0)?.toUpperCase() || '?'}
                              </span>
                            </div>
                            <div>
                              <div class="text-sm font-semibold text-gray-900">{company.razon_social}</div>
                              {#if company.nombre_comercial && company.nombre_comercial !== company.razon_social}
                                <div class="text-xs text-gray-500">{company.nombre_comercial}</div>
                              {/if}
                              <div class="text-xs font-mono text-gray-400 mt-0.5">RFC: {company.rfc}</div>
                            </div>
                          </div>
                        </td>
                        <td class="px-5 py-4">
                          {#if company.rpu}
                            <div class="text-xs font-mono text-gray-700 bg-gray-100 px-2 py-0.5 rounded inline-block mb-1">{company.rpu}</div>
                          {:else}
                            <div class="text-xs text-gray-300 italic mb-1">Sin RPU</div>
                          {/if}
                          <div class="flex flex-wrap gap-1">
                            <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-700">
                              {company.tipo_suministro}
                            </span>
                            {#if company.clasificacion}
                              <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-600">
                                {company.clasificacion}
                              </span>
                            {/if}
                          </div>
                        </td>
                        <td class="px-5 py-4 text-sm text-gray-600">
                          {#if company.ciudad || company.estado}
                            <div class="flex items-center gap-1.5">
                              <svg class="w-3.5 h-3.5 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/>
                              </svg>
                              {[company.ciudad, company.estado].filter(Boolean).join(', ')}
                            </div>
                          {:else}
                            <span class="text-gray-300">—</span>
                          {/if}
                        </td>
                        <td class="px-5 py-4 text-right">
                          {#if company.demanda_contratada_kw}
                            <div class="text-sm font-semibold text-gray-800">{company.demanda_contratada_kw.toLocaleString('es-MX')} <span class="text-xs font-normal text-gray-500">kW</span></div>
                          {/if}
                          {#if company.costo_mensual_aproximado}
                            <div class="text-xs text-green-600 font-medium mt-0.5">
                              ${company.costo_mensual_aproximado.toLocaleString('es-MX', {minimumFractionDigits: 0})}/mes
                            </div>
                          {/if}
                          {#if !company.demanda_contratada_kw && !company.costo_mensual_aproximado}
                            <span class="text-gray-300">—</span>
                          {/if}
                        </td>
                        <td class="px-5 py-4 text-center">
                          {#if company.is_active}
                            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">Activa</span>
                          {:else}
                            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">Inactiva</span>
                          {/if}
                        </td>
                        <td class="px-5 py-4 text-right">
                          <div class="flex items-center justify-end gap-3">
                            <button onclick={() => openDocsView(company)}
                              class="text-gray-500 hover:text-gray-800 text-xs font-medium flex items-center gap-1"
                              title="Ver documentos">
                              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                              </svg>
                              Docs
                            </button>
                            <button onclick={() => openEditCompanyForm(company)}
                              class="text-blue-600 hover:text-blue-900 text-xs font-medium">
                              Editar
                            </button>
                          </div>
                        </td>
                      </tr>
                    {/each}
                  </tbody>
                </table>
              </div>
            {/if}
          </div>

        <!-- ── Vista: Documentos ── -->
        {:else if companiesView === 'docs'}
          <div class="p-6">
            <div class="flex items-center justify-between mb-4">
              <div>
                <h3 class="text-base font-semibold text-gray-900">{selectedCompanyForDocs?.razon_social}</h3>
                <p class="text-sm text-gray-500">RFC: {selectedCompanyForDocs?.rfc}</p>
              </div>
              <button onclick={() => companiesView = 'list'}
                class="text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1.5">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
                </svg>
                Volver a lista
              </button>
            </div>

            {#if loadingDocs}
              <div class="flex justify-center py-12">
                <svg class="animate-spin h-8 w-8 text-gray-400" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                </svg>
              </div>
            {:else if companyDocs.length === 0}
              <div class="text-center py-14 text-gray-400">
                <div class="w-14 h-14 bg-gray-100 rounded-xl flex items-center justify-center mx-auto mb-3">
                  <svg class="w-7 h-7 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                  </svg>
                </div>
                <p class="text-sm font-medium text-gray-500">Sin documentos cargados</p>
                <p class="text-xs text-gray-400 mt-1">Este cliente aún no ha subido documentos para esta empresa</p>
              </div>
            {:else}
              <div class="overflow-hidden rounded-lg border border-gray-200">
                <table class="min-w-full divide-y divide-gray-200">
                  <thead class="bg-gray-50">
                    <tr>
                      <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Documento</th>
                      <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tipo</th>
                      <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tamaño</th>
                      <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Vigencia</th>
                      <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fecha subida</th>
                      <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
                    </tr>
                  </thead>
                  <tbody class="bg-white divide-y divide-gray-200">
                    {#each companyDocs as doc}
                      <tr class="hover:bg-gray-50 transition-colors">
                        <td class="px-4 py-3">
                          <div class="flex items-center gap-2.5">
                            <div class="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center flex-shrink-0">
                              {#if doc.mime_type?.includes('pdf')}
                                <svg class="w-4 h-4 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                                  <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clip-rule="evenodd"/>
                                </svg>
                              {:else if doc.mime_type?.includes('image')}
                                <svg class="w-4 h-4 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
                                  <path fill-rule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clip-rule="evenodd"/>
                                </svg>
                              {:else}
                                <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                                </svg>
                              {/if}
                            </div>
                            <div>
                              <div class="text-sm font-medium text-gray-900 max-w-xs truncate">{doc.nombre_original}</div>
                              {#if doc.descripcion}
                                <div class="text-xs text-gray-400">{doc.descripcion}</div>
                              {/if}
                            </div>
                          </div>
                        </td>
                        <td class="px-4 py-3">
                          <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-700">
                            {TIPO_LABELS[doc.tipo_documento] ?? doc.tipo_documento}
                          </span>
                        </td>
                        <td class="px-4 py-3 text-sm text-gray-500">{formatBytes(doc.tamano_bytes)}</td>
                        <td class="px-4 py-3 text-sm text-gray-500">
                          {#if doc.vigencia}
                            {new Date(doc.vigencia) < new Date()
                              ? `⚠️ ${new Date(doc.vigencia).toLocaleDateString('es-MX')}`
                              : new Date(doc.vigencia).toLocaleDateString('es-MX')}
                          {:else}
                            <span class="text-gray-300">—</span>
                          {/if}
                        </td>
                        <td class="px-4 py-3 text-sm text-gray-500">
                          {new Date(doc.created_at).toLocaleDateString('es-MX')}
                        </td>
                        <td class="px-4 py-3 text-right">
                          <div class="flex items-center justify-end gap-2">
                            <button onclick={() => viewDocument(doc)}
                              class="inline-flex items-center gap-1.5 text-xs font-medium text-green-600 hover:text-green-800">
                              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                              </svg>
                              Ver
                            </button>
                            <button onclick={() => downloadDocument(doc)}
                              class="inline-flex items-center gap-1.5 text-xs font-medium text-blue-600 hover:text-blue-800">
                              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
                              </svg>
                              Descargar
                            </button>
                          </div>
                        </td>
                      </tr>
                    {/each}
                  </tbody>
                </table>
              </div>
              <p class="text-xs text-gray-400 mt-2 text-right">
                {companyDocs.length} documento{companyDocs.length !== 1 ? 's' : ''}
              </p>
            {/if}
          </div>

        <!-- ── Vista: Formulario (crear / editar) ── -->
        {:else}
          <form onsubmit={(e) => { e.preventDefault(); handleCompanySubmit(); }} class="flex flex-col h-full">

            <!-- Sub-tabs del formulario -->
            <div class="border-b border-gray-200 px-6 bg-gray-50 flex-shrink-0">
              <div class="flex gap-0">
                {#each [
                  { id: 'general',   label: 'General',         icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' },
                  { id: 'contacto',  label: 'Contacto',        icon: 'M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z' },
                  { id: 'electrico', label: 'Datos Eléctricos', icon: 'M13 10V3L4 14h7v7l9-11h-7z' }
                ] as tab}
                  <button type="button"
                    onclick={() => companyFormTab = tab.id as any}
                    class="flex items-center gap-2 px-5 py-3 text-sm font-medium border-b-2 transition-colors -mb-px {companyFormTab === tab.id ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'}"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d={tab.icon}/>
                    </svg>
                    {tab.label}
                  </button>
                {/each}
              </div>
            </div>

            <!-- Contenido de sub-tabs -->
            <div class="flex-1 overflow-y-auto p-6">

              {#if companyFormTab === 'general'}
                <div class="space-y-5">
                  <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div class="md:col-span-2">
                      <label class="block text-sm font-medium text-gray-700 mb-1">Razón Social <span class="text-red-500">*</span></label>
                      <input type="text" bind:value={companyForm.razon_social} required
                        placeholder="Empresa Industrial S.A. de C.V."
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"/>
                    </div>
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">Nombre Comercial</label>
                      <input type="text" bind:value={companyForm.nombre_comercial}
                        placeholder="Nombre corto"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"/>
                    </div>
                  </div>

                  <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">RFC <span class="text-red-500">*</span></label>
                      <input type="text" bind:value={companyForm.rfc} required maxlength="13"
                        placeholder="EMP123456789"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm font-mono uppercase focus:ring-2 focus:ring-blue-500 focus:border-transparent"/>
                    </div>
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">RPU <span class="text-xs text-gray-400 font-normal">(opcional)</span></label>
                      <input type="text" bind:value={companyForm.rpu}
                        placeholder="001-000-000000000"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm font-mono focus:ring-2 focus:ring-blue-500 focus:border-transparent"/>
                    </div>
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">Tipo Suministro <span class="text-red-500">*</span></label>
                      <select bind:value={companyForm.tipo_suministro} required
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white">
                        <option value="GDMTH">GDMTH — Gran Demanda Media Tensión Horaria</option>
                        <option value="GDMTO">GDMTO — Gran Demanda Media Tensión Ordinaria</option>
                        <option value="GDBT">GDBT — Gran Demanda Baja Tensión</option>
                        <option value="DIST">DIST — Distribución</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Tensión de Suministro</label>
                    <input type="text" bind:value={companyForm.tension_suministro}
                      placeholder="ej. 13.8 kV"
                      class="w-full max-w-xs px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"/>
                  </div>
                </div>

              {:else if companyFormTab === 'contacto'}
                <div class="space-y-5">
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">Teléfono</label>
                      <input type="text" bind:value={companyForm.telefono}
                        placeholder="55 1234 5678"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"/>
                    </div>
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">Correo electrónico</label>
                      <input type="email" bind:value={companyForm.email}
                        placeholder="contacto@empresa.com"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"/>
                    </div>
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Dirección</label>
                    <input type="text" bind:value={companyForm.direccion}
                      placeholder="Calle, número, colonia"
                      class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"/>
                  </div>
                  <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">Ciudad</label>
                      <input type="text" bind:value={companyForm.ciudad}
                        placeholder="Ciudad de México"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"/>
                    </div>
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">Estado</label>
                      <input type="text" bind:value={companyForm.estado}
                        placeholder="CDMX"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"/>
                    </div>
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">Código Postal</label>
                      <input type="text" bind:value={companyForm.codigo_postal} maxlength="5"
                        placeholder="06600"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"/>
                    </div>
                  </div>
                </div>

              {:else}
                <!-- Datos Eléctricos -->
                <div class="space-y-5">
                  <div class="bg-gray-50 border border-gray-200 rounded-lg p-4 text-sm text-gray-600">
                    💡 La clasificación (Micro / Pequeña / Mediana / Grande) se calcula automáticamente según la demanda contratada.
                  </div>
                  <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">Demanda Contratada (kW)</label>
                      <input type="number" bind:value={companyForm.demanda_contratada_kw} min="0" step="0.1"
                        placeholder="500"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"/>
                    </div>
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">Consumo Mensual (kWh)</label>
                      <input type="number" bind:value={companyForm.consumo_mensual_kwh} min="0"
                        placeholder="150000"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"/>
                    </div>
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">Costo Mensual Aprox. ($)</label>
                      <input type="number" bind:value={companyForm.costo_mensual_aproximado} min="0"
                        placeholder="280000"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"/>
                    </div>
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Notas</label>
                    <textarea bind:value={companyForm.notas} rows="3"
                      placeholder="Observaciones adicionales sobre la instalación eléctrica..."
                      class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"></textarea>
                  </div>
                </div>
              {/if}

            </div>

            <!-- Footer del formulario -->
            <div class="border-t border-gray-200 px-6 py-4 flex items-center justify-between flex-shrink-0">
              <div class="flex items-center gap-2">
                {#if companyFormTab !== 'general'}
                  <button type="button"
                    onclick={() => companyFormTab = companyFormTab === 'electrico' ? 'contacto' : 'general'}
                    class="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 flex items-center gap-1.5">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
                    </svg>
                    Anterior
                  </button>
                {/if}
                {#if companyFormTab !== 'electrico'}
                  <button type="button"
                    onclick={() => companyFormTab = companyFormTab === 'general' ? 'contacto' : 'electrico'}
                    class="px-4 py-2 text-sm text-gray-700 hover:text-gray-900 flex items-center gap-1.5 font-medium">
                    Siguiente
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                    </svg>
                  </button>
                {/if}
              </div>
              <div class="flex items-center gap-3">
                <button type="button"
                  onclick={() => { companiesView = 'list'; isEditingCompany = false; currentCompanyId = null; }}
                  class="px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50">
                  Cancelar
                </button>
                <button type="submit"
                  class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium flex items-center gap-2">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                  </svg>
                  {isEditingCompany ? 'Guardar cambios' : 'Crear empresa'}
                </button>
              </div>
            </div>

          </form>
        {/if}

      </div>
    </div>
  </div>
{/if}

<!-- Modal: Visor de documentos -->
{#if showDocViewerModal && viewingDocUrl}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-lg w-full max-w-5xl max-h-[90vh] flex flex-col">
      <!-- Header -->
      <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between bg-gray-50">
        <div class="flex items-center gap-3">
          <svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
          </svg>
          <div>
            <h3 class="text-lg font-semibold text-gray-900">{viewingDocName}</h3>
            <p class="text-xs text-gray-500">{viewingDocType}</p>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <a href={viewingDocUrl} target="_blank" 
            class="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
            title="Abrir en nueva pestaña">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/>
            </svg>
          </a>
          <button onclick={() => { showDocViewerModal = false; viewingDocUrl = null; }}
            class="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded transition-colors">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
      </div>
      
      <!-- Viewer content -->
      <div class="flex-1 overflow-auto bg-gray-100">
        {#if viewingDocType.includes('pdf')}
          <iframe src={viewingDocUrl} class="w-full h-full min-h-[600px]" title={viewingDocName}></iframe>
        {:else if viewingDocType.includes('image')}
          <div class="flex items-center justify-center p-8 h-full">
            <img src={viewingDocUrl} alt={viewingDocName} class="max-w-full max-h-full object-contain rounded shadow-lg"/>
          </div>
        {:else}
          <div class="flex flex-col items-center justify-center p-12 h-full">
            <svg class="w-16 h-16 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
            </svg>
            <p class="text-gray-600 font-medium mb-2">Vista previa no disponible</p>
            <p class="text-sm text-gray-500 mb-4">Este tipo de archivo no se puede previsualizar en el navegador</p>
            <a href={viewingDocUrl} target="_blank"
              class="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
              </svg>
              Descargar archivo
            </a>
          </div>
        {/if}
      </div>
    </div>
  </div>
{/if}
