import { Mail, CheckCircle, XCircle, AlertCircle } from 'lucide-svelte';
import type { ComponentType } from 'svelte';

export function formatAmount(amount?: number): string {
	if (amount === undefined || amount === null) return '-';
	return `$${amount.toFixed(2)}`;
}

export function getStatusIcon(status: string): ComponentType {
	switch (status) {
		case 'forwarded':
			return CheckCircle;
		case 'blocked':
		case 'ignored':
			return XCircle;
		case 'error':
			return AlertCircle;
		default:
			return Mail;
	}
}

export function getStatusColor(status: string): string {
	switch (status) {
		case 'forwarded':
			return 'bg-emerald-100 text-emerald-800 border-emerald-200';
		case 'blocked':
		case 'ignored':
			return 'bg-gray-100 text-gray-600 border-gray-200 dark:bg-gray-800 dark:text-gray-400 dark:border-gray-700';
		case 'error':
			return 'bg-red-100 text-red-800 border-red-200';
		default:
			return 'bg-blue-100 text-blue-600 border-blue-200';
	}
}
