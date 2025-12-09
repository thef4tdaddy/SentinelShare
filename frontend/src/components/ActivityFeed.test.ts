import { render, screen } from '@testing-library/svelte';
import { describe, it, expect } from 'vitest';
import ActivityFeed from './ActivityFeed.svelte';

describe('ActivityFeed Component', () => {
    it('renders empty state message when no activities', () => {
        render(ActivityFeed, { activities: [] });
        expect(screen.getByText('No activity found.')).toBeTruthy();
    });

    it('renders activity rows correctly', () => {
        const activities = [
            { id: 1, subject: 'Receipt 1', sender: 'amazon', status: 'forwarded', category: 'amazon', processed_at: new Date().toISOString() },
            { id: 2, subject: 'Spam 1', sender: 'unknown', status: 'blocked', category: null, processed_at: new Date().toISOString() }
        ];
        render(ActivityFeed, { activities });
        expect(screen.getByText('Receipt 1')).toBeTruthy();
        expect(screen.getByText('Spam 1')).toBeTruthy();
        expect(screen.getAllByRole('row').length).toBe(3); // Header + 2 rows
    });

    it('renders table headers correctly', () => {
        render(ActivityFeed, { activities: [] });
        expect(screen.getByText('Date')).toBeTruthy();
        expect(screen.getByText('Subject')).toBeTruthy();
        expect(screen.getByText('Sender')).toBeTruthy();
        expect(screen.getByText('Status')).toBeTruthy();
        expect(screen.getByText('Category')).toBeTruthy();
    });

    it('renders Recent Activity title', () => {
        render(ActivityFeed, { activities: [] });
        expect(screen.getByText('Recent Activity')).toBeTruthy();
    });

    it('formats dates correctly', () => {
        const testDate = '2024-01-15T10:30:00Z';
        const activities = [
            { id: 1, subject: 'Test', sender: 'test', status: 'forwarded', category: 'test', processed_at: testDate }
        ];
        render(ActivityFeed, { activities });
        
        // The date should be formatted using toLocaleString
        const formattedDate = new Date(testDate).toLocaleString();
        expect(screen.getByText(formattedDate)).toBeTruthy();
    });

    it('renders status badge with correct class', () => {
        const activities = [
            { id: 1, subject: 'Test', sender: 'test', status: 'forwarded', category: 'test', processed_at: new Date().toISOString() }
        ];
        const { container } = render(ActivityFeed, { activities });
        const badge = container.querySelector('.badge.forwarded');
        expect(badge).toBeTruthy();
        expect(badge?.textContent?.trim()).toBe('forwarded');
    });

    it('renders category when present', () => {
        const activities = [
            { id: 1, subject: 'Test', sender: 'test', status: 'forwarded', category: 'amazon', processed_at: new Date().toISOString() }
        ];
        render(ActivityFeed, { activities });
        expect(screen.getByText('amazon')).toBeTruthy();
    });

    it('does not render category badge when category is null', () => {
        const activities = [
            { id: 1, subject: 'Test', sender: 'test', status: 'blocked', category: null, processed_at: new Date().toISOString() }
        ];
        const { container } = render(ActivityFeed, { activities });
        
        // Find the row and check the category cell
        const rows = container.querySelectorAll('tbody tr');
        expect(rows.length).toBe(1);
        
        const cells = rows[0].querySelectorAll('td');
        const categoryCell = cells[4]; // Category is the 5th column
        expect(categoryCell.textContent?.trim()).toBe('');
    });

    it('handles empty date string', () => {
        const activities = [
            { id: 1, subject: 'Test', sender: 'test', status: 'forwarded', category: 'test', processed_at: '' }
        ];
        render(ActivityFeed, { activities });
        expect(screen.getByText('Test')).toBeTruthy();
    });

    it('renders multiple activities with different statuses', () => {
        const activities = [
            { id: 1, subject: 'Receipt 1', sender: 'amazon', status: 'forwarded', category: 'amazon', processed_at: new Date().toISOString() },
            { id: 2, subject: 'Spam', sender: 'spam@example.com', status: 'blocked', category: null, processed_at: new Date().toISOString() },
            { id: 3, subject: 'Receipt 2', sender: 'ebay', status: 'forwarded', category: 'ebay', processed_at: new Date().toISOString() }
        ];
        render(ActivityFeed, { activities });
        
        expect(screen.getByText('Receipt 1')).toBeTruthy();
        expect(screen.getByText('Spam')).toBeTruthy();
        expect(screen.getByText('Receipt 2')).toBeTruthy();
        expect(screen.getAllByRole('row').length).toBe(4); // Header + 3 rows
    });
});
