import { writable } from 'svelte/store';

type Theme = 'light' | 'dark';

const isBrowser = typeof window !== 'undefined';

function getInitialTheme(): Theme {
	if (!isBrowser) return 'light';
	
	// Check localStorage first
	const stored = localStorage.getItem('theme') as Theme | null;
	if (stored === 'light' || stored === 'dark') {
		return stored;
	}
	
	// Check system preference
	if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
		return 'dark';
	}
	
	return 'light';
}

function createThemeStore() {
	const initialTheme = getInitialTheme();
	const { subscribe, set, update } = writable<Theme>(initialTheme);
	
	// Initialize dark class on document
	if (isBrowser) {
		if (initialTheme === 'dark') {
			document.documentElement.classList.add('dark');
		} else {
			document.documentElement.classList.remove('dark');
		}

		// Listen for system theme preference changes when there is no explicit user preference
		if (typeof window.matchMedia === 'function') {
			const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

			const handleChange = (event: MediaQueryListEvent) => {
				// Do not override an explicit user choice stored in localStorage
				const stored = localStorage.getItem('theme') as Theme | null;
				if (stored === 'light' || stored === 'dark') {
					return;
				}

				const newTheme: Theme = event.matches ? 'dark' : 'light';
				// Update the store value without persisting to localStorage
				set(newTheme);

				if (newTheme === 'dark') {
					document.documentElement.classList.add('dark');
				} else {
					document.documentElement.classList.remove('dark');
				}
			};

			if (typeof mediaQuery.addEventListener === 'function') {
				mediaQuery.addEventListener('change', handleChange);
			} else if (typeof mediaQuery.addListener === 'function') {
				// Fallback for older browsers
				mediaQuery.addListener(handleChange);
			}
		}
	}
	
	return {
		subscribe,
		toggle: () => {
			update(current => {
				const newTheme = current === 'dark' ? 'light' : 'dark';
				if (isBrowser) {
					localStorage.setItem('theme', newTheme);
					if (newTheme === 'dark') {
						document.documentElement.classList.add('dark');
					} else {
						document.documentElement.classList.remove('dark');
					}
				}
				return newTheme;
			});
		},
		set: (theme: Theme) => {
			if (isBrowser) {
				localStorage.setItem('theme', theme);
				if (theme === 'dark') {
					document.documentElement.classList.add('dark');
				} else {
					document.documentElement.classList.remove('dark');
				}
			}
			set(theme);
		}
	};
}

export const theme = createThemeStore();
