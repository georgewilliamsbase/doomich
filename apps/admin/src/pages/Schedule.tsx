import {
  CheckOutlined, DeleteOutlined, DownloadOutlined, EditOutlined, InboxOutlined, PlusOutlined, SyncOutlined,
} from '@ant-design/icons';
import {
  Alert, App, Button, Card, DatePicker, Descriptions, Form, Input, Modal, Popconfirm, Radio, Select, Space, Switch,
  Table, Tabs, Tag, Typography, Upload,
} from 'antd';
import dayjs, { Dayjs } from 'dayjs';
import { useState } from 'react';

import { api, download, errorText, Group, ImportReport, Lesson, Source, Tenant } from '../api';
import { jsonRule, JsonInput, LoadError, NoTenant, PageTitle, parseJson, SyncStatusTag } from '../components';
import { useLoad } from '../hooks';
import { useCanManage, useTenant } from '../session';
import { fmt, fromWall, toWall } from '../time';

const KINDS: [string, string][] = [
  ['lecture', 'лекция'], ['practice', 'практика, семинар'], ['lab', 'лабораторная'],
  ['exam', 'экзамен'], ['credit', 'зачёт'], ['consultation', 'консультация'], ['other', 'другое'],
];
const kindLabel = Object.fromEntries(KINDS);

const SOURCE_HINTS: Record<string, string> = {
  xlsx_url: '{"url": "https://example.ru/schedule.xlsx", "strict": false}',
  csv_url: '{"url": "https://example.ru/schedule.csv"}',
  ics_url: '{"feeds": [{"group": "ИВТ-21", "url": "https://example.ru/ivt-21.ics"}]}',
  json_api: '{"url": "https://example.ru/api/lessons?group={group}&from={date_from}&to={date_to}", "groups": ["ИВТ-21"], "items_path": "data", "fields": {"group": "group", "subject": "title", "start": "start", "end": "end", "room": "room"}}',
  html_table: '{"pages": [{"group": "ИВТ-21", "url": "https://example.ru/ivt-21.html"}], "table": "table"}',
  python: '{"class": "university_adapter:Adapter"}',
};

export default function SchedulePage() {
  const tenant = useTenant();
  if (!tenant) return <NoTenant />;
  return (
    <>
      <PageTitle
        title="Расписание"
        extra={<Button icon={<DownloadOutlined />} onClick={() => download('/schedule/template.xlsx', 'doomich-schedule-template.xlsx')}>Шаблон Excel</Button>}
      />
      <Tabs
        destroyOnHidden
        items={[
          { key: 'import', label: 'Загрузка файла', children: <ImportTab tenant={tenant} /> },
          { key: 'sources', label: 'Автоматические источники', children: <SourcesTab tenant={tenant} /> },
          { key: 'lessons', label: 'Занятия', children: <LessonsTab tenant={tenant} /> },
        ]}
      />
    </>
  );
}

