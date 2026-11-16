import { DeleteOutlined, MinusCircleOutlined, PlusOutlined } from '@ant-design/icons';
import {
  App, Button, Card, Checkbox, Col, DatePicker, Form, Input, InputNumber, Modal, Popconfirm, Radio, Row, Select, Space,
  Switch, Table, Tag,
} from 'antd';
import dayjs, { Dayjs } from 'dayjs';
import { useState } from 'react';

import { api, Campus, errorText, Tenant, Term } from '../api';
import { LoadError, NoTenant, PageTitle } from '../components';
import { useLoad } from '../hooks';
import { useCanManage, useSession, useTenant } from '../session';

const FEATURES: [string, string][] = [
  ['voice', 'Голосовой режим'],
  ['documents', 'Документы и вопросы по ним'],
  ['schedule', 'Расписание'],
  ['lectures', 'Конспекты лекций'],
  ['knowledge_base', 'База знаний вуза'],
  ['qr_login', 'Вход на ПК по QR-коду'],
  ['navigation', 'Навигация по кампусу'],
  ['courses', 'Курсы и материалы преподавателей'],
  ['wake_word', 'Слово активации'],
];
const DEFAULT_ON = new Set(['voice', 'documents', 'schedule', 'lectures', 'knowledge_base', 'qr_login']);
const TIME_RE = /^([01]\d|2[0-3]):[0-5]\d$/;
const TIMEZONES = ['Europe/Kaliningrad', 'Europe/Moscow', 'Europe/Samara', 'Asia/Yekaterinburg', 'Asia/Omsk',
  'Asia/Novosibirsk', 'Asia/Krasnoyarsk', 'Asia/Irkutsk', 'Asia/Yakutsk', 'Asia/Vladivostok', 'Asia/Magadan',
  'Asia/Kamchatka'];

type SettingsForm = {
  name: string; short_name?: string; timezone: string; is_active: boolean;
  teacher_names_mode: 'hide' | 'store'; download_site?: string; support_contact?: string;
  features: string[]; bells: { start: string; end: string }[];
};

function toForm(t: Tenant): SettingsForm {
  const st = t.settings ?? {};
  const features = st.features ?? {};
  return {
    name: t.name, short_name: t.short_name ?? undefined, timezone: t.timezone, is_active: t.is_active,
    teacher_names_mode: st.teacher_names_mode ?? 'hide', download_site: st.download_site, support_contact: st.support_contact,
    features: FEATURES.map(([k]) => k).filter((k) => (k in features ? !!features[k] : DEFAULT_ON.has(k))),
    bells: (st.bell_schedule ?? []).map(([start, end]: [string, string]) => ({ start, end })),
  };
}

export default function TenantsPage() {
  const { admin, reloadTenants, setTenantId } = useSession();
  const tenant = useTenant();
  const [creating, setCreating] = useState(false);
  const isSuper = admin.role === 'superadmin';
  return (
    <>
      <PageTitle
        title="Вуз и кампусы"
        extra={isSuper && <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreating(true)}>Новый вуз</Button>}
      />
      {tenant ? (
        <Row gutter={[16, 16]}>
          <Col xs={24} xl={14}><TenantSettings key={tenant.id} tenant={tenant} onSaved={reloadTenants} /></Col>
          <Col xs={24} xl={10}>
            <Space orientation="vertical" style={{ width: '100%' }} size={16}>
              <Campuses tenantId={tenant.id} />
              <Terms tenantId={tenant.id} />
            </Space>
          </Col>
        </Row>
      ) : (
        <NoTenant />
      )}
      <CreateTenant
        open={creating}
        onClose={() => setCreating(false)}
        onCreated={async (t) => {
          setCreating(false);
          await reloadTenants();
          setTenantId(t.id);
        }}
      />
    </>
  );
}

