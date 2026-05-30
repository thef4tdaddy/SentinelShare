export interface Email {
	id: number;
	email_id: string;
	subject: string;
	sender: string;
	received_at: string;
	processed_at: string;
	status: string;
	account_email?: string;
	category?: string;
	amount?: number;
	reason?: string;
}

export interface Run {
	run_time: string;
	first_processed: string;
	last_processed: string;
	total_emails: number;
	forwarded: number;
	blocked: number;
	errors: number;
	email_ids: number[];
}

export interface AnalysisOutcome {
	email_id: number;
	analysis: {
		steps: Array<{
			step: string;
			result: boolean;
			detail?: string;
		}>;
		final_decision: boolean;
	};
}

export interface Stats {
	total: number;
	forwarded: number;
	blocked: number;
	errors: number;
	total_amount: number;
	status_breakdown: Record<string, number>;
}

export interface Filters {
	status: string;
	date_from: string;
	date_to: string;
	sender: string;
	min_amount: string;
	max_amount: string;
}

export interface Pagination {
	page: number;
	per_page: number;
	total: number;
	total_pages: number;
}
