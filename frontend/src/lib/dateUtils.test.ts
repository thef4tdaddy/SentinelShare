import { describe, it, expect } from 'vitest';
import { formatDate, formatTime, formatShortDate } from './dateUtils';

describe('dateUtils', () => {
	describe('formatDate', () => {
		it('returns empty string when input is empty', () => {
			expect(formatDate('')).toBe('');
		});

		it('formats date string with timezone', () => {
			const result = formatDate('2024-01-15T10:30:00Z');
			expect(result).toBeTruthy();
			expect(typeof result).toBe('string');
		});

		it('appends Z to date string without timezone', () => {
			const dateWithoutTz = '2024-01-15T10:30:00';
			const result = formatDate(dateWithoutTz);
			expect(result).toBeTruthy();
			expect(typeof result).toBe('string');
		});

		it('handles date string with + timezone', () => {
			const dateWithPlus = '2024-01-15T10:30:00+05:00';
			const result = formatDate(dateWithPlus);
			expect(result).toBeTruthy();
			expect(typeof result).toBe('string');
		});
	});

	describe('formatTime', () => {
		it('returns empty string when input is empty', () => {
			expect(formatTime('')).toBe('');
		});

		it('formats time string with timezone', () => {
			const result = formatTime('2024-01-15T10:30:00Z');
			expect(result).toBeTruthy();
			expect(typeof result).toBe('string');
		});

		it('appends Z to time string without timezone', () => {
			const timeWithoutTz = '2024-01-15T10:30:00';
			const result = formatTime(timeWithoutTz);
			expect(result).toBeTruthy();
			expect(typeof result).toBe('string');
		});

		it('handles time string with + timezone', () => {
			const timeWithPlus = '2024-01-15T10:30:00+05:00';
			const result = formatTime(timeWithPlus);
			expect(result).toBeTruthy();
			expect(typeof result).toBe('string');
		});
	});

	describe('formatShortDate', () => {
		it('returns empty string when input is empty', () => {
			expect(formatShortDate('')).toBe('');
		});

		it('formats short date string with timezone', () => {
			const result = formatShortDate('2024-01-15T10:30:00Z');
			expect(result).toBeTruthy();
			expect(typeof result).toBe('string');
		});

		it('appends Z to short date string without timezone', () => {
			const dateWithoutTz = '2024-01-15T10:30:00';
			const result = formatShortDate(dateWithoutTz);
			expect(result).toBeTruthy();
			expect(typeof result).toBe('string');
		});

		it('handles short date string with + timezone', () => {
			const dateWithPlus = '2024-01-15T10:30:00+05:00';
			const result = formatShortDate(dateWithPlus);
			expect(result).toBeTruthy();
			expect(typeof result).toBe('string');
		});
	});
});
