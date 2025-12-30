<script lang="ts">
	import { onMount } from 'svelte';
	import { Upload, FileText, X } from 'lucide-svelte';

	interface DropzoneProps {
		onFileSelected: (file: File) => void;
		onClearFile?: () => void;
		accept?: string;
		maxSizeMB?: number;
		disabled?: boolean;
		registerApi?: (api: { clearFile: () => void }) => void;
	}

	let {
		onFileSelected,
		onClearFile,
		accept = '.pdf,.png,.jpg,.jpeg',
		maxSizeMB = 10,
		disabled = false,
		registerApi
	}: DropzoneProps = $props();

	let isDragging = $state(false);
	let selectedFile = $state<File | null>(null);
	let error = $state<string | null>(null);
	let fileInputElement: HTMLInputElement;

	const allowedTypes = ['application/pdf', 'image/png', 'image/jpeg'];

	function handleDragOver(e: DragEvent) {
		if (disabled) return;
		e.preventDefault();
		isDragging = true;
	}

	function handleDragLeave(e: DragEvent) {
		if (disabled) return;
		e.preventDefault();
		isDragging = false;
	}

	function handleDrop(e: DragEvent) {
		if (disabled) return;
		e.preventDefault();
		isDragging = false;

		const files = e.dataTransfer?.files;
		if (files && files.length > 0) {
			handleFile(files[0]);
		}
	}

	function handleFileInput(e: Event) {
		if (disabled) return;
		const target = e.target as HTMLInputElement;
		const files = target.files;
		if (files && files.length > 0) {
			handleFile(files[0]);
		}
	}

	function handleFile(file: File) {
		// Prevent handling new files if disabled (e.g., during upload)
		if (disabled) return;

		error = null;

		// Validate file type
		if (!allowedTypes.includes(file.type)) {
			error = 'Invalid file type. Please upload PDF, PNG, or JPG files.';
			return;
		}

		// Validate file size
		const maxSizeBytes = maxSizeMB * 1024 * 1024;
		if (file.size > maxSizeBytes) {
			error = `File size exceeds ${maxSizeMB}MB limit.`;
			return;
		}

		selectedFile = file;
		onFileSelected(file);
	}

	function clearFile() {
		selectedFile = null;
		error = null;
		if (fileInputElement) {
			fileInputElement.value = '';
		}
		// Notify parent component if callback is provided
		if (onClearFile) {
			onClearFile();
		}
	}

	function openFileDialog() {
		if (disabled) return;
		fileInputElement?.click();
	}

	// Register API once on mount
	onMount(() => {
		if (registerApi) {
			registerApi({ clearFile });
		}
	});
</script>

<div class="w-full">
	<input
		bind:this={fileInputElement}
		type="file"
		{accept}
		onchange={handleFileInput}
		class="hidden"
		{disabled}
		aria-label="File upload input"
	/>

	{#if !selectedFile}
		<button
			type="button"
			onclick={openFileDialog}
			ondragover={handleDragOver}
			ondragleave={handleDragLeave}
			ondrop={handleDrop}
			{disabled}
			aria-busy={disabled}
			aria-describedby="dropzone-help-text"
			class="w-full border-2 border-dashed rounded-lg p-8 transition-all duration-200 {isDragging
				? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
				: 'border-border dark:border-border-dark hover:border-blue-400 dark:hover:border-blue-600'} {disabled
				? 'opacity-50 cursor-not-allowed'
				: 'cursor-pointer'}"
		>
			<div class="flex flex-col items-center justify-center gap-3 text-center">
				<div
					class="p-3 rounded-full {isDragging
						? 'bg-blue-500 text-white'
						: 'bg-gray-100 text-text-secondary dark:bg-gray-800 dark:text-text-secondary-dark'}"
				>
					<Upload size={24} />
				</div>
				<div>
					<p class="text-base font-semibold text-text-main dark:text-text-main-dark mb-1">
						{isDragging ? 'Drop file here' : 'Upload Receipt'}
					</p>
					<p class="text-sm text-text-secondary dark:text-text-secondary-dark">
						Drag & drop or click to browse
					</p>
					<p
						id="dropzone-help-text"
						class="text-xs text-text-tertiary dark:text-text-tertiary-dark mt-2"
					>
						PDF, PNG, JPG (max {maxSizeMB}MB)
					</p>
				</div>
			</div>
		</button>
	{:else}
		<div
			class="border border-border dark:border-border-dark rounded-lg p-4 bg-bg-card dark:bg-bg-card-dark"
		>
			<div class="flex items-start gap-3">
				<div class="p-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
					<FileText size={24} class="text-blue-600 dark:text-blue-400" />
				</div>
				<div class="flex-1 min-w-0">
					<p
						class="text-sm font-medium text-text-main dark:text-text-main-dark truncate"
						title={selectedFile.name}
					>
						{selectedFile.name}
					</p>
					<p class="text-xs text-text-secondary dark:text-text-secondary-dark mt-1">
						{(selectedFile.size / 1024 / 1024).toFixed(2)} MB
					</p>
				</div>
				<button
					type="button"
					onclick={clearFile}
					{disabled}
					class="p-1 text-text-secondary hover:text-red-600 dark:text-text-secondary-dark dark:hover:text-red-400 transition-colors"
					aria-label="Remove file"
				>
					<X size={20} />
				</button>
			</div>
		</div>
	{/if}

	{#if error}
		<p class="mt-2 text-sm text-red-600 dark:text-red-400" role="alert">{error}</p>
	{/if}

	<div class="sr-only" aria-live="polite">
		{#if selectedFile}
			File {selectedFile.name} selected.
		{:else if error}
			Error: {error}
		{/if}
	</div>
</div>
