import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import Login from './Login.svelte';

// Mock fetch globally
globalThis.fetch = vi.fn() as typeof fetch;

describe('Login Component', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	afterEach(() => {
		vi.restoreAllMocks();
	});

	it('renders the component with title and logo', () => {
		const onLoginSuccess = vi.fn();
		render(Login, { props: { onLoginSuccess } });

		expect(screen.getByText('SentinelShare')).toBeTruthy();
		expect(screen.getByText('Single-User Access')).toBeTruthy();
	});

	it('renders password input field', () => {
		const onLoginSuccess = vi.fn();
		render(Login, { props: { onLoginSuccess } });

		const passwordInput = screen.getByLabelText('Password');
		expect(passwordInput).toBeTruthy();
		expect(passwordInput.getAttribute('type')).toBe('password');
		expect(passwordInput.getAttribute('placeholder')).toBe('Enter dashboard password...');
	});

	it('renders submit button with correct text', () => {
		const onLoginSuccess = vi.fn();
		render(Login, { props: { onLoginSuccess } });

		expect(screen.getByText('Access Dashboard')).toBeTruthy();
	});

	it('updates password value when typing', async () => {
		const onLoginSuccess = vi.fn();
		render(Login, { props: { onLoginSuccess } });

		const passwordInput = screen.getByLabelText('Password') as HTMLInputElement;
		await fireEvent.input(passwordInput, { target: { value: 'test123' } });

		expect(passwordInput.value).toBe('test123');
	});

	it('calls onLoginSuccess on successful login', async () => {
		const onLoginSuccess = vi.fn();
		vi.mocked(fetch).mockResolvedValueOnce({
			ok: true,
			json: async () => ({ status: 'success' })
		} as Response);

		render(Login, { props: { onLoginSuccess } });

		const passwordInput = screen.getByLabelText('Password');
		const submitButton = screen.getByText('Access Dashboard');

		await fireEvent.input(passwordInput, { target: { value: 'correctpass' } });
		await fireEvent.click(submitButton);

		await waitFor(() => {
			expect(fetch).toHaveBeenCalledWith('/api/auth/login', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ password: 'correctpass' })
			});
			expect(onLoginSuccess).toHaveBeenCalled();
		});
	});

	it('displays error message on invalid password', async () => {
		const onLoginSuccess = vi.fn();
		vi.mocked(fetch).mockResolvedValueOnce({
			ok: false
		} as Response);

		render(Login, { props: { onLoginSuccess } });

		const passwordInput = screen.getByLabelText('Password');
		const submitButton = screen.getByText('Access Dashboard');

		await fireEvent.input(passwordInput, { target: { value: 'wrongpass' } });
		await fireEvent.click(submitButton);

		await waitFor(() => {
			expect(screen.getByText('Invalid password')).toBeTruthy();
		});

		expect(onLoginSuccess).not.toHaveBeenCalled();
	});

	it('displays error message on connection error', async () => {
		const onLoginSuccess = vi.fn();
		vi.mocked(fetch).mockRejectedValueOnce(new Error('Network error'));

		render(Login, { props: { onLoginSuccess } });

		const passwordInput = screen.getByLabelText('Password');
		const submitButton = screen.getByText('Access Dashboard');

		await fireEvent.input(passwordInput, { target: { value: 'testpass' } });
		await fireEvent.click(submitButton);

		await waitFor(() => {
			expect(screen.getByText('Connection error')).toBeTruthy();
		});

		expect(onLoginSuccess).not.toHaveBeenCalled();
	});

	it('shows loading state and disables button during login attempt', async () => {
		const onLoginSuccess = vi.fn();
		let resolvePromise: (value: Response) => void;
		const fetchPromise = new Promise<Response>((resolve) => {
			resolvePromise = resolve;
		});
		vi.mocked(fetch).mockReturnValueOnce(fetchPromise);

		render(Login, { props: { onLoginSuccess } });

		const passwordInput = screen.getByLabelText('Password');
		const submitButton = screen.getByText('Access Dashboard') as HTMLButtonElement;

		await fireEvent.input(passwordInput, { target: { value: 'testpass' } });
		await fireEvent.click(submitButton);

		// Verify loading UI appears
		await waitFor(() => {
			expect(screen.getByText('Verifying...')).toBeTruthy();
			expect(submitButton.disabled).toBe(true);
		});

		// Resolve the promise
		resolvePromise!({
			ok: true,
			json: async () => ({ status: 'success' })
		} as Response);

		// Verify button is re-enabled after completion
		await waitFor(() => {
			expect(submitButton.disabled).toBe(false);
			expect(onLoginSuccess).toHaveBeenCalled();
		});
	});

	it('handles form submission via onsubmit event', async () => {
		const onLoginSuccess = vi.fn();
		vi.mocked(fetch).mockResolvedValueOnce({
			ok: true,
			json: async () => ({ status: 'success' })
		} as Response);

		render(Login, { props: { onLoginSuccess } });

		const passwordInput = screen.getByLabelText('Password');
		const form = passwordInput.closest('form') as HTMLFormElement;

		await fireEvent.input(passwordInput, { target: { value: 'testpass' } });
		await fireEvent.submit(form);

		await waitFor(() => {
			expect(fetch).toHaveBeenCalled();
			expect(onLoginSuccess).toHaveBeenCalled();
		});
	});

	it('clears error message on subsequent login attempt', async () => {
		const onLoginSuccess = vi.fn();
		
		// First attempt - failure
		vi.mocked(fetch).mockResolvedValueOnce({
			ok: false
		} as Response);

		render(Login, { props: { onLoginSuccess } });

		const passwordInput = screen.getByLabelText('Password');
		const submitButton = screen.getByText('Access Dashboard');

		await fireEvent.input(passwordInput, { target: { value: 'wrongpass' } });
		await fireEvent.click(submitButton);

		await waitFor(() => {
			expect(screen.getByText('Invalid password')).toBeTruthy();
		});

		// Second attempt - success
		vi.mocked(fetch).mockResolvedValueOnce({
			ok: true,
			json: async () => ({ status: 'success' })
		} as Response);

		await fireEvent.input(passwordInput, { target: { value: 'correctpass' } });
		await fireEvent.click(submitButton);

		await waitFor(() => {
			expect(onLoginSuccess).toHaveBeenCalled();
		});

		// Error should be cleared
		expect(screen.queryByText('Invalid password')).toBeFalsy();
	});

	it('does not call onLoginSuccess if response status is not success', async () => {
		const onLoginSuccess = vi.fn();
		vi.mocked(fetch).mockResolvedValueOnce({
			ok: true,
			json: async () => ({ status: 'failed' })
		} as Response);

		render(Login, { props: { onLoginSuccess } });

		const passwordInput = screen.getByLabelText('Password');
		const submitButton = screen.getByText('Access Dashboard');

		await fireEvent.input(passwordInput, { target: { value: 'testpass' } });
		await fireEvent.click(submitButton);

		await waitFor(() => {
			expect(fetch).toHaveBeenCalled();
		});

		expect(onLoginSuccess).not.toHaveBeenCalled();
	});

	it('renders Lock icon in header', () => {
		const onLoginSuccess = vi.fn();
		const { container } = render(Login, { props: { onLoginSuccess } });

		// Check for Lock icon SVG element within the blue circle container
		const lockIconContainer = container.querySelector('.bg-blue-50');
		expect(lockIconContainer).toBeTruthy();
		
		// Verify SVG icon is present (lucide-svelte renders as SVG)
		const svgIcon = lockIconContainer?.querySelector('svg');
		expect(svgIcon).toBeTruthy();
		expect(svgIcon?.classList.contains('lucide-icon')).toBe(true);
	});

	it('renders LogIn icon on submit button when not loading', () => {
		const onLoginSuccess = vi.fn();
		render(Login, { props: { onLoginSuccess } });

		const button = screen.getByText('Access Dashboard');
		expect(button).toBeTruthy();
		
		// Verify LogIn icon SVG is present in button (not loading state)
		const svgIcon = button.querySelector('svg');
		expect(svgIcon).toBeTruthy();
		expect(svgIcon?.classList.contains('lucide-icon')).toBe(true);
	});
});
