<script lang="ts">
	import { onMount } from 'svelte';
        import { authStore } from '../stores/auth';
		return localStorage.getItem('access_token') || '';
	}

	interface Company {
		id: number;
		razon_social: string;
		nombre_comercial?: string;
		rfc?: string;
		clasificacion?: string;
		tipo_suministro?: string;
		is_active: boolean;
	}

	interface Project {
		id: number;
		name: string;
		company_name: string;
		company_id: number;
		project_type: string;
		status: string;
		priority?: string;
		start_date?: string;
		due_date?: string;
		total_tasks: number;
		completed_tasks: number;
		progress_percentage: number;
	}

	interface Task {
		id: number;
		code?: string;
		title: string;
		description?: string;
		notes?: string;
		task_type: string;
		status: string;
		assignee_name?: string;
		due_date?: string;
		evidence_count: number;
		progress_percentage: number;
	}

	interface Evidence {
		id: number;
		evidence_type: string;
		filename: string;
		file_url?: string;
		comment?: string;
		uploader_name?: string;
		uploaded_at: string;
		size_bytes?: number;
		mime_type?: string;
	}

	interface Obligation {
		id: number;
		codigo: string;
		nombre: string;
		descripcion: string;
		estado_aplicabilidad: string;
		notas: string;
	}

	interface ProjectDetail {
		id: number;
		company_id: number;
		company_name: string;
		name: string;
		description?: string;
		project_type: string;
		status: string;
		priority?: string;
		start_date?: string;
		due_date?: string;
		created_at?: string;
		completed_at?: string;
		tasks: Task[];
		total_tasks: number;
		completed_tasks: number;
		progress_percentage: number;
	}

	let projects = $state<Project[]>([]);
	let companies = $state<Company[]>([]);
	let selectedProject = $state<ProjectDetail | null>(null);
	let loading = $state(true);
	let error = $state('');
	let modalError = $state('');
	let savingProject = $state(false);
	let searchInput = $state<HTMLInputElement | null>(null);

	// Search & pagination
	let searchTerm = $state('');
	let currentPage = $state(1);
	const pageSize = 10;
	
	// Modals
	let showCreateModal = $state(false);
	let showDetailModal = $state(false);
	let showTaskModal = $state(false);
	let showEvidenceModal = $state(false);

	// Task modal tabs
	let taskModalTab = $state<'obligations' | 'custom'>('obligations');
	let availableObligations = $state<Obligation[]>([]);
	let loadingObligations = $state(false);
	let selectedObligationIds = $state<Set<number>>(new Set());
	let obligationSearchFilter = $state('');
	let obligationsClassified = $state(true);
	let obligationAdditionalContextById = $state<Record<number, string>>({});
	let obligationEvidenceFilesById = $state<Record<number, File[]>>({});
	let customTaskFiles = $state<FileList | null>(null);
	let customTaskEvidenceComment = $state('');

	// View evidences modal
	let showViewEvidencesModal = $state(false);
	let taskEvidences = $state<Evidence[]>([]);
	let loadingEvidences = $state(false);
	let previewEvidence = $state<Evidence | null>(null);

	// Report
	let showReportModal = $state(false);
	let reportDate = $state('');
	let reportEvidences = $state<Record<number, Evidence[]>>({});
	let reportLoadingEvidences = $state(false);
	
	// Filters
	let filterCompany = $state('');
	let filterStatus = $state('');
	let filterType = $state('');
	
	// Form data
	let formData = $state({
		company_id: 0,
		name: '',
		description: '',
		project_type: 'AUDITORIA',
		priority: 'MEDIA',
		start_date: '',
		due_date: '',
		include_all_obligations: false
	});

	let taskFormData = $state({
		title: '',
		description: '',
		due_date: '',
		assignee_user_id: null as number | null
	});

	let selectedTask = $state<Task | null>(null);
	let evidenceFile = $state<File | null>(null);
	let evidenceType = $state('FOTO');
	let evidenceComment = $state('');
	let uploadingEvidence = $state(false);
	let deletingEvidenceId = $state<number | null>(null);
	let confirmingDeleteId = $state<number | null>(null);

	const projectTypeLabels: Record<string, string> = {
		AUDITORIA: 'Auditoría',
		CORRECTIVO: 'Correctivo',
		MANTENIMIENTO: 'Mantenimiento',
		REVISION_RUTINA: 'Revisión de Rutina',
		TC: 'Transformadores Cambio'
	};

	const statusLabels: Record<string, string> = {
		ABIERTO: 'Abierto',
		EN_PROGRESO: 'En Progreso',
		COMPLETADO: 'Completado',
		CERRADO: 'Cerrado',
		NO_INICIADO: 'No Iniciado'
	};

	const priorityLabels: Record<string, string> = {
		BAJA: 'Baja',
		MEDIA: 'Media',
		ALTA: 'Alta',
		CRITICA: 'Crítica'
	};

	const evidenceTypeLabels: Record<string, string> = {
		MEDICION: 'Medición',
		FOTO: 'Fotografía',
		INFORME: 'Informe',
		BITACORA: 'Bitácora',
		DICTAMEN: 'Dictamen',
		MANUAL: 'Manual',
		OTRO: 'Otro'
	};

	async function loadProjects() {
		try {
			loading = true;
			const response = await authStore.fetch(
				`${import.meta.env.VITE_API_BASE_URL}/api/v1/projects/`,
				{ headers: { Authorization: `Bearer ${getToken()}` } }
			);
			if (!response.ok) throw new Error('Error al cargar proyectos');
			const data = await response.json();
			projects = Array.isArray(data) ? data : (data.projects ?? data.items ?? []);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Error desconocido';
		} finally {
			loading = false;
		}
	}

	async function loadCompanies() {
		try {
			const response = await authStore.fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/companies/?page=1&page_size=100`, {
				headers: { Authorization: `Bearer ${getToken()}` }
			});
			
			if (!response.ok) throw new Error('Error al cargar empresas');
			const data = await response.json();
			// El endpoint devuelve { total, companies: [...] }
			companies = Array.isArray(data) ? data : (data.companies ?? data.items ?? []);
		} catch (err) {
			console.error('Error al cargar empresas:', err);
		}
	}

	async function createProject() {
		modalError = '';
		if (!formData.company_id || formData.company_id === 0) {
			modalError = 'Seleccione una empresa';
			return;
		}
		if (!formData.name.trim()) {
			modalError = 'El nombre del proyecto es requerido';
			return;
		}
		try {
			savingProject = true;
			const payload = {
				...formData,
				start_date: formData.start_date || null,
				due_date: formData.due_date || null
			};
			const response = await authStore.fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/projects/`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					Authorization: `Bearer ${getToken()}`
				},
				body: JSON.stringify(payload)
			});
			if (!response.ok) {
				const data = await response.json();
				if (Array.isArray(data.detail)) {
					modalError = data.detail.map((e: any) => {
						const field = e.loc?.[e.loc.length - 1] ?? '';
						return field ? `${field}: ${e.msg}` : e.msg;
					}).join(' · ');
				} else {
					modalError = data.detail || 'Error al crear proyecto';
				}
				return;
			}
			showCreateModal = false;
			resetForm();
			await loadProjects();
		} catch (err) {
			modalError = err instanceof Error ? err.message : 'Error desconocido';
		} finally {
			savingProject = false;
		}
	}

	async function loadProjectDetail(projectId: number) {
		try {
			const response = await authStore.fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/projects/${projectId}`, {
				headers: { Authorization: `Bearer ${getToken()}` }
			});
			if (!response.ok) throw new Error('Error al cargar detalle');
			selectedProject = await response.json();
			showDetailModal = true;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Error desconocido';
		}
	}

	async function updateTaskStatus(taskId: number, newStatus: string) {
		try {
			const response = await authStore.fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/projects/tasks/${taskId}`, {
				method: 'PUT',
				headers: {
					'Content-Type': 'application/json',
					Authorization: `Bearer ${getToken()}`
				},
				body: JSON.stringify({ status: newStatus })
			});

			if (!response.ok) throw new Error('Error al actualizar tarea');

			// Refresh modal detail + background-refresh the table
			if (selectedProject) {
				await loadProjectDetail(selectedProject.id);
				loadProjects(); // no await — updates table counts silently
			}
		} catch (err) {
			error = err instanceof Error ? err.message : 'Error desconocido';
		}
	}

	async function addCustomTask() {
		if (!selectedProject) return;

		try {
			const response = await authStore.fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/projects/${selectedProject.id}/tasks`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					Authorization: `Bearer ${getToken()}`
				},
				body: JSON.stringify(taskFormData)
			});

			if (!response.ok) throw new Error('Error al agregar tarea');
			const createdTask = await response.json();
			// Subir fotos adjuntas como evidencias de la nueva tarea
			if (customTaskFiles && customTaskFiles.length > 0) {
				for (const file of Array.from(customTaskFiles)) {
					const formData = new FormData();
					formData.append('file', file);
					formData.append('evidence_type', 'FOTO');
					if (customTaskEvidenceComment) {
						formData.append('comment', customTaskEvidenceComment);
					}
					const evResponse = await authStore.fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/projects/tasks/${createdTask.id}/evidences`, {
						method: 'POST',
						headers: {
							Authorization: `Bearer ${getToken()}`
						},
						body: formData
					});
					// Si alguna evidencia falla, lo registramos pero no rompemos todo el flujo
					if (!evResponse.ok) {
						console.error('Error al subir evidencia de tarea custom');
					}
				}
			}
			
			showTaskModal = false;
			taskFormData = { title: '', description: '', due_date: '', assignee_user_id: null };
			customTaskFiles = null;
			customTaskEvidenceComment = '';
			await loadProjectDetail(selectedProject.id);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Error desconocido';
		}
	}

	async function loadAvailableObligations() {
		if (!selectedProject) return;
		try {
			loadingObligations = true;
			const response = await authStore.fetch(
				`${import.meta.env.VITE_API_BASE_URL}/api/v1/projects/${selectedProject.id}/available-obligations`,
				{ headers: { Authorization: `Bearer ${getToken()}` } }
			);
			if (!response.ok) throw new Error('Error al cargar obligaciones');
			const data = await response.json();
			availableObligations = data.obligations ?? [];
			obligationsClassified = data.classified ?? true;
		} catch (err) {
			console.error('Error cargando obligaciones:', err);
			availableObligations = [];
		} finally {
			loadingObligations = false;
		}
	}

	async function addObligationTasks() {
		if (!selectedProject || selectedObligationIds.size === 0) return;
		try {
			const promises = Array.from(selectedObligationIds).map(async reqId => {
				const obl = availableObligations.find(o => o.id === reqId);
				const extra = obligationAdditionalContextById[reqId] ?? '';
				const baseDescription = obl?.descripcion ?? '';
				const files = obligationEvidenceFilesById[reqId] ?? [];
				const taskRes = await authStore.fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/projects/${selectedProject!.id}/tasks`, {
					method: 'POST',
					headers: {
						'Content-Type': 'application/json',
						Authorization: `Bearer ${getToken()}`
					},
					body: JSON.stringify({
						title: obl?.nombre ?? '',
						description: baseDescription || undefined,
						notes: extra || undefined,
						requirement_id: reqId,
						task_type: 'OBLIGATION'
					})
				});
				if (!taskRes.ok) throw new Error('Error al crear tarea');
				const createdTask = await taskRes.json();
				// Subir fotos de esta obligación como evidencias iniciales de esta tarea
				if (files.length > 0) {
					for (const file of files) {
						const formData = new FormData();
						formData.append('file', file);
						formData.append('evidence_type', 'FOTO');
						if (extra) {
							formData.append('comment', extra);
						}
						const evRes = await authStore.fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/projects/tasks/${createdTask.id}/evidences`, {
							method: 'POST',
							headers: {
								Authorization: `Bearer ${getToken()}`
							},
							body: formData
						});
						if (!evRes.ok) {
							console.error('Error al subir evidencia para tarea desde obligación');
						}
					}
				}
			});
			await Promise.all(promises);
			showTaskModal = false;
			selectedObligationIds = new Set();
			obligationAdditionalContextById = {};
			obligationEvidenceFilesById = {};
			await loadProjectDetail(selectedProject.id);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Error desconocido';
		}
	}

	function openTaskModal() {
		taskModalTab = 'obligations';
		selectedObligationIds = new Set();
		obligationSearchFilter = '';
		showTaskModal = true;
		loadAvailableObligations();
	}

	async function updateTaskProgress(taskId: number, progress: number) {
		if (progress < 0 || progress > 100) return;
		try {
			await authStore.fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/projects/tasks/${taskId}`, {
				method: 'PUT',
				headers: {
					'Content-Type': 'application/json',
					Authorization: `Bearer ${getToken()}`
				},
				body: JSON.stringify({ progress_percentage: progress })
			});
			if (selectedProject) {
				await loadProjectDetail(selectedProject.id);
				loadProjects(); // no await — updates table counts silently
			}
		} catch (err) {
			error = err instanceof Error ? err.message : 'Error desconocido';
		}
	}

	async function viewTaskEvidences(task: Task) {
		selectedTask = task;
		showViewEvidencesModal = true;
		loadingEvidences = true;
		taskEvidences = [];
		try {
			const response = await authStore.fetch(
				`${import.meta.env.VITE_API_BASE_URL}/api/v1/projects/tasks/${task.id}/evidences`,
				{ headers: { Authorization: `Bearer ${getToken()}` } }
			);
			if (!response.ok) throw new Error('Error al cargar evidencias');
			taskEvidences = await response.json();
		} catch (err) {
			console.error(err);
		} finally {
			loadingEvidences = false;
		}
	}

	function formatFileSize(bytes?: number): string {
		if (!bytes) return '';
		if (bytes < 1024) return `${bytes} B`;
		if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
		return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
	}

	function canPreview(evidence: Evidence): boolean {
		if (!evidence.mime_type) return false;
		return (
			evidence.mime_type.startsWith('image/') ||
			evidence.mime_type === 'application/pdf' ||
			evidence.mime_type.startsWith('video/')
		);
	}

	async function uploadEvidence() {
		if (!selectedTask || !evidenceFile || uploadingEvidence) return;

		uploadingEvidence = true;
		try {
			const formData = new FormData();
			formData.append('file', evidenceFile);
			formData.append('evidence_type', evidenceType);
			if (evidenceComment) formData.append('comment', evidenceComment);

			const response = await authStore.fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/projects/tasks/${selectedTask.id}/evidences`, {
				method: 'POST',
				headers: {
					Authorization: `Bearer ${getToken()}`
				},
				body: formData
			});

			if (!response.ok) throw new Error('Error al subir evidencia');
			
			showEvidenceModal = false;
			evidenceFile = null;
			evidenceComment = '';
			if (selectedProject) {
				await loadProjectDetail(selectedProject.id);
			}
		} catch (err) {
			error = err instanceof Error ? err.message : 'Error desconocido';
		} finally {
			uploadingEvidence = false;
		}
	}

	async function deleteEvidence(evidenceId: number) {
		if (deletingEvidenceId !== null) return;

		deletingEvidenceId = evidenceId;
		confirmingDeleteId = null;
		try {
			const response = await authStore.fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/projects/evidences/${evidenceId}`, {
				method: 'DELETE',
				headers: {
					Authorization: `Bearer ${getToken()}`
				}
			});

			if (!response.ok) {
				let msg = `Error ${response.status}`;
				try {
					const errData = await response.json();
					msg = errData.detail || msg;
				} catch { /* body vacío (204 sin body en error) */ }
				console.error('[deleteEvidence] HTTP', response.status, msg);
				throw new Error(msg);
			}

			// Recargar evidencias y detalle
			if (selectedTask) await viewTaskEvidences(selectedTask);
			if (selectedProject) await loadProjectDetail(selectedProject.id);
		} catch (err) {
			const msg = err instanceof Error ? err.message : 'Error desconocido';
			console.error('[deleteEvidence] catch:', msg);
			alert(`No se pudo eliminar la evidencia: ${msg}`);
		} finally {
			deletingEvidenceId = null;
		}
	}

	function resetForm() {
		formData = {
			company_id: 0,
			name: '',
			description: '',
			project_type: 'AUDITORIA',
			priority: 'MEDIA',
			start_date: '',
			due_date: '',
			include_all_obligations: false
		};
	}

	function openCreateModal() {
		resetForm();
		modalError = '';
		showCreateModal = true;
	}

	function openEvidenceModal(task: Task) {
		selectedTask = task;
		showEvidenceModal = true;
	}

	function getStatusColor(status: string): string {
		const colors: Record<string, string> = {
			ABIERTO: 'bg-blue-100 text-blue-800',
			EN_PROGRESO: 'bg-yellow-100 text-yellow-800',
			COMPLETADO: 'bg-green-100 text-green-800',
			CERRADO: 'bg-gray-100 text-gray-800',
			NO_INICIADO: 'bg-gray-100 text-gray-600'
		};
		return colors[status] || 'bg-gray-100 text-gray-800';
	}

	function getPriorityColor(priority?: string): string {
		if (!priority) return 'bg-gray-100 text-gray-800';
		const colors: Record<string, string> = {
			BAJA: 'bg-blue-100 text-blue-800',
			MEDIA: 'bg-yellow-100 text-yellow-800',
			ALTA: 'bg-orange-100 text-orange-800',
			CRITICA: 'bg-red-100 text-red-800'
		};
		return colors[priority] || 'bg-gray-100 text-gray-800';
	}

	function formatDate(dateString?: string): string {
		if (!dateString) return '-';
		return new Date(dateString).toLocaleDateString('es-MX');
	}

	function printReport() {
		window.print();
	}

	function openReport() {
		reportDate = new Date().toLocaleString('es-MX', {
			year: 'numeric', month: 'long', day: 'numeric',
			hour: '2-digit', minute: '2-digit'
		});
		showReportModal = true;
	}

	async function loadAndReport(projectId: number) {
		// Ensure detail (with metrics) is loaded before opening the report
		await loadProjectDetail(projectId);
		// Load evidences for all tasks in parallel
		reportEvidences = {};
		if (selectedProject && selectedProject.tasks.length > 0) {
			reportLoadingEvidences = true;
			try {
				const evMap: Record<number, Evidence[]> = {};
				await Promise.all(
					selectedProject.tasks.map(async (task) => {
						try {
							const res = await authStore.fetch(
								`${import.meta.env.VITE_API_BASE_URL}/api/v1/projects/tasks/${task.id}/evidences`,
								{ headers: { Authorization: `Bearer ${getToken()}` } }
							);
							if (res.ok) evMap[task.id] = await res.json();
						} catch { /* ignore per-task failure */ }
					})
				);
				reportEvidences = evMap;
			} finally {
				reportLoadingEvidences = false;
			}
		}
		openReport();
	}

	function reportStatusStyle(status: string): string {
		const map: Record<string, string> = {
			COMPLETADO:  'background:#dcfce7;color:#166534;border:1px solid #bbf7d0;',
			EN_PROGRESO: 'background:#fef9c3;color:#854d0e;border:1px solid #fde68a;',
			ABIERTO:     'background:#dbeafe;color:#1e40af;border:1px solid #bfdbfe;',
			CERRADO:     'background:#f3f4f6;color:#374151;border:1px solid #e5e7eb;',
			NO_INICIADO: 'background:#f3f4f6;color:#374151;border:1px solid #e5e7eb;',
		};
		return map[status] ?? 'background:#f3f4f6;color:#374151;border:1px solid #e5e7eb;';
	}

	function reportPriorityStyle(priority: string): string {
		const map: Record<string, string> = {
			CRITICA: 'background:#fee2e2;color:#991b1b;border:1px solid #fecaca;',
			ALTA:    'background:#ffedd5;color:#9a3412;border:1px solid #fed7aa;',
			MEDIA:   'background:#fef9c3;color:#854d0e;border:1px solid #fde68a;',
			BAJA:    'background:#f0fdf4;color:#166534;border:1px solid #bbf7d0;',
		};
		return map[priority] ?? 'background:#f3f4f6;color:#374151;border:1px solid #e5e7eb;';
	}

	function normalizeStr(s: string): string {
		return s.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
	}

	const filteredProjects = $derived.by(() => {
		const term = normalizeStr(searchTerm.trim());
		return projects.filter(p => {
			const matchesCompany = !filterCompany || String(p.company_id) === String(filterCompany);
			const matchesStatus  = !filterStatus  || p.status === filterStatus;
			const matchesType    = !filterType    || p.project_type === filterType;
			const matchesSearch  = !term ||
				normalizeStr(p.name).includes(term) ||
				normalizeStr(p.company_name).includes(term);
			return matchesCompany && matchesStatus && matchesType && matchesSearch;
		});
	});

	const totalFiltered = $derived(filteredProjects.length);
	const totalPages    = $derived(Math.ceil(totalFiltered / pageSize));
	const pagedProjects = $derived(
		filteredProjects.slice((currentPage - 1) * pageSize, currentPage * pageSize)
	);

	// Reset to page 1 when any filter/search changes
	$effect(() => {
		searchTerm; filterCompany; filterStatus; filterType;
		currentPage = 1;
	});

	onMount(() => {
		loadProjects();
		loadCompanies();
		setTimeout(() => searchInput?.focus(), 100);
	});
</script>

<div class="p-6">
	<div class="flex justify-between items-center mb-6">
		<h1 class="text-3xl font-bold text-gray-900">Proyectos</h1>
		<button
			onclick={() => openCreateModal()}
			class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
		>
			+ Nuevo Proyecto
		</button>
	</div>

	{#if error}
		<div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
			{error}
			<button onclick={() => error = ''} class="float-right font-bold">×</button>
		</div>
	{/if}

	<!-- Search bar (like Mis Empresas) -->
	<div class="bg-white rounded-lg shadow p-4 mb-4">
		<label class="block text-sm font-medium text-gray-700 mb-2">Buscar</label>
		<div class="relative">
			<svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0"/>
			</svg>
			<input
				bind:this={searchInput}
				type="text"
				bind:value={searchTerm}
				placeholder="Nombre del proyecto, empresa... (tiempo real)"
				class="w-full pl-9 pr-9 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
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

	<!-- Filters -->
	<div class="bg-white p-4 rounded-lg shadow mb-6">
		<div class="grid grid-cols-1 md:grid-cols-3 gap-4">
			<div>
				<label class="block text-sm font-medium text-gray-700 mb-1">Empresa</label>
				<select bind:value={filterCompany} class="w-full border border-gray-300 rounded-lg px-3 py-2">
					<option value="">Todas</option>
					{#each companies as company}
						<option value={company.id}>{company.razon_social}</option>
					{/each}
				</select>
			</div>
			<div>
				<label class="block text-sm font-medium text-gray-700 mb-1">Estado</label>
				<select bind:value={filterStatus} class="w-full border border-gray-300 rounded-lg px-3 py-2">
					<option value="">Todos</option>
					<option value="ABIERTO">Abierto</option>
					<option value="EN_PROGRESO">En Progreso</option>
					<option value="COMPLETADO">Completado</option>
					<option value="CERRADO">Cerrado</option>
				</select>
			</div>
			<div>
				<label class="block text-sm font-medium text-gray-700 mb-1">Tipo</label>
				<select bind:value={filterType} class="w-full border border-gray-300 rounded-lg px-3 py-2">
					<option value="">Todos</option>
					{#each Object.entries(projectTypeLabels) as [value, label]}
						<option value={value}>{label}</option>
					{/each}
				</select>
			</div>
		</div>
	</div>

	<!-- Projects Table -->
	{#if loading}
		<div class="bg-white rounded-lg shadow p-6">
			<div class="animate-pulse space-y-4">
				{#each Array(5) as _}
					<div class="h-16 bg-gray-200 rounded"></div>
				{/each}
			</div>
		</div>
	{:else if projects.length === 0}
		<div class="bg-white rounded-lg shadow p-12 text-center">
			<svg class="w-16 h-16 mx-auto text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
			</svg>
			<p class="text-gray-500 text-lg mb-4">No hay proyectos registrados</p>
			<button onclick={() => openCreateModal()} class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg">Crear el primer proyecto</button>
		</div>
	{:else if filteredProjects.length === 0}
		<div class="bg-white rounded-lg shadow p-10 text-center">
			<svg class="w-12 h-12 mx-auto text-gray-300 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0"/>
			</svg>
			<p class="text-gray-500">Sin resultados para los filtros aplicados</p>
			<button onclick={() => { searchTerm = ''; filterCompany = ''; filterStatus = ''; filterType = ''; }} class="mt-3 text-sm text-blue-600 hover:underline">Limpiar filtros</button>
		</div>
	{:else}
		<!-- Desktop table -->
		<div class="hidden md:block bg-white rounded-lg shadow overflow-hidden">
			<div class="overflow-x-auto">
				<table class="min-w-full divide-y divide-gray-200">
					<thead class="bg-gray-50">
						<tr>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nombre</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Empresa</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tipo</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Prioridad</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tareas</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Vencimiento</th>
							<th class="sticky right-0 z-10 bg-gray-50 px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider shadow-[-4px_0_6px_-1px_rgba(0,0,0,0.08)]">Acciones</th>
						</tr>
					</thead>
					<tbody class="bg-white divide-y divide-gray-200">
						{#each pagedProjects as project (project.id)}
							<tr class="hover:bg-gray-50 group">
								<td class="px-6 py-4 whitespace-nowrap">
									<div class="text-sm font-medium text-gray-900">{project.name}</div>
								</td>
								<td class="px-6 py-4 whitespace-nowrap">
									<div class="text-sm text-gray-600">{project.company_name}</div>
								</td>
								<td class="px-6 py-4 whitespace-nowrap">
									<span class="text-sm text-gray-600">{projectTypeLabels[project.project_type] ?? project.project_type}</span>
								</td>
								<td class="px-6 py-4 whitespace-nowrap">
									<span class="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full {getStatusColor(project.status)}">
										{statusLabels[project.status] ?? project.status}
									</span>
								</td>
								<td class="px-6 py-4 whitespace-nowrap">
									{#if project.priority}
										<span class="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full {getPriorityColor(project.priority)}">
											{priorityLabels[project.priority] ?? project.priority}
										</span>
									{:else}
										<span class="text-sm text-gray-400">—</span>
									{/if}
								</td>
								<td class="px-6 py-4 whitespace-nowrap">
									<div class="text-sm">
										<span class="text-green-600 font-semibold">{project.completed_tasks}</span>
										<span class="text-gray-400">/</span>
										<span class="text-gray-600">{project.total_tasks}</span>
									</div>
								</td>
								<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
									{formatDate(project.due_date)}
								</td>
								<td class="sticky right-0 z-10 bg-white group-hover:bg-gray-50 px-4 py-4 whitespace-nowrap text-sm shadow-[-4px_0_6px_-1px_rgba(0,0,0,0.08)] transition-colors">
									<div class="flex items-center gap-1">
										<button
											onclick={() => loadProjectDetail(project.id)}
											title="Ver detalle"
											class="p-2 rounded-lg text-blue-600 hover:bg-blue-50 hover:text-blue-800 transition-colors"
										>
											<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
											</svg>
										</button>
										<button
											onclick={() => loadAndReport(project.id)}
											title="Generar reporte"
											class="p-2 rounded-lg text-indigo-600 hover:bg-indigo-50 hover:text-indigo-800 transition-colors"
										>
											<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
											</svg>
										</button>
									</div>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</div>

		<!-- Mobile cards -->
		<div class="md:hidden space-y-3">
			{#each pagedProjects as project (project.id)}
				<div class="bg-white rounded-lg shadow p-4">
					<div class="flex justify-between items-start mb-2">
						<div class="flex-1 min-w-0 pr-2">
							<h3 class="font-semibold text-gray-900 text-sm truncate">{project.name}</h3>
							<p class="text-xs text-gray-500 mt-0.5 truncate">{project.company_name}</p>
						</div>
						<span class="px-2 py-1 text-xs font-semibold rounded-full flex-shrink-0 {getStatusColor(project.status)}">
							{statusLabels[project.status] ?? project.status}
						</span>
					</div>
					<div class="flex flex-wrap gap-2 mt-2 mb-3">
						<span class="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">{projectTypeLabels[project.project_type] ?? project.project_type}</span>
						{#if project.priority}
							<span class="text-xs font-semibold px-2 py-1 rounded-full {getPriorityColor(project.priority)}">{priorityLabels[project.priority] ?? project.priority}</span>
						{/if}
						<span class="text-xs text-gray-500">Tareas: <strong class="text-green-600">{project.completed_tasks}</strong>/{project.total_tasks}</span>
						{#if project.due_date}
							<span class="text-xs text-gray-500">Vence: {formatDate(project.due_date)}</span>
						{/if}
					</div>
					<button
						onclick={() => loadProjectDetail(project.id)}
						class="w-full flex items-center justify-center gap-2 px-3 py-2 bg-blue-50 text-blue-700 hover:bg-blue-100 rounded-lg text-sm font-medium transition-colors"
					>
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
						</svg>
						Ver Detalle
					</button>
				</div>
			{/each}
		</div>

		<!-- Pagination -->
		{#if totalPages > 1}
			<div class="flex items-center justify-between mt-4 px-1">
				<p class="text-sm text-gray-500">
					Mostrando {Math.min((currentPage - 1) * pageSize + 1, totalFiltered)}–{Math.min(currentPage * pageSize, totalFiltered)} de {totalFiltered} proyectos
				</p>
				<div class="flex items-center gap-1">
					<button
						onclick={() => currentPage = Math.max(1, currentPage - 1)}
						disabled={currentPage <= 1}
						class="p-2 rounded-lg hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
					>
						<svg class="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
						</svg>
					</button>
					<span class="px-3 py-1 text-sm text-gray-700 font-medium">{currentPage} / {totalPages}</span>
					<button
						onclick={() => currentPage = Math.min(totalPages, currentPage + 1)}
						disabled={currentPage >= totalPages}
						class="p-2 rounded-lg hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
					>
						<svg class="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
						</svg>
					</button>
				</div>
			</div>
		{/if}
	{/if}
</div>

<!-- Create Project Modal -->
{#if showCreateModal}
	<div class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
		<div class="relative top-20 mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-md bg-white">
			<div class="flex justify-between items-center mb-4">
				<h3 class="text-xl font-bold">Nuevo Proyecto</h3>
				<button onclick={() => showCreateModal = false} class="text-gray-400 hover:text-gray-600 text-2xl">&times;</button>
			</div>

			<form onsubmit={(e) => { e.preventDefault(); createProject(); }}>
				<div class="space-y-4">
					<div>
						<label class="block text-sm font-medium text-gray-700 mb-1">Empresa *</label>
						<select bind:value={formData.company_id} required class="w-full border border-gray-300 rounded-lg px-3 py-2">
							<option value={0}>Seleccionar empresa</option>
							{#each companies as company}
								<option value={company.id}>
									{company.razon_social}{company.clasificacion ? ` (${company.clasificacion})` : ''}
								</option>
							{/each}
						</select>
					</div>

					<div>
						<label class="block text-sm font-medium text-gray-700 mb-1">Nombre del Proyecto *</label>
						<input
							type="text"
							bind:value={formData.name}
							required
							class="w-full border border-gray-300 rounded-lg px-3 py-2"
							placeholder="Ej: Auditoría Anual 2026"
						/>
					</div>

					<div>
						<label class="block text-sm font-medium text-gray-700 mb-1">Descripción</label>
						<textarea
							bind:value={formData.description}
							rows="3"
							class="w-full border border-gray-300 rounded-lg px-3 py-2"
							placeholder="Descripción del proyecto..."
						></textarea>
					</div>

					<div class="grid grid-cols-2 gap-4">
						<div>
							<label class="block text-sm font-medium text-gray-700 mb-1">Tipo de Proyecto *</label>
							<select bind:value={formData.project_type} required class="w-full border border-gray-300 rounded-lg px-3 py-2">
								{#each Object.entries(projectTypeLabels) as [value, label]}
									<option value={value}>{label}</option>
								{/each}
							</select>
						</div>

						<div>
							<label class="block text-sm font-medium text-gray-700 mb-1">Prioridad</label>
							<select bind:value={formData.priority} class="w-full border border-gray-300 rounded-lg px-3 py-2">
								{#each Object.entries(priorityLabels) as [value, label]}
									<option value={value}>{label}</option>
								{/each}
							</select>
						</div>
					</div>

					<div class="grid grid-cols-2 gap-4">
						<div>
							<label class="block text-sm font-medium text-gray-700 mb-1">Fecha Inicio</label>
							<input
								type="date"
								bind:value={formData.start_date}
								class="w-full border border-gray-300 rounded-lg px-3 py-2"
							/>
						</div>

						<div>
							<label class="block text-sm font-medium text-gray-700 mb-1">Fecha Vencimiento</label>
							<input
								type="date"
								bind:value={formData.due_date}
								class="w-full border border-gray-300 rounded-lg px-3 py-2"
							/>
						</div>
					</div>

					<div class="flex items-center">
						<input
							type="checkbox"
							bind:checked={formData.include_all_obligations}
							id="includeAll"
							class="h-4 w-4 text-blue-600 border-gray-300 rounded"
						/>
						<label for="includeAll" class="ml-2 text-sm text-gray-700">
							Incluir TODAS las obligaciones (ignorar clasificación de empresa)
						</label>
					</div>
				</div>

				{#if modalError}
					<div class="mt-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
						{modalError}
					</div>
				{/if}

				<div class="flex justify-end gap-3 mt-6">
					<button
						type="button"
						onclick={() => { showCreateModal = false; modalError = ''; }}
						disabled={savingProject}
						class="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 disabled:opacity-50"
					>
						Cancelar
					</button>
					<button
						type="submit"
						disabled={savingProject}
						class="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-60 disabled:cursor-not-allowed"
					>
						{#if savingProject}
							<svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
								<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
								<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
							</svg>
							Creando...
						{:else}
							Crear Proyecto
						{/if}
					</button>
				</div>
			</form>
		</div>
	</div>
{/if}

<!-- Project Detail Modal -->
{#if showDetailModal && selectedProject}
	<div class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
		<div class="relative top-10 mx-auto p-5 border w-full max-w-6xl shadow-lg rounded-md bg-white mb-10">
			<div class="flex justify-between items-start mb-4">
				<div>
					<h3 class="text-2xl font-bold">{selectedProject.name}</h3>
					<p class="text-sm text-gray-600">{selectedProject.company_name}</p>
				</div>
				<button onclick={() => { showDetailModal = false; loadProjects(); }} class="text-gray-400 hover:text-gray-600 text-2xl leading-none">&times;</button>
			</div>

			<!-- Project Info -->
			<div class="grid grid-cols-4 gap-4 mb-6">
				<div class="bg-gray-50 p-3 rounded">
					<p class="text-xs text-gray-600">Tipo</p>
					<p class="font-semibold">{projectTypeLabels[selectedProject.project_type]}</p>
				</div>
				<div class="bg-gray-50 p-3 rounded">
					<p class="text-xs text-gray-600">Estado</p>
					<span class="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full {getStatusColor(selectedProject.status)}">
						{statusLabels[selectedProject.status]}
					</span>
				</div>
				<div class="bg-gray-50 p-3 rounded">
					<p class="text-xs text-gray-600">Progreso</p>
					<p class="font-semibold">{selectedProject.progress_percentage}%</p>
				</div>
				<div class="bg-gray-50 p-3 rounded">
					<p class="text-xs text-gray-600">Vencimiento</p>
					<p class="font-semibold">{formatDate(selectedProject.due_date)}</p>
				</div>
			</div>

			<!-- Tasks -->
			<div class="mb-4">
				<div class="flex justify-between items-center mb-3">
					<h4 class="text-lg font-bold">Tareas ({selectedProject.tasks.length})</h4>
					<button
						onclick={() => openTaskModal()}
						class="text-sm bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded"
					>
						+ Agregar Tarea
					</button>
				</div>

				<div class="space-y-2 max-h-96 overflow-y-auto">
					{#each selectedProject.tasks as task}
						<div class="border rounded-lg p-4 hover:bg-gray-50">
							<div class="flex justify-between items-start">
								<div class="flex-1">
									<div class="flex items-center gap-2 mb-1 flex-wrap">
										{#if task.code}
											<span class="text-xs bg-gray-200 text-gray-700 px-2 py-1 rounded">{task.code}</span>
										{/if}
										<span class="text-xs px-2 py-1 rounded {task.task_type === 'OBLIGATION' ? 'bg-blue-100 text-blue-700' : 'bg-purple-100 text-purple-700'}">
											{task.task_type === 'OBLIGATION' ? 'Obligación' : 'Custom'}
										</span>
										<span class="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full {getStatusColor(task.status)}">
											{statusLabels[task.status]}
										</span>
									</div>
									<p class="font-medium text-gray-900">{task.title}</p>
									{#if task.description}
										<p class="text-sm text-gray-700 mt-1 whitespace-pre-line">{task.description}</p>
									{/if}
									{#if task.notes}
										<p class="text-xs text-gray-500 mt-1 whitespace-pre-line">Notas: {task.notes}</p>
									{/if}
									<div class="flex gap-3 mt-1 text-sm text-gray-500 flex-wrap">
										{#if task.assignee_name}
											<span>{task.assignee_name}</span>
										{/if}
										{#if task.due_date}
											<span>Vence: {formatDate(task.due_date)}</span>
										{/if}
									</div>
									<!-- Barra de progreso -->
									<div class="mt-3 flex items-center gap-2">
										<div class="flex-1 bg-gray-200 rounded-full h-2">
											<div
												class="bg-blue-500 h-2 rounded-full transition-all"
												style="width: {task.progress_percentage ?? 0}%"
											></div>
										</div>
										<input
											type="number"
											min="0"
											max="100"
											value={task.progress_percentage ?? 0}
											class="w-14 text-xs border border-gray-300 rounded px-1 py-0.5 text-center"
											onchange={(e) => updateTaskProgress(task.id, Number((e.target as HTMLInputElement).value))}
										/>
										<span class="text-xs text-gray-500">%</span>
									</div>
								</div>
								<div class="flex flex-col gap-2 ml-4 flex-shrink-0">
									<select
										value={task.status}
										onchange={(e) => updateTaskStatus(task.id, (e.target as HTMLSelectElement).value)}
										class="text-sm border border-gray-300 rounded px-2 py-1"
									>
										<option value="NO_INICIADO">No Iniciado</option>
										<option value="EN_PROGRESO">En Progreso</option>
										<option value="COMPLETADO">Completado</option>
										<option value="CERRADO">Cerrado</option>
									</select>
									<div class="flex gap-1">
										<button
											onclick={() => viewTaskEvidences(task)}
											class="text-xs border border-gray-300 hover:bg-gray-50 text-gray-700 px-2 py-1 rounded flex-1 whitespace-nowrap"
										>
											Evidencias ({task.evidence_count})
										</button>
										<button
											onclick={() => openEvidenceModal(task)}
											class="text-xs bg-blue-600 hover:bg-blue-700 text-white px-2 py-1 rounded whitespace-nowrap"
										>
											+ Adjuntar
										</button>
									</div>
								</div>
							</div>
						</div>
					{/each}
				</div>
			</div>
		</div>
	</div>
{/if}

<!-- Add Task Modal (Obligaciones + Custom) -->
{#if showTaskModal}
	<div class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
		<div class="relative top-10 mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-md bg-white mb-10">
			<div class="flex justify-between items-center mb-4">
				<h3 class="text-xl font-bold">Agregar Tarea</h3>
				<button
					onclick={() => { showTaskModal = false; selectedObligationIds = new Set(); }}
					class="text-gray-400 hover:text-gray-600 text-2xl"
				>&times;</button>
			</div>

			<!-- Tabs -->
			<div class="flex border-b mb-4">
				<button
					class="px-4 py-2 text-sm font-medium {taskModalTab === 'obligations' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500 hover:text-gray-700'}"
					onclick={() => taskModalTab = 'obligations'}
				>
					Desde Obligaciones{#if selectedObligationIds.size > 0} ({selectedObligationIds.size}){/if}
				</button>
				<button
					class="px-4 py-2 text-sm font-medium {taskModalTab === 'custom' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500 hover:text-gray-700'}"
					onclick={() => taskModalTab = 'custom'}
				>
					Tarea Custom
				</button>
			</div>

			{#if taskModalTab === 'obligations'}
				<!-- Obligations Tab -->
				{#if !obligationsClassified}
					<div class="bg-yellow-50 border border-yellow-200 text-yellow-800 px-4 py-3 rounded mb-4 text-sm">
						Aviso: Esta empresa no tiene clasificación de centro de carga. Se muestran todas las obligaciones del catálogo.
					</div>
				{/if}

				<div class="mb-3">
					<input
						type="text"
						bind:value={obligationSearchFilter}
						placeholder="Buscar por código o nombre..."
						class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
					/>
				</div>

				{#if loadingObligations}
					<div class="text-center py-8">
						<div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
						<p class="mt-2 text-sm text-gray-500">Cargando obligaciones...</p>
					</div>
				{:else if availableObligations.length === 0}
					<div class="text-center py-8 text-gray-500 border rounded-lg">
						<p class="font-medium">No hay obligaciones disponibles para agregar</p>
						<p class="text-sm mt-1">Todas las obligaciones ya están en este proyecto, o la empresa no tiene obligaciones configuradas en la matriz.</p>
					</div>
				{:else}
					<div class="space-y-2 max-h-80 overflow-y-auto border rounded-lg p-2">
						{#each availableObligations.filter(o =>
							!obligationSearchFilter ||
							o.codigo.toLowerCase().includes(obligationSearchFilter.toLowerCase()) ||
							o.nombre.toLowerCase().includes(obligationSearchFilter.toLowerCase())
						) as obligation}
							<div
								class="flex flex-col gap-2 p-3 rounded cursor-pointer border {selectedObligationIds.has(obligation.id) ? 'bg-blue-50 border-blue-300' : 'border-transparent hover:bg-gray-50'}"
								onclick={() => {
									const next = new Set(selectedObligationIds);
									if (next.has(obligation.id)) {
										next.delete(obligation.id);
									} else {
										next.add(obligation.id);
									}
									selectedObligationIds = next;
								}}
							>
								<div class="flex items-start gap-3">
									<input
										type="checkbox"
										checked={selectedObligationIds.has(obligation.id)}
										class="mt-1 h-4 w-4 text-blue-600 rounded flex-shrink-0"
										readonly
									/>
									<div class="min-w-0">
										<div class="flex items-center gap-2 flex-wrap">
											<span class="text-xs bg-gray-200 text-gray-700 px-2 py-0.5 rounded font-mono">{obligation.codigo}</span>
											<span class="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">{obligation.estado_aplicabilidad}</span>
										</div>
										<p class="text-sm font-medium text-gray-900 mt-1">{obligation.nombre}</p>
										{#if obligation.descripcion}
											<p class="text-xs text-gray-500 mt-0.5 line-clamp-2">{obligation.descripcion}</p>
										{/if}
									</div>
								</div>
								<!-- Descripción adicional por tarea -->
								<div class="mt-2">
									<label class="block text-xs font-medium text-gray-600 mb-1">
										Descripción adicional para la tarea
									</label>
									<textarea
										bind:value={obligationAdditionalContextById[obligation.id]}
										rows="2"
										placeholder="Notas específicas para esta obligación"
										class="w-full border border-gray-300 rounded-lg px-2 py-1 text-xs resize-y bg-white"
									></textarea>
								</div>

								<div class="mt-2">
									<label class="block text-xs font-medium text-gray-600 mb-1">
										Fotos para esta obligación (opcional)
									</label>
									<input
										type="file"
										accept="image/*"
										multiple
										onchange={(e) => {
											const files = Array.from((e.target as HTMLInputElement).files ?? []);
											obligationEvidenceFilesById = { ...obligationEvidenceFilesById, [obligation.id]: files };
										}}
										class="w-full text-xs text-gray-700"
									/>
									{#if obligationEvidenceFilesById[obligation.id]?.length}
										<p class="text-[11px] text-gray-500 mt-1">
											{obligationEvidenceFilesById[obligation.id].length} foto(s) seleccionada(s)
										</p>
									{/if}
								</div>
							</div>
						{/each}
					</div>
				{/if}

				<div class="flex justify-between items-center mt-4">
					<span class="text-sm text-gray-600">
						{selectedObligationIds.size} obligación(es) seleccionada(s)
					</span>
					<div class="flex gap-3">
						<button
							type="button"
							onclick={() => { showTaskModal = false; selectedObligationIds = new Set(); obligationAdditionalContextById = {}; obligationFiles = null; obligationEvidenceComment = ''; }}
							class="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
						>
							Cancelar
						</button>
						<button
							type="button"
							disabled={selectedObligationIds.size === 0}
							onclick={() => addObligationTasks()}
							class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
						>
							Agregar {selectedObligationIds.size > 0 ? selectedObligationIds.size : ''} Tarea(s)
						</button>
					</div>
				</div>

			{:else}
				<!-- Custom Task Tab -->
				<form onsubmit={(e) => { e.preventDefault(); addCustomTask(); }}>
					<div class="space-y-4">
						<div>
							<label class="block text-sm font-medium text-gray-700 mb-1">Título *</label>
							<input
								type="text"
								bind:value={taskFormData.title}
								required
								class="w-full border border-gray-300 rounded-lg px-3 py-2"
							/>
						</div>

						<div>
							<label class="block text-sm font-medium text-gray-700 mb-1">Descripción</label>
							<textarea
								bind:value={taskFormData.description}
								rows="3"
								class="w-full border border-gray-300 rounded-lg px-3 py-2"
							></textarea>
						</div>

						<div>
							<label class="block text-sm font-medium text-gray-700 mb-1">Fecha Vencimiento</label>
							<input
								type="date"
								bind:value={taskFormData.due_date}
								class="w-full border border-gray-300 rounded-lg px-3 py-2"
							/>
						</div>

						<div>
							<label class="block text-sm font-medium text-gray-700 mb-1">Fotos (opcional)</label>
							<input
								type="file"
								accept="image/*"
								multiple
								onchange={(e) => { customTaskFiles = (e.target as HTMLInputElement).files; }}
								class="w-full text-sm text-gray-700"
							/>
							<p class="text-xs text-gray-500 mt-1">Puedes adjuntar una o varias fotos que quedarán como evidencias iniciales de la tarea.</p>
						</div>

						<div>
							<label class="block text-sm font-medium text-gray-700 mb-1">Comentario para las fotos (opcional)</label>
							<textarea
								bind:value={customTaskEvidenceComment}
								rows="2"
								class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
								placeholder="Ejemplo: Fotos de estado inicial, evidencia de visita, etc."
							></textarea>
						</div>
					</div>

					<div class="flex justify-end gap-3 mt-6">
						<button
							type="button"
							onclick={() => { showTaskModal = false; selectedObligationIds = new Set(); customTaskFiles = null; customTaskEvidenceComment = ''; }}
							class="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
						>
							Cancelar
						</button>
						<button
							type="submit"
							class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
						>
							Agregar Tarea
						</button>
					</div>
				</form>
			{/if}
		</div>
	</div>
{/if}

<!-- View Evidences Modal -->
{#if showViewEvidencesModal && selectedTask}
	<div class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
		<div class="relative top-8 mx-auto p-5 border w-full max-w-3xl shadow-lg rounded-md bg-white mb-10">
			<div class="flex justify-between items-center mb-4">
				<div>
					<h3 class="text-xl font-bold">Evidencias</h3>
					<p class="text-sm text-gray-600 mt-0.5">{selectedTask.title}</p>
				</div>
				<button onclick={() => { showViewEvidencesModal = false; previewEvidence = null; }} class="text-gray-400 hover:text-gray-600 text-2xl">&times;</button>
			</div>

			{#if loadingEvidences}
				<div class="text-center py-8">
					<div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
					<p class="mt-2 text-sm text-gray-500">Cargando evidencias...</p>
				</div>
			{:else if taskEvidences.length === 0}
				<div class="text-center py-10 text-gray-500 border rounded-lg">
					<p class="font-medium">Sin evidencias registradas</p>
					<p class="text-sm mt-1">Use el botón "+ Adjuntar" en la tarea para agregar archivos.</p>
				</div>
			{:else}
				<!-- Preview panel -->
				{#if previewEvidence}
					<div class="mb-4 border rounded-lg overflow-hidden bg-gray-50">
						<div class="flex justify-between items-center px-3 py-2 bg-gray-100 border-b">
							<span class="text-sm font-medium text-gray-700 truncate">{previewEvidence.filename}</span>
							<button onclick={() => previewEvidence = null} class="text-gray-400 hover:text-gray-600 ml-2 flex-shrink-0">×</button>
						</div>
						{#if previewEvidence.mime_type?.startsWith('image/')}
							<div class="flex justify-center p-2 bg-gray-900">
								<img
									src={previewEvidence.file_url}
									alt={previewEvidence.filename}
									class="max-h-96 object-contain"
								/>
							</div>
						{:else if previewEvidence.mime_type === 'application/pdf'}
							<iframe
								src={previewEvidence.file_url}
								title={previewEvidence.filename}
								class="w-full h-96 border-0"
							></iframe>
						{:else if previewEvidence.mime_type?.startsWith('video/')}
							<!-- svelte-ignore a11y_media_has_caption -->
							<video controls class="w-full max-h-64 bg-black">
								<source src={previewEvidence.file_url} type={previewEvidence.mime_type} />
							</video>
						{:else}
							<div class="flex flex-col items-center justify-center py-10 text-gray-500">
								<p class="text-sm">No se puede previsualizar este tipo de archivo</p>
								<p class="text-xs mt-1 text-gray-400">{previewEvidence.mime_type ?? 'Tipo desconocido'}</p>
								<a
									href={previewEvidence.file_url}
									target="_blank"
									rel="noopener noreferrer"
									class="mt-3 text-sm text-blue-600 hover:text-blue-800 border border-blue-200 rounded px-3 py-1 hover:bg-blue-50"
								>
									Abrir archivo
								</a>
							</div>
						{/if}
					</div>
				{/if}

				<!-- Evidence list -->
				<div class="space-y-2 max-h-80 overflow-y-auto">
					{#each taskEvidences as evidence}
						<div class="border rounded-lg overflow-hidden {previewEvidence?.id === evidence.id ? 'border-blue-400 ring-1 ring-blue-300' : ''}">
							<div class="flex items-center gap-3 p-3">
								<!-- File type icon area -->
								<div class="flex-shrink-0 w-10 h-10 rounded bg-gray-100 flex items-center justify-center text-lg font-bold text-gray-400 select-none">
									{#if evidence.mime_type?.startsWith('image/')}
										<span class="text-xs text-center leading-tight text-gray-500">IMG</span>
									{:else if evidence.mime_type === 'application/pdf'}
										<span class="text-xs text-red-500 font-bold">PDF</span>
									{:else if evidence.mime_type?.startsWith('video/')}
										<span class="text-xs text-purple-500 font-bold">VID</span>
									{:else if evidence.mime_type?.includes('spreadsheet') || evidence.mime_type?.includes('excel') || evidence.filename.endsWith('.xlsx') || evidence.filename.endsWith('.csv')}
										<span class="text-xs text-green-600 font-bold">XLS</span>
									{:else if evidence.mime_type?.includes('word') || evidence.filename.endsWith('.docx')}
										<span class="text-xs text-blue-600 font-bold">DOC</span>
									{:else}
										<span class="text-xs text-gray-500">FILE</span>
									{/if}
								</div>

								<div class="min-w-0 flex-1">
									<p class="text-sm font-medium text-gray-900 truncate">{evidence.filename}</p>
									<div class="flex items-center gap-2 mt-0.5 flex-wrap">
										<span class="text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded">
											{evidenceTypeLabels[evidence.evidence_type] ?? evidence.evidence_type}
										</span>
										<span class="text-xs text-gray-400">{formatDate(evidence.uploaded_at)}</span>
										{#if evidence.size_bytes}
											<span class="text-xs text-gray-400">{formatFileSize(evidence.size_bytes)}</span>
										{/if}
										{#if evidence.uploader_name}
											<span class="text-xs text-gray-400">{evidence.uploader_name}</span>
										{/if}
									</div>
									{#if evidence.comment}
										<p class="text-xs text-gray-500 mt-0.5 line-clamp-1">{evidence.comment}</p>
									{/if}
								</div>

								<!-- Actions -->
								<div class="flex gap-1 flex-shrink-0">
									{#if evidence.file_url && canPreview(evidence)}
										<button
											onclick={() => previewEvidence = previewEvidence?.id === evidence.id ? null : evidence}
											class="text-xs px-2 py-1 rounded border {previewEvidence?.id === evidence.id ? 'bg-blue-600 text-white border-blue-600' : 'border-gray-300 text-gray-600 hover:bg-gray-50'}"
										>
											{previewEvidence?.id === evidence.id ? 'Cerrar' : 'Ver'}
										</button>
									{/if}
									{#if evidence.file_url}
										<a
											href={evidence.file_url}
											target="_blank"
											rel="noopener noreferrer"
											class="text-xs px-2 py-1 rounded border border-gray-300 text-gray-600 hover:bg-gray-50"
										>
											Descargar
										</a>
									{/if}
									{#if deletingEvidenceId === evidence.id}
										<button disabled class="text-xs px-2 py-1 rounded border border-red-200 text-red-400 flex items-center gap-1 cursor-not-allowed">
											<svg class="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25"/><path fill="currentColor" d="M4 12a8 8 0 018-8v8z" class="opacity-75"/></svg>
											Eliminando…
										</button>
									{:else if confirmingDeleteId === evidence.id}
										<span class="text-xs text-gray-600 font-medium">¿Seguro?</span>
										<button
											onclick={() => deleteEvidence(evidence.id)}
											class="text-xs px-2 py-1 rounded bg-red-600 text-white border border-red-600 hover:bg-red-700"
										>Sí, eliminar</button>
										<button
											onclick={() => confirmingDeleteId = null}
											class="text-xs px-2 py-1 rounded border border-gray-300 text-gray-600 hover:bg-gray-50"
										>No</button>
									{:else}
										<button
											onclick={() => confirmingDeleteId = evidence.id}
											class="text-xs px-2 py-1 rounded border border-red-200 text-red-600 hover:bg-red-50"
											title="Eliminar evidencia"
										>Eliminar</button>
									{/if}
								</div>
							</div>
						</div>
					{/each}
				</div>
			{/if}

			<div class="flex justify-between items-center mt-4 pt-4 border-t">
				<span class="text-sm text-gray-500">{taskEvidences.length} evidencia(s)</span>
				<div class="flex gap-2">
					<button
						type="button"
						onclick={() => { showViewEvidencesModal = false; previewEvidence = null; openEvidenceModal(selectedTask!); }}
						class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
					>
						+ Agregar evidencia
					</button>
					<button
						type="button"
						onclick={() => { showViewEvidencesModal = false; previewEvidence = null; }}
						class="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 text-sm"
					>
						Cerrar
					</button>
				</div>
			</div>
		</div>
	</div>
{/if}

<!-- Upload Evidence Modal -->
{#if showEvidenceModal && selectedTask}
	<div class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
		<div class="relative top-20 mx-auto p-5 border w-full max-w-lg shadow-lg rounded-md bg-white">
			<div class="flex justify-between items-center mb-4">
				<h3 class="text-xl font-bold">Subir Evidencia</h3>
				<button onclick={() => showEvidenceModal = false} class="text-gray-400 hover:text-gray-600 text-2xl">&times;</button>
			</div>

			<form onsubmit={(e) => { e.preventDefault(); uploadEvidence(); }}>
				<div class="space-y-4">
					<div>
						<p class="text-sm text-gray-600 mb-2">Tarea: <span class="font-medium">{selectedTask.title}</span></p>
					</div>

					<div>
						<label class="block text-sm font-medium text-gray-700 mb-1">Tipo de Evidencia *</label>
						<select bind:value={evidenceType} required class="w-full border border-gray-300 rounded-lg px-3 py-2">
							{#each Object.entries(evidenceTypeLabels) as [value, label]}
								<option value={value}>{label}</option>
							{/each}
						</select>
					</div>

					<div>
						<label class="block text-sm font-medium text-gray-700 mb-1">Archivo *</label>
						<input
							type="file"
							onchange={(e) => evidenceFile = (e.target as HTMLInputElement).files?.[0] || null}
							required
							class="w-full border border-gray-300 rounded-lg px-3 py-2"
						/>
					</div>

					<div>
						<label class="block text-sm font-medium text-gray-700 mb-1">Comentario</label>
						<textarea
							bind:value={evidenceComment}
							rows="3"
							class="w-full border border-gray-300 rounded-lg px-3 py-2"
							placeholder="Descripción de la evidencia..."
						></textarea>
					</div>
				</div>

				<div class="flex justify-end gap-3 mt-6">
					<button
						type="button"
						onclick={() => showEvidenceModal = false}
						class="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
					>
						Cancelar
					</button>
					<button
						type="submit"
						disabled={uploadingEvidence}
						class="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-60 disabled:cursor-not-allowed"
					>
						{#if uploadingEvidence}
							<svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25"/><path fill="currentColor" d="M4 12a8 8 0 018-8v8z" class="opacity-75"/></svg>
							Subiendo…
						{:else}
							Subir Evidencia
						{/if}
					</button>
				</div>
			</form>
		</div>
	</div>
{/if}
<!-- ══════════════════ REPORT MODAL ══════════════════ -->
{#if showReportModal && selectedProject}
	{@const rptCompany = companies.find(c => c.id === selectedProject!.company_id)}
	{@const rptTotal = selectedProject.total_tasks}
	{@const rptCompleted = selectedProject.completed_tasks}
	{@const rptInProgress = selectedProject.tasks.filter(t => t.status === 'EN_PROGRESO').length}
	{@const rptPending = selectedProject.tasks.filter(t => t.status !== 'COMPLETADO' && t.status !== 'CERRADO').length}
	{@const rptOverdue = selectedProject.tasks.filter(t => !!t.due_date && new Date(t.due_date) < new Date() && t.status !== 'COMPLETADO' && t.status !== 'CERRADO').length}
	{@const rptProgress = selectedProject.progress_percentage}
	{@const rptFolio = `PRY-${new Date().getFullYear()}-${String(selectedProject.id).padStart(4, '0')}`}
	<div class="rpt-overlay" style="position:fixed;inset:0;z-index:200;background:#e5e7eb;overflow-y:auto;">

		<!-- Botones flotantes DENTRO del overlay (position:sticky al fondo del viewport) -->
		<div class="rpt-no-print" style="position:sticky;top:calc(100vh - 160px);margin-left:auto;width:fit-content;padding-right:32px;display:flex;flex-direction:column;align-items:center;gap:12px;z-index:10;pointer-events:none;">
			{#if reportLoadingEvidences}
				<div style="background:#1e293b;color:#fbbf24;font-size:10px;font-weight:700;padding:6px 12px;border-radius:99px;white-space:nowrap;box-shadow:0 4px 14px rgba(0,0,0,0.4);pointer-events:auto;">
					⏳ Cargando evidencias…
				</div>
			{/if}
			<button
				type="button"
				onclick={printReport}
				title="Imprimir / Guardar PDF"
				style="width:56px;height:56px;border-radius:50%;background:#1e293b;color:#fff;border:none;cursor:pointer;display:flex;align-items:center;justify-content:center;box-shadow:0 6px 20px rgba(0,0,0,0.4);pointer-events:auto;"
			>
				<svg style="width:22px;height:22px;" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z"/>
				</svg>
			</button>
			<button
				type="button"
				onclick={() => { showReportModal = false; }}
				title="Cerrar"
				style="width:56px;height:56px;border-radius:50%;background:#ffffff;color:#374151;border:2px solid #d1d5db;cursor:pointer;display:flex;align-items:center;justify-content:center;box-shadow:0 4px 14px rgba(0,0,0,0.18);pointer-events:auto;"
			>
				<svg style="width:22px;height:22px;" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
				</svg>
			</button>
		</div>

	<!-- ─── DOCUMENT ─── -->
	<div class="rpt-page max-w-4xl mx-auto my-8 bg-white shadow-2xl" style="font-family:'Segoe UI',Arial,sans-serif;color:#1e293b;">

		<!-- ═══ HEADER ═══ -->
		<div style="border-top:5px solid #334155;padding:0;">
			<!-- Banda superior institucional -->
			<div style="background:#f1f5f9;padding:7px 40px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #e2e8f0;">
				<span style="color:#64748b;font-size:9px;font-weight:700;letter-spacing:2.5px;text-transform:uppercase;">Sistema de Gestión de Cumplimiento Regulatorio</span>
				<span style="color:#94a3b8;font-size:9px;font-weight:600;letter-spacing:1px;">DOCUMENTO CONFIDENCIAL</span>
			</div>
			<!-- Contenido principal del encabezado -->
			<div style="background:#ffffff;padding:28px 40px 26px;display:flex;justify-content:space-between;align-items:flex-start;gap:24px;border-bottom:1px solid #cbd5e1;">
				<div style="flex:1;">
					<div style="width:44px;height:3px;background:#334155;border-radius:2px;margin-bottom:12px;"></div>
					<p style="color:#64748b;font-size:9px;font-weight:700;letter-spacing:3px;text-transform:uppercase;margin:0 0 6px;">Informe Técnico de Proyecto</p>
					<h1 style="color:#0f172a;font-size:22px;font-weight:800;margin:0 0 6px;line-height:1.25;">{selectedProject.name}</h1>
					<p style="color:#475569;font-size:13px;margin:0 0 14px;font-weight:500;">{selectedProject.company_name}</p>
					<div style="display:inline-flex;gap:8px;flex-wrap:wrap;">
						<span style="background:#f1f5f9;color:#475569;font-size:10px;font-weight:600;padding:3px 10px;border-radius:4px;border:1px solid #e2e8f0;">
							{projectTypeLabels[selectedProject.project_type] ?? selectedProject.project_type}
						</span>
						<span style="font-size:10px;font-weight:700;padding:3px 10px;border-radius:4px;{reportStatusStyle(selectedProject.status)}">
							{statusLabels[selectedProject.status] ?? selectedProject.status}
						</span>
						{#if selectedProject.priority}
							<span style="font-size:10px;font-weight:700;padding:3px 10px;border-radius:4px;{reportPriorityStyle(selectedProject.priority)}">
								{priorityLabels[selectedProject.priority] ?? selectedProject.priority}
							</span>
						{/if}
					</div>
				</div>
				<div style="text-align:right;flex-shrink:0;min-width:180px;">
					<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:14px 18px;margin-bottom:10px;">
						<p style="color:#94a3b8;font-size:8px;text-transform:uppercase;letter-spacing:2px;font-weight:700;margin:0 0 4px;">Folio del Documento</p>
						<p style="color:#0f172a;font-size:16px;font-weight:800;margin:0;letter-spacing:1px;font-family:monospace;">{rptFolio}</p>
					</div>
					<p style="color:#94a3b8;font-size:8px;text-transform:uppercase;letter-spacing:1px;font-weight:600;margin:0 0 3px;">Generado el</p>
					<p style="color:#475569;font-size:11px;font-weight:500;margin:0;">{reportDate}</p>
				</div>
			</div>
		</div>

		<!-- ═══ SECTION I: EMPRESA ═══ -->
		<div style="padding:24px 40px;border-bottom:1px solid #e2e8f0;">
			<div style="display:flex;align-items:center;gap:10px;margin-bottom:14px;">
				<div style="width:4px;height:20px;background:#1d4ed8;border-radius:2px;flex-shrink:0;"></div>
				<p style="font-size:11px;font-weight:800;color:#0f2244;text-transform:uppercase;letter-spacing:2px;margin:0;">I · Datos de la Empresa</p>
			</div>
			<div style="display:grid;grid-template-columns:1fr 1fr;gap:0;border:1px solid #e2e8f0;border-radius:8px;overflow:hidden;">
				<div style="padding:10px 14px;border-right:1px solid #e2e8f0;border-bottom:1px solid #e2e8f0;background:#f8fafc;">
					<p style="font-size:9px;color:#64748b;text-transform:uppercase;letter-spacing:1px;font-weight:700;margin:0 0 3px;">Razón Social</p>
					<p style="font-size:13px;font-weight:700;color:#0f172a;margin:0;">{rptCompany?.razon_social ?? selectedProject.company_name}</p>
				</div>
				<div style="padding:10px 14px;border-bottom:1px solid #e2e8f0;background:#f8fafc;">
					<p style="font-size:9px;color:#64748b;text-transform:uppercase;letter-spacing:1px;font-weight:700;margin:0 0 3px;">RFC</p>
					<p style="font-size:13px;font-weight:700;color:#0f172a;margin:0;font-family:monospace;">{rptCompany?.rfc ?? '—'}</p>
				</div>
				<div style="padding:10px 14px;border-right:1px solid #e2e8f0;border-bottom:1px solid #e2e8f0;">
					<p style="font-size:9px;color:#64748b;text-transform:uppercase;letter-spacing:1px;font-weight:700;margin:0 0 3px;">Nombre Comercial</p>
					<p style="font-size:12px;color:#334155;margin:0;">{rptCompany?.nombre_comercial ?? '—'}</p>
				</div>
				<div style="padding:10px 14px;border-bottom:1px solid #e2e8f0;">
					<p style="font-size:9px;color:#64748b;text-transform:uppercase;letter-spacing:1px;font-weight:700;margin:0 0 3px;">Clasificación</p>
					<p style="font-size:12px;color:#334155;margin:0;">{rptCompany?.clasificacion ?? '—'}</p>
				</div>
				<div style="padding:10px 14px;border-right:1px solid #e2e8f0;">
					<p style="font-size:9px;color:#64748b;text-transform:uppercase;letter-spacing:1px;font-weight:700;margin:0 0 3px;">Tipo de Suministro</p>
					<p style="font-size:12px;color:#334155;margin:0;">{rptCompany?.tipo_suministro ?? '—'}</p>
				</div>
				<div style="padding:10px 14px;">
					<p style="font-size:9px;color:#64748b;text-transform:uppercase;letter-spacing:1px;font-weight:700;margin:0 0 3px;">Estatus de la Empresa</p>
					<p style="font-size:12px;color:#334155;margin:0;">{rptCompany?.is_active ? '✓ Activa' : '✗ Inactiva'}</p>
				</div>
			</div>
		</div>

		<!-- ═══ SECTION II: PROYECTO ═══ -->
		<div style="padding:24px 40px;border-bottom:1px solid #e2e8f0;">
			<div style="display:flex;align-items:center;gap:10px;margin-bottom:14px;">
				<div style="width:4px;height:20px;background:#1d4ed8;border-radius:2px;flex-shrink:0;"></div>
				<p style="font-size:11px;font-weight:800;color:#0f2244;text-transform:uppercase;letter-spacing:2px;margin:0;">II · Datos Generales del Proyecto</p>
			</div>
			<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:0;border:1px solid #e2e8f0;border-radius:8px;overflow:hidden;">
				<div style="padding:10px 14px;border-right:1px solid #e2e8f0;border-bottom:1px solid #e2e8f0;background:#f8fafc;">
					<p style="font-size:9px;color:#64748b;text-transform:uppercase;letter-spacing:1px;font-weight:700;margin:0 0 3px;">Tipo de Proyecto</p>
					<p style="font-size:12px;font-weight:600;color:#0f172a;margin:0;">{projectTypeLabels[selectedProject.project_type] ?? selectedProject.project_type}</p>
				</div>
				<div style="padding:10px 14px;border-right:1px solid #e2e8f0;border-bottom:1px solid #e2e8f0;background:#f8fafc;">
					<p style="font-size:9px;color:#64748b;text-transform:uppercase;letter-spacing:1px;font-weight:700;margin:0 0 3px;">Estado</p>
					<p style="font-size:12px;font-weight:600;color:#0f172a;margin:0;">{statusLabels[selectedProject.status] ?? selectedProject.status}</p>
				</div>
				<div style="padding:10px 14px;border-bottom:1px solid #e2e8f0;background:#f8fafc;">
					<p style="font-size:9px;color:#64748b;text-transform:uppercase;letter-spacing:1px;font-weight:700;margin:0 0 3px;">Prioridad</p>
					<p style="font-size:12px;font-weight:600;color:#0f172a;margin:0;">{priorityLabels[selectedProject.priority ?? ''] ?? '—'}</p>
				</div>
				<div style="padding:10px 14px;border-right:1px solid #e2e8f0;border-bottom:1px solid #e2e8f0;">
					<p style="font-size:9px;color:#64748b;text-transform:uppercase;letter-spacing:1px;font-weight:700;margin:0 0 3px;">Fecha de Inicio</p>
					<p style="font-size:12px;font-weight:600;color:#0f172a;margin:0;">{formatDate(selectedProject.start_date)}</p>
				</div>
				<div style="padding:10px 14px;border-right:1px solid #e2e8f0;border-bottom:1px solid #e2e8f0;">
					<p style="font-size:9px;color:#64748b;text-transform:uppercase;letter-spacing:1px;font-weight:700;margin:0 0 3px;">Fecha de Vencimiento</p>
					<p style="font-size:12px;font-weight:600;color:#0f172a;margin:0;">{formatDate(selectedProject.due_date)}</p>
				</div>
				<div style="padding:10px 14px;border-bottom:1px solid #e2e8f0;">
					<p style="font-size:9px;color:#64748b;text-transform:uppercase;letter-spacing:1px;font-weight:700;margin:0 0 3px;">ID del Proyecto</p>
					<p style="font-size:12px;font-weight:600;color:#0f172a;margin:0;font-family:monospace;">{selectedProject.id}</p>
				</div>
				{#if selectedProject.description}
					<div style="padding:10px 14px;grid-column:span 3;">
						<p style="font-size:9px;color:#64748b;text-transform:uppercase;letter-spacing:1px;font-weight:700;margin:0 0 4px;">Descripción del Proyecto</p>
						<p style="font-size:12px;color:#334155;margin:0;line-height:1.6;">{selectedProject.description}</p>
					</div>
				{/if}
			</div>
		</div>

		<!-- ═══ SECTION III: MÉTRICAS ═══ -->
		<div style="padding:24px 40px;border-bottom:1px solid #e2e8f0;background:#fafbff;">
			<div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;">
				<div style="width:4px;height:20px;background:#1d4ed8;border-radius:2px;flex-shrink:0;"></div>
				<p style="font-size:11px;font-weight:800;color:#0f2244;text-transform:uppercase;letter-spacing:2px;margin:0;">III · Resumen Ejecutivo de Avance</p>
			</div>
			<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-bottom:20px;">
				<div style="border:2px solid #e2e8f0;border-radius:10px;padding:14px 10px;text-align:center;background:#fff;">
					<p style="font-size:30px;font-weight:900;color:#0f172a;margin:0 0 3px;line-height:1;">{rptTotal}</p>
					<p style="font-size:9px;color:#64748b;text-transform:uppercase;letter-spacing:1px;font-weight:700;margin:0;">Total</p>
				</div>
				<div style="border:2px solid #bbf7d0;border-radius:10px;padding:14px 10px;text-align:center;background:#f0fdf4;">
					<p style="font-size:30px;font-weight:900;color:#166534;margin:0 0 3px;line-height:1;">{rptCompleted}</p>
					<p style="font-size:9px;color:#166534;text-transform:uppercase;letter-spacing:1px;font-weight:700;margin:0;">Completadas</p>
				</div>
				<div style="border:2px solid #bfdbfe;border-radius:10px;padding:14px 10px;text-align:center;background:#eff6ff;">
					<p style="font-size:30px;font-weight:900;color:#1e40af;margin:0 0 3px;line-height:1;">{rptInProgress}</p>
					<p style="font-size:9px;color:#1e40af;text-transform:uppercase;letter-spacing:1px;font-weight:700;margin:0;">En Progreso</p>
				</div>
				<div style="border:2px solid #fde68a;border-radius:10px;padding:14px 10px;text-align:center;background:#fefce8;">
					<p style="font-size:30px;font-weight:900;color:#854d0e;margin:0 0 3px;line-height:1;">{rptPending}</p>
					<p style="font-size:9px;color:#854d0e;text-transform:uppercase;letter-spacing:1px;font-weight:700;margin:0;">Pendientes</p>
				</div>
				<div style="border:2px solid #fecaca;border-radius:10px;padding:14px 10px;text-align:center;background:#fef2f2;">
					<p style="font-size:30px;font-weight:900;color:#991b1b;margin:0 0 3px;line-height:1;">{rptOverdue}</p>
					<p style="font-size:9px;color:#991b1b;text-transform:uppercase;letter-spacing:1px;font-weight:700;margin:0;">Vencidas</p>
				</div>
			</div>
			<div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:16px 20px;">
				<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
					<span style="font-size:11px;font-weight:700;color:#334155;">Avance Global del Proyecto</span>
					<span style="font-size:24px;font-weight:900;color:{rptProgress >= 100 ? '#16a34a' : rptProgress >= 60 ? '#1d4ed8' : rptProgress >= 30 ? '#d97706' : '#dc2626'};">{rptProgress}%</span>
				</div>
				<div style="background:#e2e8f0;border-radius:99px;height:14px;overflow:hidden;">
					<div style="height:14px;border-radius:99px;background:{rptProgress >= 100 ? 'linear-gradient(90deg,#16a34a,#4ade80)' : rptProgress >= 60 ? 'linear-gradient(90deg,#1d4ed8,#38bdf8)' : rptProgress >= 30 ? 'linear-gradient(90deg,#d97706,#fbbf24)' : 'linear-gradient(90deg,#dc2626,#f87171)'};width:{rptProgress}%;"></div>
				</div>
				<div style="display:flex;justify-content:space-between;margin-top:5px;">
					<span style="font-size:9px;color:#94a3b8;">0%</span>
					<span style="font-size:9px;color:#94a3b8;">100%</span>
				</div>
			</div>
		</div>

		<!-- ═══ SECTION IV: TAREAS ═══ -->
		<div style="padding:24px 40px;">
			<div style="display:flex;align-items:center;gap:10px;margin-bottom:20px;">
				<div style="width:4px;height:20px;background:#1d4ed8;border-radius:2px;flex-shrink:0;"></div>
				<p style="font-size:11px;font-weight:800;color:#0f2244;text-transform:uppercase;letter-spacing:2px;margin:0;">IV · Análisis Detallado de Tareas ({selectedProject.tasks.length})</p>
			</div>

			{#if selectedProject.tasks.length === 0}
				<div style="text-align:center;padding:32px;border:2px dashed #e2e8f0;border-radius:10px;color:#94a3b8;">
					<p style="font-size:13px;font-weight:600;margin:0;">Sin tareas registradas para este proyecto</p>
				</div>
			{:else}
				<div style="display:flex;flex-direction:column;gap:18px;">
					{#each selectedProject.tasks as task, i}
						{@const taskEvs = reportEvidences[task.id] ?? []}
						{@const imgEvs = taskEvs.filter(e => e.mime_type?.startsWith('image/'))}
						{@const fileEvs = taskEvs.filter(e => !e.mime_type?.startsWith('image/'))}
						{@const isOverdue = !!task.due_date && new Date(task.due_date) < new Date() && task.status !== 'COMPLETADO' && task.status !== 'CERRADO'}
						<div style="border:1px solid {task.status === 'COMPLETADO' ? '#bbf7d0' : isOverdue ? '#fecaca' : '#e2e8f0'};border-radius:10px;overflow:hidden;page-break-inside:avoid;">
							<!-- Task header -->
							<div style="background:{task.status === 'COMPLETADO' ? '#f0fdf4' : isOverdue ? '#fef2f2' : '#f8fafc'};padding:12px 16px;border-bottom:1px solid {task.status === 'COMPLETADO' ? '#bbf7d0' : isOverdue ? '#fecaca' : '#e2e8f0'};display:flex;justify-content:space-between;align-items:flex-start;gap:12px;">
								<div style="flex:1;min-width:0;">
									<div style="display:flex;align-items:center;gap:6px;margin-bottom:5px;flex-wrap:wrap;">
										<span style="font-size:9px;font-weight:800;color:#94a3b8;background:#f1f5f9;padding:1px 6px;border-radius:3px;">#{i + 1}</span>
										{#if task.code}
											<span style="font-size:9px;background:#e0e7ff;color:#3730a3;padding:2px 8px;border-radius:4px;font-weight:700;font-family:monospace;">{task.code}</span>
										{/if}
										<span style="font-size:9px;padding:2px 8px;border-radius:4px;font-weight:600;{task.task_type === 'OBLIGATION' ? 'background:#dbeafe;color:#1e40af;' : 'background:#f3e8ff;color:#6b21a8;'}">
											{task.task_type === 'OBLIGATION' ? '📋 Obligación Regulatoria' : '⚙️ Tarea Custom'}
										</span>
									</div>
									<p style="font-size:13px;font-weight:700;color:#0f172a;margin:0;">{task.title}</p>
								</div>
								<div style="flex-shrink:0;text-align:right;">
									<span style="font-size:10px;padding:3px 10px;border-radius:20px;font-weight:700;display:block;margin-bottom:4px;{reportStatusStyle(task.status)}">
										{statusLabels[task.status] ?? task.status}
									</span>
									{#if isOverdue}
										<span style="font-size:9px;background:#fef2f2;color:#dc2626;border:1px solid #fecaca;padding:2px 8px;border-radius:20px;font-weight:700;">⚠ VENCIDA</span>
									{/if}
								</div>
							</div>
							<!-- Metadata grid -->
							<div style="padding:12px 16px;display:grid;grid-template-columns:repeat(4,1fr);gap:10px;border-bottom:1px solid #f1f5f9;">
								<div>
									<p style="font-size:8px;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;font-weight:700;margin:0 0 2px;">Responsable</p>
									<p style="font-size:11px;color:#334155;font-weight:600;margin:0;">{task.assignee_name ?? '—'}</p>
								</div>
								<div>
									<p style="font-size:8px;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;font-weight:700;margin:0 0 2px;">Fecha Límite</p>
									<p style="font-size:11px;color:{isOverdue ? '#dc2626' : '#334155'};font-weight:600;margin:0;">{formatDate(task.due_date)}</p>
								</div>
								<div>
									<p style="font-size:8px;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;font-weight:700;margin:0 0 2px;">Evidencias</p>
									<p style="font-size:11px;font-weight:700;color:{task.evidence_count > 0 ? '#1d4ed8' : '#94a3b8'};margin:0;">{task.evidence_count} archivo{task.evidence_count !== 1 ? 's' : ''}</p>
								</div>
								<div>
									<p style="font-size:8px;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;font-weight:700;margin:0 0 2px;">Avance</p>
									<div style="display:flex;align-items:center;gap:6px;margin-top:3px;">
										<div style="flex:1;background:#e2e8f0;border-radius:99px;height:6px;overflow:hidden;">
											<div style="height:6px;border-radius:99px;background:{(task.progress_percentage ?? 0) >= 100 ? '#16a34a' : '#2563eb'};width:{task.progress_percentage ?? 0}%;"></div>
										</div>
										<span style="font-size:10px;color:#475569;font-weight:700;">{task.progress_percentage ?? 0}%</span>
									</div>
								</div>
							</div>
							<!-- Description + Notes -->
							{#if task.description || task.notes}
								<div style="padding:12px 16px;border-bottom:1px solid #f1f5f9;background:#fefefe;">
									{#if task.description}
										<p style="font-size:8px;color:#64748b;text-transform:uppercase;letter-spacing:1px;font-weight:700;margin:0 0 4px;">Descripción</p>
										<p style="font-size:11px;color:#334155;margin:0 0 {task.notes ? '10px' : '0'};line-height:1.6;">{task.description}</p>
									{/if}
									{#if task.notes}
										<p style="font-size:8px;color:#64748b;text-transform:uppercase;letter-spacing:1px;font-weight:700;margin:0 0 4px;">Notas / Observaciones</p>
										<p style="font-size:11px;color:#475569;margin:0;line-height:1.6;font-style:italic;">{task.notes}</p>
									{/if}
								</div>
							{/if}
							<!-- Photo evidences -->
							{#if imgEvs.length > 0}
								<div style="padding:14px 16px;border-bottom:1px solid #f1f5f9;background:#fafbff;">
									<p style="font-size:9px;color:#1d4ed8;text-transform:uppercase;letter-spacing:1px;font-weight:700;margin:0 0 10px;">📷 Fotografías y evidencias visuales ({imgEvs.length})</p>
									<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;">
										{#each imgEvs as ev}
											<div style="border:1px solid #e2e8f0;border-radius:8px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.08);">
												<img src="{ev.file_url}" alt="{ev.filename}" style="width:100%;height:160px;object-fit:cover;display:block;" />
												<div style="padding:7px 10px;background:#f8fafc;border-top:1px solid #e2e8f0;">
													<p style="font-size:9px;color:#475569;font-weight:600;margin:0 0 2px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{ev.filename}</p>
													{#if ev.comment}
														<p style="font-size:9px;color:#64748b;margin:0 0 2px;line-height:1.4;font-style:italic;">"{ev.comment}"</p>
													{/if}
													<p style="font-size:8px;color:#94a3b8;margin:0;">{evidenceTypeLabels[ev.evidence_type] ?? ev.evidence_type}{ev.uploader_name ? ` · ${ev.uploader_name}` : ''}{ev.uploaded_at ? ` · ${new Date(ev.uploaded_at).toLocaleDateString('es-MX')}` : ''}</p>
												</div>
											</div>
										{/each}
									</div>
								</div>
							{/if}
							<!-- File evidences -->
							{#if fileEvs.length > 0}
								<div style="padding:10px 16px;background:#f8fafc;">
									<p style="font-size:9px;color:#64748b;text-transform:uppercase;letter-spacing:1px;font-weight:700;margin:0 0 8px;">📎 Documentos adjuntos ({fileEvs.length})</p>
									<div style="display:flex;flex-direction:column;gap:4px;">
										{#each fileEvs as ev}
											<div style="display:flex;align-items:center;gap:10px;padding:6px 10px;border:1px solid #e2e8f0;border-radius:6px;background:#fff;">
												<span style="font-size:18px;flex-shrink:0;">📄</span>
												<div style="flex:1;min-width:0;">
													<p style="font-size:10px;font-weight:600;color:#334155;margin:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{ev.filename}</p>
													{#if ev.comment}
														<p style="font-size:9px;color:#64748b;margin:1px 0 0;font-style:italic;">{ev.comment}</p>
													{/if}
												</div>
												<div style="text-align:right;flex-shrink:0;">
													<span style="font-size:9px;color:#94a3b8;display:block;">{evidenceTypeLabels[ev.evidence_type] ?? ev.evidence_type}</span>
													{#if ev.uploader_name}<span style="font-size:8px;color:#94a3b8;">{ev.uploader_name}</span>{/if}
												</div>
											</div>
										{/each}
									</div>
								</div>
							{/if}
						</div>
					{/each}
				</div>
			{/if}
		</div>

		<!-- ═══ SECTION V: FIRMAS ═══ -->
		<div style="padding:28px 40px;border-top:2px solid #e2e8f0;background:#f8fafc;">
			<div style="display:flex;align-items:center;gap:10px;margin-bottom:20px;">
				<div style="width:4px;height:20px;background:#1d4ed8;border-radius:2px;flex-shrink:0;"></div>
				<p style="font-size:11px;font-weight:800;color:#0f2244;text-transform:uppercase;letter-spacing:2px;margin:0;">V · Certificación y Firmas</p>
			</div>
			<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:24px;margin-bottom:20px;">
				<div style="text-align:center;">
					<div style="height:60px;border-bottom:2px solid #334155;margin-bottom:8px;"></div>
					<p style="font-size:10px;font-weight:700;color:#334155;margin:0;">Responsable del Proyecto</p>
					<p style="font-size:9px;color:#64748b;margin:2px 0 0;">Nombre, Cargo y Firma</p>
				</div>
				<div style="text-align:center;">
					<div style="height:60px;border-bottom:2px solid #334155;margin-bottom:8px;"></div>
					<p style="font-size:10px;font-weight:700;color:#334155;margin:0;">Supervisor / Revisor</p>
					<p style="font-size:9px;color:#64748b;margin:2px 0 0;">Nombre, Cargo y Firma</p>
				</div>
				<div style="text-align:center;">
					<div style="height:60px;border-bottom:2px solid #334155;margin-bottom:8px;"></div>
					<p style="font-size:10px;font-weight:700;color:#334155;margin:0;">Autorizado por</p>
					<p style="font-size:9px;color:#64748b;margin:2px 0 0;">Nombre, Cargo y Firma</p>
				</div>
			</div>
			<div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;padding:12px 16px;">
				<p style="font-size:10px;color:#1e40af;font-weight:700;margin:0 0 4px;">Declaración de autenticidad</p>
				<p style="font-size:9px;color:#3730a3;margin:0;line-height:1.6;">El presente informe técnico ha sido generado de forma automática por el Sistema de Gestión de Cumplimiento Regulatorio con base en la información registrada en la plataforma. Los datos aquí consignados reflejan el estado actualizado del proyecto al momento de la generación del documento. Folio: {rptFolio} · Fecha: {reportDate}.</p>
			</div>
		</div>

		<!-- ═══ FOOTER ═══ -->
		<div style="background:#0f2244;padding:14px 40px;display:flex;justify-content:space-between;align-items:center;">
			<p style="color:#7dd3fc;font-size:9px;font-weight:600;margin:0;text-transform:uppercase;letter-spacing:1px;">Sistema de Gestión de Cumplimiento Regulatorio</p>
			<p style="color:#bfdbfe;font-size:9px;margin:0;">Folio: {rptFolio} · {reportDate} · CONFIDENCIAL</p>
		</div>

	</div><!-- end rpt-page -->
	</div><!-- end rpt-overlay -->
{/if}

<style>
	@media print {
		/* Ocultar todo el contenido de la página */
		:global(body *) {
			visibility: hidden;
		}
		/* Mostrar el overlay y todo su contenido interno */
		:global(.rpt-overlay),
		:global(.rpt-overlay *) {
			visibility: visible;
		}
		/* Posicionar el overlay para cubrir la hoja completa */
		:global(.rpt-overlay) {
			position: absolute !important;
			left: 0 !important;
			top: 0 !important;
			width: 100% !important;
			overflow: visible !important;
			background: #fff !important;
			z-index: 9999 !important;
		}
		/* Ocultar la barra de acciones al imprimir */
		:global(.rpt-no-print),
		:global(.rpt-no-print *) {
			visibility: hidden !important;
			display: none !important;
		}
		/* Página del reporte ocupa todo el ancho */
		:global(.rpt-page) {
			max-width: 100% !important;
			margin: 0 !important;
			box-shadow: none !important;
		}
	}
</style>

