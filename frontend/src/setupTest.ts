import { cleanup } from '@testing-library/svelte';
import { afterEach } from 'vitest';
import '@testing-library/jest-dom'; // Optional: for custom matchers

afterEach(() => {
	cleanup();
});
