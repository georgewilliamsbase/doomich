import { DeleteOutlined, EditOutlined, PlusOutlined } from '@ant-design/icons';
import { App, Button, Form, Input, InputNumber, Modal, Popconfirm, Radio, Select, Space, Table, Tag, Typography } from 'antd';
import { useState } from 'react';

import { api, Binding, Campus, errorText } from '../api';
import { jsonRule, JsonInput, LoadError, PageTitle, parseJson } from '../components';
import { useLoad } from '../hooks';
import { useSession, useTenant } from '../session';
import { fmt } from '../time';

const COMPONENTS: [string, string][] = [
  ['llm_adapter', 'Адаптер языковой модели (вуз)'],
  ['asr_profile', 'Профиль распознавания речи'],
  ['tts_voice', 'Голос синтеза'],
  ['kws_model', 'Слово активации'],
  ['vpr_index', 'Навигация по фото (кампус)'],
  ['embed_model', 'Модель эмбеддингов'],
];
const componentLabel = Object.fromEntries(COMPONENTS);

type BindingForm = {
  scope: 'global' | 'tenant'; campus_id?: string; component: string; model_ref: string; stage: 'canary' | 'production';
  traffic_pct: number; params: string;
};

export default function BindingsPage() {
  const tenant = useTenant();
  const { tenants } = useSession();
  const { message } = App.useApp();
  const [editing, setEditing] = useState<Binding | 'new' | null>(null);
  const [form] = Form.useForm<BindingForm>();
  const scope = Form.useWatch('scope', form);
  const component = Form.useWatch('component', form);
  const stage = Form.useWatch('stage', form);
  const list = useLoad(() => api.get<Binding[]>(`/bindings${tenant ? `?tenant_id=${tenant.id}` : ''}`), [tenant?.id]);
  const campuses = useLoad(() => (tenant ? api.get<Campus[]>(`/tenants/${tenant.id}/campuses`) : Promise.resolve([])), [tenant?.id]);
  const campusName = (id: string | null) => campuses.data?.find((c) => c.id === id)?.name ?? id?.slice(0, 8);

  const open = (b: Binding | 'new') => {
    setEditing(b);
    form.setFieldsValue(b === 'new'
      ? { scope: 'tenant', component: 'llm_adapter', model_ref: '', stage: 'production', traffic_pct: 100, params: '{}', campus_id: undefined }
      : { scope: b.tenant_id ? 'tenant' : 'global', campus_id: b.campus_id ?? undefined, component: b.component, model_ref: b.model_ref,
          stage: b.stage, traffic_pct: b.traffic_pct, params: JSON.stringify(b.params, null, 2) });
  };
  const save = async (v: BindingForm) => {
    try {
      await api.put('/bindings', {
        tenant_id: v.scope === 'tenant' ? tenant?.id : null,
        campus_id: v.scope === 'tenant' && v.component === 'vpr_index' ? v.campus_id ?? null : null,
        component: v.component, model_ref: v.model_ref, stage: v.stage,
        traffic_pct: v.stage === 'production' ? 100 : v.traffic_pct, params: parseJson(v.params),
      });
      setEditing(null);
      list.reload();
    } catch (e) {
      message.error(errorText(e));
    }
  };
  const remove = async (b: Binding) => {
    try {
      await api.del(`/bindings/${b.id}`);
      list.reload();
    } catch (e) {
      message.error(errorText(e));
    }
  };

  return (
    <>
      <PageTitle title="Модели" extra={<Button type="primary" icon={<PlusOutlined />} onClick={() => open('new')}>Привязать модель</Button>} />
      <Typography.Paragraph type="secondary">
        Какая модель обслуживает вуз или кампус. Обычно привязки создаёт ML-платформа командой dml deploy после оценки модели,
        здесь их можно проверить и откатить. Канареечная привязка получает указанную долю пользователей.
      </Typography.Paragraph>
      <LoadError error={list.error} />
      <Table
        rowKey="id"
        loading={list.loading}
        dataSource={list.data}
        pagination={false}
        columns={[
          { title: 'Компонент', dataIndex: 'component', render: (v) => componentLabel[v] ?? v },
          {
            title: 'Где', render: (_, b) => (b.tenant_id
              ? <Space size={4}><Tag color="blue">{tenants.find((t) => t.id === b.tenant_id)?.slug ?? 'вуз'}</Tag>{b.campus_id && <Tag>{campusName(b.campus_id)}</Tag>}</Space>
              : <Tag>все вузы</Tag>),
          },
          { title: 'Модель', dataIndex: 'model_ref', render: (v) => <Typography.Text code>{v}</Typography.Text> },
          { title: 'Стадия', render: (_, b) => (b.stage === 'canary' ? <Tag color="orange">канарейка {b.traffic_pct}%</Tag> : <Tag color="green">основная</Tag>) },
          { title: 'Обновлена', dataIndex: 'updated_at', render: (v) => fmt(v, tenant?.timezone ?? 'Europe/Moscow') },
          {
            title: '', width: 96, render: (_, b) => (
              <Space>
                <Button size="small" icon={<EditOutlined />} onClick={() => open(b)} />
                <Popconfirm title="Удалить привязку? Компонент вернётся к модели уровнем выше." onConfirm={() => remove(b)}>
                  <Button size="small" danger icon={<DeleteOutlined />} />
                </Popconfirm>
              </Space>
            ),
          },
        ]}
      />
      <Modal title="Привязка модели" open={editing !== null} onCancel={() => setEditing(null)} onOk={() => form.submit()} okText="Сохранить" forceRender width={600}>
        <Form form={form} layout="vertical" onFinish={save}>
          <Form.Item name="component" label="Компонент"><Select options={COMPONENTS.map(([value, label]) => ({ value, label }))} disabled={editing !== 'new'} /></Form.Item>
          <Form.Item name="scope" label="Для кого">
            <Radio.Group disabled={editing !== 'new'} options={[{ value: 'tenant', label: `вуз ${tenant?.slug ?? ''}`, disabled: !tenant }, { value: 'global', label: 'все вузы по умолчанию' }]} />
          </Form.Item>
          {scope === 'tenant' && component === 'vpr_index' && (
            <Form.Item name="campus_id" label="Кампус" rules={[{ required: true }]}>
              <Select disabled={editing !== 'new'} options={(campuses.data ?? []).map((c) => ({ value: c.id, label: c.name }))} />
            </Form.Item>
          )}
          <Form.Item name="model_ref" label="Модель из реестра" rules={[{ required: true }]} extra="Имя и версия из реестра ML-платформы, например llm-lora-spbgu@3">
            <Input />
          </Form.Item>
          <Space size={16}>
            <Form.Item name="stage" label="Стадия">
              <Radio.Group disabled={editing !== 'new'} options={[{ value: 'production', label: 'основная' }, { value: 'canary', label: 'канарейка' }]} />
            </Form.Item>
            {stage === 'canary' && <Form.Item name="traffic_pct" label="Доля, %"><InputNumber min={0} max={100} /></Form.Item>}
          </Space>
          <Form.Item name="params" label="Параметры (JSON)" rules={[jsonRule]}><JsonInput rows={4} /></Form.Item>
        </Form>
      </Modal>
    </>
  );
}
