import { DislikeTwoTone, LikeTwoTone } from '@ant-design/icons';
import { Radio, Space, Table, Tag, Typography } from 'antd';
import { useState } from 'react';

import { api, FeedbackItem } from '../api';
import { LoadError, NoTenant, PageTitle } from '../components';
import { useLoad } from '../hooks';
import { useTenant } from '../session';

const CATEGORY: Record<string, string> = {
  wrong: 'неверно', no_source: 'нет источника', voice: 'плохо с голосом', slow: 'долго', other: 'другое',
};

export default function FeedbackPage() {
  const tenant = useTenant();
  // 0 значит все оценки
  const [rating, setRating] = useState(-1);
  const list = useLoad(
    () => (tenant ? api.get<FeedbackItem[]>(`/tenants/${tenant.id}/feedback?limit=500${rating === 0 ? '' : `&rating=${rating}`}`) : Promise.resolve([])),
    [tenant?.id, rating],
  );
  if (!tenant) return <NoTenant />;
  return (
    <>
      <PageTitle
        title="Оценки ответов"
        extra={
          <Radio.Group
            value={rating}
            onChange={(e) => setRating(e.target.value)}
            optionType="button"
            options={[{ value: -1, label: 'Неудачные' }, { value: 1, label: 'Полезные' }, { value: 0, label: 'Все' }]}
          />
        }
      />
      <Typography.Paragraph type="secondary">
        Текст вопроса и ответа есть только там, где пользователь сам разрешил его приложить к оценке.
        Логинов здесь нет: оценки обезличены.
      </Typography.Paragraph>
      <LoadError error={list.error} />
      <Table
        rowKey="id"
        loading={list.loading}
        dataSource={list.data}
        pagination={{ pageSize: 50, showSizeChanger: false }}
        expandable={{
          rowExpandable: (f) => !!(f.question || f.answer),
          expandedRowRender: (f) => (
            <Space orientation="vertical" style={{ width: '100%' }}>
              {f.question && <><Typography.Text strong>Вопрос</Typography.Text><Typography.Paragraph style={{ whiteSpace: 'pre-wrap' }}>{f.question}</Typography.Paragraph></>}
              {f.answer && <><Typography.Text strong>Ответ</Typography.Text><Typography.Paragraph style={{ whiteSpace: 'pre-wrap' }}>{f.answer}</Typography.Paragraph></>}
            </Space>
          ),
        }}
        columns={[
          { title: '', dataIndex: 'rating', width: 48, render: (v) => (v > 0 ? <LikeTwoTone twoToneColor="#52c41a" /> : <DislikeTwoTone twoToneColor="#ff4d4f" />) },
          { title: 'Дата', dataIndex: 'created_on', width: 110 },
          { title: 'Причина', dataIndex: 'category', width: 140, render: (v) => v && <Tag>{CATEGORY[v] ?? v}</Tag> },
          { title: 'Комментарий', dataIndex: 'comment' },
          { title: 'Режим', dataIndex: 'mode', width: 90, render: (v) => (v === 'voice' ? 'голос' : v === 'text' ? 'текст' : v) },
          { title: 'Модель', dataIndex: 'model_version', width: 200, ellipsis: true },
        ]}
      />
    </>
  );
}
