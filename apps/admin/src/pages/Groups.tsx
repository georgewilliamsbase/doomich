import { DeleteOutlined, EditOutlined, PlusOutlined } from '@ant-design/icons';
import { App, Button, Form, Input, InputNumber, Modal, Popconfirm, Select, Space, Switch, Table, Tag } from 'antd';
import { useState } from 'react';

import { api, errorText, Group } from '../api';
import { LoadError, NoTenant, PageTitle } from '../components';
import { useLoad } from '../hooks';
import { useCanManage, useTenant } from '../session';

type GroupForm = { code: string; name?: string; faculty?: string; year?: number; subgroups?: string[]; is_active: boolean };

export default function GroupsPage() {
  const tenant = useTenant();
  const { message } = App.useApp();
  const canManage = useCanManage();
  const [q, setQ] = useState('');
  const [editing, setEditing] = useState<Group | 'new' | null>(null);
  const [form] = Form.useForm<GroupForm>();
  const list = useLoad(
    () => (tenant ? api.get<Group[]>(`/tenants/${tenant.id}/groups${q ? `?q=${encodeURIComponent(q)}` : ''}`) : Promise.resolve([])),
    [tenant?.id, q],
  );
  if (!tenant) return <NoTenant />;

  const save = async (v: GroupForm) => {
    try {
      const body = { ...v, name: v.name || null, faculty: v.faculty || null, year: v.year ?? null, subgroups: v.subgroups ?? [] };
      if (editing === 'new') await api.post(`/tenants/${tenant.id}/groups`, body);
      else if (editing) await api.patch(`/groups/${editing.id}`, body);
      setEditing(null);
      list.reload();
    } catch (e) {
      message.error(errorText(e));
    }
  };
  const remove = async (g: Group) => {
    try {
      await api.del(`/groups/${g.id}`);
      list.reload();
    } catch (e) {
      message.error(errorText(e));
    }
  };
  const open = (g: Group | 'new') => {
    setEditing(g);
    form.resetFields();
    if (g !== 'new') {
      form.setFieldsValue({ code: g.code, name: g.name ?? undefined, faculty: g.faculty ?? undefined, year: g.year ?? undefined,
        subgroups: g.subgroups, is_active: g.is_active });
    }
  };

  return (
    <>
      <PageTitle
        title="Группы"
        extra={[
          <Input.Search key="q" placeholder="Поиск по коду" allowClear onSearch={setQ} style={{ width: 220 }} />,
          <Button key="n" type="primary" icon={<PlusOutlined />} onClick={() => open('new')}>Новая группа</Button>,
        ]}
      />
      <LoadError error={list.error} />
      <Table
        rowKey="id"
        loading={list.loading}
        dataSource={list.data}
        pagination={{ pageSize: 50, showSizeChanger: false }}
        columns={[
          { title: 'Код', dataIndex: 'code', sorter: (a, b) => a.code.localeCompare(b.code) },
          { title: 'Название', dataIndex: 'name' },
          { title: 'Факультет', dataIndex: 'faculty' },
          { title: 'Курс', dataIndex: 'year', width: 80 },
          { title: 'Подгруппы', dataIndex: 'subgroups', render: (v: string[]) => v.map((x) => <Tag key={x}>{x}</Tag>) },
          { title: 'Активна', dataIndex: 'is_active', width: 90, render: (v) => (v ? 'да' : <Tag>нет</Tag>) },
          {
            title: '', width: 96, render: (_, g) => (
              <Space>
                <Button size="small" icon={<EditOutlined />} onClick={() => open(g)} />
                {canManage && (
                  <Popconfirm title="Удалить группу? Её занятия удалятся, студенты останутся без группы." onConfirm={() => remove(g)}>
                    <Button size="small" danger icon={<DeleteOutlined />} />
                  </Popconfirm>
                )}
              </Space>
            ),
          },
        ]}
      />
      <Modal
        title={editing === 'new' ? 'Новая группа' : 'Группа'}
        open={editing !== null}
        onCancel={() => setEditing(null)}
        onOk={() => form.submit()}
        okText="Сохранить"
        forceRender
      >
        <Form form={form} layout="vertical" onFinish={save} initialValues={{ code: '', subgroups: [], is_active: true }}>
          <Form.Item name="code" label="Код группы" rules={[{ required: true, max: 50 }]} extra="Как в расписании вуза, например ИВТ-21">
            <Input />
          </Form.Item>
          <Form.Item name="name" label="Название"><Input /></Form.Item>
          <Form.Item name="faculty" label="Факультет или институт"><Input /></Form.Item>
          <Form.Item name="year" label="Курс"><InputNumber min={1} max={7} /></Form.Item>
          <Form.Item name="subgroups" label="Подгруппы">
            <Select mode="tags" tokenSeparators={[',', ' ']} placeholder="1, 2" open={false} />
          </Form.Item>
          <Form.Item name="is_active" label="Активна" valuePropName="checked"><Switch /></Form.Item>
        </Form>
      </Modal>
    </>
  );
}
