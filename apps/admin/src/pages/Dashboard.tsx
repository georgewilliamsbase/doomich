import { CheckCircleTwoTone, CloseCircleTwoTone, ReloadOutlined } from '@ant-design/icons';
import { Button, Card, Col, Descriptions, Empty, Row, Statistic, Table, Tag, Typography } from 'antd';

import { api, Stats, Status } from '../api';
import { LoadError, PageTitle, SyncStatusTag } from '../components';
import { useLoad } from '../hooks';
import { useTenant } from '../session';
import { fmt, fmtBytes } from '../time';

const pct = (v: number | null | undefined) => (v === null || v === undefined ? 'нет данных' : `${Math.round(v * 100)}%`);
const Note = ({ children }: { children: string }) => <Typography.Text type="secondary" style={{ fontSize: 14 }}>{children}</Typography.Text>;

function Ok({ ok }: { ok: boolean | null | undefined }) {
  if (ok === null || ok === undefined) return <Tag>неизвестно</Tag>;
  return ok ? <CheckCircleTwoTone twoToneColor="#52c41a" /> : <CloseCircleTwoTone twoToneColor="#ff4d4f" />;
}

export default function DashboardPage() {
  const tenant = useTenant();
  const tz = tenant?.timezone ?? 'Europe/Moscow';
  const status = useLoad(() => api.get<Status>('/status'), []);
  const stats = useLoad(() => (tenant ? api.get<Stats>(`/tenants/${tenant.id}/stats`) : Promise.resolve(undefined)), [tenant?.id]);
  const st = status.data;
  const s = stats.data;

  return (
    <>
      <PageTitle
        title="Состояние"
        extra={[
          st?.grafana_url && <Button key="g" href={st.grafana_url} target="_blank">Графики (Grafana)</Button>,
          <Button key="r" icon={<ReloadOutlined />} onClick={() => { status.reload(); stats.reload(); }}>Обновить</Button>,
        ]}
      />
      <LoadError error={status.error ?? stats.error} />
      {s && (
        <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
          <Col xs={12} md={6}><Card><Statistic title="Пользователей" value={s.users} /></Card></Col>
          <Col xs={12} md={6}><Card><Statistic title="Активны сегодня" value={s.dau} /></Card></Col>
          <Col xs={12} md={6}><Card><Statistic title="Активны за неделю" value={s.wau} suffix={<Note>{`${pct(s.wau_share)} от всех`}</Note>} /></Card></Col>
          <Col xs={12} md={6}><Card><Statistic title="Документов" value={s.documents} suffix={<Note>{`загружали ${pct(s.users_with_documents_share)}`}</Note>} /></Card></Col>
          <Col xs={12} md={6}><Card><Statistic title="Вопросов за 7 дней" value={Object.values(s.messages_7d).reduce((a, b) => a + b, 0)} /></Card></Col>
          <Col xs={12} md={6}><Card><Statistic title="Доля голосовых" value={pct(s.voice_share_7d)} /></Card></Col>
          <Col xs={12} md={6}><Card><Statistic title="Полезных ответов (30 дней)" value={pct(s.feedback_30d.up_share)} /></Card></Col>
          <Col xs={12} md={6}><Card><Statistic title="Оценок 👍 / 👎" value={`${s.feedback_30d.up} / ${s.feedback_30d.down}`} /></Card></Col>
        </Row>
      )}
      {st && (
        <Row gutter={[16, 16]}>
          <Col xs={24} lg={12}>
            <Card title="Сервисы">
              <Descriptions column={1} size="small">
                <Descriptions.Item label="Окружение"><Tag color={st.env === 'prod' ? 'red' : 'blue'}>{st.env}</Tag></Descriptions.Item>
                <Descriptions.Item label="Языковая модель"><Ok ok={st.llm_ok} /></Descriptions.Item>
                <Descriptions.Item label="Заглушки вместо моделей">
                  {st.mock_components.length ? st.mock_components.map((m) => <Tag key={m} color="orange">{m}</Tag>) : 'нет'}
                </Descriptions.Item>
                <Descriptions.Item label="Очереди задач">
                  {Object.keys(st.queues).length
                    ? Object.entries(st.queues).map(([q, n]) => <Tag key={q}>{q}: {n ?? '?'}</Tag>)
                    : 'брокер в памяти'}
                </Descriptions.Item>
                <Descriptions.Item label="Документы">
                  {Object.keys(st.documents).length
                    ? Object.entries(st.documents).map(([k, n]) => <Tag key={k} color={k === 'failed' ? 'red' : undefined}>{k}: {n}</Tag>)
                    : 'пока нет'}
                </Descriptions.Item>
              </Descriptions>
            </Card>
          </Col>
          <Col xs={24} lg={12}>
            <Card title="Резервные копии">
              {st.backup ? (
                <Descriptions column={1} size="small">
                  <Descriptions.Item label="Последняя копия"><Ok ok={st.backup.ok} /> {fmt(st.backup.finished_at, tz)}</Descriptions.Item>
                  {st.backup.snapshot && <Descriptions.Item label="Снимок">{st.backup.snapshot}</Descriptions.Item>}
                  {st.backup.size_bytes !== undefined && <Descriptions.Item label="Размер">{fmtBytes(st.backup.size_bytes)}</Descriptions.Item>}
                  {(st.backup.message || st.backup.error) && (
                    <Descriptions.Item label="Сообщение"><Typography.Text type="danger">{st.backup.message ?? st.backup.error}</Typography.Text></Descriptions.Item>
                  )}
                </Descriptions>
              ) : (
                <Empty description="Сведений о копиях нет. Проверьте таймер doomich-backup на сервере." />
              )}
            </Card>
          </Col>
          <Col span={24}>
            <Card title="Источники расписания">
              <Table
                size="small"
                rowKey="id"
                pagination={false}
                dataSource={st.schedule_sources}
                locale={{ emptyText: 'Автоматических источников нет' }}
                columns={[
                  { title: 'Название', dataIndex: 'name' },
                  { title: 'Тип', dataIndex: 'kind' },
                  { title: 'Статус', dataIndex: 'last_status', render: (v) => <SyncStatusTag value={v} /> },
                  { title: 'Синхронизация', dataIndex: 'last_sync_at', render: (v) => fmt(v, tz) },
                  { title: 'Ошибка', dataIndex: 'last_error', ellipsis: true },
                ]}
              />
            </Card>
          </Col>
        </Row>
      )}
    </>
  );
}