function ImportTab({ tenant }: { tenant: Tenant }) {
  const { message } = App.useApp();
  const [file, setFile] = useState<File | null>(null);
  const [group, setGroup] = useState('');
  const [report, setReport] = useState<ImportReport | null>(null);
  const [busy, setBusy] = useState(false);
  const isIcs = file?.name.toLowerCase().endsWith('.ics') ?? false;

  const send = async (dryRun: boolean, force = false) => {
    if (!file) return;
    const fd = new FormData();
    fd.append('file', file);
    fd.append('dry_run', String(dryRun));
    fd.append('force', String(force));
    if (group) fd.append('group', group);
    setBusy(true);
    try {
      const out = await api.post<ImportReport>(`/tenants/${tenant.id}/schedule/import`, fd);
      setReport(out);
      if (out.applied) message.success(`Загружено занятий: ${out.lessons}`);
    } catch (e) {
      message.error(errorText(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Space orientation="vertical" style={{ width: '100%' }} size={16}>
      <Typography.Paragraph type="secondary" style={{ margin: 0 }}>
        Подходит шаблон Думыча (xlsx или csv) и файлы iCalendar (.ics). Сначала файл проверяется без записи: вы увидите,
        сколько строк разобрано и где ошибки. Загрузка заменяет занятия, внесённые вручную, в тех же группах и датах.
      </Typography.Paragraph>
      <Upload.Dragger
        accept=".xlsx,.csv,.ics"
        maxCount={1}
        beforeUpload={(f) => {
          setFile(f);
          setReport(null);
          return false;
        }}
        onRemove={() => {
          setFile(null);
          setReport(null);
        }}
      >
        <p className="ant-upload-drag-icon"><InboxOutlined /></p>
        <p>Перетащите файл сюда или нажмите, чтобы выбрать</p>
      </Upload.Dragger>
      {isIcs && <Input addonBefore="Группа" value={group} onChange={(e) => setGroup(e.target.value)} placeholder="ИВТ-21" style={{ maxWidth: 360 }} />}
      <Space>
        <Button onClick={() => send(true)} disabled={!file || (isIcs && !group)} loading={busy}>Проверить</Button>
        {report && !report.applied && (
          <Button type="primary" icon={<CheckOutlined />} disabled={report.lessons === 0} loading={busy}
            onClick={() => send(false, report.errors_total > 0)}>
            {report.errors_total > 0 ? 'Загрузить без ошибочных строк' : 'Загрузить'}
          </Button>
        )}
      </Space>
      {report && <ReportView report={report} />}
    </Space>
  );
}

function ReportView({ report }: { report: ImportReport }) {
  return (
    <Card size="small" title={report.applied ? 'Загружено' : 'Результат проверки'}>
      <Descriptions size="small" column={{ xs: 1, md: 3 }}>
        <Descriptions.Item label="Строк">{report.rows_total}</Descriptions.Item>
        <Descriptions.Item label="Разобрано">{report.rows_ok}</Descriptions.Item>
        <Descriptions.Item label="Занятий">{report.lessons}</Descriptions.Item>
        <Descriptions.Item label="Группы" span={3}>{report.groups.map((g) => <Tag key={g}>{g}</Tag>)}</Descriptions.Item>
        {report.sync && (
          <Descriptions.Item label="Изменения" span={3}>
            добавлено {report.sync.added}, изменено {report.sync.modified}, удалено {report.sync.removed}, без изменений {report.sync.unchanged}
            {report.sync.groups_created?.length ? `, новые группы: ${report.sync.groups_created.join(', ')}` : ''}
          </Descriptions.Item>
        )}
      </Descriptions>
      {report.errors_total > 0 && (
        <>
          <Alert type="warning" showIcon style={{ margin: '12px 0' }}
            title={`Ошибок: ${report.errors_total}${report.errors_total > report.errors.length ? `, показаны первые ${report.errors.length}` : ''}`} />
          <Table
            size="small" rowKey={(e) => `${e.row}-${e.column}-${e.message}`} dataSource={report.errors}
            pagination={{ pageSize: 20, showSizeChanger: false }}
            columns={[
              { title: 'Строка', dataIndex: 'row', width: 80 },
              { title: 'Столбец', dataIndex: 'column', width: 140 },
              { title: 'Что не так', dataIndex: 'message' },
            ]}
          />
        </>
      )}
    </Card>
  );
}

type SourceForm = { name: string; kind: string; config: string; enabled: boolean; require_review_on_spike: boolean };

function SourcesTab({ tenant }: { tenant: Tenant }) {
  const { message } = App.useApp();
  const canManage = useCanManage();
  const list = useLoad(() => api.get<Source[]>(`/tenants/${tenant.id}/schedule/sources`), [tenant.id]);
  const kinds = useLoad(() => api.get<string[]>('/schedule/adapters'), []);
  const [editing, setEditing] = useState<Source | 'new' | null>(null);
  const [syncing, setSyncing] = useState<string | null>(null);
  const [form] = Form.useForm<SourceForm>();
  const kind = Form.useWatch('kind', form);

  const open = (x: Source | 'new') => {
    setEditing(x);
    form.setFieldsValue(x === 'new'
      ? { name: '', kind: 'xlsx_url', config: SOURCE_HINTS.xlsx_url, enabled: true, require_review_on_spike: true }
      : { ...x, config: JSON.stringify(x.config, null, 2) });
  };
  const save = async (v: SourceForm) => {
    try {
      const body = { ...v, config: parseJson(v.config) };
      if (editing === 'new') await api.post(`/tenants/${tenant.id}/schedule/sources`, body);
      else if (editing) await api.patch(`/schedule/sources/${editing.id}`, body);
      setEditing(null);
      list.reload();
    } catch (e) {
      message.error(errorText(e));
    }
  };
  const sync = async (x: Source, force: boolean) => {
    setSyncing(x.id);
    try {
      const out = await api.post<Record<string, any>>(`/schedule/sources/${x.id}/sync?force=${force}`);
      if (out.status === 'queued') message.info('Синхронизация поставлена в очередь');
      else if (out.status === 'needs_review') message.warning(out.review_reason ?? 'Изменений слишком много, нужна проверка');
      else if (out.status === 'error') message.error('Источник вернул ошибку, подробности в таблице');
      else message.success(`Готово: добавлено ${out.added ?? 0}, изменено ${out.modified ?? 0}, удалено ${out.removed ?? 0}`);
      list.reload();
    } catch (e) {
      message.error(errorText(e));
    } finally {
      setSyncing(null);
    }
  };
  const remove = async (x: Source) => {
    try {
      await api.del(`/schedule/sources/${x.id}`);
      list.reload();
    } catch (e) {
      message.error(errorText(e));
    }
  };

  return (
    <>
      <Space style={{ marginBottom: 12 }}>
        {canManage && <Button type="primary" icon={<PlusOutlined />} onClick={() => open('new')}>Новый источник</Button>}
      </Space>
      <LoadError error={list.error} />
      <Table
        rowKey="id"
        loading={list.loading}
        dataSource={list.data?.filter((x) => x.kind !== 'manual')}
        pagination={false}
        expandable={{ rowExpandable: (x) => !!x.last_error, expandedRowRender: (x) => <Typography.Text type="danger">{x.last_error}</Typography.Text> }}
        columns={[
          { title: 'Название', dataIndex: 'name' },
          { title: 'Тип', dataIndex: 'kind', render: (v) => <Tag>{v}</Tag> },
          { title: 'Включён', dataIndex: 'enabled', render: (v) => (v ? 'да' : <Tag>нет</Tag>) },
          { title: 'Статус', dataIndex: 'last_status', render: (v, x) => <Space><SyncStatusTag value={v} />{x.has_pending && <Tag color="orange">есть непринятые изменения</Tag>}</Space> },
          { title: 'Последний раз', dataIndex: 'last_sync_at', render: (v) => fmt(v, tenant.timezone) },
          { title: 'Занятий', dataIndex: 'last_count' },
          {
            title: '', width: 200, render: (_, x) => (
              <Space>
                <Button size="small" icon={<SyncOutlined spin={syncing === x.id} />} onClick={() => sync(x, false)}>Сейчас</Button>
                {x.has_pending && canManage && (
                  <Popconfirm title="Принять изменения, несмотря на резкий скачок числа занятий?" onConfirm={() => sync(x, true)}>
                    <Button size="small" type="primary" icon={<CheckOutlined />} />
                  </Popconfirm>
                )}
                {canManage && <Button size="small" icon={<EditOutlined />} onClick={() => open(x)} />}
                {canManage && (
                  <Popconfirm title="Удалить источник? Его будущие занятия удалятся." onConfirm={() => remove(x)}>
                    <Button size="small" danger icon={<DeleteOutlined />} />
                  </Popconfirm>
                )}
              </Space>
            ),
          },
        ]}
      />
      <Modal title="Источник расписания" open={editing !== null} onCancel={() => setEditing(null)} onOk={() => form.submit()} okText="Сохранить" forceRender width={640}>
        <Form form={form} layout="vertical" onFinish={save}>
          <Form.Item name="name" label="Название" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="kind" label="Тип" rules={[{ required: true }]}>
            <Select
              options={(kinds.data ?? []).filter((k) => k !== 'manual').map((k) => ({ value: k, label: k }))}
              onChange={(k: string) => editing === 'new' && form.setFieldValue('config', SOURCE_HINTS[k] ?? '{}')}
            />
          </Form.Item>
          <Form.Item name="config" label="Настройки (JSON)" rules={[jsonRule]} extra={kind && SOURCE_HINTS[kind] ? `Пример: ${SOURCE_HINTS[kind]}` : undefined}>
            <JsonInput rows={8} />
          </Form.Item>
          <Form.Item name="enabled" label="Синхронизировать автоматически" valuePropName="checked"><Switch /></Form.Item>
          <Form.Item name="require_review_on_spike" label="Останавливаться при резком изменении числа занятий" valuePropName="checked"><Switch /></Form.Item>
        </Form>
      </Modal>
    </>
  );
}

type LessonForm = {
  subject: string; kind: string; date: Dayjs; start: Dayjs; end: Dayjs; room?: string; note?: string;
  subgroup?: string; status: 'scheduled' | 'cancelled';
};

function LessonsTab({ tenant }: { tenant: Tenant }) {
  const { message } = App.useApp();
  const tz = tenant.timezone;
  const groups = useLoad(() => api.get<Group[]>(`/tenants/${tenant.id}/groups`), [tenant.id]);
  const [groupId, setGroupId] = useState<string | undefined>();
  const [range, setRange] = useState<[Dayjs, Dayjs]>(() => [dayjs().startOf('week'), dayjs().startOf('week').add(13, 'day')]);
  const [editing, setEditing] = useState<Lesson | 'new' | null>(null);
  const [form] = Form.useForm<LessonForm>();
  const from = range[0].format('YYYY-MM-DD');
  const to = range[1].format('YYYY-MM-DD');
  const lessons = useLoad(
    () => (groupId ? api.get<Lesson[]>(`/tenants/${tenant.id}/lessons?group_id=${groupId}&from=${from}&to=${to}`) : Promise.resolve([])),
    [tenant.id, groupId, from, to],
  );
  const group = groups.data?.find((g) => g.id === groupId);

  const open = (x: Lesson | 'new') => {
    setEditing(x);
    if (x === 'new') {
      form.setFieldsValue({ subject: '', kind: 'lecture', date: range[0], start: undefined, end: undefined, room: '', note: '', subgroup: undefined, status: 'scheduled' });
    } else {
      const s = toWall(x.starts_at, tz);
      form.setFieldsValue({ subject: x.subject, kind: x.kind, date: s, start: s, end: toWall(x.ends_at, tz), room: x.room ?? '',
        note: x.note ?? '', subgroup: x.subgroup ?? undefined, status: x.status });
    }
  };
  const save = async (v: LessonForm) => {
    const at = (t: Dayjs) => fromWall(v.date.hour(t.hour()).minute(t.minute()).second(0), tz);
    const body = {
      group_id: groupId, subject: v.subject, kind: v.kind, starts_at: at(v.start), ends_at: at(v.end),
      room: v.room || null, note: v.note || null, subgroup: v.subgroup || null, status: v.status,
    };
    try {
      if (editing === 'new') await api.post(`/tenants/${tenant.id}/lessons`, body);
      else if (editing) await api.patch(`/lessons/${editing.id}`, body);
      setEditing(null);
      lessons.reload();
    } catch (e) {
      message.error(errorText(e));
    }
  };
  const remove = async (x: Lesson) => {
    try {
      await api.del(`/lessons/${x.id}`);
      lessons.reload();
    } catch (e) {
      message.error(errorText(e));
    }
  };

  return (
    <>
      <Space wrap style={{ marginBottom: 12 }}>
        <Select
          showSearch optionFilterProp="label" placeholder="Группа" style={{ width: 220 }} value={groupId} onChange={setGroupId}
          options={(groups.data ?? []).map((g) => ({ value: g.id, label: g.code }))}
        />
        <DatePicker.RangePicker format="DD.MM.YYYY" value={range} allowClear={false} onChange={(v) => v?.[0] && v[1] && setRange([v[0], v[1]])} />
        <Button icon={<PlusOutlined />} disabled={!groupId} onClick={() => open('new')}>Добавить занятие</Button>
      </Space>
      <Typography.Paragraph type="secondary">
        Время показано по часовому поясу вуза ({tz}). Изменения сегодняшних и будущих занятий попадут в уведомления студентам.
      </Typography.Paragraph>
      <LoadError error={lessons.error ?? groups.error} />
      <Table
        rowKey="id"
        size="small"
        loading={lessons.loading}
        dataSource={lessons.data}
        pagination={{ pageSize: 100, showSizeChanger: false }}
        locale={{ emptyText: groupId ? 'Занятий в этом диапазоне нет' : 'Выберите группу' }}
        columns={[
          { title: 'День', dataIndex: 'starts_at', render: (v) => fmt(v, tz, 'dd DD.MM') },
          { title: 'Время', render: (_, x) => `${fmt(x.starts_at, tz, 'HH:mm')}-${fmt(x.ends_at, tz, 'HH:mm')}` },
          { title: 'Дисциплина', dataIndex: 'subject', render: (v, x) => (x.status === 'cancelled' ? <Typography.Text delete>{v}</Typography.Text> : v) },
          { title: 'Тип', dataIndex: 'kind', render: (v) => kindLabel[v] ?? v },
          { title: 'Аудитория', dataIndex: 'room' },
          { title: 'Подгруппа', dataIndex: 'subgroup' },
          { title: 'Примечание', dataIndex: 'note', ellipsis: true },
          { title: '', dataIndex: 'source_id', width: 40, render: (_, x) => x.status === 'cancelled' && <Tag color="red">отмена</Tag> },
          {
            title: '', width: 90, render: (_, x) => (
              <Space>
                <Button size="small" icon={<EditOutlined />} onClick={() => open(x)} />
                <Popconfirm title="Удалить занятие?" onConfirm={() => remove(x)}>
                  <Button size="small" danger icon={<DeleteOutlined />} />
                </Popconfirm>
              </Space>
            ),
          },
        ]}
      />
      <Modal title={editing === 'new' ? 'Новое занятие' : 'Занятие'} open={editing !== null} onCancel={() => setEditing(null)} onOk={() => form.submit()} okText="Сохранить" forceRender>
        <Form form={form} layout="vertical" onFinish={save}>
          <Form.Item name="subject" label="Дисциплина" rules={[{ required: true }]}><Input /></Form.Item>
          <Space wrap>
            <Form.Item name="kind" label="Тип"><Select style={{ width: 170 }} options={KINDS.map(([value, label]) => ({ value, label }))} /></Form.Item>
            <Form.Item name="date" label="Дата" rules={[{ required: true }]}><DatePicker format="DD.MM.YYYY" /></Form.Item>
            <Form.Item name="start" label="Начало" rules={[{ required: true }]}><DatePicker.TimePicker format="HH:mm" minuteStep={5} /></Form.Item>
            <Form.Item
              name="end" label="Конец" dependencies={['start']}
              rules={[{ required: true }, ({ getFieldValue }) => ({
                validator: async (_, v?: Dayjs) => {
                  const s: Dayjs | undefined = getFieldValue('start');
                  if (v && s && v.hour() * 60 + v.minute() <= s.hour() * 60 + s.minute()) throw new Error('конец раньше начала');
                },
              })]}
            >
              <DatePicker.TimePicker format="HH:mm" minuteStep={5} />
            </Form.Item>
          </Space>
          <Space wrap>
            <Form.Item name="room" label="Аудитория"><Input style={{ width: 140 }} /></Form.Item>
            <Form.Item name="subgroup" label="Подгруппа">
              <Select allowClear style={{ width: 140 }} options={(group?.subgroups ?? []).map((s) => ({ value: s, label: s }))} />
            </Form.Item>
            <Form.Item name="status" label="Состояние">
              <Radio.Group options={[{ value: 'scheduled', label: 'идёт' }, { value: 'cancelled', label: 'отменено' }]} />
            </Form.Item>
          </Space>
          <Form.Item name="note" label="Примечание"><Input.TextArea rows={2} maxLength={500} /></Form.Item>
        </Form>
      </Modal>
    </>
  );
}
