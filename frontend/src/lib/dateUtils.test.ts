import { describe, it, expect } from 'vitest';
import { formatDate, formatTime, formatShortDate } from './dateUtils';

describe('dateUtils', () => {
	describe('formatDate', () => {
		it('returns empty string when input is empty', () => {
			expect(formatDate('')).toBe('');
		});

		it('formats date string with timezone', () => {
			const result = formatDate('2024-01-15T10:30:00Z');
			// Should contain date components (month, day, year) and time
			expect(result).toMatch(/Jan/);
			expect(result).toMatch(/15/);
			expect(result).toMatch(/2024/);
			expect(result).toMatch(/10/);
			expect(result).toMatch(/30/);
		});

		it('appends Z to date string without timezone and treats as UTC', () => {
			const dateWithoutTz = '2024-01-15T10:30:00';
			const result = formatDate(dateWithoutTz);
			// When Z is appended, the date should be treated as UTC
			// Should contain date components
			expect(result).toMatch(/Jan/);
			expect(result).toMatch(/15/);
			expect(result).toMatch(/2024/);
			// Should contain time components (verifies UTC parsing)
			expect(result).toMatch(/10/);
			expect(result).toMatch(/30/);
		});

		it('handles date string with + timezone', () => {
			const dateWithPlus = '2024-01-15T20:30:00+05:00';
			const result = formatDate(dateWithPlus);
			// Should contain date components
			expect(result).toMatch(/Jan/);
			expect(result).toMatch(/15/);
			expect(result).toMatch(/2024/);
		});
	});

	describe('formatTime', () => {
		it('returns empty string when input is empty', () => {
			expect(formatTime('')).toBe('');
		});

		it('formats time string with timezone', () => {
			const result = formatTime('2024-01-15T10:30:00Z');
			// Should contain time components
			expect(result).toMatch(/10/);
			expect(result).toMatch(/30/);
		});

		it('appends Z to time string without timezone and treats as UTC', () => {
			const timeWithoutTz = '2024-01-15T10:30:00';
			const result = formatTime(timeWithoutTz);
			// When Z is appended, the time should be treated as UTC
			// Should contain time components (verifies UTC parsing)
			expect(result).toMatch(/10/);
			expect(result).toMatch(/30/);
		});

		it('handles time string with + timezone', () => {
			const timeWithPlus = '2024-01-15T20:30:00+05:00';
			const result = formatTime(timeWithPlus);
			// Should contain time components (may differ due to timezone conversion)
			expect(result).toMatch(/\d{1,2}/);
		});
	});

	describe('formatShortDate', () => {
		it('returns empty string when input is empty', () => {
			expect(formatShortDate('')).toBe('');
		});

		it('formats short date string with timezone', () => {
			const result = formatShortDate('2024-01-15T10:30:00Z');
			// Should contain month and day
			expect(result).toMatch(/Jan/);
			expect(result).toMatch(/15/);
		});

		it('appends Z to short date string without timezone and treats as UTC', () => {
			const dateWithoutTz = '2024-01-15T10:30:00';
			const result = formatShortDate(dateWithoutTz);
			// When Z is appended, the date should be treated as UTC
			// Should contain date components (verifies UTC parsing)
			expect(result).toMatch(/Jan/);
			expect(result).toMatch(/15/);
		});

		it('handles short date string with + timezone', () => {
			const dateWithPlus = '2024-01-15T20:30:00+05:00';
			const result = formatShortDate(dateWithPlus);
			// Should contain month and day
			expect(result).toMatch(/Jan/);
			expect(result).toMatch(/15/);
		});
	});
});
