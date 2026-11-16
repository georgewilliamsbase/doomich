import dayjs, { Dayjs } from 'dayjs';
import timezone from 'dayjs/plugin/timezone';
import utc from 'dayjs/plugin/utc';

dayjs.extend(utc);
dayjs.extend(timezone);

/** Момент времени в часовом поясе вуза, например "12.02 08:30". */
export function fmt(iso: string | null | undefined, tz: string, pattern = 'DD.MM.YYYY HH:mm'): string {
  if (!iso) return '';
  return dayjs(iso).tz(tz).format(pattern);
}

/**
 * Пикеры antd работают в часовом поясе браузера. Чтобы администратор видел время вуза,
 * переводим момент в "настенное" время вуза и обратно.
 */
export function toWall(iso: string, tz: string): Dayjs {
  return dayjs(dayjs(iso).tz(tz).format('YYYY-MM-DDTHH:mm:ss'));
}

export function fromWall(wall: Dayjs, tz: string): string {
  return dayjs.tz(wall.format('YYYY-MM-DDTHH:mm:ss'), tz).toISOString();
}

export function fmtBytes(n: number | undefined): string {
  if (n === undefined) return '';
  const units = ['Б', 'КБ', 'МБ', 'ГБ', 'ТБ'];
  let v = n;
  let i = 0;
  while (v >= 1024 && i < units.length - 1) {
    v /= 1024;
    i += 1;
  }
  return `${v.toFixed(i ? 1 : 0)} ${units[i]}`;
}