function TenantSettings({ tenant, onSaved }: { tenant: Tenant; onSaved: () => Promise<void> }) {
  const { message } = App.useApp();
  const { admin } = useSession();
  const canManage = useCanManage();
  const [form] = Form.useForm<SettingsForm>();
  const [busy, setBusy] = useState(false);

  const save = async (v: SettingsForm) => {
    setBusy(true);
    try {
      const features = Object.fromEntries(FEATURES.map(([k]) => [k, v.features.includes(k)]));
      await api.patch(`/tenants/${tenant.id}`, {
        name: v.name, short_name: v.short_name ?? '', timezone: v.timezone,
        is_active: admin.role === 'superadmin' ? v.is_active : undefined,
        settings: {
          teacher_names_mode: v.teacher_names_mode, download_site: v.download_site || null,
          support_contact: v.support_contact || null, features,
          bell_schedule: v.bells.map((b) => [b.start, b.end]),
        },
      });
      message.success('Сохранено');
      await onSaved();
    } catch (e) {
      message.error(errorText(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card title={`Настройки: ${tenant.name}`} extra={<Tag>{tenant.slug}</Tag>}>
      <Form form={form} layout="vertical" initialValues={toForm(tenant)} onFinish={save} disabled={!canManage}>
        <Row gutter={16}>
          <Col xs={24} md={16}><Form.Item name="name" label="Полное название" rules={[{ required: true, min: 2 }]}><Input /></Form.Item></Col>
          <Col xs={24} md={8}><Form.Item name="short_name" label="Краткое"><Input maxLength={50} /></Form.Item></Col>
          <Col xs={24} md={12}>
            <Form.Item name="timezone" label="Часовой пояс" rules={[{ required: true }]}>
              <Select showSearch options={TIMEZONES.map((z) => ({ value: z, label: z }))} />
            </Form.Item>
          </Col>
          <Col xs={24} md={12}>
            <Form.Item name="is_active" label="Вуз включён" valuePropName="checked">
              <Switch disabled={admin.role !== 'superadmin'} />
            </Form.Item>
          </Col>
        </Row>
        <Form.Item
          name="teacher_names_mode"
          label="Имена преподавателей в расписании"
          extra="Если не хранить, сервер знает только обезличенный ключ. Преподаватель увидит свои пары, указав имя в приложении."
        >
          <Radio.Group options={[{ value: 'hide', label: 'Не хранить на сервере' }, { value: 'store', label: 'Хранить и показывать' }]} />
        </Form.Item>
        <Row gutter={16}>
          <Col xs={24} md={12}>
            <Form.Item name="download_site" label="Сайт для скачивания (на листовках)"><Input placeholder="doomich.ru" /></Form.Item>
          </Col>
          <Col xs={24} md={12}>
            <Form.Item name="support_contact" label="Контакт поддержки"><Input placeholder="почта или чат" /></Form.Item>
          </Col>
        </Row>
        <Form.Item name="features" label="Возможности">
          <Checkbox.Group options={FEATURES.map(([value, label]) => ({ value, label }))} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: 4 }} />
        </Form.Item>
        <Form.Item label="Звонки (для шаблона с номерами пар)">
          <Form.List name="bells">
            {(fields, { add, remove }) => (
              <>
                {fields.map((f, i) => (
                  <div key={f.key} style={{ display: 'flex', gap: 8, alignItems: 'baseline' }}>
                    <span style={{ width: 56, display: 'inline-block' }}>{i + 1} пара</span>
                    <Form.Item name={[f.name, 'start']} rules={[{ required: true, pattern: TIME_RE, message: 'ЧЧ:ММ' }]}>
                      <Input placeholder="08:30" style={{ width: 90 }} />
                    </Form.Item>
                    <Form.Item name={[f.name, 'end']} rules={[{ required: true, pattern: TIME_RE, message: 'ЧЧ:ММ' }]}>
                      <Input placeholder="10:00" style={{ width: 90 }} />
                    </Form.Item>
                    <MinusCircleOutlined onClick={() => remove(f.name)} />
                  </div>
                ))}
                <Button type="dashed" onClick={() => add({ start: '', end: '' })} icon={<PlusOutlined />}>Добавить пару</Button>
              </>
            )}
          </Form.List>
        </Form.Item>
        <Button type="primary" htmlType="submit" loading={busy}>Сохранить</Button>
      </Form>
    </Card>
  );
}

function Campuses({ tenantId }: { tenantId: string }) {
  const { message } = App.useApp();
  const canManage = useCanManage();
  const list = useLoad(() => api.get<Campus[]>(`/tenants/${tenantId}/campuses`), [tenantId]);
  const [form] = Form.useForm();
  const add = async (v: { name: string; address?: string; lat?: number; lon?: number }) => {
    try {
      await api.post(`/tenants/${tenantId}/campuses`, v);
      form.resetFields();
      list.reload();
    } catch (e) {
      message.error(errorText(e));
    }
  };
  const remove = async (id: string) => {
    try {
      await api.del(`/campuses/${id}`);
      list.reload();
    } catch (e) {
      message.error(errorText(e));
    }
  };
  return (
    <Card title="Кампусы">
      <LoadError error={list.error} />
      <Table
        size="small" rowKey="id" pagination={false} loading={list.loading} dataSource={list.data}
        columns={[
          { title: 'Название', dataIndex: 'name' },
          { title: 'Адрес', dataIndex: 'address' },
          {
            title: '', width: 48, render: (_, c) => canManage && (
              <Popconfirm title="Удалить кампус? Привязки моделей этого кампуса тоже удалятся." onConfirm={() => remove(c.id)}>
                <Button size="small" danger icon={<DeleteOutlined />} />
              </Popconfirm>
            ),
          },
        ]}
      />
      {canManage && (
        <Form form={form} layout="inline" onFinish={add} style={{ marginTop: 12, rowGap: 8 }}>
          <Form.Item name="name" rules={[{ required: true }]}><Input placeholder="Название" /></Form.Item>
          <Form.Item name="address"><Input placeholder="Адрес" /></Form.Item>
          <Form.Item name="lat"><InputNumber placeholder="Широта" step={0.0001} style={{ width: 110 }} /></Form.Item>
          <Form.Item name="lon"><InputNumber placeholder="Долгота" step={0.0001} style={{ width: 110 }} /></Form.Item>
          <Button htmlType="submit" icon={<PlusOutlined />}>Добавить</Button>
        </Form>
      )}
    </Card>
  );
}

function Terms({ tenantId }: { tenantId: string }) {
  const { message } = App.useApp();
  const canManage = useCanManage();
  const list = useLoad(() => api.get<Term[]>(`/tenants/${tenantId}/terms`), [tenantId]);
  const [open, setOpen] = useState(false);
  const [form] = Form.useForm();
  const create = async (v: { name: string; range: [Dayjs, Dayjs]; first_week_odd: boolean; holidays?: Dayjs[] }) => {
    try {
      await api.post(`/tenants/${tenantId}/terms`, {
        name: v.name, starts_on: v.range[0].format('YYYY-MM-DD'), ends_on: v.range[1].format('YYYY-MM-DD'),
        first_week_odd: v.first_week_odd, holidays: (v.holidays ?? []).map((d) => d.format('YYYY-MM-DD')),
      });
      setOpen(false);
      form.resetFields();
      list.reload();
    } catch (e) {
      message.error(errorText(e));
    }
  };
  const remove = async (id: string) => {
    try {
      await api.del(`/terms/${id}`);
      list.reload();
    } catch (e) {
      message.error(errorText(e));
    }
  };
  return (
    <Card title="Семестры" extra={canManage && <Button icon={<PlusOutlined />} onClick={() => setOpen(true)}>Добавить</Button>}>
      <LoadError error={list.error} />
      <Table
        size="small" rowKey="id" pagination={false} loading={list.loading} dataSource={list.data}
        columns={[
          { title: 'Название', dataIndex: 'name' },
          { title: 'Даты', render: (_, t) => `${dayjs(t.starts_on).format('DD.MM.YYYY')} по ${dayjs(t.ends_on).format('DD.MM.YYYY')}` },
          { title: 'Первая неделя', dataIndex: 'first_week_odd', render: (v) => (v ? 'нечётная' : 'чётная') },
          { title: 'Выходных', dataIndex: 'holidays', render: (v: string[]) => v.length },
          {
            title: '', width: 48, render: (_, t) => canManage && (
              <Popconfirm title="Удалить семестр?" onConfirm={() => remove(t.id)}>
                <Button size="small" danger icon={<DeleteOutlined />} />
              </Popconfirm>
            ),
          },
        ]}
      />
      <Modal title="Новый семестр" open={open} onCancel={() => setOpen(false)} onOk={() => form.submit()} okText="Создать" destroyOnHidden>
        <Form form={form} layout="vertical" onFinish={create} initialValues={{ first_week_odd: true }}>
          <Form.Item name="name" label="Название" rules={[{ required: true }]}><Input placeholder="Весна 2027" /></Form.Item>
          <Form.Item name="range" label="Даты" rules={[{ required: true }]}><DatePicker.RangePicker format="DD.MM.YYYY" /></Form.Item>
          <Form.Item name="first_week_odd" label="Первая учебная неделя" valuePropName="checked">
            <Switch checkedChildren="нечётная" unCheckedChildren="чётная" />
          </Form.Item>
          <Form.Item name="holidays" label="Нерабочие дни">
            <DatePicker multiple format="DD.MM.YYYY" style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  );
}

function CreateTenant(props: { open: boolean; onClose: () => void; onCreated: (t: Tenant) => void }) {
  const { message } = App.useApp();
  const [form] = Form.useForm();
  const create = async (v: { slug: string; name: string; short_name?: string; timezone: string }) => {
    try {
      const t = await api.post<Tenant>('/tenants', {
        ...v,
        settings: { teacher_names_mode: 'hide', features: Object.fromEntries(FEATURES.map(([k]) => [k, DEFAULT_ON.has(k)])) },
      });
      form.resetFields();
      props.onCreated(t);
    } catch (e) {
      message.error(errorText(e));
    }
  };
  return (
    <Modal title="Новый вуз" open={props.open} onCancel={props.onClose} onOk={() => form.submit()} okText="Создать" destroyOnHidden>
      <Form form={form} layout="vertical" onFinish={create} initialValues={{ timezone: 'Europe/Moscow' }}>
        <Form.Item name="slug" label="Код (латиница)" rules={[{ required: true, pattern: /^[a-z0-9-]{2,64}$/, message: 'строчные латинские буквы, цифры и дефис' }]}>
          <Input placeholder="spbgu" />
        </Form.Item>
        <Form.Item name="name" label="Полное название" rules={[{ required: true, min: 2 }]}><Input /></Form.Item>
        <Form.Item name="short_name" label="Краткое название"><Input maxLength={50} /></Form.Item>
        <Form.Item name="timezone" label="Часовой пояс"><Select options={TIMEZONES.map((z) => ({ value: z, label: z }))} /></Form.Item>
      </Form>
    </Modal>
  );
}
