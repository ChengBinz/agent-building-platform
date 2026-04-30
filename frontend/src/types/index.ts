// Shared TypeScript type definitions
// TODO: expand

export interface User {
  id: string;
  username: string;
  email: string;
  display_name?: string;
  is_active: boolean;
  is_superuser: boolean;
}
