import { Alert, Button, Card, Form, Input, QRCode, Space, Typography } from 'antd';
import { useState } from 'react';

import { api, errorText } from '../api';

type LoginOut = {
  token?: string;
  totp_setup_required?: boolean;
  setup_token?: string;
  otpauth_uri?: string;
  secret?: string;
};

export default function LoginPage({ onToken }: { onToken: (token: string) => Promise<void> }) {
  const [error, setError] = useState<string | null>(null);
  const [needTotp, setNeedTotp] = useState(false);
  const [setup, setSetup] = useState<LoginOut | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (v: { login: string; password: string; totp?: string }) => {
    setBusy(true);
    setError(null);
    try {
      const out = await api.post<LoginOut>('/auth/login', { login: v.login, password: v.password, totp: v.totp || undefined });
      if (out.totp_setup_required) setSetup(out);
      else if (out.token) await onToken(out.token);
    } catch (e: any) {
      if (e?.code === 'totp_required') setNeedTotp(true);
      setError(errorText(e));
    } finally {
      setBusy(false);
    }
  };

  const confirm = async (v: { code: string }) => {
    setBusy(true);
    try {
      const out = await api.post<LoginOut>('/auth/totp/confirm', { setup_token: setup?.setup_token, code: v.code });
      if (out.token) await onToken(out.token);
    } catch (e) {
      setError(errorText(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={{ display: 'grid', placeItems: 'center', minHeight: '100vh', padding: 16 }}>
      <Card style={{ width: 400, maxWidth: '100%' }} title="Думыч: вход для администраторов">
        {error && <Alert type="error" title={error} style={{ marginBottom: 16 }} showIcon />}
        {setup ? (
          <Space orientation="vertical" style={{ width: '100%' }}>
            <Typography.Paragraph>
              Для входа нужен второй фактор. Отсканируйте код в приложении-аутентификаторе и введите шесть цифр.
            </Typography.Paragraph>
            <QRCode value={setup.otpauth_uri ?? ''} />
            <Typography.Text copyable code>{setup.secret}</Typography.Text>
            <Form layout="vertical" onFinish={confirm}>
              <Form.Item name="code" label="Код" rules={[{ required: true, len: 6 }]}>
                <Input inputMode="numeric" autoComplete="one-time-code" />
              </Form.Item>
              <Button type="primary" htmlType="submit" loading={busy} block>Подтвердить</Button>
            </Form>
          </Space>
        ) : (
          <Form layout="vertical" onFinish={submit}>
            <Form.Item name="login" label="Логин" rules={[{ required: true }]}>
              <Input autoFocus autoComplete="username" />
            </Form.Item>
            <Form.Item name="password" label="Пароль" rules={[{ required: true }]}>
              <Input.Password autoComplete="current-password" />
            </Form.Item>
            {needTotp && (
              <Form.Item name="totp" label="Код из приложения-аутентификатора" rules={[{ required: true, len: 6 }]}>
                <Input inputMode="numeric" autoComplete="one-time-code" />
              </Form.Item>
            )}
            <Button type="primary" htmlType="submit" loading={busy} block>Войти</Button>
          </Form>
        )}
      </Card>
    </div>
  );
}
