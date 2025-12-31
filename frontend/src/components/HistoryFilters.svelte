<script lang="ts">
	import { Download } from 'lucide-svelte';

	interface Filters {
		status: string;
		date_from: string;
		date_to: string;
		sender: string;
		min_amount: string;
		max_amount: string;
	}

	interface Pagination {
		page: number;
		per_page: number;
		total: number;
		total_pages: number;
	}

	interface HistoryFiltersProps {
		filters: Filters;
		pagination: Pagination;
		loading: boolean;
		onFilterChange: () => void;
		onClearFilters: () => void;
		onExport: () => void;
	}

	let {
		filters = $bindable(),
		pagination,
		loading,
		onFilterChange,
		onClearFilters,
		onExport
	}: HistoryFiltersProps = $props();
</script>

<div class="card mb-6" role="search" aria-label="Email filters">
	<div class="flex flex-wrap gap-4 items-end">
		<div class="flex-1 min-w-[200px]">
			<label for="status-filter" class="block text-sm font-medium text-text-main mb-2">
				Status
			</label>
			<select
				id="status-filter"
				bind:value={filters.status}
				onchange={onFilterChange}
				class="input"
			>
				<option value="">All</option>
				<option value="forwarded">Forwarded</option>
				<option value="blocked">Blocked</option>
				<option value="ignored">Ignored</option>
				<option value="error">Error</option>
			</select>
		</div>

		<div class="flex-1 min-w-[200px]">
			<label for="sender-filter" class="block text-sm font-medium text-text-main mb-2">
				Vendor/Sender
			</label>
			<input
				id="sender-filter"
				type="text"
				bind:value={filters.sender}
				onchange={onFilterChange}
				placeholder="Search by sender..."
				class="input"
			/>
		</div>

		<div class="flex-1 min-w-[200px]">
			<label for="date-from" class="block text-sm font-medium text-text-main mb-2">
				From Date
			</label>
			<input
				id="date-from"
				type="datetime-local"
				bind:value={filters.date_from}
				onchange={onFilterChange}
				class="input"
			/>
		</div>

		<div class="flex-1 min-w-[200px]">
			<label for="date-to" class="block text-sm font-medium text-text-main mb-2"> To Date </label>
			<input
				id="date-to"
				type="datetime-local"
				bind:value={filters.date_to}
				onchange={onFilterChange}
				class="input"
			/>
		</div>

		<div class="flex-1 min-w-[150px]">
			<label for="min-amount" class="block text-sm font-medium text-text-main mb-2">
				Min Amount
			</label>
			<input
				id="min-amount"
				type="number"
				bind:value={filters.min_amount}
				onchange={onFilterChange}
				placeholder="0.00"
				step="0.01"
				min="0"
				class="input"
			/>
		</div>

		<div class="flex-1 min-w-[150px]">
			<label for="max-amount" class="block text-sm font-medium text-text-main mb-2">
				Max Amount
			</label>
			<input
				id="max-amount"
				type="number"
				bind:value={filters.max_amount}
				onchange={onFilterChange}
				placeholder="999.99"
				step="0.01"
				min="0"
				class="input"
			/>
		</div>

		<div class="sr-only" aria-live="polite">
			{loading ? 'Loading emails...' : `${pagination.total} emails found`}
		</div>

		<button onclick={onClearFilters} class="btn btn-secondary"> Clear Filters </button>

		<button onclick={onExport} class="btn btn-primary" title="Export to CSV">
			<Download size={16} />
			Export
		</button>
	</div>
</div>
