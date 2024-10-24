interface ApiErrorData {
  message: string;
  status?: number;
  code?: string;
}

export const createApiError = (error: ApiErrorData): Error => {
  const errorMessage = `API Error: ${error.message}${error.code ? ` (${error.code})` : ''}`;
  return new Error(errorMessage);
};

export const handleApiError = (error: unknown): Error => {
  if (error instanceof Error) {
    return createApiError({ message: error.message });
  }
  return createApiError({ message: 'An unexpected error occurred' });
};
