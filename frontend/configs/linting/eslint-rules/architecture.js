export default {
  'no-restricted-imports': [
    'error',
    {
      paths: [
        {
          name: 'axios',
          message:
            'Please use the Service Layer and Custom Hooks (e.g., useUser, usePTO) instead of direct axios calls in components.',
        },
      ],
    },
  ],
};
