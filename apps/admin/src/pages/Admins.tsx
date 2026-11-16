import { PlusOutlined } from '@ant-design/icons';
import { App, Button, Dropdown, Form, Input, Modal, Radio, Select, Table, Tag } from 'antd';
import { useState } from 'react';

import { AdminRow, api, errorText } from '../api';
import { LoadError, PageTitle } from '../components';
import { useLoad } from '../hooks';
import { useSession } from '../session';

const ROLES = [
  { value: 'superadmin', label: 'суперадмин' },
  { value: 'tenant_admin', label: 'администратор вуза' },
  { value: 'operator', label: 'оператор (расписание, группы)' },
];
const roleLabel = Object.fromEntries(ROLES.map((r) => [r.value, r.label]));

type AdminForm = { login: string; password: string; role: AdminRow['role']; tenant_id?: string };

export default function AdminsPage() {
  const { tenants, admin: me } = useSession();
  const { message, modal } = App.useApp();
  const [open, setOpen] = useState(false);
  const [form] = Form.useForm<AdminForm>();
  const role = Form.useWatch('role', form);
  const list = useLoad(() => api.get<AdminRow[]>('/admins'), []);

  const create = async (v: AdminForm) => {
    try {
      await api.post('/admins', v);
      setOpen(false);
      form.resetFields();
      list.reload();
    } catch (e) {
      message.error(errorText(e));
    }
  };
  const patch = async (a: AdminRow, body: Record<string, unknown>, done: string) => {
    try {
      await api.patch(`/admins/${a.id}`, body);
      message.success(done);
      list.reload();
    } catch (e) {
      message.error(errorText(e));
    }
  };
  const askPassword = (a: AdminRow) => {
    let value = '';
    modal.confirm({
      title: `Новый пароль для ${a.login}`,
      content: <Input.Password autoFocus onChange={(e) => { value = e.target.value; }} placeholder="не короче 12 символов" />,
      okText: 'Сменить',
      onOk: async () => {
        if (value.length < 12) {
          message.error('Пароль короче 12 символов');
          throw new Error('short');
        }
        await patch(a, { password: value }, 'Пароль изменён');
      },
    });
  };

  return (
    <>
      <PageTitle title="Администраторы" extra={<Button type="primary" icon={<PlusOutlined />} onClick={() => setOpen(true)}>Добавить</Button>} />
      <LoadError error={list.error} />
      <Table
        rowKey="id"
        loading={list.loading}
        dataSource={list.data}
        pagination={false}
        columns={[
          { title: 'Логин', dataIndex: 'login' },
          { title: 'Роль', dataIndex: 'role', render: (v) => roleLabel[v] },
          { title: 'Вуз', dataIndex: 'tenant_id', render: (v) => (v ? tenants.find((t) => t.id === v)?.slug ?? v.slice(0, 8) : 'все') },
          { title: 'Второй фактор', dataIndex: 'totp_enabled', render: (v) => (v ? <Tag color="green">настроен</Tag> : <Tag color="orange">нет</Tag>) },
          { title: 'Состояние', dataIndex: 'disabled', render: (v) => (v ? <Tag color="red">отключён</Tag> : 'активен') },
          {
            title: '', width: 120, render: (_, a) => a.id !== me.id && (
              <Dropdown
                trigger={['click']}
                menu={{
                  items: [
                    { key: 'toggle', label: a.disabled ? 'Включить' : 'Отключить', danger: !a.disabled },
                    { key: 'totp', label: 'Сбросить второй фактор' },
                    { key: 'password', label: 'Сменить пароль' },
                  ],
                  onClick: ({ key }) => {
                    if (key === 'toggle') patch(a, { disabled: !a.disabled }, a.disabled ? 'Включён' : 'Отключён');
                    if (key === 'totp') patch(a, { reset_totp: true }, 'При следующем входе он настроит код заново');
                    if (key === 'password') askPassword(a);
                  },
                }}
              >
                <Button size="small">Действия</Button>
              </Dropdown>
            ),
          },
        ]}
      />
      <Modal title="Новый администратор" open={open} onCancel={() => setOpen(false)} onOk={() => form.submit()} okText="Создать" forceRender>
        <Form form={form} layout="vertical" onFinish={create} initialValues={{ role: 'tenant_admin' }}>
          <Form.Item name="login" label="Логин" rules={[{ required: true, pattern: /^[a-z0-9._-]{3,64}$/, message: 'латиница, цифры, точка, дефис' }]}>
            <Input autoComplete="off" />
          </Form.Item>
          <Form.Item name="password" label="Временный пароль" rules={[{ required: true, min: 12 }]} extra="Передайте его лично. Второй фактор администратор настроит при первом входе.">
            <Input.Password autoComplete="new-password" />
          </Form.Item>
          <Form.Item name="role" label="Роль"><Radio.Group options={ROLES} /></Form.Item>
          {role !== 'superadmin' && (
            <Form.Item name="tenant_id" label="Вуз" rules={[{ required: true }]}>
              <Select options={tenants.map((t) => ({ value: t.id, label: t.short_name || t.name }))} />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </>
  );
}
