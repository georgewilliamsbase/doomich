import dayjs from 'dayjs';
import { describe, expect, it } from 'vitest';

import { fmt, fmtBytes, fromWall, toWall } from './time';

describe('время вуза', () => {
  it('показывает момент в часовом поясе вуза', () => {
    expect(fmt('2027-02-10T05:30:00Z', 'Europe/Moscow', 'HH:mm')).toBe('08:30');
    expect(fmt('2027-02-10T05:30:00Z', 'Asia/Vladivostok', 'HH:mm')).toBe('15:30');
  });

  it('настенное время туда и обратно', () => {
    const iso = '2027-02-10T05:30:00.000Z';
    const wall = toWall(iso, 'Asia/Novosibirsk');
    expect(wall.format('HH:mm')).toBe('12:30');
    expect(fromWall(wall, 'Asia/Novosibirsk')).toBe(iso);
  });

  it('новое занятие получает время вуза, а не браузера', () => {
    const picked = dayjs('2027-03-01T10:10:00');
    expect(fromWall(picked, 'Europe/Moscow')).toBe('2027-03-01T07:10:00.000Z');
  });

  it('размер файла', () => {
    expect(fmtBytes(512)).toBe('512 Б');
    expect(fmtBytes(5 * 1024 * 1024)).toBe('5.0 МБ');
  });
});
