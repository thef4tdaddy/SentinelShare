import { render, screen } from '@testing-library/svelte';
import { describe, it, expect } from 'vitest';
import StatsCard from './StatsCard.svelte';

describe('StatsCard Component', () => {
    it('renders title and value correctly', () => {
        render(StatsCard, { title: 'Test Stat', value: 42 });
        expect(screen.getByText('Test Stat')).toBeTruthy();
        expect(screen.getByText('42')).toBeTruthy();
    });

    it('renders subtext when provided', () => {
        render(StatsCard, { title: 'Test Stat', value: 10, subtext: 'more info' });
        expect(screen.getByText('more info')).toBeTruthy();
    });

    it('does not render subtext when not provided', () => {
        render(StatsCard, { title: 'Test Stat', value: 10 });
        const subtext = screen.queryByText('more info');
        expect(subtext).toBeNull();
    });

    it('renders with string value', () => {
        render(StatsCard, { title: 'Status', value: 'Active' });
        expect(screen.getByText('Status')).toBeTruthy();
        expect(screen.getByText('Active')).toBeTruthy();
    });

    it('renders with zero value', () => {
        render(StatsCard, { title: 'Count', value: 0 });
        expect(screen.getByText('Count')).toBeTruthy();
        expect(screen.getByText('0')).toBeTruthy();
    });

    it('renders with large number value', () => {
        render(StatsCard, { title: 'Total', value: 1000000 });
        expect(screen.getByText('Total')).toBeTruthy();
        expect(screen.getByText('1000000')).toBeTruthy();
    });

    it('renders with negative value', () => {
        render(StatsCard, { title: 'Balance', value: -50 });
        expect(screen.getByText('Balance')).toBeTruthy();
        expect(screen.getByText('-50')).toBeTruthy();
    });

    it('renders with empty subtext', () => {
        render(StatsCard, { title: 'Test', value: 5, subtext: '' });
        expect(screen.getByText('Test')).toBeTruthy();
        expect(screen.getByText('5')).toBeTruthy();
        // Empty subtext should not be rendered due to the {#if subtext} check
    });

    it('has correct card class', () => {
        const { container } = render(StatsCard, { title: 'Test', value: 42 });
        const card = container.querySelector('.card');
        expect(card).toBeTruthy();
    });

    it('renders long title correctly', () => {
        const longTitle = 'This is a very long title for testing purposes';
        render(StatsCard, { title: longTitle, value: 100 });
        expect(screen.getByText(longTitle)).toBeTruthy();
    });

    it('renders long subtext correctly', () => {
        const longSubtext = 'This is a very long subtext that provides detailed information';
        render(StatsCard, { title: 'Test', value: 50, subtext: longSubtext });
        expect(screen.getByText(longSubtext)).toBeTruthy();
    });
});
