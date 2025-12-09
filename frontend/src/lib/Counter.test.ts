import { render, screen, fireEvent } from '@testing-library/svelte';
import { describe, it, expect } from 'vitest';
import Counter from './Counter.svelte';

describe('Counter Component', () => {
    it('renders with initial count of 0', () => {
        render(Counter);
        expect(screen.getByText('count is 0')).toBeTruthy();
    });

    it('increments count when button is clicked', async () => {
        render(Counter);
        const button = screen.getByText('count is 0');
        await fireEvent.click(button);
        expect(screen.getByText('count is 1')).toBeTruthy();
    });

    it('increments count multiple times', async () => {
        render(Counter);
        const button = screen.getByRole('button');
        await fireEvent.click(button);
        await fireEvent.click(button);
        await fireEvent.click(button);
        expect(screen.getByText('count is 3')).toBeTruthy();
    });
});
