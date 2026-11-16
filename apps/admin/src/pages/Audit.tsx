import { Table, Tag, Typography } from 'antd';

import { api, AuditItem } from '../api';
import { LoadError, PageTitle } from '../components';
import { useLoad } from '../hooks';
import { useSession, useTenant } from '../session';
import { fmt } from '../time';

export default function AuditPage() {
  const tenant = useTenant();
  const { tenants } = useSession();
  const tz = tenant?.timezone ?? 'Europe/Moscow';
  const list = useLoad(
    () => api.get<AuditItem[]>(`/audit?limit=1000${tenant ? `&tenant_id=${tenant.id}` : ''}`),
    [tenant?.id],
  );
  const tenantName = (id: string | null) => (id ? tenants.find((t) => t.id === id)?.slug ?? id.slice(0, 8) : 'общее');
  return (
    <>
      <PageTitle title="Журнал действий" />
      <Typography.Paragraph type="secondary">
        Здесь записаны действия администраторов: выпуск кодов, правки расписания, смена настроек. Записи нельзя изменить.
      </Typography.Paragraph>
      <LoadError error={list.error} />
      <Table
        rowKey="id"
        size="small"
        loading={list.loading}
        dataSource={list.data}
        pagination={{ pageSize: 100, showSizeChanger: false }}
        columns={[
          { title: 'Когда', dataIndex: 'created_at', width: 160, render: (v) => fmt(v, tz) },
          { title: 'Кто', dataIndex: 'admin', width: 140 },
          { title: 'Действие', dataIndex: 'action', render: (v) => <Tag>{v}</Tag> },
          { title: 'Объект', render: (_, a) => (a.object_type ? `${a.object_type} ${a.object_id?.slice(0, 8) ?? ''}` : '') },
          { title: 'Вуз', dataIndex: 'tenant_id', width: 120, render: tenantName },
          {
            title: 'Подробности', dataIndex: 'details', ellipsis: true,
            render: (v) => v && Object.keys(v).length ? <Typography.Text code>{JSON.stringify(v)}</Typography.Text> : null,
          },
        ]}
      />
    </>
  );
}
