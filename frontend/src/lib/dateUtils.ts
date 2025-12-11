export function formatDate(dateStr: string): string {
	if (!dateStr) return '';

	// Ensure the date string is treated as UTC if it doesn't have timezone info
	let safeDateStr = dateStr;
	if (!dateStr.endsWith('Z') && !dateStr.includes('+')) {
		safeDateStr += 'Z';
	}

	return new Date(safeDateStr).toLocaleString(undefined, {
		month: 'short',
		day: 'numeric',
		year: 'numeric',
		hour: '2-digit',
		minute: '2-digit'
	});
}

export function formatTime(dateStr: string): string {
	if (!dateStr) return '';

	let safeDateStr = dateStr;
	if (!dateStr.endsWith('Z') && !dateStr.includes('+')) {
		safeDateStr += 'Z';
	}

	return new Date(safeDateStr).toLocaleTimeString([], {
		hour: '2-digit',
		minute: '2-digit'
	});
}

export function formatShortDate(dateStr: string): string {
	if (!dateStr) return '';

	let safeDateStr = dateStr;
	if (!dateStr.endsWith('Z') && !dateStr.includes('+')) {
		safeDateStr += 'Z';
	}

	return new Date(safeDateStr).toLocaleDateString(undefined, {
		month: 'short',
		day: 'numeric'
	});
}
