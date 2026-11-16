import {
  ApartmentOutlined,
  AuditOutlined,
  CalendarOutlined,
  CloudUploadOutlined,
  DashboardOutlined,
  ExperimentOutlined,
  KeyOutlined,
  LikeOutlined,
  LogoutOutlined,
  QrcodeOutlined,
  StopOutlined,
  TeamOutlined,
  UserOutlined,
} from '@ant-design/icons';
import { Button, Layout, Menu, Select, Space, Spin, Typography } from 'antd';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom';

import { Admin, api, setUnauthorizedHandler, Tenant, tokenStore } from './api';
import AdminsPage from './pages/Admins';
import AuditPage from './pages/Audit';
import BindingsPage from './pages/Bindings';
import DashboardPage from './pages/Dashboard';
import FeedbackPage from './pages/Feedback';
import GroupsPage from './pages/Groups';
import InvitesPage from './pages/Invites';
import LoginPage from './pages/Login';
import ReleasesPage from './pages/Releases';
import SchedulePage from './pages/Schedule';
import TenantsPage from './pages/Tenants';
import UsersPage from './pages/Users';
import { Session, SessionContext, useSession } from './session';

const TENANT_KEY = 'doomich.admin.tenant';

function readTenant(): string | null {
  try {
    return localStorage.getItem(TENANT_KEY);
  } catch {
    return null;
  }
}

async function fetchSession(token: string): Promise<{ me: Admin; list: Tenant[] }> {
  tokenStore.set(token);
  const [me, list] = await Promise.all([api.get<Admin>('/me'), api.get<Tenant[]>('/tenants')]);
  return { me, list };
}

export default function App() {
  const [admin, setAdmin] = useState<Admin | null>(null);
  const [loading, setLoading] = useState(() => tokenStore.get() !== null);
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [tenantId, setTenantIdState] = useState<string | null>(readTenant);
  const navigate = useNavigate();

  const setTenantId = useCallback((id: string) => {
    setTenantIdState(id);
    try {
      localStorage.setItem(TENANT_KEY, id);
    } catch {
      // хранилище недоступно, выбор просто не запомнится
    }
  }, []);

  const applyTenants = useCallback((list: Tenant[]) => {
    setTenants(list);
    setTenantIdState((cur) => (cur && list.some((t) => t.id === cur) ? cur : list[0]?.id ?? null));
  }, []);

  const reloadTenants = useCallback(async () => {
    applyTenants(await api.get<Tenant[]>('/tenants'));
  }, [applyTenants]);

  const apply = useCallback(({ me, list }: { me: Admin; list: Tenant[] }) => {
    applyTenants(list);
    setAdmin(me);
  }, [applyTenants]);

  const signIn = useCallback(async (token: string) => apply(await fetchSession(token)), [apply]);

  const signOut = useCallback(() => {
    tokenStore.clear();
    setAdmin(null);
    navigate('/login');
  }, [navigate]);

  useEffect(() => {
    setUnauthorizedHandler(() => setAdmin(null));
    const token = tokenStore.get();
    if (!token) return;
    fetchSession(token)
      .then(apply, () => tokenStore.clear())
      .finally(() => setLoading(false));
  }, [apply]);

  const session = useMemo<Session | null>(
    () => (admin ? { admin, tenants, tenantId, setTenantId, reloadTenants, signOut } : null),
    [admin, tenants, tenantId, setTenantId, reloadTenants, signOut],
  );

  if (loading) return <Spin fullscreen />;
  if (!session) {
    return (
      <Routes>
        <Route path="/login" element={<LoginPage onToken={signIn} />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }
  return (
    <SessionContext.Provider value={session}>
      <Routes>
        <Route path="/login" element={<Navigate to="/" replace />} />
        <Route path="/*" element={<Shell />} />
      </Routes>
    </SessionContext.Provider>
  );
}

function Shell() {
  const { admin, tenants, tenantId, setTenantId, signOut } = useSession();
  const location = useLocation();
  const navigate = useNavigate();
  const isSuper = admin.role === 'superadmin';
  const items = [
    { key: '/', icon: <DashboardOutlined />, label: 'Состояние' },
    { key: '/tenants', icon: <ApartmentOutlined />, label: 'Вуз и кампусы' },
    { key: '/groups', icon: <TeamOutlined />, label: 'Группы' },
    { key: '/invites', icon: <QrcodeOutlined />, label: 'Коды приглашения' },
    { key: '/schedule', icon: <CalendarOutlined />, label: 'Расписание' },
    { key: '/feedback', icon: <LikeOutlined />, label: 'Оценки ответов' },
    { key: '/users', icon: <StopOutlined />, label: 'Блокировка' },
    { key: '/audit', icon: <AuditOutlined />, label: 'Журнал действий' },
    ...(isSuper
      ? [
          { key: '/bindings', icon: <ExperimentOutlined />, label: 'Модели' },
          { key: '/releases', icon: <CloudUploadOutlined />, label: 'Релизы приложений' },
          { key: '/admins', icon: <KeyOutlined />, label: 'Администраторы' },
        ]
      : []),
  ];
  const selected = items.find((i) => i.key !== '/' && location.pathname.startsWith(i.key))?.key ?? '/';
  const roleName = { superadmin: 'суперадмин', tenant_admin: 'администратор вуза', operator: 'оператор' }[admin.role];
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Layout.Sider breakpoint="lg" collapsedWidth={64} theme="light" width={240}>
        <div style={{ padding: 16 }}>
          <Typography.Title level={4} style={{ margin: 0 }}>Думыч</Typography.Title>
          <Typography.Text type="secondary">администрирование</Typography.Text>
        </div>
        <Menu mode="inline" selectedKeys={[selected]} items={items} onClick={(e) => navigate(e.key)} />
      </Layout.Sider>
      <Layout>
        <Layout.Header
          style={{ background: 'transparent', display: 'flex', flexWrap: 'wrap', gap: 12, justifyContent: 'space-between', alignItems: 'center', paddingInline: 24, height: 'auto', minHeight: 64 }}
        >
          <Space>
            <Typography.Text>Вуз:</Typography.Text>
            <Select
              style={{ minWidth: 260 }}
              value={tenantId ?? undefined}
              onChange={setTenantId}
              options={tenants.map((t) => ({ value: t.id, label: t.short_name ? `${t.short_name} (${t.slug})` : t.name }))}
              disabled={!isSuper}
              placeholder="вузов пока нет"
            />
          </Space>
          <Space>
            <UserOutlined />
            <Typography.Text>{admin.login}, {roleName}</Typography.Text>
            <Button icon={<LogoutOutlined />} onClick={signOut}>Выйти</Button>
          </Space>
        </Layout.Header>
        <Layout.Content style={{ padding: 24 }}>
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/tenants" element={<TenantsPage />} />
            <Route path="/groups" element={<GroupsPage />} />
            <Route path="/invites" element={<InvitesPage />} />
            <Route path="/schedule" element={<SchedulePage />} />
            <Route path="/feedback" element={<FeedbackPage />} />
            <Route path="/users" element={<UsersPage />} />
            <Route path="/audit" element={<AuditPage />} />
            {isSuper && <Route path="/bindings" element={<BindingsPage />} />}
            {isSuper && <Route path="/releases" element={<ReleasesPage />} />}
            {isSuper && <Route path="/admins" element={<AdminsPage />} />}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Layout.Content>
      </Layout>
    </Layout>
  );
}

