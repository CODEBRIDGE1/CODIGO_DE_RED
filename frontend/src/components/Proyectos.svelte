<script lang="ts">
	import { onMount } from 'svelte';

	function getToken(): string {
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
		project_type: string;
		status: string;
		priority?: string;
		start_date?: string;
		due_date?: string;
		task_summary?: {
			total: number;
			completed: number;
			pending: number;
		};
	}

	interface Task {
		id: number;
		code?: string;
		title: string;
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
		name: string;
		description?: string;
		company_name: string;
		project_type: string;
		status: string;
		priority?: string;
		start_date?: string;
		due_date?: string;
		tasks: Task[];
		metrics: {
			total_tasks: number;
			completed_tasks: number;
			pending_tasks: number;
			overdue_tasks: number;
			completion_percentage: number;
		};
	}

	let projects = $state<Project[]>([]);
	let companies = $state<Company[]>([]);
	let selectedProject = $state<ProjectDetail | null>(null);
	let loading = $state(true);
	let error = $state('');
	
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

	onMount(() => {
		loadProjects();
		loadCompanies();
	});

	async function loadProjects() {
		try {
			loading = true;
			console.log('Loading projects...');
			const params = new URLSearchParams();
			if (filterCompany) params.append('company_id', filterCompany);
			if (filterStatus) params.append('status', filterStatus);
			if (filterType) params.append('project_type', filterType);

			const url = `/api/v1/projects/?${params}`;
			console.log('Fetching:', url);
			const response = await fetch(url, {
				headers: { Authorization: `Bearer ${getToken()}` }
			});
			
			console.log('Response status:', response.status);
			if (!response.ok) throw new Error('Error al cargar proyectos');
			const data = await response.json();
			console.log('Data received:', data);
			projects = Array.isArray(data) ? data : (data.projects ?? data.items ?? []);
			console.log('Projects loaded:', projects.length);
		} catch (err) {
			console.error('Error loading projects:', err);
			error = err instanceof Error ? err.message : 'Error desconocido';
		} finally {
			loading = false;
			console.log('Loading finished');
		}
	}

	async function loadCompanies() {
		try {
			const response = await fetch(`/api/v1/companies/?page=1&page_size=100`, {
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
		try {
			const response = await fetch(`/api/v1/projects/`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					Authorization: `Bearer ${getToken()}`
				},
				body: JSON.stringify(formData)
			});

			if (!response.ok) {
				const data = await response.json();
				throw new Error(data.detail || 'Error al crear proyecto');
			}

			showCreateModal = false;
			resetForm();
			await loadProjects();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Error desconocido';
		}
	}

	async function loadProjectDetail(projectId: number) {
		try {
			console.log('Loading project detail for:', projectId);
			const response = await fetch(`/api/v1/projects/${projectId}`, {
				headers: { Authorization: `Bearer ${getToken()}` }
			});
			
			console.log('Response status:', response.status);
			if (!response.ok) throw new Error('Error al cargar detalle');
			selectedProject = await response.json();
			console.log('Selected project:', selectedProject);
			console.log('Opening modal, showDetailModal = true');
			showDetailModal = true;
			console.log('showDetailModal is now:', showDetailModal);
		} catch (err) {
			console.error('Error loading project detail:', err);
			error = err instanceof Error ? err.message : 'Error desconocido';
		}
	}

	async function updateTaskStatus(taskId: number, newStatus: string) {
		try {
			const response = await fetch(`/api/v1/projects/tasks/${taskId}`, {
				method: 'PUT',
				headers: {
					'Content-Type': 'application/json',
					Authorization: `Bearer ${getToken()}`
				},
				body: JSON.stringify({ status: newStatus })
			});

			if (!response.ok) throw new Error('Error al actualizar tarea');
			
			// Reload project detail
			if (selectedProject) {
				await loadProjectDetail(selectedProject.id);
			}
		} catch (err) {
			error = err instanceof Error ? err.message : 'Error desconocido';
		}
	}

	async function addCustomTask() {
		if (!selectedProject) return;

		try {
			const response = await fetch(`/api/v1/projects/${selectedProject.id}/tasks`, {
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
					const evResponse = await fetch(`/api/v1/projects/tasks/${createdTask.id}/evidences`, {
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
			const response = await fetch(
				`/api/v1/projects/${selectedProject.id}/available-obligations`,
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
				const taskRes = await fetch(`/api/v1/projects/${selectedProject!.id}/tasks`, {
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
						const evRes = await fetch(`/api/v1/projects/tasks/${createdTask.id}/evidences`, {
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
			await fetch(`/api/v1/projects/tasks/${taskId}`, {
				method: 'PUT',
				headers: {
					'Content-Type': 'application/json',
					Authorization: `Bearer ${getToken()}`
				},
				body: JSON.stringify({ progress_percentage: progress })
			});
			if (selectedProject) await loadProjectDetail(selectedProject.id);
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
			const response = await fetch(
				`/api/v1/projects/tasks/${task.id}/evidences`,
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
		if (!selectedTask || !evidenceFile) return;

		try {
			const formData = new FormData();
			formData.append('file', evidenceFile);
			formData.append('evidence_type', evidenceType);
			if (evidenceComment) formData.append('comment', evidenceComment);

			const response = await fetch(`/api/v1/projects/tasks/${selectedTask.id}/evidences`, {
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

	$effect(() => {
		if (filterCompany || filterStatus || filterType) {
			loadProjects();
		}
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
		<div class="text-center py-12">
			<div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
			<p class="mt-4 text-gray-600">Cargando proyectos...</p>
		</div>
	{:else if projects.length === 0}
		<div class="bg-white rounded-lg shadow p-12 text-center">
			<p class="text-gray-500 text-lg">No hay proyectos registrados</p>
			<button
				onclick={() => openCreateModal()}
				class="mt-4 text-blue-600 hover:text-blue-700"
			>
				Crear el primer proyecto
			</button>
		</div>
	{:else}
		<div class="bg-white rounded-lg shadow overflow-hidden">
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
						<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
					</tr>
				</thead>
				<tbody class="bg-white divide-y divide-gray-200">
					{#each projects as project}
						<tr class="hover:bg-gray-50">
							<td class="px-6 py-4 whitespace-nowrap">
								<div class="text-sm font-medium text-gray-900">{project.name}</div>
							</td>
							<td class="px-6 py-4 whitespace-nowrap">
								<div class="text-sm text-gray-900">{project.company_name}</div>
							</td>
							<td class="px-6 py-4 whitespace-nowrap">
								<span class="text-sm text-gray-600">{projectTypeLabels[project.project_type]}</span>
							</td>
							<td class="px-6 py-4 whitespace-nowrap">
								<span class="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full {getStatusColor(project.status)}">
									{statusLabels[project.status]}
								</span>
							</td>
							<td class="px-6 py-4 whitespace-nowrap">
								{#if project.priority}
									<span class="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full {getPriorityColor(project.priority)}">
										{priorityLabels[project.priority]}
									</span>
								{:else}
									<span class="text-sm text-gray-400">-</span>
								{/if}
							</td>
							<td class="px-6 py-4 whitespace-nowrap">
								{#if project.task_summary}
									<div class="text-sm">
										<span class="text-green-600 font-semibold">{project.task_summary.completed}</span>
										<span class="text-gray-400">/</span>
										<span class="text-gray-600">{project.task_summary.total}</span>
									</div>
								{:else}
									<span class="text-sm text-gray-400">0/0</span>
								{/if}
							</td>
							<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
								{formatDate(project.due_date)}
							</td>
							<td class="px-6 py-4 whitespace-nowrap text-sm">
								<button
									onclick={() => loadProjectDetail(project.id)}
									class="text-blue-600 hover:text-blue-900 mr-3"
								>
									Ver Detalle
								</button>
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
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

				<div class="flex justify-end gap-3 mt-6">
					<button
						type="button"
						onclick={() => showCreateModal = false}
						class="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
					>
						Cancelar
					</button>
					<button
						type="submit"
						class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
					>
						Crear Proyecto
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
			<div class="flex justify-between items-center mb-4">
				<div>
					<h3 class="text-2xl font-bold">{selectedProject.name}</h3>
					<p class="text-sm text-gray-600">{selectedProject.company_name}</p>
				</div>
				<button onclick={() => showDetailModal = false} class="text-gray-400 hover:text-gray-600 text-2xl">&times;</button>
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
						class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
					>
						Subir Evidencia
					</button>
				</div>
			</form>
		</div>
	</div>
{/if}
