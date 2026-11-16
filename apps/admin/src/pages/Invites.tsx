import { DownloadOutlined, EyeOutlined, PlusOutlined, PrinterOutlined, StopOutlined } from '@ant-design/icons';
import {
  Alert, App, Button, DatePicker, Drawer, Form, Input, InputNumber, Modal, Popconfirm, Radio, Select, Space, Switch, Table,
  Tag, Typography,
} from 'antd';
import type { Dayjs } from 'dayjs';
import { useState } from 'react';

import { api, Batch, BatchCode, download, errorText, Group } from '../api';
import { LoadError, NoTenant, PageTitle, roleLabels } from '../components';
import { useLoad } from '../hooks';
import { useCanManage, useSession, useTenant } from '../session';
import { fmt } from '../time';

type CreateForm = {
  label: string; count: number; role: 'student' | 'teacher' | 'staff'; kind: 'register' | 'role_upgrade';
  group_id?: string; max_uses: number; expires_on?: Dayjs; is_beta: boolean;
};

function saveText(lines: string[], filename: string) {
  const url = URL.createObjectURL(new Blob([lines.join('\n') + '\n'], { type: 'text/plain;charset=utf-8' }));
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export default function InvitesPage() {
  const tenant = useTenant();
  const { admin } = useSession();
  const canManage = useCanManage();
  const { message } = App.useApp();
  const [creating, setCreating] = useState(false);
  const [created, setCreated] = useState<{ batch: Batch; codes: string[] } | null>(null);
  const [viewing, setViewing] = useState<Batch | null>(null);
  const [form] = Form.useForm<CreateForm>();
  const tid = tenant?.id;
  const batches = useLoad(() => (tid ? api.get<Batch[]>(`/tenants/${tid}/invite-batches`) : Promise.resolve([])), [tid]);
  const groups = useLoad(() => (tid ? api.get<Group[]>(`/tenants/${tid}/groups`) : Promise.resolve([])), [tid]);
  if (!tenant) return <NoTenant />;
  const groupCode = (id: string | null) => groups.data?.find((g) => g.id === id)?.code ?? '';

  const create = async (v: CreateForm) => {
    try {
      const out = await api.post<{ batch: Batch; codes: string[] }>(`/tenants/${tenant.id}/invite-batches`, {
        ...v, expires_on: v.expires_on?.format('YYYY-MM-DD'),
      });
      setCreating(false);
      form.resetFields();
      setCreated(out);
      batches.reload();
    } catch (e) {
      message.error(errorText(e));
    }
  };
  const print = (b: Batch) => download(`/invite-batches/${b.id}/print.pdf`, `invites-${b.label}.pdf`).catch((e) => message.error(errorText(e)));
  const revoke = async (b: Batch) => {
    try {
      await api.post(`/invite-batches/${b.id}/revoke`);
      message.success('Коды отозваны');
      batches.reload();
    } catch (e) {
      message.error(errorText(e));
    }
  };

  return (
    <>
      <PageTitle
        title="Коды приглашения"
        extra={canManage && <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreating(true)}>Выпустить коды</Button>}
      />
      <Typography.Paragraph type="secondary">
        Код нужен для регистрации. Сервер не связывает код с человеком: кому достался какой листок, знает только тот, кто раздавал.
      </Typography.Paragraph>
      <LoadError error={batches.error} />
      <Table
        rowKey="id"
        loading={batches.loading}
        dataSource={batches.data}
        pagination={{ pageSize: 30, showSizeChanger: false }}
        columns={[
          { title: 'Партия', dataIndex: 'label' },
          {
            title: 'Кому', render: (_, b) => (
              <Space size={4} wrap>
                <Tag color={b.kind === 'role_upgrade' ? 'purple' : 'blue'}>{b.kind === 'role_upgrade' ? 'смена роли' : 'регистрация'}</Tag>
                <Tag>{roleLabels[b.role]}</Tag>
                {b.group_id && <Tag color="geekblue">{groupCode(b.group_id)}</Tag>}
                {b.is_beta && <Tag color="gold">бета</Tag>}
              </Space>
            ),
          },
          { title: 'Кодов', dataIndex: 'code_count', width: 80 },
          { title: 'Активаций', render: (_, b) => `${b.stats.activations ?? 0} из ${b.code_count * b.max_uses}` },
          { title: 'Отозвано', render: (_, b) => b.stats.revoked ?? 0, width: 90 },
          { title: 'Действует до', dataIndex: 'expires_on', render: (v) => v ?? 'бессрочно' },
          { title: 'Создана', dataIndex: 'created_at', render: (v) => fmt(v, tenant.timezone) },
          {
            title: '', width: 140, render: (_, b) => canManage && (
              <Space>
                <Button size="small" icon={<EyeOutlined />} onClick={() => setViewing(b)} title="Коды" />
                <Button size="small" icon={<PrinterOutlined />} onClick={() => print(b)} title="Листовки PDF" />
                <Popconfirm title="Отозвать все коды партии? Уже зарегистрированные останутся." onConfirm={() => revoke(b)}>
                  <Button size="small" danger icon={<StopOutlined />} title="Отозвать" />
                </Popconfirm>
              </Space>
            ),
          },
        ]}
      />

      <Modal title="Новая партия кодов" open={creating} onCancel={() => setCreating(false)} onOk={() => form.submit()} okText="Выпустить" forceRender>
        <Form
          form={form}
          layout="vertical"
          onFinish={create}
          initialValues={{ count: 30, role: 'student', kind: 'register', max_uses: 1, is_beta: false }}
        >
          <Form.Item name="label" label="Название партии" rules={[{ required: true }]} extra="Только для вас, например: ИВТ-21, раздача 1 сентября">
            <Input />
          </Form.Item>
          <Form.Item name="kind" label="Назначение">
            <Radio.Group options={[{ value: 'register', label: 'Регистрация' }, { value: 'role_upgrade', label: 'Подтверждение роли' }]} />
          </Form.Item>
          <Form.Item name="role" label="Роль">
            <Radio.Group
              options={[
                { value: 'student', label: 'студент' },
                { value: 'teacher', label: 'преподаватель' },
                { value: 'staff', label: 'сотрудник', disabled: admin.role !== 'superadmin' },
              ]}
            />
          </Form.Item>
          <Form.Item name="group_id" label="Группа (подставится при регистрации)">
            <Select allowClear showSearch optionFilterProp="label" options={(groups.data ?? []).map((g) => ({ value: g.id, label: g.code }))} />
          </Form.Item>
          <Space size={16} wrap>
            <Form.Item name="count" label="Количество кодов" rules={[{ required: true }]}><InputNumber min={1} max={5000} /></Form.Item>
            <Form.Item name="max_uses" label="Активаций на код" extra="Больше 1 для общего кода на поток"><InputNumber min={1} max={10000} /></Form.Item>
            <Form.Item name="expires_on" label="Действует до"><DatePicker format="DD.MM.YYYY" /></Form.Item>
            <Form.Item name="is_beta" label="Бета-версия" valuePropName="checked"><Switch /></Form.Item>
          </Space>
        </Form>
      </Modal>

      <Modal
        title={`Коды выпущены: ${created?.batch.label ?? ''}`}
        open={created !== null}
        onCancel={() => setCreated(null)}
        footer={[
          <Button key="t" icon={<DownloadOutlined />} onClick={() => created && saveText(created.codes, `invites-${created.batch.label}.txt`)}>Текстом</Button>,
          <Button key="p" icon={<PrinterOutlined />} onClick={() => created && print(created.batch)}>Листовки PDF</Button>,
          <Button key="c" type="primary" onClick={() => setCreated(null)}>Готово</Button>,
        ]}
      >
        <Alert type="info" showIcon style={{ marginBottom: 12 }} title="Коды можно посмотреть и распечатать позже из списка партий." />
        <Input.TextArea readOnly rows={10} value={created?.codes.join('\n')} style={{ fontFamily: 'monospace' }} />
      </Modal>

      <BatchDrawer batch={viewing} onClose={() => setViewing(null)} />
    </>
  );
}

function BatchDrawer({ batch, onClose }: { batch: Batch | null; onClose: () => void }) {
  const detail = useLoad(
    () => (batch ? api.get<Batch & { codes: BatchCode[] }>(`/invite-batches/${batch.id}`) : Promise.resolve(undefined)),
    [batch?.id],
  );
  return (
    <Drawer title={batch?.label} open={batch !== null} onClose={onClose} size={480}>
      <LoadError error={detail.error} />
      <Table
        size="small"
        rowKey="id"
        loading={detail.loading}
        dataSource={detail.data?.codes}
        pagination={{ pageSize: 100, showSizeChanger: false }}
        columns={[
          { title: 'Код', dataIndex: 'code', render: (v) => <Typography.Text code copyable>{v}</Typography.Text> },
          { title: 'Активаций', dataIndex: 'uses', width: 100 },
          { title: '', dataIndex: 'revoked', width: 90, render: (v) => v && <Tag color="red">отозван</Tag> },
        ]}
      />
    </Drawer>
  );
}
