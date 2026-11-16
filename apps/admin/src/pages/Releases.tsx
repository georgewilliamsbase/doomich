import { PlusOutlined } from '@ant-design/icons';
import { App, Button, Form, Input, InputNumber, Modal, Radio, Select, Space, Table, Tag, Typography } from 'antd';
import { useState } from 'react';

import { api, errorText, Release } from '../api';
import { LoadError, PageTitle } from '../components';
import { useLoad } from '../hooks';
import { fmt } from '../time';

const PLATFORMS = ['android', 'windows', 'linux-deb', 'linux-rpm', 'linux-appimage'];

type ReleaseForm = Omit<Release, 'id' | 'published_at'> & { signature?: string; notes_ru?: string; notes_en?: string };

export default function ReleasesPage() {
  const { message } = App.useApp();
  const [open, setOpen] = useState(false);
  const [form] = Form.useForm<ReleaseForm>();
  const list = useLoad(() => api.get<Release[]>('/releases'), []);
  const create = async (v: ReleaseForm) => {
    try {
      await api.post('/releases', v);
      setOpen(false);
      form.resetFields();
      list.reload();
    } catch (e) {
      message.error(errorText(e));
    }
  };
  return (
    <>
      <PageTitle title="Релизы приложений" extra={<Button type="primary" icon={<PlusOutlined />} onClick={() => setOpen(true)}>Опубликовать</Button>} />
      <Typography.Paragraph type="secondary">
        Приложения сверяются с этим списком и предлагают обновиться. Сборку и контрольную сумму готовит конвейер CI,
        файл должен лежать по указанной ссылке. Если сборка ниже минимальной, приложение попросит обновиться обязательно.
      </Typography.Paragraph>
      <LoadError error={list.error} />
      <Table
        rowKey="id"
        size="small"
        loading={list.loading}
        dataSource={list.data}
        pagination={{ pageSize: 50, showSizeChanger: false }}
        columns={[
          { title: 'Приложение', dataIndex: 'app', render: (v) => (v === 'mobile' ? 'телефон' : 'компьютер') },
          { title: 'Платформа', dataIndex: 'platform' },
          { title: 'Канал', dataIndex: 'channel', render: (v) => <Tag color={v === 'beta' ? 'gold' : 'green'}>{v}</Tag> },
          { title: 'Версия', render: (_, r) => `${r.version} (${r.build})` },
          { title: 'Минимальная', dataIndex: 'min_supported_build' },
          { title: 'Файл', dataIndex: 'url', ellipsis: true, render: (v) => <a href={v}>{v}</a> },
          { title: 'Опубликован', dataIndex: 'published_at', render: (v) => fmt(v, 'Europe/Moscow') },
        ]}
      />
      <Modal title="Новый релиз" open={open} onCancel={() => setOpen(false)} onOk={() => form.submit()} okText="Опубликовать" forceRender width={640}>
        <Form form={form} layout="vertical" onFinish={create} initialValues={{ app: 'mobile', platform: 'android', channel: 'stable', min_supported_build: 0 }}>
          <Space size={16} wrap>
            <Form.Item name="app" label="Приложение">
              <Radio.Group options={[{ value: 'mobile', label: 'телефон' }, { value: 'desktop', label: 'компьютер' }]} />
            </Form.Item>
            <Form.Item name="platform" label="Платформа"><Select style={{ width: 180 }} options={PLATFORMS.map((p) => ({ value: p, label: p }))} /></Form.Item>
            <Form.Item name="channel" label="Канал">
              <Radio.Group options={[{ value: 'stable', label: 'stable' }, { value: 'beta', label: 'beta' }]} />
            </Form.Item>
          </Space>
          <Space size={16} wrap>
            <Form.Item name="version" label="Версия" rules={[{ required: true, pattern: /^\d+\.\d+\.\d+$/, message: 'вида 1.2.3' }]}><Input style={{ width: 120 }} /></Form.Item>
            <Form.Item name="build" label="Сборка" rules={[{ required: true }]}><InputNumber min={1} /></Form.Item>
            <Form.Item name="min_supported_build" label="Минимальная сборка"><InputNumber min={0} /></Form.Item>
          </Space>
          <Form.Item name="url" label="Ссылка на файл" rules={[{ required: true, type: 'url' }]}><Input /></Form.Item>
          <Form.Item name="sha256" label="SHA-256" rules={[{ required: true, pattern: /^[0-9a-f]{64}$/, message: '64 шестнадцатеричных символа' }]}>
            <Input style={{ fontFamily: 'monospace' }} />
          </Form.Item>
          <Form.Item name="signature" label="Подпись (minisign, необязательно)"><Input /></Form.Item>
          <Form.Item name="notes_ru" label="Что нового"><Input.TextArea rows={3} maxLength={4000} /></Form.Item>
          <Form.Item name="notes_en" label="What's new"><Input.TextArea rows={2} maxLength={4000} /></Form.Item>
        </Form>
      </Modal>
    </>
  );
}
