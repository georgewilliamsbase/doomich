import { Alert, Input, Space, Tag, Typography } from 'antd';
import type { ReactNode } from 'react';

export function NoTenant() {
  return <Typography.Paragraph type="secondary">Сначала создайте вуз в разделе "Вуз и кампусы".</Typography.Paragraph>;
}

export function PageTitle({ title, extra }: { title: string; extra?: ReactNode }) {
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
      <Typography.Title level={3} style={{ margin: 0 }}>{title}</Typography.Title>
      {extra && <Space wrap>{extra}</Space>}
    </div>
  );
}

export function LoadError({ error }: { error?: string }) {
  return error ? <Alert type="error" showIcon title={error} style={{ marginBottom: 16 }} /> : null;
}

/** Поле формы для JSON: хранит текст, проверка в rules через jsonRule. */
export function JsonInput(props: { value?: string; onChange?: (v: string) => void; rows?: number }) {
  return (
    <Input.TextArea
      value={props.value}
      onChange={(e) => props.onChange?.(e.target.value)}
      rows={props.rows ?? 6}
      style={{ fontFamily: 'monospace' }}
      spellCheck={false}
    />
  );
}

export const jsonRule = {
  validator: async (_: unknown, v: string | undefined) => {
    if (!v || !v.trim()) return;
    const parsed = JSON.parse(v);
    if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) throw new Error('нужен объект JSON');
  },
  message: 'нужен корректный объект JSON',
};

export function parseJson(v: string | undefined): Record<string, any> {
  return v && v.trim() ? JSON.parse(v) : {};
}

export const roleLabels: Record<string, string> = { student: 'студент', teacher: 'преподаватель', staff: 'сотрудник' };

const syncStatus: Record<string, { color: string; text: string }> = {
  ok: { color: 'green', text: 'в порядке' },
  error: { color: 'red', text: 'ошибка' },
  needs_review: { color: 'orange', text: 'ждёт проверки' },
};

export function SyncStatusTag({ value }: { value: string | null }) {
  const s = value ? syncStatus[value] : undefined;
  return <Tag color={s?.color}>{s?.text ?? value ?? 'не запускался'}</Tag>;
}
