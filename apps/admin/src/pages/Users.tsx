import { App, Button, Card, Form, Input, Radio, Typography } from 'antd';
import { useState } from 'react';

import { api, errorText } from '../api';
import { NoTenant, PageTitle } from '../components';
import { useCanManage, useTenant } from '../session';

export default function UsersPage() {
  const tenant = useTenant();
  const canManage = useCanManage();
  const { message } = App.useApp();
  const [busy, setBusy] = useState(false);
  if (!tenant) return <NoTenant />;
  const submit = async (v: { login: string; blocked: boolean }) => {
    setBusy(true);
    try {
      const out = await api.post<{ login: string; status: string }>(`/tenants/${tenant.id}/users/block`, v);
      message.success(out.status === 'blocked' ? `${out.login} заблокирован, доступ закрыт сразу` : `${out.login} разблокирован`);
    } catch (e) {
      message.error(errorText(e));
    } finally {
      setBusy(false);
    }
  };
  return (
    <>
      <PageTitle title="Блокировка пользователя" />
      <Card style={{ maxWidth: 560 }}>
        <Typography.Paragraph>
          Пользователи зарегистрированы под псевдонимами, и в панели нет их списка. Если на нарушителя пожаловались,
          узнайте у заявителя псевдоним (виден в настройках приложения) и введите его здесь.
        </Typography.Paragraph>
        <Form layout="vertical" onFinish={submit} initialValues={{ blocked: true }} disabled={!canManage}>
          <Form.Item name="login" label="Псевдоним" rules={[{ required: true }]}><Input autoComplete="off" /></Form.Item>
          <Form.Item name="blocked">
            <Radio.Group options={[{ value: true, label: 'Заблокировать' }, { value: false, label: 'Разблокировать' }]} />
          </Form.Item>
          <Button type="primary" danger htmlType="submit" loading={busy}>Применить</Button>
        </Form>
      </Card>
    </>
  );
}
