import { createContext, useContext } from 'react';

import type { Admin, Tenant } from './api';

export type Session = {
  admin: Admin;
  tenants: Tenant[];
  tenantId: string | null;
  setTenantId: (id: string) => void;
  reloadTenants: () => Promise<void>;
  signOut: () => void;
};

export const SessionContext = createContext<Session | null>(null);

export function useSession(): Session {
  const s = useContext(SessionContext);
  if (!s) throw new Error('нет SessionContext');
  return s;
}

/** Выбранный вуз. Администратор вуза всегда видит только свой. */
export function useTenant(): Tenant | undefined {
  const { tenants, tenantId } = useSession();
  return tenants.find((t) => t.id === tenantId);
}

/** Может ли администратор менять настройки (оператор только смотрит и правит расписание). */
export function useCanManage(): boolean {
  const { admin } = useSession();
  return admin.role !== 'operator';
}
